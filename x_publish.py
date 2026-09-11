"""Publicación real en X (tweets con foto o video vía Media Upload v2)."""
from __future__ import annotations

import json
import time
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
import x_oauth

API_HOSTS = ("https://api.x.com/2", "https://api.twitter.com/2")
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}
GIF_EXT = {".gif"}
VIDEO_EXT = {".mp4", ".mov", ".m4v"}
TEXT_MAX = 280
CHUNK = 4 * 1024 * 1024
MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".m4v": "video/mp4",
}


def _api_error(data: dict[str, Any], fallback: str) -> str:
    if data.get("detail"):
        return str(data.get("detail"))[:220]
    if data.get("title"):
        return str(data.get("title"))[:220]
    errs = data.get("errors")
    if isinstance(errs, list) and errs:
        first = errs[0]
        if isinstance(first, dict):
            msg = str(first.get("message") or first.get("detail") or "").strip()
            if msg:
                return msg[:220]
    return (fallback or "X API error")[:220]


def _is_credits_error(err: str) -> bool:
    low = (err or "").lower()
    return "credit" in low or "usagecap" in low or "usage cap" in low or "429" in low
    if data.get("detail"):
        return str(data.get("detail"))[:220]
    if data.get("title"):
        return str(data.get("title"))[:220]
    errs = data.get("errors")
    if isinstance(errs, list) and errs:
        first = errs[0]
        if isinstance(first, dict):
            msg = str(first.get("message") or first.get("detail") or "").strip()
            if msg:
                return msg[:220]
    return (fallback or "X API error")[:220]


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
        return True
    return expires - datetime.now(timezone.utc) < timedelta(minutes=10)


def _refresh_row(row: dict[str, Any]) -> dict[str, Any]:
    refresh = str(row.get("refresh_token") or "").strip()
    if not refresh:
        raise ValueError("missing_token")
    data = x_oauth.refresh_access_token(refresh)
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("missing_token")
    new_refresh = str(data.get("refresh_token") or "").strip() or refresh
    expires_in = data.get("expires_in")
    db.update_oauth_tokens(
        str(row["id"]),
        access_token=token,
        refresh_token=new_refresh,
        expires_in=int(expires_in) if expires_in is not None else 7200,
    )
    return db.get_oauth_account_row(str(row["id"])) or row


def _token_row(account_link_id: str | None) -> tuple[str, dict[str, Any]]:
    oid = db.resolve_oauth_account_id("x", account_link_id=account_link_id)
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


def _caption(title: str, description: str) -> str:
    parts = [str(title or "").strip(), str(description or "").strip()]
    text = "\n\n".join(p for p in parts if p)
    if len(text) <= TEXT_MAX:
        return text
    return text[: TEXT_MAX - 1].rstrip() + "…"


