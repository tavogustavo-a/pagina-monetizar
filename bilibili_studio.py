"""Subida real al estudio web de Bilibili.com (sesión SESSDATA, no Open Platform)."""
from __future__ import annotations

import base64
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from bilibili_publish import TITLE_MAX, _extract_cover, _tag, _tid

PREUPLOAD_URL = "https://member.bilibili.com/preupload"
COVER_URL = "https://member.bilibili.com/x/vu/web/cover/up"
ADD_URL = "https://member.bilibili.com/x/vu/web/add/v3"
PREDICT_URL = "https://member.bilibili.com/x/vupre/web/archive/types/predict"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
REFERER = "https://member.bilibili.com/platform/upload/video/frame"
PROFILE = "ugcfx/bup"


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _headers(cookie: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    hdrs = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": REFERER,
        "Origin": "https://member.bilibili.com",
        "Cookie": cookie,
    }
    if extra:
        hdrs.update(extra)
    return hdrs


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 90,
) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), resp.read()
    except urllib.error.HTTPError as e:
        raw = e.read() if e.fp else b""
        return int(e.code), raw


def _json_or_raise(raw: bytes, fallback: str) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    if "<html" in text[:200].lower():
        raise ValueError("session_dead")
    data = _parse_json(text)
    code = data.get("code")
    if code not in (None, 0, "0"):
        if code in (-101, "-101"):
            raise ValueError("session_dead")
        msg = str(data.get("message") or data.get("msg") or fallback or text)[:220]
        raise ValueError(msg or fallback)
    return data


def _upos_base(pre: dict[str, Any]) -> str:
    endpoint = str(pre.get("endpoint") or "").strip()
    if endpoint.startswith("//"):
        host = "https:" + endpoint
    elif endpoint.startswith("http"):
        host = endpoint.rstrip("/")
    else:
        host = "https://" + endpoint.lstrip("/")
    uri = str(pre.get("upos_uri") or "").replace("upos://", "").lstrip("/")
    return host.rstrip("/") + "/" + uri


def _filename_stem(upos_uri: str) -> str:
    name = str(upos_uri or "").replace("upos://", "").split("/")[-1]
    return Path(name).stem


def _preupload(cookie: str, path: Path) -> dict[str, Any]:
    q = urllib.parse.urlencode(
        {
            "name": path.name,
            "size": str(path.stat().st_size),
            "r": "upos",
            "profile": PROFILE,
            "ssl": "0",
            "version": "2.14.0.0",
            "build": "2140000",
            "webVersion": "2.13.0",
        }
    )
    status, raw = _request(
        f"{PREUPLOAD_URL}?{q}",
        headers=_headers(cookie),
        timeout=60,
    )
    data = _json_or_raise(raw, f"HTTP {status}")
    if int(data.get("OK") or 0) != 1:
        raise ValueError(str(data.get("message") or "preupload failed")[:220])
    if not data.get("auth") or not data.get("upos_uri") or not data.get("biz_id"):
        raise ValueError("website_changed")
    return data


def _post_meta(cookie: str, pre: dict[str, Any], size: int) -> str:
    chunk = int(pre.get("chunk_size") or 10 * 1024 * 1024)
    q = urllib.parse.urlencode(
        {
            "uploads": "",
            "output": "json",
            "profile": PROFILE,
            "filesize": str(size),
            "partsize": str(chunk),
            "biz_id": str(pre.get("biz_id") or ""),
        }
    )
    status, raw = _request(
        f"{_upos_base(pre)}?{q}",
        method="POST",
        data=b"",
        headers=_headers(cookie, {"X-Upos-Auth": str(pre.get("auth") or "")}),
        timeout=60,
    )
    data = _json_or_raise(raw, f"HTTP {status}")
    upload_id = str(data.get("upload_id") or "").strip()
    if not upload_id:
        raise ValueError("website_changed")
    return upload_id


def _put_parts(cookie: str, pre: dict[str, Any], path: Path, upload_id: str) -> int:
    size = path.stat().st_size
    chunk_size = int(pre.get("chunk_size") or 10 * 1024 * 1024)
    chunks = max(1, math.ceil(size / chunk_size))
    auth = str(pre.get("auth") or "")
    base = _upos_base(pre)
    with path.open("rb") as fh:
        for index in range(chunks):
            data = fh.read(chunk_size)
            if not data:
                break
            start = index * chunk_size
            end = start + len(data)
            q = urllib.parse.urlencode(
                {
                    "partNumber": str(index + 1),
                    "uploadId": upload_id,
                    "chunk": str(index),
                    "chunks": str(chunks),
                    "size": str(len(data)),
                    "start": str(start),
                    "end": str(end),
                    "total": str(size),
                }
            )
            last_err = "upload part failed"
            for _ in range(3):
                status, raw = _request(
                    f"{base}?{q}",
                    method="PUT",
                    data=data,
                    headers=_headers(
                        cookie,
                        {
                            "X-Upos-Auth": auth,
                            "Content-Type": "application/octet-stream",
                        },
                    ),
                    timeout=180,
                )
                text = raw.decode("utf-8", errors="replace")
                if status in (200, 201) and (
                    "MULTIPART_PUT_SUCCESS" in text or _parse_json(text).get("OK") == 1 or not text.strip()
                ):
                    last_err = ""
                    break
                last_err = text[:180] or f"HTTP {status}"
                time.sleep(1.2)
            if last_err:
                raise ValueError(last_err)
    return chunks


