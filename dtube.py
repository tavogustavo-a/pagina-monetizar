"""DTube: subida IPFS al cluster y post real en Hive (posting WIF)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import ffmpeg_bin

UA = "Tuyaho/1.0 (DTube Hive publish)"
HIVE_NODES = (
    "https://api.hive.blog",
    "https://api.openhive.network",
    "https://hive-api.arcange.eu",
)
CLUSTER = "https://cluster.d.tube"
CLUSTER_FALLBACK = "https://uploader.oneloved.tube"
VIDEO_EXT = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".m4v"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
# JPEG 1×1 mínimo por si no hay miniatura (DTube pide snaphash).
TINY_JPEG = bytes(
    [
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
        0x7F, 0xFF, 0xD9,
    ]
)


class DTubeError(ValueError):
    pass


def _fail_message(lang: str, err: BaseException) -> str:
    from i18n import t

    text = str(err or "")
    low = text.lower()
    dns = (
        "name or service not known",
        "nodename nor servname provided",
        "getaddrinfo failed",
        "temporary failure in name resolution",
        "errno -2",
        "errno 11001",
        "errno 8",
    )
    if any(m in low for m in dns):
        return t("pub.dtube.dns_fail", lang)
    if "timed out" in low or "timeout" in low:
        return t("pub.dtube.timeout", lang)
    if any(
        m in low
        for m in (
            "connection refused",
            "network is unreachable",
            "no route to host",
            "connection reset",
        )
    ):
        return t("pub.dtube.unreachable", lang)
    return t("pub.dtube.upload_fail", lang, error=text[:180])


def _parse(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def hive_username(login: str) -> str:
    return (login or "").strip().lstrip("@").lower()


def _b58decode(value: str) -> bytes:
    n = 0
    for ch in value:
        n = n * 58 + B58.index(ch)
    h = n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")
    pad = 0
    for ch in value:
        if ch != "1":
            break
        pad += 1
    return b"\x00" * pad + h


def wif_checksum_ok(wif: str) -> bool:
    raw = (wif or "").strip()
    if len(raw) < 51:
        return False
    try:
        decoded = _b58decode(raw)
    except (ValueError, KeyError, IndexError):
        return False
    if len(decoded) not in (37, 38):
        return False
    payload, check = decoded[:-4], decoded[-4:]
    digest = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return check == digest


def _hive_rpc(method: str, params: Any) -> Any:
    payload = json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    ).encode("utf-8")
    last = "hive rpc failed"
    for node in HIVE_NODES:
        req = urllib.request.Request(
            node,
            data=payload,
            method="POST",
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = _parse(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            last = e.read().decode("utf-8", errors="replace")[:180] if e.fp else str(e)
            continue
        except Exception as e:
            last = str(e)[:180]
            continue
        if data.get("error"):
            err = data["error"]
            last = str(err.get("message") if isinstance(err, dict) else err)[:180]
            continue
        return data.get("result")
    raise DTubeError(last)


def get_hive_account(username: str) -> dict[str, Any]:
    name = hive_username(username)
    if not name:
        raise DTubeError("missing_username")
    rows = _hive_rpc("condenser_api.get_accounts", [[name]])
    if not isinstance(rows, list) or not rows:
        raise DTubeError("hive account not found")
    acc = rows[0] if isinstance(rows[0], dict) else {}
    if str(acc.get("name") or "").lower() != name:
        raise DTubeError("hive account not found")
    return acc


def probe_account(login: str, secret: str, extra: str = "", account_id: str = "") -> tuple[bool, str]:
    if is_email_account(login):
        return _browser_probe(login, secret, account_id)
    name = hive_username(login)
    wif = (secret or "").strip()
    if not name or not wif:
        return False, "missing_fields"
    if not wif_checksum_ok(wif):
        return False, "invalid posting WIF"
    try:
        acc = get_hive_account(name)
    except DTubeError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)[:280]
    return True, str(acc.get("name") or name)


def _multipart(fields: dict[str, str], files: list[tuple[str, str, str, bytes]]) -> tuple[bytes, str]:
    boundary = f"----Tuyaho{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, val in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        chunks.append(str(val).encode("utf-8"))
        chunks.append(b"\r\n")
    for field, filename, ctype, raw in files:
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
        )
        chunks.append(f"Content-Type: {ctype}\r\n\r\n".encode())
        chunks.append(raw)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _post_cluster(url: str, files: list[tuple[str, str, str, bytes]], timeout: int = 300) -> dict[str, Any]:
    body, ctype = _multipart({}, files)
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"User-Agent": UA, "Accept": "application/json", "Content-Type": ctype},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _parse(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        data = _parse(raw)
        if data:
            return data
        raise DTubeError(raw[:280] or f"HTTP {e.code}")


def _progress(base: str, token: str) -> dict[str, Any]:
    url = f"{base}/getProgressByToken/{urllib.parse.quote(token)}"
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return _parse(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return _parse(raw)


def _first_hash(data: dict[str, Any]) -> str:
    for key in ("hash", "ipfsHash", "videohash", "cid", "sourceHash"):
        val = data.get(key)
        if isinstance(val, str) and len(val) >= 20:
            return val.strip()
    ipfs = data.get("ipfs")
    if isinstance(ipfs, dict):
        return _first_hash(ipfs)
    result = data.get("result")
    if isinstance(result, dict):
        return _first_hash(result)
    video = data.get("video")
    if isinstance(video, dict):
        return _first_hash(video)
    return ""


def _upload_and_wait(kind: str, filename: str, ctype: str, raw: bytes) -> dict[str, Any]:
    path = "uploadVideo" if kind == "video" else "uploadImage"
    last_err = "cluster upload failed"
    for base in (CLUSTER, CLUSTER_FALLBACK):
        try:
            data = _post_cluster(f"{base}/{path}", [("files", filename, ctype, raw)])
        except DTubeError as e:
            last_err = str(e)
            continue
        except Exception as e:
            last_err = str(e)[:180]
            continue
        token = str(data.get("token") or data.get("id") or "").strip()
        digest = _first_hash(data)
        if digest and not token:
            return data if data.get("video") or data.get("ipfs") else {"hash": digest, **data}
        if token:
            deadline = time.time() + 420
            while time.time() < deadline:
                prog = _progress(base, token)
                merged = {**data, **prog}
                if _first_hash(merged) and str(prog.get("status") or "").lower() in {
                    "",
                    "done",
                    "finished",
                    "complete",
                    "ok",
                    "100",
                }:
                    return merged
                if _first_hash(merged) and int(float(prog.get("progress") or prog.get("percent") or 0) or 0) >= 100:
                    return merged
                err = prog.get("error") or prog.get("message")
                if err and str(prog.get("status") or "").lower() in {"error", "failed"}:
                    last_err = str(err)[:180]
                    break
                if _first_hash(merged) and not prog:
                    return merged
                time.sleep(2)
            if _first_hash({**data, **locals().get("prog", {})}):
                return {**data, **prog}
        if digest:
            return {"hash": digest, **data}
        last_err = str(data.get("error") or data.get("message") or last_err)
    raise DTubeError(last_err)


def _snap_bytes(video_path: Path) -> bytes:
    try:
        tmp = video_path.with_suffix(".dtube-snap.jpg")
        subprocess.run(
            [
                ffmpeg_bin.ffmpeg_exe(),
                "-y",
                "-ss",
                "1",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "4",
                str(tmp),
            ],
            check=True,
            capture_output=True,
            timeout=40,
        )
        if tmp.is_file() and tmp.stat().st_size > 0:
            raw = tmp.read_bytes()
            tmp.unlink(missing_ok=True)
            return raw
    except Exception:
        pass
    return TINY_JPEG


def _hashes_from_upload(data: dict[str, Any]) -> dict[str, str]:
    video = data.get("video") if isinstance(data.get("video"), dict) else {}
    content = video.get("content") if isinstance(video.get("content"), dict) else {}
    info = video.get("info") if isinstance(video.get("info"), dict) else {}
    ipfs = data.get("ipfs") if isinstance(data.get("ipfs"), dict) else {}
    source = (
        str(content.get("videohash") or info.get("sourceHash") or ipfs.get("source") or _first_hash(data) or "").strip()
    )
    out = {
        "videohash": source,
        "video240hash": str(content.get("video240hash") or ipfs.get("240") or "").strip(),
        "video480hash": str(content.get("video480hash") or ipfs.get("480") or "").strip(),
        "video720hash": str(content.get("video720hash") or ipfs.get("720") or "").strip(),
        "video1080hash": str(content.get("video1080hash") or ipfs.get("1080") or "").strip(),
        "snaphash": str(info.get("snaphash") or ipfs.get("snap") or data.get("snaphash") or "").strip(),
        "spritehash": str(info.get("spritehash") or "").strip(),
    }
    return out


def build_json_metadata(
    *,
    title: str,
    description: str,
    hashes: dict[str, str],
    duration: int = 0,
    filesize: int = 0,
) -> dict[str, Any]:
    content = {
        "videohash": hashes.get("videohash") or "",
        "description": description or "",
        "tags": ["dtube"],
    }
    for key in ("video240hash", "video480hash", "video720hash", "video1080hash"):
        if hashes.get(key):
            content[key] = hashes[key]
    info = {
        "title": title,
        "snaphash": hashes.get("snaphash") or "",
        "filesize": filesize,
        "duration": duration,
        "type": 0,
    }
    if hashes.get("spritehash"):
        info["spritehash"] = hashes["spritehash"]
    return {
        "video": {"info": info, "content": content},
        "tags": ["dtube"],
        "app": "dtube/0.9",
    }


def _broadcast(username: str, wif: str, title: str, body: str, permlink: str, metadata: dict[str, Any]) -> str:
    try:
        from beem import Hive
    except ImportError as e:
        raise DTubeError("Hive signing library (beem) is not installed") from e
    hive = Hive(node=list(HIVE_NODES), keys=[wif], num_retries=3)
    try:
        hive.post(
            title,
            body,
            author=username,
            permlink=permlink,
            tags=["dtube"],
            json_metadata=metadata,
            beneficiaries=[{"account": "dtube", "weight": 1000}],
        )
    except Exception:
        hive.post(
            title,
            body,
            author=username,
            permlink=permlink,
            tags=["dtube"],
            json_metadata=metadata,
        )
    return f"https://d.tube/#!/v/{username}/{permlink}"


# ====================================================================
# Modo navegador: cuentas email de d.tube (login web + sesión persistente).
# d.tube usa Supabase: el token vive en localStorage y se renueva solo al
# abrir la web con el perfil guardado; si muere, se reloguea con email/pass.
# La subida exige un Cloudflare Turnstile; si no se resuelve, se reporta
# error claro (nunca se simula el envío).
# ====================================================================

BASE_URL = "https://d.tube/"
LOGIN_URL = "https://d.tube/auth/login"
UPLOAD_URL = "https://d.tube/upload"
PUBLISH_LOCK_S = 20 * 60
TURNSTILE_WAIT_S = 90
UPLOAD_WAIT_S = 10 * 60
KEEP_DAYS_MIN = 3
KEEP_DAYS_MAX = 5
RETRY_HOURS_MIN = 8
RETRY_HOURS_MAX = 20


def is_email_account(login: str, secret: str = "") -> bool:
    """Cuenta nueva de d.tube (email); las antiguas usan usuario Hive + WIF."""
    return "@" in (login or "").strip()


def profile_dir(account_id: str) -> Path:
    from db_engine import DATA_DIR

    safe = "".join(ch for ch in (account_id or "").strip() if ch.isalnum() or ch in "-_")
    return DATA_DIR / "dtube_profiles" / (safe or "_invalid")


def remove_profile(account_id: str) -> None:
    import shutil

    path = profile_dir(account_id)
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def playwright_ready() -> tuple[bool, str]:
    import playwright_session

    return playwright_session.playwright_ready()


def _with_browser(account_id: str, fn, *, lock_wait_s: int | None = None) -> tuple[bool, str]:
    import db
    import playwright_session

    proxy_url = db.get_active_proxy_url_for_source("chain", account_id)
    kwargs: dict[str, Any] = {"proxy_url": proxy_url, "locale": "en-US"}
    if lock_wait_s is not None:
        kwargs["lock_wait_s"] = lock_wait_s
    return playwright_session.with_persistent_browser(profile_dir(account_id), fn, **kwargs)


def _looks_logged_in(page) -> bool:
    try:
        el = page.query_selector("a[href='/upload'], a[href*='/upload']")
        if el and el.is_visible():
            return True
        for sel in ("a", "button"):
            for cand in page.query_selector_all(sel):
                try:
                    txt = (cand.inner_text() or "").strip().lower()
                except Exception:
                    continue
                if txt == "upload" and cand.is_visible():
                    return True
    except Exception:
        return False
    return False


def _login_error_text(page) -> str:
    try:
        body = " ".join((page.inner_text("body") or "").split()).lower()
    except Exception:
        return ""
    for marker in ("invalid login", "invalid email", "incorrect", "wrong password", "invalid credentials"):
        if marker in body:
            return marker
    return ""


def _ensure_session(page, email: str, password: str) -> tuple[bool, str]:
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "browser_error"
    page.wait_for_timeout(4500)
    if _looks_logged_in(page):
        return True, email
    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "browser_error"
    page.wait_for_timeout(4000)
    if _looks_logged_in(page):
        return True, email
    em_input = page.query_selector("input[type=email]")
    pw_input = page.query_selector("input[type=password]")
    if not em_input or not pw_input:
        return False, "website_changed"
    try:
        em_input.fill(email)
        pw_input.fill(password)
    except Exception:
        return False, "website_changed"
    clicked = False
    for btn in page.query_selector_all("button"):
        try:
            txt = (btn.inner_text() or "").strip().lower()
        except Exception:
            continue
        if txt == "login" and btn.is_visible():
            try:
                btn.click()
                clicked = True
                break
            except Exception:
                continue
    if not clicked:
        return False, "website_changed"
    for _ in range(10):
        page.wait_for_timeout(2000)
        if _looks_logged_in(page):
            return True, email
        if _login_error_text(page):
            return False, "login_failed"
    if "/auth/login" in (page.url or ""):
        return False, "login_failed"
    return False, "website_changed"


def _turnstile_token(page) -> str:
    tok = page.query_selector("input[name='cf-turnstile-response']")
    if not tok:
        return ""
    try:
        return str(tok.evaluate("e => e.value || ''") or "")
    except Exception:
        return ""


def _try_click_turnstile(page) -> None:
    """Intenta pulsar el checkbox 'Verify you are human' del widget."""
    try:
        box = page.evaluate(
            """() => {
                const inp = document.querySelector("input[name='cf-turnstile-response']");
                if (!inp) return null;
                let host = inp.parentElement;
                while (host && host.offsetHeight < 20) host = host.parentElement;
                if (!host) return null;
                const r = host.getBoundingClientRect();
                return {x: r.x, y: r.y, w: r.width, h: r.height};
            }"""
        )
    except Exception:
        return
    if not box:
        return
    try:
        x = float(box["x"]) + 30
        y = float(box["y"]) + float(box["h"]) / 2
        page.mouse.move(x - 7, y - 4)
        page.wait_for_timeout(350)
        page.mouse.click(x, y)
    except Exception:
        pass


def _wait_turnstile(page, wait_s: int = TURNSTILE_WAIT_S) -> bool:
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if _turnstile_token(page):
            return True
        _try_click_turnstile(page)
        page.wait_for_timeout(3000)
    return bool(_turnstile_token(page))


def _fill_upload_title(page, title: str) -> bool:
    for el in page.query_selector_all("input[type=text]"):
        ph = (el.get_attribute("placeholder") or "").lower()
        if "search" in ph:
            continue
        try:
            el.fill(title)
            return True
        except Exception:
            continue
    return False


def _browser_upload(page, path: Path, title: str, description: str) -> tuple[bool, str]:
    try:
        page.goto(UPLOAD_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "browser_error"
    page.wait_for_timeout(5000)
    file_input = page.query_selector("input[type=file]")
    if not file_input:
        return False, "session_dead" if "/auth/login" in (page.url or "") else "website_changed"
    try:
        file_input.set_input_files(str(path))
    except Exception:
        return False, "website_changed"
    page.wait_for_timeout(1200)
    if not _fill_upload_title(page, title):
        return False, "website_changed"
    try:
        page.fill("textarea", description or title)
    except Exception:
        pass
    if not _wait_turnstile(page):
        return False, "captcha"
    btn = None
    for cand in page.query_selector_all("button"):
        try:
            txt = (cand.inner_text() or "").strip().lower()
        except Exception:
            continue
        if "upload video" in txt:
            btn = cand
            break
    if not btn:
        return False, "website_changed"
    try:
        for _ in range(20):
            if not btn.evaluate("e => e.disabled"):
                break
            page.wait_for_timeout(1000)
        btn.click()
    except Exception:
        return False, "website_changed"
    deadline = time.time() + UPLOAD_WAIT_S
    while time.time() < deadline:
        page.wait_for_timeout(4000)
        url = str(page.url or "")
        if "/v/" in url:
            return True, url
        try:
            body = " ".join((page.inner_text("body") or "").split()).lower()
        except Exception:
            body = ""
        if "upload failed" in body or ("error" in body and "upload" in body):
            return False, "upload_failed"
        if "uploaded successfully" in body or "upload complete" in body:
            return True, url or "https://d.tube/"
    return False, "upload_timeout"


def keep_alive_account(account: dict[str, Any]) -> tuple[bool, str]:
    oid = str(account.get("id") or "").strip()
    em = str(account.get("login") or "").strip()
    pw = str(account.get("secret") or "").strip()
    if not oid:
        return False, "need_saved_account"
    return _with_browser(oid, lambda page: _ensure_session(page, em, pw))


def pick_next_keepalive(*, except_id: str = "", soon: bool = False) -> str:
    import random
    from datetime import timedelta, timezone as _tz

    import publish_schedule

    now_local = publish_schedule.now_publish_tz()
    if soon:
        candidate = now_local + timedelta(
            hours=random.randint(RETRY_HOURS_MIN, RETRY_HOURS_MAX),
            minutes=random.randint(0, 59),
        )
    else:
        days = random.randint(KEEP_DAYS_MIN, KEEP_DAYS_MAX)
        candidate = (now_local + timedelta(days=days)).replace(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=0,
            microsecond=0,
        )
        if candidate <= now_local:
            candidate += timedelta(days=1)
    return candidate.astimezone(_tz.utc).isoformat()


def run_daily_keep_alive_if_due() -> None:
    """Reconexión automática: visita d.tube y reloguea si la sesión caducó."""
    from datetime import datetime, timezone as _tz

    import db

    now = datetime.now(_tz.utc)
    due: list[dict[str, Any]] = []
    for row in db.list_chain_accounts_raw("dtube"):
        oid = str(row.get("id") or "").strip()
        if not oid or not is_email_account(str(row.get("login") or "")):
            continue
        nxt = str(row.get("next_keepalive_at") or "").strip()
        if not nxt:
            db.update_chain_next_keepalive(oid, pick_next_keepalive(except_id=oid))
            continue
        try:
            parsed = datetime.fromisoformat(nxt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=_tz.utc)
        except ValueError:
            continue
        if parsed <= now:
            due.append(row)
    if not due:
        return
    due.sort(key=lambda r: str(r.get("next_keepalive_at") or ""))
    row = due[0]
    oid = str(row.get("id") or "")
    ok, code = keep_alive_account(row)
    soon = (not ok) and code in {"session_dead", "login_failed", "browser_error"}
    db.update_chain_browser_session(
        oid,
        session_ok=ok,
        last_ok_at=now.isoformat() if ok else str(row.get("last_ok_at") or ""),
        last_error="" if ok else code,
        next_keepalive_at=pick_next_keepalive(except_id=oid, soon=soon),
    )


def _browser_probe(login: str, secret: str, account_id: str) -> tuple[bool, str]:
    em = (login or "").strip()
    pw = (secret or "").strip()
    if not em or not pw:
        return False, "email_password_required"
    oid = (account_id or "").strip()
    if not oid:
        return False, "need_saved_account"
    return _with_browser(oid, lambda page: _ensure_session(page, em, pw))


def _publish_via_browser(
    *,
    file_path: Path,
    title: str,
    description: str,
    lang: str,
    account: dict[str, Any],
) -> tuple[bool, str]:
    from i18n import t

    oid = str(account.get("id") or "").strip()
    em = str(account.get("login") or "").strip()
    pw = str(account.get("secret") or "").strip()
    if not oid or not em or not pw:
        return False, t("pub.dtube.no_account", lang)
    path = Path(file_path)
    label = (title or "").strip() or path.stem
    desc = (description or "").strip()

    def body(page) -> tuple[bool, str]:
        ok, code = _ensure_session(page, em, pw)
        if not ok:
            return False, code
        return _browser_upload(page, path, label, desc)

    ok, code = _with_browser(oid, body, lock_wait_s=PUBLISH_LOCK_S)
    if ok:
        return True, t("pub.dtube.ok", lang, url=code or "https://d.tube/")
    key = {
        "session_dead": "dtube.err_session",
        "captcha": "dtube.err_captcha",
        "website_changed": "dtube.err_website",
        "browser_busy": "dtube.err_busy",
        "browser_error": "dtube.err_browser",
        "playwright_missing": "bilibili_tv.err_playwright",
        "login_failed": "dtube.err_login",
        "upload_failed": "dtube.err_upload",
        "upload_timeout": "dtube.err_upload",
    }.get((code or "").strip())
    if key:
        return False, t(key, lang)
    return False, t("pub.dtube.upload_fail", lang, error=(code or "upload")[:180])


def publish_video(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account: dict[str, Any],
) -> tuple[bool, str]:
    from i18n import t

    path = Path(file_path)
    if content_type == "photo" or path.suffix.lower() in PHOTO_EXT:
        return False, t("pub.dtube.no_photo", lang)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.dtube.file_missing", lang)
    if path.suffix.lower() not in VIDEO_EXT:
        return False, t("pub.dtube.bad_video", lang)
    if is_email_account(str(account.get("login") or "")):
        return _publish_via_browser(
            file_path=path,
            title=title,
            description=description,
            lang=lang,
            account=account,
        )
    user = hive_username(str(account.get("login") or ""))
    wif = str(account.get("secret") or "").strip()
    if not user or not wif:
        return False, t("pub.dtube.no_account", lang)
    if not wif_checksum_ok(wif):
        return False, t("pub.dtube.bad_wif", lang)
    try:
        get_hive_account(user)
        video_raw = path.read_bytes()
        video_data = _upload_and_wait("video", path.name, "video/mp4", video_raw)
        hashes = _hashes_from_upload(video_data)
        if not hashes.get("videohash"):
            raise DTubeError("IPFS cluster did not return a video hash")
        snap = _snap_bytes(path)
        try:
            snap_data = _upload_and_wait("files", "snap.jpg", "image/jpeg", snap)
            snap_hash = _first_hash(snap_data)
            if snap_hash:
                hashes["snaphash"] = snap_hash
        except DTubeError:
            pass
        if not hashes.get("snaphash"):
            raise DTubeError("IPFS cluster did not return a thumbnail hash")
        slug = re.sub(r"[^a-z0-9]+", "", (title or "video").lower())[:8] or "video"
        permlink = f"{slug}{uuid.uuid4().hex[:8]}"
        meta = build_json_metadata(
            title=title or path.stem,
            description=description or "",
            hashes=hashes,
            filesize=path.stat().st_size,
        )
        watch = _broadcast(
            user,
            wif,
            title or path.stem,
            f"[DTube](https://d.tube/#!/v/{user}/{permlink})",
            permlink,
            meta,
        )
        return True, t("pub.dtube.ok", lang, url=watch)
    except DTubeError as e:
        return False, _fail_message(lang, e)
    except Exception as e:
        return False, _fail_message(lang, e)
