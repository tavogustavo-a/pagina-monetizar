"""Publicaciones aceptadas por la plataforma pero aún en procesamiento/revisión.

YouTube e Instagram aceptan el video y lo procesan minutos. La petición HTTP
termina enseguida (estado pending). Un hilo y el worker del servidor consultan
hasta que la red acepte (ok) o rechace (fail). El trabajo se guarda en la base
para que recargar la página o subir otro video no lo borre.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

import db

CheckFn = Callable[[], tuple[str, str]]

CHECK_INTERVAL_SECONDS = 30.0
MAX_WAIT_SECONDS = 30 * 60.0

_local = threading.local()


def clear() -> None:
    _local.check = None
    _local.job = None


def mark(
    check: CheckFn,
    *,
    platform: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    """Se llama durante la publicación: captura el proxy activo para el hilo vigía."""
    import proxy_util

    proxy_url = proxy_util.active_proxy_url()
    data = dict(payload or {})
    if proxy_url:
        data.setdefault("proxy_url", proxy_url)
    _local.check = check
    _local.job = {
        "platform": (platform or "").strip(),
        "payload": data,
        "proxy_url": proxy_url,
    }


def has_pending() -> bool:
    return getattr(_local, "check", None) is not None


def pop() -> tuple[CheckFn | None, dict[str, Any] | None]:
    check = getattr(_local, "check", None)
    job = getattr(_local, "job", None)
    _local.check = None
    _local.job = None
    return check, job


def attach(log_id: str) -> None:
    """Tras insertar la fila pending: guarda el trabajo y vigila en segundo plano."""
    check, job = pop()
    lid = (log_id or "").strip()
    if not lid:
        return
    if job and job.get("platform") and job.get("payload"):
        try:
            db.save_publish_pending_job(
                log_id=lid,
                platform_id=str(job["platform"]),
                payload=job["payload"],
            )
        except Exception:
            pass
    if not check:
        return
    proxy_url = str((job or {}).get("proxy_url") or "")

    def _run() -> None:
        import proxy_util

        deadline = time.monotonic() + MAX_WAIT_SECONDS
        while time.monotonic() < deadline:
            time.sleep(CHECK_INTERVAL_SECONDS)
            try:
                # El hilo no hereda el ContextVar del proxy: se reactiva aquí.
                with proxy_util.using_proxy(proxy_url):
                    status, message = check()
            except Exception:
                continue
            if status in ("ok", "fail"):
                _finish(lid, status, message)
                return

    threading.Thread(
        target=_run, daemon=True, name=f"pending-pub-{lid[:8]}"
    ).start()


def _finish(log_id: str, status: str, message: str) -> None:
    try:
        db.finalize_publication_log_pending(
            log_id, status=status, message=message
        )
    except Exception:
        pass
    try:
        db.delete_publish_pending_job(log_id)
    except Exception:
        pass


def resume_job(platform_id: str, payload: dict[str, Any]) -> tuple[str, str]:
    import proxy_util

    pid = (platform_id or "").strip()
    data = payload if isinstance(payload, dict) else {}
    proxy_url = str(data.get("proxy_url") or "")
    if pid == "instagram":
        import instagram_publish

        with proxy_util.using_proxy(proxy_url):
            return instagram_publish.resume_pending(data)
    if pid == "youtube":
        import youtube_publish

        with proxy_util.using_proxy(proxy_url):
            return youtube_publish.resume_pending(data)
    return "pending", ""


def process_saved_jobs() -> int:
    """El worker retoma pendientes si el hilo se perdió (reinicio) o sigue en curso."""
    from datetime import datetime, timezone

    from i18n import t

    done = 0
    now = datetime.now(timezone.utc)
    for job in db.list_publish_pending_jobs():
        log_id = str(job.get("log_id") or "")
        if not log_id:
            continue
        created = None
        raw = str(job.get("created_at") or "")
        try:
            created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
        except ValueError:
            created = None
        age = (now - created).total_seconds() if created else 0
        payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        lang = str(payload.get("lang") or "es")
        if age > MAX_WAIT_SECONDS:
            key = "pub.pending_timeout_proxy" if payload.get("proxy_url") else "pub.pending_timeout"
            _finish(log_id, "fail", t(key, lang))
            done += 1
            continue
        try:
            status, message = resume_job(
                str(job.get("platform_id") or ""),
                payload,
            )
        except Exception:
            continue
        if status in ("ok", "fail"):
            _finish(log_id, status, message)
            done += 1
    return done
