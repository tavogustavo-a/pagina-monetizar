"""Publicación real en Páginas de Facebook (fotos y videos por multipart)."""
from __future__ import annotations

import json
import uuid
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
import facebook_oauth

GRAPH = "https://graph.facebook.com/v21.0"
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v"}
TEXT_MAX = 63206
TITLE_MAX = 255
MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".m4v": "video/mp4",
}


def _graph_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        msg = str(err.get("message") or err.get("error_user_msg") or "").strip()
        if msg:
            return msg[:220]
    return (fallback or "Facebook API error")[:220]


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


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
        return False
    return expires - now < timedelta(days=10)


def _refresh_row(row: dict[str, Any]) -> dict[str, Any]:
    user_token = str(row.get("refresh_token") or "").strip()
    if not user_token:
        raise ValueError("missing_token")
    try:
        data = facebook_oauth.exchange_long_lived(user_token)
        user_token = str(data.get("access_token") or user_token).strip()
        expires_in = data.get("expires_in")
    except ValueError:
        expires_in = None
    pages = facebook_oauth.list_pages(user_token)
    page_id = str(row.get("open_id") or "").strip()
    match = next((p for p in pages if p.get("open_id") == page_id), None)
    if not match:
        raise ValueError("missing_token")
    token = str(match.get("access_token") or "").strip()
    if not token:
        raise ValueError("missing_token")
    db.update_oauth_tokens(
        str(row["id"]),
        access_token=token,
        refresh_token=user_token,
        expires_in=int(expires_in) if expires_in is not None else None,
    )
    return db.get_oauth_account_row(str(row["id"])) or row


def _token_and_page(account_link_id: str | None) -> tuple[str, str, dict[str, Any]]:
    oid = db.resolve_oauth_account_id("facebook", account_link_id=account_link_id)
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
    page_id = str(row.get("open_id") or "").strip()
    if not page_id:
        profile = facebook_oauth.fetch_page_profile(token)
        page_id = str(profile.get("open_id") or "").strip()
    if not page_id:
        raise ValueError("missing_token")
    return token, page_id, row


def _caption(title: str, description: str) -> str:
    parts = [str(title or "").strip(), str(description or "").strip()]
    return "\n\n".join(p for p in parts if p)[:TEXT_MAX]


def _title(title: str) -> str:
    return (str(title or "").strip() or "Video")[:TITLE_MAX]


def _multipart(fields: dict[str, str], file_field: str, path: Path, mime: str) -> tuple[bytes, str]:
    boundary = "----FbBoundary" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    safe_name = path.name.replace('"', "")
    chunks.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{safe_name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(path.read_bytes())
    chunks.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _post_multipart(url: str, body: bytes, content_type: str, timeout: int) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": content_type},
    )
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


def _upload(page_id: str, token: str, path: Path, *, is_photo: bool, title: str, description: str) -> str:
    caption = _caption(title, description)
    mime = MIME.get(path.suffix.lower(), "application/octet-stream")
    if is_photo:
        fields = {"access_token": token, "published": "true"}
        if caption:
            fields["caption"] = caption
        body, ctype = _multipart(fields, "source", path, mime)
        data = _post_multipart(f"{GRAPH}/{page_id}/photos", body, ctype, 120)
    else:
        fields = {"access_token": token, "title": _title(title)}
        if caption:
            fields["description"] = caption
        body, ctype = _multipart(fields, "source", path, mime)
        data = _post_multipart(f"{GRAPH}/{page_id}/videos", body, ctype, 300)
    media_id = str(data.get("post_id") or data.get("id") or "").strip()
    if not media_id:
        raise ValueError("Facebook did not return a post id.")
    return media_id


def publish_media(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    from i18n import explain_provider_error, t

    path = Path(file_path)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.facebook.file_missing", lang)

    suffix = path.suffix.lower()
    is_photo = content_type == "photo" or suffix in PHOTO_EXT
    is_video = content_type == "video" or suffix in VIDEO_EXT
    if is_photo and suffix not in PHOTO_EXT:
        return False, t("pub.facebook.bad_photo", lang)
    if is_video and suffix not in VIDEO_EXT:
        return False, t("pub.facebook.bad_video", lang)
    if not is_photo and not is_video:
        return False, t("pub.facebook.bad_file", lang)

    try:
        token, page_id, row = _token_and_page(account_link_id)
    except ValueError:
        return False, t("pub.facebook.no_token", lang)

    def _send(access: str) -> str:
        return _upload(
            page_id,
            access,
            path,
            is_photo=is_photo,
            title=title,
            description=description,
        )

    try:
        try:
            media_id = _send(token)
        except ValueError as e:
            msg = str(e).lower()
            if "session" in msg or "token" in msg or "oauth" in msg or "190" in msg:
                row = _refresh_row(row)
                token = str(row.get("access_token") or "").strip()
                media_id = _send(token)
            else:
                raise
        if is_photo:
            return True, t("pub.facebook.photo_ok", lang, id=media_id)
        return True, t("pub.facebook.video_ok", lang, id=media_id)
    except ValueError as e:
        if str(e) == "missing_token":
            return False, t("pub.facebook.no_token", lang)
        return False, t(
            "pub.facebook.upload_fail",
            lang,
            error=explain_provider_error("facebook", str(e), lang),
        )
    except Exception as e:
        return False, t(
            "pub.facebook.upload_fail",
            lang,
            error=explain_provider_error("facebook", str(e), lang),
        )
