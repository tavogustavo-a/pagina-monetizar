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
) -> tuple[int, int, list[dict]]:
    """Publica un video en las plataformas indicadas. Devuelve ok, fail y fallos para email."""
    path = upload_dir / video.file_name
    ok_n = 0
    fail_n = 0
    failures_for_email: list[dict] = []
    batch_id = str(uuid.uuid4())

    for pid in selected_platforms:
        ok, message = platform_publish.publish_to_platform(
            pid,
            file_path=path,
            content_type=content_type,
            title=video.title,
            description=video.description,
            lang=lang,
            tiktok_config_id=tiktoker_config_id if pid == "tiktok" else None,
            account_link_id=account_link_id,
        )
        status = "ok" if ok else "fail"
        if ok:
            ok_n += 1
        else:
            fail_n += 1
            failures_for_email.append(
                {
                    "platform_id": pid,
                    "platform_name": i18n.t(f"platform.{pid}", lang),
                    "message": message,
                }
            )
        db.insert_publication_log(
            user_id=user_id,
            video_id=video.id,
            platform_id=pid,
            content_type=content_type,
            status=status,
            message=message,
            account_link_id=account_link_id,
            batch_id=batch_id,
        )

    if failures_for_email:
        notify.send_publish_failure_alert(
            video_title=video.title,
            failures=failures_for_email,
            lang=lang,
            user_id=user_id,
        )

    return ok_n, fail_n, failures_for_email


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
                continue
            ok_n, fail_n, _ = execute_video_publish(
                upload_dir=upload_dir,
                user_id=row["user_id"],
                video=video,
                selected_platforms=platforms_list,
                tiktoker_config_id=(row.get("tiktok_config_id") or "").strip(),
                content_type=row.get("content_type") or "video",
                lang=row.get("lang") or "es",
                account_link_id=(row.get("account_link_id") or "").strip(),
            )
            if fail_n and not ok_n:
                db.complete_scheduled_publication(
                    sched_id,
                    "failed",
                    f"All platforms failed ({fail_n})",
                )
            else:
                db.complete_scheduled_publication(sched_id, "done")
            processed += 1
        except OSError as e:
            db.complete_scheduled_publication(sched_id, "failed", str(e))
        except Exception as e:
            db.complete_scheduled_publication(sched_id, "failed", str(e))
    return processed
