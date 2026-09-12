"""Publicación real en Snapchat Public Profile (Stories / Spotlight)."""
from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
import ffmpeg_bin
import snapchat_oauth
import video_probe

API = "https://businessapi.snapchat.com"
UA = "CreatorHub/1.0 (Snapchat Public Profile API)"
CHUNK = 32 * 1024 * 1024
VIDEO_EXT = {".mp4"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}
STORY_MIN = 5.0
SPOTLIGHT_MIN = 6.0
MAX_SECONDS = 55.0
TRIM_SECONDS = 55.0
MIN_W = 540
MIN_H = 960


def locale() -> str:
    return (os.environ.get("SNAPCHAT_LOCALE") or "en_US").strip() or "en_US"


def _debug(message: str) -> None:
    """Registra el fallo en oauth_debug.log para diagnosticar el 403 en producción."""
    try:
        import time

        from db_engine import DATA_DIR

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with (DATA_DIR / "oauth_debug.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} [snapchat] {message}\n")
    except Exception:
        pass


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _api_error(data: dict[str, Any], fallback: str = "") -> str:
    msg = str(
        data.get("display_message")
        or data.get("debug_message")
        or data.get("error_code")
        or data.get("message")
        or ""
    ).strip()
    return (msg or fallback or "Snapchat API error")[:220]


def _is_permission_error(message: str) -> bool:
    low = (message or "").lower()
    return any(
        m in low
        for m in (
            "authorization_permission_denied",
            "permission_denied",
            "permission denied",
            "not authorized",
            "unauthorized",
            "forbidden",
            "http 403",
            " 403",
            "allowlist",
            "access_denied",
        )
    )


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
    return expires - datetime.now(timezone.utc) < timedelta(minutes=5)


def _refresh_row(row: dict[str, Any]) -> dict[str, Any]:
    refresh = str(row.get("refresh_token") or "").strip()
    if not refresh:
        raise ValueError("missing_token")
    data = snapchat_oauth.refresh_access_token(refresh)
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("missing_token")
    new_refresh = str(data.get("refresh_token") or "").strip() or refresh
    expires = data.get("expires_in")
    try:
        expires_in = int(expires) if expires is not None else 3600
    except (TypeError, ValueError):
        expires_in = 3600
    db.update_oauth_tokens(
        str(row["id"]),
        access_token=token,
        refresh_token=new_refresh,
        expires_in=expires_in,
    )
    return db.get_oauth_account_row(str(row["id"])) or row


def _token_row(account_link_id: str | None) -> tuple[str, dict[str, Any]]:
    oid = db.resolve_oauth_account_id("snapchat", account_link_id=account_link_id)
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


def _profile_id(row: dict[str, Any]) -> str:
    return str(row.get("open_id") or "").strip()


def _auth_headers(token: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    hdrs = {"Authorization": f"Bearer {token}", "User-Agent": UA, **(extra or {})}
    return hdrs


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 90,
) -> dict[str, Any]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        parsed = _parse_json(raw)
        detail = _api_error(parsed, raw or str(e))
        # Adjunta el código HTTP para que publish_video distinga 403 (allowlist) de 401 (token).
        raise ValueError(f"http {e.code}: {detail}") from e
    parsed = _parse_json(raw)
    status = str(parsed.get("request_status") or "").upper()
    if parsed and status not in ("", "SUCCESS", "PARTIAL"):
        raise ValueError(_api_error(parsed, raw))
    return parsed


