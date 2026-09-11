"""Programación de publicaciones en hora Colombia / Chicago (UTC-5 fijo)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid

import db
import i18n
import notify
import platform_publish
import platforms
import publish_pending

# Colombia y Chicago (CST) comparten UTC-5 sin cambio horario estacional.
PUBLISH_TZ = timezone(timedelta(hours=-5))


def now_publish_tz() -> datetime:
    return datetime.now(PUBLISH_TZ)


def min_datetime_local_input() -> str:
    return now_publish_tz().strftime("%Y-%m-%dT%H:%M")


def parse_local_date_range(date_from: str, date_to: str) -> tuple[str, str] | None:
    """Rango inclusive YYYY-MM-DD en hora local → límites ISO UTC."""
    try:
        start_naive = datetime.strptime((date_from or "").strip(), "%Y-%m-%d")
        end_naive = datetime.strptime((date_to or "").strip(), "%Y-%m-%d")
    except ValueError:
        return None
    if end_naive < start_naive:
        return None
    start = start_naive.replace(tzinfo=PUBLISH_TZ)
    end = end_naive.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=PUBLISH_TZ)
    return start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat()


def parse_scheduled_at_local(raw: str) -> datetime | None:
    """Interpreta datetime-local como hora local Colombia/Chicago y devuelve UTC."""
    s = (raw or "").strip()
    if not s:
        return None
    try:
        if len(s) == 16:
            s = f"{s}:00"
        naive = datetime.fromisoformat(s)
        local = naive.replace(tzinfo=PUBLISH_TZ)
        return local.astimezone(timezone.utc)
    except ValueError:
        return None


def format_scheduled_local(utc_iso: str, lang: str) -> str:
    try:
        dt = datetime.fromisoformat(str(utc_iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone(PUBLISH_TZ)
        return local.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(utc_iso)[:16]


def remaining_platform_ids(failures: list[dict]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in failures:
        pid = str(item.get("platform_id") or "").strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        out.append(pid)
    return out


def persist_awaiting_retry(
    *,
    sched_id: str | None,
    user_id: str,
    video_id: str,
    failures: list[dict],
    tiktoker_config_id: str,
    content_type: str,
    lang: str,
    account_link_id: str,
    error_message: str = "",
    x_use_funding: bool = False,
) -> str | None:
    """Deja el video en cola hasta que un admin republica o cancela."""
    remaining = remaining_platform_ids(failures)
    if not remaining:
        if sched_id:
            db.complete_scheduled_publication(sched_id, "done")
        return None
    if sched_id:
        db.set_scheduled_awaiting_retry(sched_id, remaining, error_message)
        return sched_id
    return db.create_scheduled_publication(
        user_id=user_id,
        video_id=video_id,
        platforms=remaining,
        tiktok_config_id=tiktoker_config_id,
        content_type=content_type,
        scheduled_at_utc=datetime.now(timezone.utc),
        lang=lang,
        account_link_id=account_link_id,
        status="awaiting_retry",
        x_use_funding=x_use_funding,
    )


def execute_video_publish(
    *,
    upload_dir: Path,
    user_id: str,
    video: db.Video,
    selected_platforms: list[str],
    tiktoker_config_id: str,
    content_type: str,
    lang: str,
    account_link_id: str = "",
    retry_sched_id: str = "",
    x_use_funding: bool = False,
) -> tuple[int, int, int, list[dict]]:
    """Publica un video en las plataformas indicadas. Devuelve ok, fail, pendientes y fallos para email."""
    path = upload_dir / video.file_name
    ok_n = 0
    fail_n = 0
    pending_n = 0
    failures_for_email: list[dict] = []
    batch_id = str(uuid.uuid4())
    sched_id = (retry_sched_id or "").strip() or None

    x_use_funding = not db.account_wants_own_x_api(account_link_id)
    for pid in selected_platforms:
        if not platforms.is_publish_enabled(pid):
            continue
        status, message = platform_publish.publish_to_platform(
            pid,
            file_path=path,
            content_type=content_type,
            title=video.title,
            description=video.description,
            lang=lang,
            tiktok_config_id=tiktoker_config_id if pid == "tiktok" else None,
            account_link_id=account_link_id,
            x_use_funding=bool(x_use_funding) if pid == "x" else False,
        )
        if status not in ("ok", "fail", "skipped", "pending"):
            status = "fail"
        if status == "ok":
            ok_n += 1
            if pid == "x" and status == "ok":
                try:
                    if x_use_funding:
                        db.record_x_funding_usage(
                            account_link_id=account_link_id,
                            video_title=video.title,
                        )
                    else:
                        src = db.x_funding_source_for_account_link(account_link_id)
                        if src:
                            db.record_x_funding_usage(
                                account_link_id=account_link_id,
                                video_title=video.title,
                                source_id=str(src.get("id") or ""),
                            )
                except Exception:
                    pass
                try:
                    import x_funding

                    x_funding.maybe_check_on_publish(account_link_id)
                except Exception:
                    pass
        elif status == "pending":
            pending_n += 1
        elif status == "fail":
            fail_n += 1
            failures_for_email.append(
                {
                    "platform_id": pid,
                    "platform_name": i18n.t(f"platform.{pid}", lang),
                    "message": message,
                }
            )
        log_id = db.insert_publication_log(
            user_id=user_id,
            video_id=video.id,
            platform_id=pid,
            content_type=content_type,
            status=status,
            message=message,
            account_link_id=account_link_id,
            batch_id=batch_id,
        )
        if status == "pending":
            publish_pending.attach(log_id)

    if failures_for_email:
        persist_awaiting_retry(
            sched_id=sched_id,
            user_id=user_id,
            video_id=video.id,
            failures=failures_for_email,
            tiktoker_config_id=tiktoker_config_id,
            content_type=content_type,
            lang=lang,
            account_link_id=account_link_id,
            x_use_funding=x_use_funding,
        )
        notify.send_publish_failure_alert(
            video_title=video.title,
            failures=failures_for_email,
            lang=lang,
            user_id=user_id,
            tiktok_config_id=tiktoker_config_id,
        )
    elif sched_id:
        db.complete_scheduled_publication(sched_id, "done")

    return ok_n, fail_n, pending_n, failures_for_email


def process_due_scheduled_publications(*, upload_dir: Path) -> int:
    """Procesa publicaciones pendientes cuya hora ya llegó. Devuelve cuántas se procesaron."""
    processed = 0
    for row in db.list_due_scheduled_publications():
        sched_id = row["id"]
        if not db.mark_scheduled_processing(sched_id):
            continue
        try:
            video = db.get_video_by_id(row["video_id"])
            if not video:
                db.complete_scheduled_publication(
                    sched_id, "failed", "Video not found"
                )
                continue
            platforms_list = json.loads(row["platforms_json"] or "[]")
            if not platforms_list:
                db.complete_scheduled_publication(
                    sched_id, "failed", "No platforms selected"
                )
                db.release_publish_file_lock_if_idle(
                    row["user_id"], getattr(video, "file_hash", "") or ""
                )
                continue
            account_link_id = (row.get("account_link_id") or "").strip()
            slot_utc, pace_reason = db.next_account_publish_slot(
                account_link_id, exclude_sched_id=sched_id
            )
            now_utc = datetime.now(timezone.utc)
            if pace_reason != "now" and slot_utc > now_utc + timedelta(seconds=30):
                db.reschedule_pending_publication(sched_id, slot_utc)
                continue
            execute_video_publish(
                upload_dir=upload_dir,
                user_id=row["user_id"],
                video=video,
                selected_platforms=platforms_list,
                tiktoker_config_id=(row.get("tiktok_config_id") or "").strip(),
                content_type=row.get("content_type") or "video",
                lang=row.get("lang") or "es",
                account_link_id=account_link_id,
                retry_sched_id=sched_id,
                x_use_funding=bool(row.get("x_use_funding") or 0),
            )
            db.release_publish_file_lock_if_idle(
                row["user_id"], getattr(video, "file_hash", "") or ""
            )
            processed += 1
        except (OSError, Exception) as e:
            try:
                raw_platforms = json.loads(row.get("platforms_json") or "[]")
            except (TypeError, ValueError):
                raw_platforms = []
            if not isinstance(raw_platforms, list):
                raw_platforms = []
            persist_awaiting_retry(
                sched_id=sched_id,
                user_id=row["user_id"],
                video_id=row["video_id"],
                failures=[{"platform_id": p} for p in raw_platforms],
                tiktoker_config_id=(row.get("tiktok_config_id") or "").strip(),
                content_type=row.get("content_type") or "video",
                lang=row.get("lang") or "es",
                account_link_id=(row.get("account_link_id") or "").strip(),
                error_message=str(e),
            )
    return processed


def cancel_awaiting_retry(*, sched_id: str, actor_user_id: str, lang: str) -> bool:
    row = db.get_scheduled_publication(sched_id)
    if not row or str(row.get("status") or "") != "awaiting_retry":
        return False
    try:
        platforms_list = json.loads(row.get("platforms_json") or "[]")
    except (TypeError, ValueError):
        platforms_list = []
    if not isinstance(platforms_list, list):
        platforms_list = []
    message = i18n.t("pub.pending_cancelled_log", lang)
    batch_id = str(uuid.uuid4())
    for pid in platforms_list:
        pid_s = str(pid or "").strip()
        if not pid_s:
            continue
        db.insert_publication_log(
            user_id=actor_user_id,
            video_id=row.get("video_id"),
            platform_id=pid_s,
            content_type=row.get("content_type") or "video",
            status="skipped",
            message=message,
            account_link_id=(row.get("account_link_id") or "").strip(),
            batch_id=batch_id,
        )
    db.complete_scheduled_publication(sched_id, "cancelled")
    video = db.get_video_by_id(str(row.get("video_id") or ""))
    if video:
        db.release_publish_file_lock_if_idle(
            str(row.get("user_id") or ""), getattr(video, "file_hash", "") or ""
        )
    return True
