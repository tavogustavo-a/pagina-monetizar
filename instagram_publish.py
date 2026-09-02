"""Publicación real en Instagram (Graph: feed foto y Reels)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from datetime import datetime, timedelta, timezone

import db
import instagram_oauth

GRAPH = "https://graph.instagram.com/v21.0"
RUPLOAD = "https://rupload.facebook.com/ig-api-upload/v21.0"
PHOTO_EXT = {".jpg", ".jpeg", ".png"}
VIDEO_EXT = {".mp4", ".mov", ".m4v"}
CAPTION_MAX = 2200
POLL_ATTEMPTS = 40
POLL_SECONDS = 3


def _graph_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        msg = str(err.get("message") or err.get("error_user_msg") or "").strip()
        if msg:
            return msg[:220]
    return (fallback or "Instagram API error")[:220]


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        parsed = _parse_json(raw)
        raise ValueError(_graph_error(parsed, raw or str(e))) from e
    parsed = _parse_json(raw)
    if parsed.get("error"):
        raise ValueError(_graph_error(parsed, raw))
    return parsed


def _graph_get(path: str, token: str, fields: dict[str, str] | None = None) -> dict[str, Any]:
    q = {"access_token": token}
    if fields:
        q.update(fields)
    return _request(f"{GRAPH}/{path.lstrip('/')}?" + urllib.parse.urlencode(q))


def _graph_post(path: str, token: str, fields: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode({**fields, "access_token": token}).encode("utf-8")
    return _request(
        f"{GRAPH}/{path.lstrip('/')}",
        method="POST",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=90,
    )


def _site_url() -> str:
    try:
        from site_config import SITE_URL

        return (SITE_URL or "").strip().rstrip("/")
    except Exception:
        return ""


def _is_public_base(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        return False
    if host.endswith(".local"):
        return False
    return url.lower().startswith("https://")


def _public_file_url(path: Path) -> str | None:
    base = _site_url()
    if not _is_public_base(base):
        return None
    name = urllib.parse.quote(path.name)
    return f"{base}/uploads/{name}"


def _caption(title: str, description: str) -> str:
    parts = [str(title or "").strip(), str(description or "").strip()]
    text = "\n\n".join(p for p in parts if p)
    return text[:CAPTION_MAX]


def _parse_iso(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _should_refresh(row: dict[str, Any]) -> bool:
    now = datetime.now(timezone.utc)
    updated = _parse_iso(str(row.get("updated_at") or ""))
    if updated and now - updated < timedelta(hours=24):
        return False
    expires = _parse_iso(str(row.get("token_expires_at") or ""))
    if not expires:
        return True
    return expires - now < timedelta(days=10)


def _refresh_row(row: dict[str, Any]) -> dict[str, Any]:
    current = str(row.get("refresh_token") or row.get("access_token") or "").strip()
    if not current:
        raise ValueError("missing_token")
    data = instagram_oauth.refresh_access_token(current)
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("missing_token")
    expires_in = data.get("expires_in")
    db.update_oauth_tokens(
        str(row["id"]),
        access_token=token,
        refresh_token=token,
        expires_in=int(expires_in) if expires_in is not None else None,
    )
    fresh = db.get_oauth_account_row(str(row["id"])) or row
    return fresh


def _token_and_user(account_link_id: str | None) -> tuple[str, str, dict[str, Any]]:
    oid = db.resolve_oauth_account_id("instagram", account_link_id=account_link_id)
    if not oid:
        raise ValueError("missing_token")
    row = db.get_oauth_account_row(oid)
    if not row:
        raise ValueError("missing_token")
    token = str(row.get("access_token") or "").strip()
    if not token:
        raise ValueError("missing_token")
    if _should_refresh(row):
        try:
            row = _refresh_row(row)
            token = str(row.get("access_token") or token).strip()
        except ValueError:
            pass
    user_id = str(row.get("open_id") or "").strip()
    if not user_id:
        profile = instagram_oauth.fetch_profile(token)
        user_id = str(profile.get("open_id") or "").strip()
    if not user_id:
        raise ValueError("missing_token")
    return token, user_id, row


def _poll_container(container_id: str, token: str) -> None:
    last = ""
    for _ in range(POLL_ATTEMPTS):
        data = _graph_get(container_id, token, {"fields": "status_code,status"})
        code = str(data.get("status_code") or "").upper()
        last = str(data.get("status") or code)
        if code in {"FINISHED", "PUBLISHED"}:
            return
        if code in {"ERROR", "EXPIRED"}:
            raise ValueError(last or code)
        time.sleep(POLL_SECONDS)
    raise ValueError(last or "timeout")


def _publish_container(user_id: str, token: str, container_id: str) -> str:
    _poll_container(container_id, token)
    data = _graph_post(f"{user_id}/media_publish", token, {"creation_id": container_id})
    return str(data.get("id") or container_id)


def _create_photo_container(user_id: str, token: str, image_url: str, caption: str) -> str:
    fields = {"image_url": image_url}
    if caption:
        fields["caption"] = caption
    data = _graph_post(f"{user_id}/media", token, fields)
    cid = str(data.get("id") or "").strip()
    if not cid:
        raise ValueError("Instagram did not return a media container.")
    return cid


def _create_reel_url_container(user_id: str, token: str, video_url: str, caption: str) -> str:
    fields = {"media_type": "REELS", "video_url": video_url}
    if caption:
        fields["caption"] = caption
    data = _graph_post(f"{user_id}/media", token, fields)
    cid = str(data.get("id") or "").strip()
    if not cid:
        raise ValueError("Instagram did not return a media container.")
    return cid


def _upload_resumable(user_id: str, token: str, path: Path, caption: str) -> str:
    fields = {"media_type": "REELS", "upload_type": "resumable"}
    if caption:
        fields["caption"] = caption
    data = _graph_post(f"{user_id}/media", token, fields)
    cid = str(data.get("id") or "").strip()
    if not cid:
        raise ValueError("Instagram did not return a media container.")
    size = path.stat().st_size
    with path.open("rb") as fh:
        binary = fh.read()
    _request(
        f"{RUPLOAD}/{cid}",
        method="POST",
        data=binary,
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(size),
            "Content-Type": "application/octet-stream",
        },
        timeout=300,
    )
    return cid


def publish_media(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    from i18n import t

    path = Path(file_path)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.instagram.file_missing", lang)

    suffix = path.suffix.lower()
    is_photo = content_type == "photo" or suffix in PHOTO_EXT
    is_video = content_type == "video" or suffix in VIDEO_EXT
    if is_photo and suffix not in PHOTO_EXT:
        return False, t("pub.instagram.bad_photo", lang)
    if is_video and suffix not in VIDEO_EXT:
        return False, t("pub.instagram.bad_video", lang)
    if not is_photo and not is_video:
        return False, t("pub.instagram.bad_file", lang)

    try:
        token, user_id, _row = _token_and_user(account_link_id)
    except ValueError:
        return False, t("pub.instagram.no_token", lang)

    caption = _caption(title, description)
    public_url = _public_file_url(path)

    try:
        if is_photo:
            if not public_url:
                return False, t("pub.instagram.need_public_url", lang)
            container = _create_photo_container(user_id, token, public_url, caption)
            media_id = _publish_container(user_id, token, container)
            return True, t("pub.instagram.photo_ok", lang, id=media_id)
        if public_url:
            container = _create_reel_url_container(user_id, token, public_url, caption)
        else:
            try:
                container = _upload_resumable(user_id, token, path, caption)
            except ValueError:
                return False, t("pub.instagram.need_public_url", lang)
        media_id = _publish_container(user_id, token, container)
        return True, t("pub.instagram.reel_ok", lang, id=media_id)
    except ValueError as e:
        key = str(e)
        if key == "missing_token":
            return False, t("pub.instagram.no_token", lang)
        return False, t("pub.instagram.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.instagram.upload_fail", lang, error=str(e)[:180])