def _end_upload(
    cookie: str,
    pre: dict[str, Any],
    path: Path,
    upload_id: str,
    chunks: int,
) -> None:
    q = urllib.parse.urlencode(
        {
            "output": "json",
            "name": path.name,
            "profile": PROFILE,
            "uploadId": upload_id,
            "biz_id": str(pre.get("biz_id") or ""),
        }
    )
    parts = [{"partNumber": i, "eTag": "etag"} for i in range(1, chunks + 1)]
    body = json.dumps({"parts": parts}, ensure_ascii=False).encode("utf-8")
    status, raw = _request(
        f"{_upos_base(pre)}?{q}",
        method="POST",
        data=body,
        headers=_headers(
            cookie,
            {
                "X-Upos-Auth": str(pre.get("auth") or ""),
                "Content-Type": "application/json; charset=UTF-8",
            },
        ),
        timeout=90,
    )
    data = _json_or_raise(raw, f"HTTP {status}")
    if int(data.get("OK") or 0) != 1 and data.get("code") not in (None, 0, "0"):
        raise ValueError(str(data.get("message") or "complete failed")[:220])


def _upload_cover(cookie: str, csrf: str, cover: Path) -> str:
    payload = urllib.parse.urlencode(
        {
            "csrf": csrf,
            "cover": "data:image/jpeg;base64,"
            + base64.b64encode(cover.read_bytes()).decode("ascii"),
        }
    ).encode("utf-8")
    q = urllib.parse.urlencode({"csrf": csrf, "ts": str(int(time.time() * 1000))})
    status, raw = _request(
        f"{COVER_URL}?{q}",
        method="POST",
        data=payload,
        headers=_headers(
            cookie,
            {"Content-Type": "application/x-www-form-urlencoded"},
        ),
        timeout=60,
    )
    data = _json_or_raise(raw, f"HTTP {status}")
    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
    return str(inner.get("url") or "").strip()


def _predict_tid(cookie: str, csrf: str, filename: str, title: str) -> int:
    q = urllib.parse.urlencode({"csrf": csrf, "ts": str(int(time.time() * 1000))})
    payload = urllib.parse.urlencode(
        {"filename": filename, "title": title, "csrf": csrf}
    ).encode("utf-8")
    try:
        status, raw = _request(
            f"{PREDICT_URL}?{q}",
            method="POST",
            data=payload,
            headers=_headers(
                cookie,
                {"Content-Type": "application/x-www-form-urlencoded"},
            ),
            timeout=30,
        )
        data = _json_or_raise(raw, f"HTTP {status}")
    except ValueError:
        return _tid()
    rows = data.get("data")
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        try:
            tid = int(rows[0].get("id") or 0)
        except (TypeError, ValueError):
            tid = 0
        if tid > 0:
            return tid
    return _tid()


def _add_archive(
    cookie: str,
    csrf: str,
    *,
    filename: str,
    cid: int,
    title: str,
    desc: str,
    cover_url: str,
    tid: int,
) -> str:
    payload: dict[str, Any] = {
        "videos": [
            {
                "filename": filename,
                "title": title,
                "desc": "",
                "cid": cid,
            }
        ],
        "cover": cover_url,
        "cover43": "",
        "title": title,
        "copyright": 1,
        "tid": tid,
        "tag": _tag(),
        "desc_format_id": 9999,
        "desc": desc[:2000],
        "recreate": -1,
        "dynamic": "",
        "interactive": 0,
        "act_reserve_create": 0,
        "no_disturbance": 0,
        "no_reprint": 1,
        "subtitle": {"open": 0, "lan": ""},
        "dolby": 0,
        "lossless_music": 0,
        "up_selection_reply": False,
        "up_close_reply": False,
        "up_close_danmu": False,
        "web_os": 3,
        "csrf": csrf,
    }
    q = urllib.parse.urlencode({"csrf": csrf, "ts": str(int(time.time() * 1000))})
    status, raw = _request(
        f"{ADD_URL}?{q}",
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_headers(
            cookie,
            {"Content-Type": "application/json; charset=utf-8"},
        ),
        timeout=90,
    )
    data = _json_or_raise(raw, f"HTTP {status}")
    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
    bvid = str(inner.get("bvid") or "").strip()
    aid = str(inner.get("aid") or "").strip()
    rid = bvid or aid
    if not rid:
        raise ValueError("Bilibili did not return a video id.")
    return rid


def upload_archive(*, path: Path, title: str, description: str, cookie: str, csrf: str) -> str:
    size = path.stat().st_size
    pre = _preupload(cookie, path)
    upload_id = _post_meta(cookie, pre, size)
    chunks = _put_parts(cookie, pre, path, upload_id)
    _end_upload(cookie, pre, path, upload_id, chunks)
    filename = _filename_stem(str(pre.get("upos_uri") or ""))
    try:
        cid = int(pre.get("biz_id") or 0)
    except (TypeError, ValueError):
        cid = 0
    if not filename or cid <= 0:
        raise ValueError("website_changed")
    label = (title or "").strip()[:TITLE_MAX] or "Video"
    desc = (description or "").strip()
    cover_url = ""
    cover_path = _extract_cover(path)
    try:
        if cover_path:
            try:
                cover_url = _upload_cover(cookie, csrf, cover_path)
            except ValueError:
                cover_url = ""
        tid = _predict_tid(cookie, csrf, filename, label)
        return _add_archive(
            cookie,
            csrf,
            filename=filename,
            cid=cid,
            title=label,
            desc=desc,
            cover_url=cover_url,
            tid=tid,
        )
    finally:
        if cover_path:
            try:
                cover_path.unlink(missing_ok=True)
            except OSError:
                pass