def _request(
    url: str,
    token: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    hdrs = {"Authorization": f"Bearer {token}", **(headers or {})}
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        parsed = _parse_json(raw)
        raise ValueError(_api_error(parsed, raw or str(e))) from e
    parsed = _parse_json(raw)
    if parsed.get("errors") and not parsed.get("data"):
        raise ValueError(_api_error(parsed, raw))
    return parsed


def _json_post(url: str, token: str, payload: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    return _request(
        url,
        token,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )


def _try_hosts(path: str, token: str, sender) -> dict[str, Any]:
    last = ValueError("X API error")
    for host in API_HOSTS:
        try:
            return sender(f"{host}{path}", token)
        except ValueError as e:
            last = e
    raise last


def _multipart(fields: dict[str, str], file_field: str, chunk: bytes, filename: str) -> tuple[bytes, str]:
    boundary = "----XBoundary" + uuid.uuid4().hex
    parts: list[bytes] = []
    for key, value in fields.items():
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(chunk)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _category(suffix: str) -> str:
    if suffix in GIF_EXT:
        return "tweet_gif"
    if suffix in VIDEO_EXT:
        return "tweet_video"
    return "tweet_image"


def _media_id_from(data: dict[str, Any]) -> str:
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    mid = str(inner.get("id") or inner.get("media_id") or inner.get("media_id_string") or "").strip()
    if not mid:
        raise ValueError("X did not return a media id.")
    return mid


def _initialize(token: str, path: Path, mime: str, category: str) -> str:
    payload = {
        "media_type": mime,
        "total_bytes": path.stat().st_size,
        "media_category": category,
    }

    def send(url: str, access: str) -> dict[str, Any]:
        return _json_post(url, access, payload)

    data = _try_hosts("/media/upload/initialize", token, send)
    return _media_id_from(data)


def _append(token: str, media_id: str, index: int, chunk: bytes) -> None:
    body, ctype = _multipart({"segment_index": str(index)}, "media", chunk, f"chunk{index}")

    def send(url: str, access: str) -> dict[str, Any]:
        return _request(
            url,
            access,
            method="POST",
            data=body,
            headers={"Content-Type": ctype},
            timeout=120,
        )

    _try_hosts(f"/media/upload/{media_id}/append", token, send)


def _finalize(token: str, media_id: str) -> dict[str, Any]:
    def send(url: str, access: str) -> dict[str, Any]:
        return _json_post(url, access, {})

    return _try_hosts(f"/media/upload/{media_id}/finalize", token, send)


def _status(token: str, media_id: str) -> dict[str, Any]:
    def send(url: str, access: str) -> dict[str, Any]:
        return _request(f"{url}?command=STATUS&media_id={media_id}", access)

    return _try_hosts("/media/upload", token, send)


def _wait_processed(token: str, media_id: str, finalize_data: dict[str, Any]) -> None:
    info = finalize_data.get("processing_info")
    if not info and isinstance(finalize_data.get("data"), dict):
        info = finalize_data["data"].get("processing_info")
    if not isinstance(info, dict):
        return
    for _ in range(40):
        state = str(info.get("state") or "").lower()
        if state in {"succeeded", "success"}:
            return
        if state in {"failed", "error"}:
            err = info.get("error") if isinstance(info.get("error"), dict) else {}
            raise ValueError(str(err.get("message") or state)[:220])
        wait = int(info.get("check_after_secs") or 3)
        time.sleep(max(1, min(wait, 15)))
        data = _status(token, media_id)
        inner = data.get("data") if isinstance(data.get("data"), dict) else data
        info = inner.get("processing_info") if isinstance(inner, dict) else None
        if not isinstance(info, dict):
            return
    raise ValueError("timeout")


def _upload_media(token: str, path: Path) -> str:
    suffix = path.suffix.lower()
    mime = MIME.get(suffix, "application/octet-stream")
    media_id = _initialize(token, path, mime, _category(suffix))
    raw = path.read_bytes()
    for i in range(0, len(raw), CHUNK):
        _append(token, media_id, i // CHUNK, raw[i : i + CHUNK])
    finalized = _finalize(token, media_id)
    _wait_processed(token, media_id, finalized)
    return media_id


def _create_tweet(token: str, text: str, media_id: str) -> str:
    payload: dict[str, Any] = {"media": {"media_ids": [media_id]}}
    if text:
        payload["text"] = text

    def send(url: str, access: str) -> dict[str, Any]:
        return _json_post(url, access, payload)

    data = _try_hosts("/tweets", token, send)
    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
    tweet_id = str(inner.get("id") or "").strip()
    if not tweet_id:
        raise ValueError("X did not return a post id.")
    return tweet_id


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
        return False, t("pub.x.file_missing", lang)

    suffix = path.suffix.lower()
    allowed = PHOTO_EXT | GIF_EXT | VIDEO_EXT
    is_photo = content_type == "photo" or suffix in PHOTO_EXT | GIF_EXT
    is_video = content_type == "video" or suffix in VIDEO_EXT
    if is_photo and suffix not in PHOTO_EXT | GIF_EXT:
        return False, t("pub.x.bad_photo", lang)
    if is_video and suffix not in VIDEO_EXT:
        return False, t("pub.x.bad_video", lang)
    if suffix not in allowed:
        return False, t("pub.x.bad_file", lang)

    try:
        token, row = _token_row(account_link_id)
    except ValueError:
        return False, t("pub.x.no_token", lang)

    if not x_oauth.oauth_configured():
        if db.x_app_mode() == "own":
            return False, t("pub.x.need_own_api", lang)
        return False, t("pub.x.need_funding_api", lang)

    text = _caption(title, description)

    try:
        try:
            media_id = _upload_media(token, path)
            tweet_id = _create_tweet(token, text, media_id)
        except ValueError as e:
            msg = str(e).lower()
            if _is_credits_error(msg):
                raise
            if "unauthorized" in msg or "expired" in msg or "token" in msg or "401" in msg:
                row = _refresh_row(row)
                token = str(row.get("access_token") or "").strip()
                media_id = _upload_media(token, path)
                tweet_id = _create_tweet(token, text, media_id)
            else:
                raise
        if is_video:
            return True, t("pub.x.video_ok", lang, id=tweet_id)
        return True, t("pub.x.photo_ok", lang, id=tweet_id)
    except ValueError as e:
        if str(e) == "missing_token":
            return False, t("pub.x.no_token", lang)
        if _is_credits_error(str(e)):
            return False, t("pub.x.credits_depleted", lang)
        return False, t("pub.x.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.x.upload_fail", lang, error=str(e)[:180])
