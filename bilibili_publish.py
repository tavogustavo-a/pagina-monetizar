"""Publicación real de video en Bilibili (Open Platform 投稿)."""
from __future__ import annotations

import json
import os
import random
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import db
import ffmpeg_bin
import bilibili_oauth
import video_probe

INIT_URL = "https://member.bilibili.com/arcopen/fn/archive/video/init"
PART_URL = "https://openupos.bilivideo.com/video/v2/part/upload"
COMPLETE_URL = "https://member.bilibili.com/arcopen/fn/archive/video/complete"
COVER_URL = "https://member.bilibili.com/arcopen/fn/archive/cover/upload"
ADD_URL = "https://member.bilibili.com/arcopen/fn/archive/add-by-utoken"
TYPE_URL = "https://member.bilibili.com/arcopen/fn/archive/type/list"
UA = "CreatorHub/1.0 (Bilibili Open Platform)"
VIDEO_EXT = {".mp4", ".flv", ".avi", ".wmv", ".mov", ".mkv", ".webm"}
CHUNK = 4 * 1024 * 1024
TITLE_MAX = 80
COVER_W = 1146
COVER_H = 717


def _tid() -> int:
    raw = (os.environ.get("BILIBILI_TID") or "21").strip()
    try:
        return int(raw)
    except ValueError:
        return 21


def _tag() -> str:
    return (os.environ.get("BILIBILI_TAG") or "生活").strip() or "生活"


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _api_error(data: dict[str, Any], fallback: str) -> str:
    msg = str(data.get("message") or data.get("msg") or "").strip()
    if msg and msg not in {"0", "ok", "success"}:
        return msg[:220]
    return (fallback or "Bilibili API error")[:220]


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
    data = bilibili_oauth.refresh_access_token(refresh)
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("missing_token")
    new_refresh = str(data.get("refresh_token") or "").strip() or refresh
    db.update_oauth_tokens(
        str(row["id"]),
        access_token=token,
        refresh_token=new_refresh,
        expires_in=bilibili_oauth.expires_seconds(data.get("expires_in")),
    )
    return db.get_oauth_account_row(str(row["id"])) or row


def _token_row(account_link_id: str | None) -> tuple[str, dict[str, Any]]:
    oid = db.resolve_oauth_account_id("bilibili", account_link_id=account_link_id)
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


def _auth_q(token: str) -> str:
    return urllib.parse.urlencode(
        {"client_id": bilibili_oauth.client_id(), "access_token": token}
    )


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    hdrs = {"User-Agent": UA, **(headers or {})}
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        parsed = _parse_json(raw)
        raise ValueError(_api_error(parsed, raw or str(e))) from e
    parsed = _parse_json(raw)
    code = parsed.get("code")
    if parsed and code not in (None, 0, "0"):
        raise ValueError(_api_error(parsed, raw))
    return parsed