def _json_post(url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    return _request(
        url,
        method="POST",
        data=body,
        headers=_auth_headers(token, {"Content-Type": "application/json", "Accept": "application/json"}),
        timeout=60,
    )


def _multipart(fields: dict[str, str], file_field: str | None, filename: str, blob: bytes | None) -> tuple[bytes, str]:
    boundary = "----SnapUpload" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    if file_field and blob is not None:
        safe = filename.replace('"', "")
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{file_field}"; filename="{safe}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(blob)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _upload_url(path: str) -> str:
    raw = (path or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if not raw.startswith("/"):
        raw = "/" + raw
    return API + raw


def _encrypt_file(src: Path) -> tuple[Path, str, str]:
    key = os.urandom(32)
    iv = os.urandom(16)
    dest = Path(tempfile.gettempdir()) / f"snap_enc_{uuid.uuid4().hex}.bin"
    try:
        _encrypt_aes_cbc(src, dest, key, iv)
    except ImportError:
        dest.unlink(missing_ok=True)
        _encrypt_file_openssl(src, dest, key, iv)
    except Exception:
        dest.unlink(missing_ok=True)
        try:
            _encrypt_file_openssl(src, dest, key, iv)
        except ValueError:
            raise
    if not dest.is_file() or dest.stat().st_size <= 0:
        dest.unlink(missing_ok=True)
        raise ValueError("need_openssl")
    return dest, base64.b64encode(key).decode("ascii"), base64.b64encode(iv).decode("ascii")


def _encrypt_file_openssl(src: Path, dest: Path, key: bytes, iv: bytes) -> None:
    cmd = [
        "openssl",
        "enc",
        "-aes-256-cbc",
        "-nosalt",
        "-e",
        "-in",
        str(src),
        "-out",
        str(dest),
        "-K",
        key.hex(),
        "-iv",
        iv.hex(),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except FileNotFoundError as e:
        dest.unlink(missing_ok=True)
        raise ValueError("need_openssl") from e
    except (subprocess.SubprocessError, OSError) as e:
        dest.unlink(missing_ok=True)
        raise ValueError(str(e)[:180]) from e


def _encrypt_aes_cbc(src: Path, dest: Path, key: bytes, iv: bytes) -> None:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7

    padder = PKCS7(128).padder()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    with src.open("rb") as inf, dest.open("wb") as out:
        while True:
            chunk = inf.read(1024 * 1024)
            if not chunk:
                break
            out.write(encryptor.update(padder.update(chunk)))
        out.write(encryptor.update(padder.finalize()) + encryptor.finalize())


def _create_media(token: str, profile_id: str, media_type: str, name: str, key_b64: str, iv_b64: str) -> dict[str, Any]:
    data = _json_post(
        f"{API}/v1/public_profiles/{profile_id}/media",
        token,
        {"type": media_type, "name": name[:80] or "media", "key": key_b64, "iv": iv_b64},
    )
    media_id = str(data.get("media_id") or "").strip()
    add_path = str(data.get("add_path") or "").strip()
    fin_path = str(data.get("finalize_path") or add_path).strip()
    if not media_id or not add_path:
        raise ValueError(_api_error(data, "Snapchat did not return a media upload path."))
    return {"media_id": media_id, "add_path": add_path, "finalize_path": fin_path}


def _upload_encrypted(token: str, add_path: str, fin_path: str, enc_path: Path) -> None:
    raw = enc_path.read_bytes()
    part = 1
    add_url = _upload_url(add_path)
    for i in range(0, max(len(raw), 1), CHUNK):
        chunk = raw[i : i + CHUNK]
        body, ctype = _multipart(
            {"action": "ADD", "part_number": str(part)},
            "file",
            f"part{part}.bin",
            chunk,
        )
        _request(
            add_url,
            method="POST",
            data=body,
            headers=_auth_headers(token, {"Content-Type": ctype}),
            timeout=180,
        )
        part += 1
    fin_body, fin_ctype = _multipart({"action": "FINALIZE"}, None, "", None)
    _request(
        _upload_url(fin_path),
        method="POST",
        data=fin_body,
        headers=_auth_headers(token, {"Content-Type": fin_ctype}),
        timeout=90,
    )


def _post_story(token: str, profile_id: str, media_id: str) -> str:
    data = _json_post(
        f"{API}/v1/public_profiles/{profile_id}/stories",
        token,
        {"media_id": media_id},
    )
    return str(data.get("story_id") or data.get("request_id") or media_id)


def _post_spotlight(token: str, profile_id: str, media_id: str, description: str) -> str:
    data = _json_post(
        f"{API}/v1/public_profiles/{profile_id}/spotlights",
        token,
        {
            "media_id": media_id,
            "skip_save_to_profile": False,
            "description": (description or "")[:160],
            "locale": locale(),
        },
    )
    sid = str(data.get("spotlight_id") or "").strip()
    if not sid:
        raise ValueError(_api_error(data, "Snapchat did not return a spotlight id."))
    return sid


def _trim_to_seconds(src: Path, seconds: float) -> Path | None:
    """Corta los primeros `seconds` a un MP4 temporal. El original no se toca."""
    tmp = Path(tempfile.gettempdir()) / f"snap_trim_{uuid.uuid4().hex}.mp4"
    t_arg = f"{seconds:.3f}"
    attempts = (
        [
            ffmpeg_bin.ffmpeg_exe(),
            "-y",
            "-i",
            str(src),
            "-t",
            t_arg,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(tmp),
        ],
        [
            ffmpeg_bin.ffmpeg_exe(),
            "-y",
            "-i",
            str(src),
            "-t",
            t_arg,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(tmp),
        ],
    )
    for cmd in attempts:
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            tmp.unlink(missing_ok=True)
            continue
        if tmp.is_file() and tmp.stat().st_size > 0:
            return tmp
        tmp.unlink(missing_ok=True)
    return None


def clip_for_snapchat(path: Path, content_type: str) -> tuple[Path, Path | None]:
    """Si el video pasa de 55 s, recorta a los primeros 55 s. El original no se toca."""
    src = Path(path)
    if content_type == "photo" or src.suffix.lower() in PHOTO_EXT:
        return src, None
    meta = video_probe.probe_video(src)
    duration = meta.get("duration_seconds")
    try:
        seconds = float(duration) if duration is not None else None
    except (TypeError, ValueError):
        seconds = None
    if seconds is not None and seconds <= TRIM_SECONDS + 0.05:
        return src, None
    trimmed = _trim_to_seconds(src, TRIM_SECONDS)
    if not trimmed:
        raise ValueError("trim_failed")
    return trimmed, trimmed


def _send_file(
    token: str,
    profile_id: str,
    path: Path,
    media_type: str,
    as_spotlight: bool,
    description: str,
) -> str:
    enc: Path | None = None
    try:
        enc, key_b64, iv_b64 = _encrypt_file(path)
        created = _create_media(token, profile_id, media_type, path.stem, key_b64, iv_b64)
        _upload_encrypted(token, created["add_path"], created["finalize_path"], enc)
        media_id = created["media_id"]
        if as_spotlight:
            return _post_spotlight(token, profile_id, media_id, description)
        return _post_story(token, profile_id, media_id)
    finally:
        if enc:
            try:
                enc.unlink(missing_ok=True)
            except OSError:
                pass


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

    path = Path(file_path)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.snapchat.file_missing", lang)

    suffix = path.suffix.lower()
    is_photo = content_type == "photo" or suffix in PHOTO_EXT
    if is_photo:
        if suffix not in PHOTO_EXT:
            return False, t("pub.snapchat.bad_photo", lang)
        media_type = "IMAGE"
        as_spotlight = False
    else:
        if suffix not in VIDEO_EXT:
            return False, t("pub.snapchat.bad_video", lang)
        media_type = "VIDEO"
        as_spotlight = True

    caption = (description or "").strip()
    trim_tmp: Path | None = None
    if not is_photo:
        try:
            path, trim_tmp = clip_for_snapchat(path, content_type)
        except ValueError:
            return False, t("pub.snapchat.trim_fail", lang)
        meta = video_probe.probe_video(path)
        duration = meta.get("duration_seconds")
        width = meta.get("width")
        height = meta.get("height")
        if duration is not None:
            try:
                seconds = float(duration)
            except (TypeError, ValueError):
                seconds = None
            else:
                if seconds < STORY_MIN or seconds > MAX_SECONDS + 0.05:
                    if trim_tmp:
                        trim_tmp.unlink(missing_ok=True)
                    return False, t("pub.snapchat.bad_duration", lang)
                as_spotlight = seconds >= SPOTLIGHT_MIN
        else:
            as_spotlight = True
        if width and height:
            try:
                if int(width) < MIN_W or int(height) < MIN_H:
                    if trim_tmp:
                        trim_tmp.unlink(missing_ok=True)
                    return False, t("pub.snapchat.bad_size", lang)
            except (TypeError, ValueError):
                pass

    try:
        token, row = _token_row(account_link_id)
    except ValueError:
        if trim_tmp:
            trim_tmp.unlink(missing_ok=True)
        return False, t("pub.snapchat.no_token", lang)
    profile_id = _profile_id(row)
    if not profile_id:
        if trim_tmp:
            trim_tmp.unlink(missing_ok=True)
        return False, t("pub.snapchat.no_profile", lang)

    def _run(access: str) -> str:
        return _send_file(access, profile_id, path, media_type, as_spotlight, caption)

    try:
        try:
            result_id = _run(token)
        except ValueError as e:
            msg = str(e).lower()
            if str(e) == "need_openssl":
                return False, t("pub.snapchat.need_openssl", lang)
            # 403 = permisos/allowlist (no se reintenta). 401/token caducado → refrescar y reintentar.
            is_403 = "http 403" in msg
            is_401 = not is_403 and (
                "http 401" in msg or "401" in msg or "expired" in msg or "unauthorized" in msg
            )
            if is_401:
                row = _refresh_row(row)
                token = str(row.get("access_token") or "").strip()
                result_id = _run(token)
            else:
                raise
        if as_spotlight:
            return True, t("pub.snapchat.ok_spotlight", lang, id=result_id)
        return True, t("pub.snapchat.ok_story", lang, id=result_id)
    except ValueError as e:
        if str(e) == "missing_token":
            return False, t("pub.snapchat.no_token", lang)
        if str(e) == "need_openssl":
            return False, t("pub.snapchat.need_openssl", lang)
        if "http 403" in str(e).lower() or _is_permission_error(str(e)):
            _debug(f"publish 403/permiso: {str(e)[:200]}")
            return False, t("pub.snapchat.need_allowlist", lang)
        return False, t("pub.snapchat.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.snapchat.upload_fail", lang, error=str(e)[:180])
    finally:
        if trim_tmp:
            try:
                trim_tmp.unlink(missing_ok=True)
            except OSError:
                pass
