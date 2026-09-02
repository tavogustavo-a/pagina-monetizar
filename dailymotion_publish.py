"""Publicación real de video en Dailymotion (API v2, con respaldo a la API clásica)."""
from __future__ import annotations

import json
import os
import uuid
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
import dailymotion_oauth

V2 = "https://api.dailymotion.com/v2"
LEGACY = "https://api.dailymotion.com"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
TITLE_MAX = 255
DESC_MAX = 3000
MIME = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".m4v": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
}


def _category() -> str:
    raw = (os.environ.get("DAILYMOTION_CATEGORY") or "news").strip().lower()
    return raw or "news"


def _visibility() -> str:
    raw = (os.environ.get("DAILYMOTION_VISIBILITY") or "public").strip().lower()
    return raw if raw in {"public", "private", "password"} else "public"


def _api_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        msg = str(err.get("message") or "").strip()
        if msg:
            return msg[:220]
    desc = str(data.get("error_description") or data.get("error_message") or "").strip()
    if err or desc:
        return f"{err}: {desc}".strip(": ")[:220]
    return (fallback or "Dailymotion API error")[:220]


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
    expires = _parse_iso(str(row.get("token_expires_at") or ""))
    if not expires:
        return bool(str(row.get("refresh_token") or "").strip())
    return expires - datetime.now(timezone.utc) < timedelta(minutes=10)


def _refresh_row(row: dict[str, Any]) -> dict[str, Any]:
    refresh = str(row.get("refresh_token") or "").strip()
    if not refresh:
        raise ValueError("missing_token")
    data = dailymotion_oauth.refresh_access_token(refresh)
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("missing_token")
    new_refresh = str(data.get("refresh_token") or "").strip() or refresh
    expires_in = data.get("expires_in")
    db.update_oauth_tokens(
        str(row["id"]),
        access_token=token,
        refresh_token=new_refresh,
        expires_in=int(expires_in) if expires_in is not None else None,
    )
    return db.get_oauth_account_row(str(row["id"])) or row


def _token_row(account_link_id: str | None) -> tuple[str, dict[str, Any]]:
    oid = db.resolve_oauth_account_id("dailymotion", account_link_id=account_link_id)
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
    return token, row


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
        raise ValueError(_api_error(parsed, raw or str(e))) from e
    parsed = _parse_json(raw)
    if parsed.get("error") and not parsed.get("url") and not parsed.get("upload_url"):
        raise ValueError(_api_error(parsed, raw))
    return parsed


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _multipart_file(path: Path, mime: str) -> tuple[bytes, str]:
    boundary = "----DmBoundary" + uuid.uuid4().hex
    name = path.name.replace('"', "")
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8")
    body = head + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, f"multipart/form-data; boundary={boundary}"


def _upload_v2(token: str, path: Path) -> str:
    session = _request(
        f"{V2}/files/upload_sessions",
        method="POST",
        headers=_bearer(token),
    )
    upload_url = str(session.get("upload_url") or "").strip()
    if not upload_url:
        raise ValueError("Dailymotion did not return an upload URL.")
    mime = MIME.get(path.suffix.lower(), "video/mp4")
    body, ctype = _multipart_file(path, mime)
    uploaded = _request(
        upload_url,
        method="POST",
        data=body,
        headers={"Content-Type": ctype},
        timeout=300,
    )
    file_url = str(uploaded.get("url") or uploaded.get("file_url") or "").strip()
    if not file_url:
        raise ValueError("Dailymotion did not return a file URL.")
    return file_url


def _upload_legacy(token: str, path: Path) -> str:
    q = urllib.parse.urlencode({"access_token": token})
    session = _request(f"{LEGACY}/file/upload?{q}")
    upload_url = str(session.get("upload_url") or "").strip()
    if not upload_url:
        raise ValueError("Dailymotion did not return an upload URL.")
    mime = MIME.get(path.suffix.lower(), "video/mp4")
    body, ctype = _multipart_file(path, mime)
    uploaded = _request(
        upload_url,
        method="POST",
        data=body,
        headers={"Content-Type": ctype},
        timeout=300,
    )
    file_url = str(uploaded.get("url") or "").strip()
    if not file_url:
        raise ValueError("Dailymotion did not return a file URL.")
    return file_url


def _create_v2(token: str, profile_id: str, file_url: str, title: str, description: str) -> str:
    payload = {
        "title": title[:TITLE_MAX] or "Video",
        "description": description[:DESC_MAX],
        "category": _category(),
        "visibility": _visibility(),
        "is_for_kids": False,
        "source": {"file_url": file_url},
    }
    data = _request(
        f"{V2}/profiles/{urllib.parse.quote(profile_id)}/videos",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={**_bearer(token), "Content-Type": "application/json"},
        timeout=90,
    )
    vid = str(data.get("video_id") or data.get("id") or "").strip()
    if not vid:
        raise ValueError("Dailymotion did not return a video id.")
    return vid


def _create_legacy(token: str, file_url: str, title: str, description: str) -> str:
    fields = {
        "access_token": token,
        "url": file_url,
        "title": title[:TITLE_MAX] or "Video",
        "description": description[:DESC_MAX],
        "published": "true",
        "channel": _category(),
        "is_created_for_kids": "false",
    }
    data = _request(
        f"{LEGACY}/me/videos",
        method="POST",
        data=urllib.parse.urlencode(fields).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=90,
    )
    vid = str(data.get("id") or "").strip()
    if not vid:
        raise ValueError("Dailymotion did not return a video id.")
    return vid


def publish_video(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    from i18n import t

    if content_type == "photo" or Path(file_path).suffix.lower() in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
    }:
        return False, t("pub.dailymotion.no_photo", lang)

    path = Path(file_path)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.dailymotion.file_missing", lang)
    if path.suffix.lower() not in VIDEO_EXT:
        return False, t("pub.dailymotion.bad_video", lang)

    try:
        token, row = _token_row(account_link_id)
    except ValueError:
        return False, t("pub.dailymotion.no_token", lang)

    label = str(title or "").strip() or "Video"
    desc = str(description or "").strip()
    profile_id = str(row.get("open_id") or "").strip()

    def _send(access: str) -> str:
        try:
            file_url = _upload_v2(access, path)
            if profile_id:
                try:
                    return _create_v2(access, profile_id, file_url, label, desc)
                except ValueError:
                    pass
            return _create_legacy(access, file_url, label, desc)
        except ValueError:
            file_url = _upload_legacy(access, path)
            return _create_legacy(access, file_url, label, desc)

    try:
        try:
            video_id = _send(token)
        except ValueError as e:
            msg = str(e).lower()
            if "token" in msg or "auth" in msg or "401" in msg or "expired" in msg:
                row = _refresh_row(row)
                token = str(row.get("access_token") or "").strip()
                video_id = _send(token)
            else:
                raise
        return True, t("pub.dailymotion.ok", lang, id=video_id)
    except ValueError as e:
        if str(e) == "missing_token":
            return False, t("pub.dailymotion.no_token", lang)
        return False, t("pub.dailymotion.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.dailymotion.upload_fail", lang, error=str(e)[:180])