def _json_post(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
    return _request(
        url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"},
        timeout=90,
    )


def _data(resp: dict[str, Any]) -> dict[str, Any]:
    inner = resp.get("data")
    return inner if isinstance(inner, dict) else {}


def _cover_seek_seconds(path: Path) -> float:
    """Un instante al azar del video (evita el primer fotograma negro)."""
    meta = video_probe.probe_video(path)
    try:
        duration = float(meta.get("duration_seconds") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 1.2:
        return 0.4 if duration > 0.5 else 0.0
    lo = max(0.5, duration * 0.08)
    hi = min(duration - 0.4, duration * 0.85)
    if hi <= lo:
        return max(0.5, duration / 2)
    return random.uniform(lo, hi)


def _extract_cover(path: Path) -> Path | None:
    tmp = Path(tempfile.gettempdir()) / f"bili_cover_{uuid.uuid4().hex}.jpg"
    ss = _cover_seek_seconds(path)
    vf = (
        f"scale={COVER_W}:{COVER_H}:force_original_aspect_ratio=increase,"
        f"crop={COVER_W}:{COVER_H}"
    )
    cmd = [
        ffmpeg_bin.ffmpeg_exe(),
        "-y",
        "-ss",
        f"{ss:.3f}",
        "-i",
        str(path),
        "-frames:v",
        "1",
        "-vf",
        vf,
        "-q:v",
        "3",
        str(tmp),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=45)
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
    if tmp.is_file() and tmp.stat().st_size > 0:
        return tmp
    return None


def _upload_cover(token: str, cover: Path) -> str:
    boundary = "----BiliCover" + uuid.uuid4().hex
    name = cover.name.replace('"', "")
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8")
    body = head + cover.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    data = _request(
        f"{COVER_URL}?{_auth_q(token)}",
        method="POST",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        timeout=60,
    )
    url = str(_data(data).get("url") or data.get("url") or "").strip()
    if not url:
        raise ValueError("Bilibili did not return a cover URL.")
    return url


def _pick_tid(token: str) -> int:
    configured = _tid()
    try:
        data = _request(f"{TYPE_URL}?{_auth_q(token)}")
    except ValueError:
        return configured
    items = data.get("data")
    rows: list[Any] = items if isinstance(items, list) else []
    if isinstance(items, dict):
        rows = items.get("typelist") or items.get("list") or []
    ids: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            ids.append(int(row.get("id") or row.get("tid") or 0))
        except (TypeError, ValueError):
            continue
        children = row.get("children") or row.get("sub") or []
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    try:
                        ids.append(int(child.get("id") or child.get("tid") or 0))
                    except (TypeError, ValueError):
                        continue
    ids = [i for i in ids if i > 0]
    if configured in ids or not ids:
        return configured
    return ids[0]


def _upload_video(token: str, path: Path) -> str:
    init = _json_post(f"{INIT_URL}?{_auth_q(token)}", {"name": path.name})
    u_token = str(_data(init).get("upload_token") or "").strip()
    if not u_token:
        raise ValueError("Bilibili did not return an upload token.")
    raw = path.read_bytes()
    part = 1
    for i in range(0, len(raw), CHUNK):
        chunk = raw[i : i + CHUNK]
        q = urllib.parse.urlencode({"upload_token": u_token, "part_number": str(part)})
        _request(
            f"{PART_URL}?{q}",
            method="POST",
            data=chunk,
            headers={"Content-Type": "application/octet-stream"},
            timeout=180,
        )
        part += 1
    _json_post(f"{COMPLETE_URL}?{urllib.parse.urlencode({'upload_token': u_token})}")
    return u_token


def _archive_add(token: str, u_token: str, title: str, desc: str, cover_url: str, tid: int) -> str:
    q = urllib.parse.urlencode(
        {
            "client_id": bilibili_oauth.client_id(),
            "access_token": token,
            "upload_token": u_token,
        }
    )
    payload: dict[str, Any] = {
        "title": title[:TITLE_MAX] or "Video",
        "tid": tid,
        "tag": _tag(),
        "copyright": 1,
        "desc": desc[:250],
        # Igual que en el panel web: open 0 = permitir subtítulos en el video.
        "subtitle": {"open": 0, "lan": ""},
        "open_subtitle": True,
    }
    if cover_url:
        payload["cover"] = cover_url
    try:
        data = _json_post(f"{ADD_URL}?{q}", payload)
    except ValueError:
        payload.pop("subtitle", None)
        payload.pop("open_subtitle", None)
        data = _json_post(f"{ADD_URL}?{q}", payload)
    inner = _data(data)
    rid = str(inner.get("resource_id") or inner.get("aid") or inner.get("bvid") or "").strip()
    if not rid:
        raise ValueError("Bilibili did not return a resource id.")
    return rid


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
        return False, t("pub.bilibili.no_photo", lang)

    path = Path(file_path)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.bilibili.file_missing", lang)
    if path.suffix.lower() not in VIDEO_EXT:
        return False, t("pub.bilibili.bad_video", lang)

    try:
        token, row = _token_row(account_link_id)
    except ValueError:
        return False, t("pub.bilibili.no_token", lang)

    label = str(title or "").strip() or "Video"
    desc = str(description or "").strip()
    cover_path = _extract_cover(path)

    def _send(access: str) -> str:
        u_token = _upload_video(access, path)
        cover_url = ""
        if cover_path:
            try:
                cover_url = _upload_cover(access, cover_path)
            except ValueError:
                cover_url = ""
        tid = _pick_tid(access)
        return _archive_add(access, u_token, label, desc, cover_url, tid)

    try:
        try:
            resource_id = _send(token)
        except ValueError as e:
            msg = str(e).lower()
            if "token" in msg or "auth" in msg or "401" in msg or "expired" in msg:
                row = _refresh_row(row)
                token = str(row.get("access_token") or "").strip()
                resource_id = _send(token)
            else:
                raise
        return True, t("pub.bilibili.ok", lang, id=resource_id)
    except ValueError as e:
        if str(e) == "missing_token":
            return False, t("pub.bilibili.no_token", lang)
        return False, t("pub.bilibili.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.bilibili.upload_fail", lang, error=str(e)[:180])
    finally:
        if cover_path:
            try:
                cover_path.unlink(missing_ok=True)
            except OSError:
                pass
