"""Subida real a TikTok (Content Posting API).

Usa Direct Post si la cuenta tiene el alcance `video.publish`.
Si no, deja el video en la bandeja de TikTok (`video.upload`) para publicarlo
desde la app.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
import tiktok_oauth

INIT_INBOX_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
INIT_DIRECT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

MAX_CHUNK = 64 * 1024 * 1024
REFRESH_SKEW = timedelta(minutes=10)
TITLE_MAX = 2200


def _tiktok_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        code = str(err.get("code") or "").strip()
        msg = str(err.get("message") or "").strip()
        if code and code.lower() not in ("ok", "0", ""):
            return f"{code}: {msg}".strip(": ")
        if msg:
            return msg
    return (fallback or "TikTok API error")[:300]


def _json_request(
    url: str,
    *,
    token: str,
    payload: dict[str, Any],
    timeout: int = 45,
) -> tuple[int, dict[str, Any], str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        status = e.code
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return status, data, raw


def _token_needs_refresh(row: dict[str, Any]) -> bool:
    raw = str(row.get("token_expires_at") or "").strip()
    if not raw:
        return False
    try:
        exp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return datetime.now(timezone.utc) >= (exp - REFRESH_SKEW)


def ensure_access_token(config_id: str, *, force_refresh: bool = False) -> str:
    row = db.get_tiktok_oauth_row(config_id)
    if not row:
        raise ValueError("missing_account")
    token = str(row.get("access_token") or "").strip()
    refresh = str(row.get("refresh_token") or "").strip()
    if token and not force_refresh and not _token_needs_refresh(row):
        return token
    if not refresh:
        if token and not force_refresh:
            return token
        raise ValueError("missing_token")
    data = tiktok_oauth.refresh_access_token(
        refresh,
        client_key_value=str(row.get("client_key") or ""),
        client_secret_value=str(row.get("client_secret") or ""),
    )
    new_token = str(data.get("access_token") or "").strip()
    if not new_token:
        raise ValueError("refresh_fail")
    db.update_tiktok_oauth_tokens(
        config_id,
        access_token=new_token,
        refresh_token=str(data.get("refresh_token") or refresh),
        expires_in=int(data["expires_in"]) if data.get("expires_in") else None,
    )
    return new_token


def _chunk_plan(size: int) -> tuple[int, int]:
    if size <= 0:
        raise ValueError("empty_file")
    if size <= MAX_CHUNK:
        return size, 1
    chunk = MAX_CHUNK
    count = (size + chunk - 1) // chunk
    return chunk, count


def _privacy_level() -> str:
    raw = (os.environ.get("TIKTOK_PRIVACY_LEVEL") or "SELF_ONLY").strip().upper()
    allowed = {
        "PUBLIC_TO_EVERYONE",
        "MUTUAL_FOLLOW_FRIENDS",
        "FOLLOWER_OF_CREATOR",
        "SELF_ONLY",
    }
    return raw if raw in allowed else "SELF_ONLY"


def _caption(title: str, description: str) -> str:
    parts = [str(title or "").strip(), str(description or "").strip()]
    text = "\n\n".join(p for p in parts if p)
    return text[:TITLE_MAX]


def _can_direct_post(row: dict[str, Any]) -> bool:
    scopes = str(row.get("oauth_scopes") or "").lower()
    return "video.publish" in scopes


def _put_chunk(url: str, chunk: bytes, start: int, total: int) -> tuple[int, str]:
    end = start + len(chunk) - 1
    req = urllib.request.Request(
        url,
        data=chunk,
        method="PUT",
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(len(chunk)),
            "Content-Range": f"bytes {start}-{end}/{total}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body


def _upload_file(upload_url: str, path: Path) -> None:
    size = path.stat().st_size
    chunk_size, _count = _chunk_plan(size)
    with path.open("rb") as fh:
        start = 0
        while start < size:
            data = fh.read(chunk_size)
            if not data:
                break
            status, body = _put_chunk(upload_url, data, start, size)
            if status >= 400:
                raise ValueError(body[:240] or f"HTTP {status}")
            start += len(data)


def _wait_status(token: str, publish_id: str) -> str:
    last = ""
    for _ in range(8):
        status, data, raw = _json_request(
            STATUS_URL, token=token, payload={"publish_id": publish_id}, timeout=30
        )
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        last = str(inner.get("status") or "")
        if last in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX", "FAILED"):
            if last == "FAILED":
                fail = inner.get("fail_reason") or _tiktok_error(data, raw)
                raise ValueError(str(fail)[:240])
            return last
        time.sleep(1.5)
    return last or "PROCESSING"


def publish_video(
    *,
    file_path: Path,
    title: str,
    description: str,
    lang: str,
    config_id: str | None = None,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    from i18n import t

    cid = db.resolve_tiktok_config_id(
        config_id=config_id, account_link_id=account_link_id
    )
    if not cid:
        return False, t("pub.fail_tiktok_token", lang)
    row = db.get_tiktok_oauth_row(cid)
    if not row:
        return False, t("pub.fail_tiktok_token", lang)

    path = Path(file_path)
    if not path.is_file():
        return False, t("pub.tiktok.file_missing", lang)
    size = path.stat().st_size
    if size <= 0:
        return False, t("pub.tiktok.file_missing", lang)

    try:
        token = ensure_access_token(cid)
    except ValueError as e:
        key = str(e)
        if key in ("missing_account", "missing_token", "refresh_fail"):
            return False, t("pub.tiktok.refresh_fail", lang)
        return False, t("pub.tiktok.upload_fail", lang, error=str(e)[:180])

    chunk_size, chunk_count = _chunk_plan(size)
    source_info = {
        "source": "FILE_UPLOAD",
        "video_size": size,
        "chunk_size": chunk_size,
        "total_chunk_count": chunk_count,
    }
    use_direct = _can_direct_post(row)
    if use_direct:
        post_info = {
            "privacy_level": _privacy_level(),
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        }
        caption = _caption(title, description)
        if caption:
            post_info["title"] = caption
        payload = {
            "post_info": post_info,
            "source_info": source_info,
        }
        init_url = INIT_DIRECT_URL
    else:
        payload = {"source_info": source_info}
        init_url = INIT_INBOX_URL

    try:
        status, data, raw = _json_request(init_url, token=token, payload=payload)
        if status in (401, 403):
            token = ensure_access_token(cid, force_refresh=True)
            status, data, raw = _json_request(init_url, token=token, payload=payload)
        err = data.get("error") if isinstance(data.get("error"), dict) else {}
        if status >= 400 or str(err.get("code") or "ok").lower() not in ("ok", ""):
            return False, t(
                "pub.tiktok.upload_fail",
                lang,
                error=_tiktok_error(data, raw)[:180],
            )
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        upload_url = str(inner.get("upload_url") or "").strip()
        publish_id = str(inner.get("publish_id") or "").strip()
        if not upload_url:
            return False, t(
                "pub.tiktok.upload_fail", lang, error="missing upload_url"
            )
        _upload_file(upload_url, path)
        if publish_id:
            try:
                _wait_status(token, publish_id)
            except ValueError as e:
                return False, t("pub.tiktok.upload_fail", lang, error=str(e)[:180])
        if use_direct:
            return True, t("pub.tiktok.direct_ok", lang)
        return True, t("pub.tiktok.inbox_ok", lang)
    except ValueError as e:
        return False, t("pub.tiktok.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.tiktok.upload_fail", lang, error=str(e)[:180])
