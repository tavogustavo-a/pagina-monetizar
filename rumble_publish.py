"""Publicación real de video en Rumble (Upload API de partners)."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import db
import ffmpeg_bin

UPLOAD_URL = "https://rumble.com/api/simple-upload.php"
UA = "CreatorHub/1.0 (Rumble Upload API)"
VIDEO_EXT = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".m4v"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _from_creds(key: str) -> str:
    try:
        raw = db.get_platform_credentials_raw("rumble") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def access_token() -> str:
    try:
        return db.cred_value("rumble", "access_token", os.environ.get("RUMBLE_ACCESS_TOKEN") or "")
    except Exception:
        return (os.environ.get("RUMBLE_ACCESS_TOKEN") or "").strip() or _from_creds("access_token")


def channel_id() -> str:
    try:
        return db.cred_value("rumble", "extra", os.environ.get("RUMBLE_CHANNEL_ID") or "")
    except Exception:
        return (os.environ.get("RUMBLE_CHANNEL_ID") or "").strip() or _from_creds("extra")


def license_type() -> str:
    raw = (os.environ.get("RUMBLE_LICENSE_TYPE") or "0").strip() or "0"
    return raw


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _error_text(data: dict[str, Any], fallback: str = "") -> str:
    errs = data.get("errors")
    parts: list[str] = []
    if isinstance(errs, dict):
        for key, val in errs.items():
            if isinstance(val, dict):
                msg = str(val.get("message") or val.get("code") or "").strip()
                parts.append(f"{key}: {msg}" if msg else str(key))
            else:
                parts.append(f"{key}: {val}")
    elif isinstance(errs, list):
        parts.extend(str(x) for x in errs if x)
    msg = str(data.get("message") or data.get("error") or "").strip()
    if msg:
        parts.append(msg)
    text = "; ".join(parts).strip()
    return (text or fallback or "Rumble API error")[:220]


def _auth_failed(data: dict[str, Any]) -> bool:
    errs = data.get("errors")
    if isinstance(errs, dict) and errs.get("access_token"):
        return True
    blob = json.dumps(data).lower()
    return "unauthorized_client" in blob or "access token or user not found" in blob


def _multipart(fields: dict[str, str], files: list[tuple[str, str, str, bytes]]) -> tuple[bytes, str]:
    boundary = "----RumbleUpload" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    for field, filename, ctype, raw in files:
        safe = filename.replace('"', "")
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field}"; filename="{safe}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(raw)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _post(
    fields: dict[str, str],
    files: list[tuple[str, str, str, bytes]] | None = None,
    *,
    timeout: int = 180,
) -> dict[str, Any]:
    body, content_type = _multipart(fields, files or [])
    req = urllib.request.Request(
        UPLOAD_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": content_type,
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        status = e.code
        data = _parse_json(raw)
        raise ValueError(_error_text(data, raw or f"HTTP {status}")) from e
    data = _parse_json(raw)
    if not data:
        raise ValueError((raw or f"HTTP {status}")[:220])
    if data.get("success") is False or _auth_failed(data):
        raise ValueError(_error_text(data, raw))
    return data


def probe_token(token: str | None = None, channel: str | None = None) -> tuple[bool, str]:
    """Comprueba el token contra la Upload API (sin enviar video)."""
    token = (token or access_token()).strip()
    if not token:
        return False, "missing_token"
    fields = {
        "access_token": token,
        "title": "token-check",
        "description": "token-check",
        "license_type": license_type(),
    }
    cid = (channel if channel is not None else channel_id()).strip()
    if cid:
        fields["channel_id"] = cid
    body, content_type = _multipart(fields, [])
    req = urllib.request.Request(
        UPLOAD_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": content_type,
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
    data = _parse_json(raw)
    if _auth_failed(data):
        return False, _error_text(data, raw or "unauthorized")
    if data.get("success") is True:
        return True, "ok"
    errs = data.get("errors")
    if isinstance(errs, dict) and errs and "access_token" not in errs:
        return True, "ok"
    if data:
        return True, "ok"
    return False, (raw or "empty")[:180]


def _extract_thumb(path: Path) -> Path | None:
    tmp = Path(tempfile.gettempdir()) / f"rumble_thumb_{uuid.uuid4().hex}.jpg"
    cmd = [
        ffmpeg_bin.ffmpeg_exe(),
        "-y",
        "-ss",
        "1",
        "-i",
        str(path),
        "-frames:v",
        "1",
        "-q:v",
        "3",
        str(tmp),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
    if tmp.is_file() and tmp.stat().st_size > 0:
        return tmp
    return None


def _result_id(data: dict[str, Any]) -> str:
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    for key in ("url", "video_id", "id", "fid", "watch"):
        val = str(inner.get(key) or data.get(key) or "").strip()
        if val:
            return val
    return "ok"


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

    _ = account_link_id
    path = Path(file_path)
    if content_type == "photo" or path.suffix.lower() in PHOTO_EXT:
        return False, t("pub.rumble.no_photo", lang)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.rumble.file_missing", lang)
    if path.suffix.lower() not in VIDEO_EXT:
        return False, t("pub.rumble.bad_video", lang)

    token = access_token()
    if not token:
        return False, t("pub.rumble.no_token", lang)
    cid = channel_id()
    if not cid:
        return False, t("pub.rumble.no_channel", lang)

    fields = {
        "access_token": token,
        "title": (title or "Video").strip()[:200] or "Video",
        "description": (description or "").strip()[:5000],
        "license_type": license_type(),
        "channel_id": cid,
    }
    files: list[tuple[str, str, str, bytes]] = [
        ("video", path.name, "video/mp4", path.read_bytes()),
    ]
    thumb = _extract_thumb(path)
    try:
        if thumb:
            files.append(("thumb", thumb.name, "image/jpeg", thumb.read_bytes()))
        data = _post(fields, files, timeout=300)
        return True, t("pub.rumble.ok", lang, id=_result_id(data))
    except ValueError as e:
        return False, t("pub.rumble.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.rumble.upload_fail", lang, error=str(e)[:180])
    finally:
        if thumb:
            try:
                thumb.unlink(missing_ok=True)
            except OSError:
                pass
