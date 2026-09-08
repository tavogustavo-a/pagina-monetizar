"""Extractor: reparte los videos de un servidor origen hacia los demás vinculados.

Funciona por ciclos: cada `interval_minutes` publica hasta `effective_batch`
videos (con descanso opcional entre videos). El lote se auto-ajusta según la
carga del servidor (memoria / lentitud) y vuelve a subir cuando se estabiliza.
Los servidores destino que dejan de aceptar publicaciones se pausan y se
reintentan automáticamente más tarde.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
import i18n
import platform_publish
import platforms

# Frecuencia del worker (main.py) y tope de publicaciones por pasada.
# El tick corre en un hilo aparte: un servidor holgado puede trabajar más por ciclo.
WORKER_TICK_SECONDS = 180
MAX_PUBLISH_PER_TICK = 20
MAX_TICK_SECONDS = 45.0

# Umbrales de auto-ajuste.
MEMORY_HIGH_PERCENT = 85.0
MEMORY_CRITICAL_PERCENT = 92.0
SLOW_PUBLISH_SECONDS = 1.5
GOOD_CYCLES_TO_RAISE = 2
POSTPONE_SECONDS = 60

# Servidores destino caídos: cuántos fallos seguidos los pausan y cada cuánto
# se reintenta.
FAILS_TO_DISABLE = 3
DISABLED_RETRY_MINUTES = 15

# Cada servidor acepta un número distinto de subidas por ciclo.
_CYCLE_CAP_FULL = 6
_CYCLE_CAP_LIMITED = 2

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

MIN_BATCH = 1
MAX_BATCH = 50
MIN_INTERVAL_MINUTES = 1
MAX_INTERVAL_MINUTES = 24 * 60
MIN_REST_SECONDS = 0
MAX_REST_SECONDS = 3600


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_iso(raw: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def memory_usage_percent() -> float | None:
    """Porcentaje de memoria usada del servidor (None si no se puede medir)."""
    try:
        import psutil  # type: ignore

        return float(psutil.virtual_memory().percent)
    except Exception:
        pass
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return float(stat.dwMemoryLoad)
    except Exception:
        pass
    try:
        total = avail = None
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    total = float(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    avail = float(line.split()[1])
                if total is not None and avail is not None:
                    break
        if total and avail is not None:
            return max(0.0, min(100.0, (1.0 - avail / total) * 100.0))
    except Exception:
        pass
    return None


def platform_cycle_cap(platform_id: str) -> int:
    """Cuántas subidas por ciclo acepta un servidor según sus capacidades."""
    p = platforms.get_platform(platform_id)
    if not p:
        return MIN_BATCH
    return _CYCLE_CAP_FULL if str(p.get("video")) == "yes" else _CYCLE_CAP_LIMITED


def _platform_name(platform_id: str, lang: str) -> str:
    return i18n.t(f"platform.{platform_id}", lang)


def _content_type_for(video: db.Video) -> str:
    return "photo" if Path(video.file_name).suffix.lower() in PHOTO_EXTS else "video"


def _target_state(state: dict[str, Any], pid: str) -> dict[str, Any]:
    entry = state.get(pid)
    if not isinstance(entry, dict):
        entry = {}
        state[pid] = entry
    entry.setdefault("fails", 0)
    entry.setdefault("disabled", False)
    entry.setdefault("disabled_at", "")
    entry.setdefault("paused", False)
    entry.setdefault("probing", False)
    entry.setdefault("last_error", "")
    entry.setdefault("cycle_sent", 0)
    return entry


def _is_blocked(entry: dict[str, Any]) -> bool:
    return bool(entry.get("paused") or entry.get("disabled"))


def set_target_paused(job_id: str, platform_id: str, *, paused: bool, lang: str) -> dict[str, Any] | None:
    """Pausa o reanuda un servidor destino de una extracción (sin tocar los demás)."""
    job = db.get_extractor_job(job_id)
    if not job:
        return None
    targets = list(job.get("target_platform_ids") or [])
    pid = str(platform_id or "").strip()
    if pid not in targets:
        return None
    if job["status"] == "done":
        return job

    state: dict[str, Any] = dict(job.get("platform_state") or {})
    entry = _target_state(state, pid)
    if bool(entry.get("paused")) == paused:
        return job

    entry["paused"] = paused
    entry["probing"] = False
    if paused:
        db.add_extractor_event(
            job["id"],
            "info",
            i18n.t(
                "extractor.ev_target_paused",
                lang,
                platform=_platform_name(pid, lang),
            ),
        )
    else:
        entry["disabled"] = False
        entry["fails"] = 0
        entry["last_error"] = ""
        db.add_extractor_event(
            job["id"],
            "info",
            i18n.t(
                "extractor.ev_target_resumed",
                lang,
                platform=_platform_name(pid, lang),
            ),
        )

    updates: dict[str, Any] = {"platform_state": state}
    enabled = [t for t in targets if not _is_blocked(_target_state(state, t))]
    if paused and not enabled:
        updates["status_note"] = i18n.t("extractor.note_targets_paused", lang)
    elif not paused:
        if enabled:
            if job["status"] == "error":
                updates["status"] = "running"
            if job["status"] in ("running", "error"):
                updates["next_action_at"] = _iso(_now())
            if job.get("status_note") == i18n.t(
                "extractor.note_targets_paused", lang
            ) or job["status"] == "error":
                updates["status_note"] = ""

    db.update_extractor_job(job["id"], **updates)
    return db.get_extractor_job(job["id"])


def scan_summary(
    account_link_id: str,
    source_platform_id: str,
    target_platform_ids: list[str],
) -> dict[str, Any]:
    """Paso 2: cuántos videos tiene el origen y cuántos faltan por destino."""
    total = db.count_extractor_source_videos(account_link_id, source_platform_id)
    targets: list[dict[str, Any]] = []
    for pid in target_platform_ids:
        pending = db.count_extractor_pending(
            account_link_id, source_platform_id, pid
        )
        targets.append({"platform_id": pid, "pending": pending})
    return {"total": total, "targets": targets}


def _publish_one(
    *,
    upload_dir: Path,
    job: dict[str, Any],
    video: db.Video,
    target_ids: list[str],
    state: dict[str, Any],
) -> tuple[int, int, float]:
    """Publica un video en los destinos indicados. Devuelve (ok, fail, segundos)."""
    lang = job.get("lang") or "es"
    content_type = _content_type_for(video)
    ok_n = 0
    fail_n = 0
    started = time.monotonic()
    batch_id = str(uuid.uuid4())

    for pid in target_ids:
        entry = _target_state(state, pid)
        cap = platforms.get_platform(pid) or {}
        cap_key = "video" if content_type == "video" else "photo"
        if str(cap.get(cap_key, "no")) == "no" or not platforms.is_publish_enabled(pid):
            # El servidor no soporta este contenido o la publicación está pausada:
            # se marca como omitido para que no quede pendiente para siempre.
            db.insert_publication_log(
                user_id=job["owner_user_id"],
                video_id=video.id,
                platform_id=pid,
                content_type=content_type,
                status="skipped",
                message=i18n.t(
                    "pub.platform_paused",
                    lang,
                    platform=i18n.t(f"platform.{pid}", lang),
                )
                if not platforms.is_publish_enabled(pid)
                else i18n.t("extractor.log_skipped", lang),
                account_link_id=job["account_link_id"],
                batch_id=batch_id,
            )
            continue

        was_probing = bool(entry.get("probing"))
        ok, message = platform_publish.publish_to_platform(
            pid,
            file_path=upload_dir / video.file_name,
            content_type=content_type,
            title=video.title,
            description=video.description,
            lang=lang,
            tiktok_config_id=db.resolve_tiktok_config_id(
                account_link_id=job.get("account_link_id")
            )
            if pid == "tiktok"
            else None,
            account_link_id=job.get("account_link_id"),
        )
        entry["cycle_sent"] = int(entry.get("cycle_sent") or 0) + 1
        db.insert_publication_log(
            user_id=job["owner_user_id"],
            video_id=video.id,
            platform_id=pid,
            content_type=content_type,
            status="ok" if ok else "fail",
            message=message,
            account_link_id=job["account_link_id"],
            batch_id=batch_id,
        )
        if ok:
            ok_n += 1
            entry["fails"] = 0
            entry["last_error"] = ""
            if was_probing:
                entry["probing"] = False
                db.add_extractor_event(
                    job["id"],
                    "info",
                    i18n.t(
                        "extractor.ev_platform_recovered",
                        lang,
                        platform=_platform_name(pid, lang),
                    ),
                )
        else:
            fail_n += 1
            entry["fails"] = int(entry.get("fails") or 0) + 1
            entry["last_error"] = message
            if was_probing or entry["fails"] >= FAILS_TO_DISABLE:
                entry["disabled"] = True
                entry["disabled_at"] = _iso(_now())
                entry["probing"] = False
                db.add_extractor_event(
                    job["id"],
                    "error",
                    i18n.t(
                        "extractor.ev_platform_down",
                        lang,
                        platform=_platform_name(pid, lang),
                        error=message,
                    ),
                )

    return ok_n, fail_n, time.monotonic() - started


def _pick_next_video(
    job: dict[str, Any], enabled_targets: list[str], state: dict[str, Any]
) -> tuple[db.Video | None, list[str]]:
    """Elige el video más antiguo pendiente y los destinos que lo recibirán."""
    candidates: dict[str, db.Video] = {}
    pending_by_target: dict[str, set[str]] = {}
    for pid in enabled_targets:
        entry = _target_state(state, pid)
        if int(entry.get("cycle_sent") or 0) >= platform_cycle_cap(pid):
            continue
        vids = db.list_extractor_pending_videos(
            job["account_link_id"],
            job["source_platform_id"],
            pid,
            limit=MAX_PUBLISH_PER_TICK,
        )
        pending_by_target[pid] = {v.id for v in vids}
        for v in vids:
            candidates.setdefault(v.id, v)
    if not candidates:
        return None, []
    ordered = sorted(candidates.values(), key=lambda v: v.created_at)
    video = ordered[0]
    targets = [pid for pid, vid_set in pending_by_target.items() if video.id in vid_set]
    return video, targets


def _has_any_pending(job: dict[str, Any]) -> bool:
    for pid in job.get("target_platform_ids") or []:
        if db.count_extractor_pending(
            job["account_link_id"], job["source_platform_id"], pid
        ) > 0:
            return True
    return False


def _finish_cycle(
    job: dict[str, Any],
    state: dict[str, Any],
    *,
    sent_videos: int,
    ok_ops: int,
    fail_ops: int,
    op_seconds: float,
) -> dict[str, Any]:
    """Cierra el ciclo: registra el resumen y aplica el auto-ajuste del lote."""
    lang = job.get("lang") or "es"
    now = _now()
    updates: dict[str, Any] = {
        "cycle_remaining": 0,
        "last_cycle_at": _iso(now),
        "next_action_at": _iso(now + timedelta(minutes=job["interval_minutes"])),
    }

    if sent_videos > 0:
        db.add_extractor_event(
            job["id"],
            "info",
            i18n.t(
                "extractor.ev_cycle_done",
                lang,
                videos=sent_videos,
                ok=ok_ops,
                fail=fail_ops,
            ),
        )

    effective = int(job["effective_batch"])
    configured = int(job["batch_size"])
    ops = ok_ops + fail_ops
    avg_op = (op_seconds / ops) if ops else 0.0
    mem = memory_usage_percent()
    mem_high = mem is not None and mem >= MEMORY_HIGH_PERCENT
    too_slow = avg_op > SLOW_PUBLISH_SECONDS

    if ops > 0 and (mem_high or too_slow) and effective > MIN_BATCH:
        new_eff = max(MIN_BATCH, effective // 2)
        updates["effective_batch"] = new_eff
        updates["good_cycles"] = 0
        updates["status_note"] = i18n.t(
            "extractor.note_lowered", lang, count=new_eff
        )
        key = "extractor.ev_lowered_memory" if mem_high else "extractor.ev_lowered_slow"
        db.add_extractor_event(
            job["id"],
            "warn",
            i18n.t(
                key,
                lang,
                prev=effective,
                new=new_eff,
                mem=int(mem or 0),
            ),
        )
    elif not (mem_high or too_slow):
        good = int(job.get("good_cycles") or 0) + 1
        if effective < configured and good >= GOOD_CYCLES_TO_RAISE:
            new_eff = min(configured, max(effective + 1, effective * 2))
            updates["effective_batch"] = new_eff
            updates["good_cycles"] = 0
            if new_eff >= configured:
                updates["status_note"] = ""
            else:
                updates["status_note"] = i18n.t(
                    "extractor.note_partial", lang, count=new_eff, total=configured
                )
            db.add_extractor_event(
                job["id"],
                "info",
                i18n.t("extractor.ev_raised", lang, new=new_eff),
            )
        else:
            updates["good_cycles"] = good

    # Reinicia el contador por servidor para el próximo ciclo.
    for pid in list(state.keys()):
        entry = state.get(pid)
        if isinstance(entry, dict):
            entry["cycle_sent"] = 0
    updates["platform_state"] = state
    return updates


def _process_job(job: dict[str, Any], *, upload_dir: Path) -> None:
    lang = job.get("lang") or "es"
    now = _now()
    state: dict[str, Any] = dict(job.get("platform_state") or {})
    targets = list(job.get("target_platform_ids") or [])
    if not targets:
        db.update_extractor_job(
            job["id"],
            status="error",
            status_note=i18n.t("extractor.note_no_targets", lang),
        )
        return

    # Memoria crítica: pospone el ciclo completo.
    mem = memory_usage_percent()
    if mem is not None and mem >= MEMORY_CRITICAL_PERCENT:
        db.add_extractor_event(
            job["id"],
            "warn",
            i18n.t("extractor.ev_postponed", lang, mem=int(mem)),
        )
        db.update_extractor_job(
            job["id"],
            next_action_at=_iso(now + timedelta(seconds=POSTPONE_SECONDS)),
        )
        return

    # Reintenta servidores caídos cuando pasó la ventana de espera.
    # Los pausados a mano no se reactivan solos.
    retry_window = timedelta(minutes=DISABLED_RETRY_MINUTES)
    for pid in targets:
        entry = _target_state(state, pid)
        if entry.get("paused") or not entry.get("disabled"):
            continue
        disabled_at = _parse_iso(entry.get("disabled_at") or "")
        if disabled_at is None or now - disabled_at >= retry_window:
            entry["disabled"] = False
            entry["probing"] = True
            entry["fails"] = 0
            db.add_extractor_event(
                job["id"],
                "info",
                i18n.t(
                    "extractor.ev_platform_retry",
                    lang,
                    platform=_platform_name(pid, lang),
                ),
            )

    enabled = [pid for pid in targets if not _is_blocked(_target_state(state, pid))]
    if not enabled:
        if all(_target_state(state, pid).get("paused") for pid in targets):
            db.update_extractor_job(
                job["id"],
                platform_state=state,
                status_note=i18n.t("extractor.note_targets_paused", lang),
                next_action_at=_iso(now + timedelta(seconds=POSTPONE_SECONDS)),
            )
            return
        db.add_extractor_event(
            job["id"], "error", i18n.t("extractor.ev_all_down", lang)
        )
        db.update_extractor_job(
            job["id"],
            status="error",
            status_note=i18n.t("extractor.note_all_down", lang),
            platform_state=state,
        )
        return

    # Arranca un ciclo nuevo si el anterior terminó.
    cycle_remaining = int(job.get("cycle_remaining") or 0)
    if cycle_remaining <= 0:
        cycle_remaining = int(job["effective_batch"])
        for pid in targets:
            _target_state(state, pid)["cycle_sent"] = 0

    sent_videos = 0
    ok_ops = 0
    fail_ops = 0
    op_seconds = 0.0
    tick_started = time.monotonic()
    per_tick_left = MAX_PUBLISH_PER_TICK
    rest_seconds = int(job.get("rest_seconds") or 0)

    while cycle_remaining > 0 and per_tick_left > 0:
        enabled = [
            pid for pid in targets if not _is_blocked(_target_state(state, pid))
        ]
        if not enabled:
            break
        video, video_targets = _pick_next_video(job, enabled, state)
        if not video:
            break
        ok_n, fail_n, seconds = _publish_one(
            upload_dir=upload_dir,
            job=job,
            video=video,
            target_ids=video_targets,
            state=state,
        )
        sent_videos += 1
        ok_ops += ok_n
        fail_ops += fail_n
        op_seconds += seconds
        cycle_remaining -= 1
        per_tick_left -= 1
        if rest_seconds > 0:
            break
        if time.monotonic() - tick_started > MAX_TICK_SECONDS:
            break

    job_after = dict(job)
    job_after["good_cycles"] = int(job.get("good_cycles") or 0)

    if not _has_any_pending(job_after):
        # Nada pendiente: la extracción terminó.
        for pid in list(state.keys()):
            entry = state.get(pid)
            if isinstance(entry, dict):
                entry["cycle_sent"] = 0
        db.add_extractor_event(
            job["id"], "info", i18n.t("extractor.ev_done", lang)
        )
        db.update_extractor_job(
            job["id"],
            status="done",
            status_note="",
            cycle_remaining=0,
            platform_state=state,
            next_action_at="",
        )
        return

    if cycle_remaining <= 0 or sent_videos == 0:
        # Ciclo completo (o sin nada que enviar por topes): cerrar y programar.
        updates = _finish_cycle(
            job_after,
            state,
            sent_videos=sent_videos,
            ok_ops=ok_ops,
            fail_ops=fail_ops,
            op_seconds=op_seconds,
        )
        db.update_extractor_job(job["id"], **updates)
        return

    # El ciclo sigue: descanso entre videos o continuar en la próxima pasada.
    delay = rest_seconds if rest_seconds > 0 else 0
    db.update_extractor_job(
        job["id"],
        cycle_remaining=cycle_remaining,
        platform_state=state,
        next_action_at=_iso(now + timedelta(seconds=delay)),
    )


def process_due_extractor_jobs(*, upload_dir: Path) -> int:
    """Procesa las extracciones en curso cuya hora ya llegó."""
    processed = 0
    now_iso = _iso(_now())
    for job in db.list_due_extractor_jobs(now_iso):
        try:
            _process_job(job, upload_dir=upload_dir)
            processed += 1
        except Exception as exc:  # noqa: BLE001 - un trabajo roto no debe frenar el resto
            try:
                db.add_extractor_event(job["id"], "error", str(exc)[:300])
                db.update_extractor_job(
                    job["id"],
                    next_action_at=_iso(_now() + timedelta(seconds=POSTPONE_SECONDS)),
                )
            except Exception:
                pass
    return processed
