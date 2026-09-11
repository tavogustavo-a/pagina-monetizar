"""Bilibili.com: sesión web con código QR (estudio member.bilibili.com), no Open Platform."""
from __future__ import annotations

import base64
import http.cookiejar
import json
import random
import re
import shutil
import threading
import time
import uuid
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import db
import notify
import playwright_session
import proxy_util
import publish_schedule

PLATFORM_ID = "bilibili_qr"
SERVER_PLATFORM_ID = "bilibili"
QR_SECRET = "qr-session"
HOME_URL = "https://www.bilibili.com/"
MEMBER_URL = "https://member.bilibili.com/"
QR_WAIT_S = 12 * 60
QR_TICK_MS = 1200
PASSPORT_GENERATE = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
PASSPORT_POLL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
KEEP_DAYS_MIN = 3
KEEP_DAYS_MAX = 5
RETRY_HOURS_MIN = 8
RETRY_HOURS_MAX = 20
ACCOUNT_GAP_HOURS_MIN = 2
ACCOUNT_GAP_HOURS_MAX = 7
JOB_TTL_S = 20 * 60
NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
STAT_URL = "https://api.bilibili.com/x/relation/stat"
FOLLOWER_GOAL = 1000
KEEP_HOUR_LOCAL = 3

_LOGIN_COOKIE_NAMES = frozenset(
    {
        "sessdata",
        "dedeuserid",
        "bili_jct",
        "dedeuserid__ckmd5",
    }
)
_CAPTCHA_RE = re.compile(
    r"captcha|recaptcha|geetest|hcaptcha|verify you|sms code|verification code|"
    r"phone code|otp|验证码|人机|短信",
    re.I,
)

_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _jobs_dir() -> Path:
    from db_engine import DATA_DIR

    path = DATA_DIR / "bilibili_qr_jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _job_file(job_id: str) -> Path:
    safe = "".join(ch for ch in (job_id or "").strip() if ch.isalnum() or ch in "-_")
    return _jobs_dir() / f"{safe or '_invalid'}.json"


def _persist_job(job: dict[str, Any]) -> None:
    jid = str(job.get("id") or "").strip()
    if not jid:
        return
    payload = {
        "id": jid,
        "account_id": job.get("account_id") or "",
        "link_name": job.get("link_name") or "",
        "is_new": bool(job.get("is_new")),
        "status": job.get("status") or "",
        "qr_png": job.get("qr_png") or "",
        "nickname": job.get("nickname") or "",
        "error": job.get("error") or "",
        "cancel": bool(job.get("cancel")),
        "created_at": float(job.get("created_at") or time.time()),
    }
    path = _job_file(jid)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.replace(path)


def _load_job_file(job_id: str) -> dict[str, Any] | None:
    path = _job_file(job_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def profile_dir(account_id: str) -> Path:
    from db_engine import DATA_DIR

    safe = "".join(ch for ch in (account_id or "").strip() if ch.isalnum() or ch in "-_")
    return DATA_DIR / "bilibili_web_profiles" / (safe or "_invalid")


def remove_profile(account_id: str) -> None:
    path = profile_dir(account_id)
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def playwright_ready() -> tuple[bool, str]:
    return playwright_session.playwright_ready()


def start_qr_login(*, link_name: str, account_id: str = "") -> dict[str, Any]:
    ready, err = playwright_ready()
    if not ready:
        return {"ok": False, "error": err}
    name = (link_name or "").strip()
    oid = (account_id or "").strip()
    is_new = not oid
    if not name and not oid:
        return {"ok": False, "error": "need_account_name"}
    if oid:
        existing = db.get_chain_account_raw(oid)
        if not existing or str(existing.get("platform_id") or "") != PLATFORM_ID:
            return {"ok": False, "error": "not_found"}
        name = name or str(existing.get("name") or existing.get("login") or "")
    else:
        oid = str(uuid.uuid4())
    proxy_url = db.get_active_proxy_url_for_source("chain", oid)
    if not proxy_url and name:
        proxy_url = db.get_active_proxy_url_for_account_name(name)
    proxy_url = (proxy_url or "").strip()
    jar = http.cookiejar.CookieJar()
    try:
        opener = _passport_opener(proxy_url, jar)
        png, key, err = _passport_generate(opener)
    except OSError:
        return {"ok": False, "error": "browser_error"}
    except Exception:
        return {"ok": False, "error": "website_changed"}
    if not png or not key:
        return {"ok": False, "error": err or "website_changed"}
    qr_b64 = base64.b64encode(png).decode("ascii")
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "account_id": oid,
        "link_name": name,
        "is_new": is_new,
        "status": "waiting",
        "qr_png": qr_b64,
        "message": "",
        "nickname": "",
        "error": "",
        "cancel": False,
        "created_at": time.time(),
        "qrcode_key": key,
        "cookiejar": jar,
        "proxy_url": proxy_url,
    }
    with _jobs_lock:
        _jobs[job_id] = job
        _persist_job(job)
    thread = threading.Thread(target=_run_qr_job, args=(job_id,), daemon=True)
    thread.start()
    return {"ok": True, "job_id": job_id, "account_id": oid, "qr_png": qr_b64}


def get_qr_job(job_id: str) -> dict[str, Any] | None:
    _purge_jobs()
    jid = (job_id or "").strip()
    with _jobs_lock:
        job = _jobs.get(jid)
    if not job:
        job = _load_job_file(jid)
        if job:
            with _jobs_lock:
                _jobs.setdefault(jid, job)
    if not job:
        return None
    return {
        "id": job.get("id") or jid,
        "account_id": job.get("account_id") or "",
        "status": job.get("status") or "",
        "qr_png": job.get("qr_png") or "",
        "nickname": job.get("nickname") or "",
        "error": job.get("error") or "",
    }


def cancel_qr_job(job_id: str) -> None:
    jid = (job_id or "").strip()
    with _jobs_lock:
        job = _jobs.get(jid) or _load_job_file(jid)
        if not job:
            return
        job["cancel"] = True
        if job.get("status") in {"starting", "waiting"}:
            job["status"] = "cancelled"
        _jobs[jid] = job
        _persist_job(job)


def keep_alive_account(account: dict[str, Any]) -> tuple[bool, str]:
    oid = str(account.get("id") or "").strip()
    if not oid:
        return False, "need_saved_account"

    def body(page) -> tuple[bool, str]:
        ok, code = _ensure_session(page)
        if ok:
            _capture_followers(page, oid, account)
        return ok, code

    return _with_browser(oid, body, link_name=str(account.get("name") or ""))


def schedule_next_visit(account_id: str, *, soon: bool = False) -> str:
    when = pick_next_keepalive(except_id=account_id, soon=soon)
    db.update_chain_next_keepalive(account_id, when)
    return when


def pick_next_keepalive(*, except_id: str, soon: bool = False) -> str:
    now_local = publish_schedule.now_publish_tz()
    if soon:
        candidate = now_local + timedelta(
            hours=random.randint(RETRY_HOURS_MIN, RETRY_HOURS_MAX),
            minutes=random.randint(0, 59),
        )
    else:
        days = random.randint(KEEP_DAYS_MIN, KEEP_DAYS_MAX)
        minute = random.randint(0, 40)
        candidate = (now_local + timedelta(days=days)).replace(
            hour=KEEP_HOUR_LOCAL, minute=minute, second=0, microsecond=0
        )
        if candidate <= now_local:
            candidate += timedelta(days=1)
    others = _other_next_times(except_id)
    gap = timedelta(hours=random.randint(ACCOUNT_GAP_HOURS_MIN, ACCOUNT_GAP_HOURS_MAX))
    for _ in range(36):
        if all(abs((candidate - other).total_seconds()) >= gap.total_seconds() for other in others):
            break
        if soon:
            candidate += gap
        else:
            candidate += timedelta(days=1)
            candidate = candidate.replace(hour=KEEP_HOUR_LOCAL, second=0, microsecond=0)
    return candidate.astimezone(timezone.utc).isoformat()


def run_keep_alive_if_due() -> None:
    """Visita como máximo una cuenta por ciclo. Si la sesión murió, no genera QR solo."""
    now = datetime.now(timezone.utc)
    due: list[dict[str, Any]] = []
    for row in db.list_chain_accounts_raw(PLATFORM_ID):
        oid = str(row.get("id") or "").strip()
        if not oid:
            continue
        nxt = str(row.get("next_keepalive_at") or "").strip()
        if not nxt:
            db.update_chain_next_keepalive(oid, pick_next_keepalive(except_id=oid))
            continue
        parsed = _parse_iso(nxt)
        if parsed and parsed <= now:
            due.append(row)
    if not due:
        return
    due.sort(key=lambda r: str(r.get("next_keepalive_at") or ""))
    row = due[0]
    oid = str(row.get("id") or "")
    ok, code = keep_alive_account(row)
    soon = (not ok) and code in {"session_dead", "browser_error"}
    next_at = pick_next_keepalive(except_id=oid, soon=soon)
    _record_session(oid, ok, code, row, next_keepalive_at=next_at)


def _purge_jobs() -> None:
    now = time.time()
    with _jobs_lock:
        dead = [
            jid
            for jid, job in _jobs.items()
            if now - float(job.get("created_at") or 0) > JOB_TTL_S
        ]
        for jid in dead:
            _jobs.pop(jid, None)
    try:
        for path in _jobs_dir().glob("*.json"):
            try:
                age = now - path.stat().st_mtime
            except OSError:
                continue
            if age > JOB_TTL_S:
                path.unlink(missing_ok=True)
    except OSError:
        pass


def _run_qr_job(job_id: str) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return
        oid = str(job.get("account_id") or "")
        link_name = str(job.get("link_name") or "")
        is_new = bool(job.get("is_new"))
        jar = job.get("cookiejar")
        key = str(job.get("qrcode_key") or "")
        proxy_url = str(job.get("proxy_url") or "")
    stored = db.get_chain_account_raw(oid) or {}
    ok, code = _poll_until_login(job_id, jar, key, proxy_url)
    nick = ""
    if ok:
        ok, code = _apply_cookies_and_verify(oid, jar, link_name)
        if ok:
            nick = code if code and code != "ok" else ""
    with _jobs_lock:
        job = _jobs.get(job_id) or job
        if job.get("cancel"):
            job["status"] = "cancelled"
            job["error"] = "cancelled"
            code = "cancelled"
            ok = False
        elif ok:
            job["status"] = "ok"
            job["error"] = ""
            if nick:
                job["nickname"] = nick
        else:
            job["status"] = code or "error"
            job["error"] = code or "error"
            job["qr_png"] = job.get("qr_png") or ""
        _persist_job(job)
    with _jobs_lock:
        nick = str((_jobs.get(job_id) or {}).get("nickname") or nick)
    label = link_name or str(stored.get("name") or "") or (nick if nick != "ok" else "")
    if ok:
        try:
            db.upsert_chain_account(
                account_id=oid,
                platform_id=PLATFORM_ID,
                name=label or nick or oid,
                login=nick if nick and nick != "ok" else (label or oid),
                secret=QR_SECRET,
                extra="",
                link_name=link_name or label,
                create_if_missing=True,
            )
        except ValueError:
            if is_new:
                remove_profile(oid)
                return
        stored = db.get_chain_account_raw(oid) or stored
        next_at = pick_next_keepalive(except_id=oid)
        _record_session(oid, True, "", stored, next_keepalive_at=next_at)
        return
    if stored:
        _record_session(oid, False, code, stored, next_keepalive_at=None)
        return
    remove_profile(oid)


def _poll_until_login(
    job_id: str,
    jar: http.cookiejar.CookieJar | None,
    key: str,
    proxy_url: str,
) -> tuple[bool, str]:
    if jar is None or not key:
        return False, "website_changed"
    try:
        opener = _passport_opener(proxy_url, jar)
    except OSError:
        return False, "browser_error"
    deadline = time.time() + QR_WAIT_S
    while time.time() < deadline:
        if _job_cancelled(job_id):
            return False, "cancelled"
        try:
            payload = _passport_poll(opener, key)
        except Exception:
            time.sleep(QR_TICK_MS / 1000)
            continue
        try:
            inner = int(payload.get("code"))
        except (TypeError, ValueError):
            inner = -1
        if inner == 0:
            return True, "ok"
        if inner == 86090:
            _set_job(job_id, status="scanned")
        elif inner == 86038:
            try:
                png, new_key, err = _passport_generate(opener)
            except Exception:
                return False, "expired"
            if not png or not new_key:
                return False, err or "expired"
            key = new_key
            with _jobs_lock:
                job = _jobs.get(job_id)
                if job:
                    job["qrcode_key"] = key
            _set_job(
                job_id,
                status="waiting",
                qr_png=base64.b64encode(png).decode("ascii"),
            )
        time.sleep(QR_TICK_MS / 1000)
    return False, "expired"


def _apply_cookies_and_verify(
    oid: str,
    jar: http.cookiejar.CookieJar | None,
    link_name: str,
) -> tuple[bool, str]:
    cookies = _playwright_cookies(jar)
    if not cookies:
        return False, "website_changed"

    def body(page) -> tuple[bool, str]:
        for item in cookies:
            try:
                page.context.add_cookies([item])
            except Exception:
                continue
        ok, code = _ensure_session(page)
        if ok:
            stored = db.get_chain_account_raw(oid) or {}
            _capture_followers(page, oid, stored)
        return ok, code

    return _with_browser(oid, body, link_name=link_name)


def _passport_headers() -> dict[str, str]:
    return {
        "User-Agent": _UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com",
    }


def _passport_opener(proxy_url: str, jar: http.cookiejar.CookieJar):
    cookie = urllib.request.HTTPCookieProcessor(jar)
    if (proxy_url or "").strip():
        opener = proxy_util._make_proxy_opener(proxy_url)
        opener.add_handler(cookie)
        return opener
    return urllib.request.build_opener(cookie)


def _http_json(opener, url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=_passport_headers())
    with opener.open(req, timeout=25) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def _passport_warmup(opener) -> None:
    try:
        req = urllib.request.Request(HOME_URL, headers=_passport_headers())
        opener.open(req, timeout=20).read()
    except Exception:
        pass


def _passport_generate(opener) -> tuple[bytes, str, str]:
    _passport_warmup(opener)
    data = _http_json(opener, PASSPORT_GENERATE)
    payload = data.get("data") if isinstance(data.get("data"), dict) else {}
    url = str(payload.get("url") or "").strip()
    key = str(payload.get("qrcode_key") or "").strip()
    if data.get("code") not in (0, "0") or not url or not key:
        return b"", "", "website_changed"
    png = _png_from_login_url(url)
    if not png:
        return b"", "", "website_changed"
    return png, key, ""


def _passport_poll(opener, key: str) -> dict[str, Any]:
    q = urllib.parse.quote(key, safe="")
    data = _http_json(opener, f"{PASSPORT_POLL}?qrcode_key={q}")
    payload = data.get("data") if isinstance(data.get("data"), dict) else {}
    return payload if isinstance(payload, dict) else {}


def _png_from_login_url(url: str) -> bytes:
    try:
        import qrcode
    except ImportError:
        return b""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _playwright_cookies(jar: http.cookiejar.CookieJar | None) -> list[dict[str, Any]]:
    if jar is None:
        return []
    out: list[dict[str, Any]] = []
    for c in jar:
        name = str(c.name or "").strip()
        value = str(c.value or "")
        if not name:
            continue
        domain = str(c.domain or "").strip() or ".bilibili.com"
        rest = getattr(c, "_rest", {}) or {}
        item: dict[str, Any] = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": c.path or "/",
            "secure": bool(c.secure),
            "httpOnly": bool(rest.get("HttpOnly") or rest.get("httponly")),
        }
        if c.expires:
            try:
                item["expires"] = float(c.expires)
            except (TypeError, ValueError):
                pass
        out.append(item)
    return out


def _ensure_session(page) -> tuple[bool, str]:
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "website_changed"
    page.wait_for_timeout(1200)
    if _looks_logged_in(page):
        try:
            page.goto(MEMBER_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(800)
        except Exception:
            pass
        return True, _nickname(page) or "ok"
    if _looks_captcha(page):
        return False, "captcha"
    return False, "session_dead"


def _extra_payload(row: dict[str, Any] | None) -> dict[str, Any]:
    raw = str((row or {}).get("extra") or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _capture_followers(page, account_id: str, row: dict[str, Any] | None) -> None:
    oid = (account_id or "").strip()
    if not oid:
        return
    mid = ""
    try:
        nav = page.context.request.get(NAV_URL, timeout=20_000).json()
        inner = nav.get("data") if isinstance(nav, dict) else {}
        if isinstance(inner, dict):
            mid = str(inner.get("mid") or "").strip()
    except Exception:
        inner = {}
    if not mid:
        try:
            for c in page.context.cookies():
                if str(c.get("name") or "").lower() == "dedeuserid":
                    mid = str(c.get("value") or "").strip()
                    break
        except Exception:
            pass
    if not mid:
        return
    try:
        stat = page.context.request.get(
            f"{STAT_URL}?vmid={urllib.parse.quote(mid)}",
            timeout=20_000,
        ).json()
        payload = stat.get("data") if isinstance(stat.get("data"), dict) else {}
        followers = int(payload.get("follower") or 0)
    except Exception:
        return
    if followers < 0:
        return
    extra = _extra_payload(row)
    extra["followers"] = followers
    extra["followers_checked_at"] = datetime.now(timezone.utc).isoformat()
    extra["followers_mid"] = mid
    already = bool(extra.get("followers_alerted"))
    if followers >= FOLLOWER_GOAL and not already:
        login = str((row or {}).get("login") or (row or {}).get("name") or "").strip() or oid
        sent = notify.send_bilibili_followers_alert(
            login=login,
            followers=followers,
            goal=FOLLOWER_GOAL,
            lang="es",
        )
        if sent or not notify.smtp_configured():
            extra["followers_alerted"] = True
            extra["followers_alerted_at"] = extra["followers_checked_at"]
    db.update_chain_extra(oid, json.dumps(extra, ensure_ascii=False))


def _with_browser(account_id: str, fn, *, link_name: str = "") -> tuple[bool, str]:
    proxy_url = db.get_active_proxy_url_for_source("chain", account_id)
    if not proxy_url:
        name = (link_name or "").strip()
        raw = db.get_chain_account_raw(account_id) or {}
        name = name or str(raw.get("name") or "")
        if name:
            proxy_url = db.get_active_proxy_url_for_account_name(name)
    return playwright_session.with_persistent_browser(
        profile_dir(account_id),
        fn,
        proxy_url=proxy_url,
        locale="zh-CN",
        lock_wait_s=240,
    )


def _job_cancelled(job_id: str) -> bool:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job and job.get("cancel"):
        return True
    disk = _load_job_file(job_id)
    return bool(disk and disk.get("cancel"))


def _set_job(job_id: str, **fields: Any) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            job = _load_job_file(job_id) or {"id": job_id}
            _jobs[job_id] = job
        job.update(fields)
        _persist_job(job)


def _nickname(page) -> str:
    try:
        cookies = page.context.cookies()
    except Exception:
        cookies = []
    uid = ""
    for c in cookies:
        if str(c.get("name") or "").lower() == "dedeuserid":
            uid = str(c.get("value") or "").strip()
            break
    for sel in (
        ".header-avatar-wrap",
        ".nav-user-info",
        ".uname",
        ".user-name",
        "[class*='nickname']",
        "[class*='username']",
    ):
        el = _first_visible(page, [sel])
        if el is None:
            continue
        try:
            text = (el.inner_text() or "").strip()
        except Exception:
            text = ""
        if text and len(text) < 80 and "login" not in text.lower():
            return text.split("\n")[0].strip()
    return uid


def _first_visible(page, selectors: list[str]):
    for sel in selectors:
        try:
            loc = page.locator(sel)
            n = loc.count()
            for i in range(min(n, 6)):
                el = loc.nth(i)
                if el.is_visible():
                    return el
        except Exception:
            continue
    return None


def _looks_captcha(page) -> bool:
    try:
        if page.locator(
            "iframe[src*='recaptcha'], iframe[src*='geetest'], iframe[src*='hcaptcha'], "
            ".geetest_holder, input[name*='captcha' i]"
        ).count():
            return True
    except Exception:
        pass
    try:
        for fr in page.frames:
            url = (fr.url or "").lower()
            if any(x in url for x in ("recaptcha", "geetest", "hcaptcha")):
                return True
    except Exception:
        pass
    try:
        text = (page.inner_text("body") or "")[:4_000]
    except Exception:
        text = ""
    return bool(_CAPTCHA_RE.search(text) and re.search(r"sms|otp|geetest|人机", text, re.I))


def _looks_logged_in(page) -> bool:
    if _session_cookies(page):
        return True
    url = (page.url or "").lower()
    host = urlparse(url).hostname or ""
    if "passport.bilibili.com" in host and "login" in url:
        return False
    try:
        if page.locator(
            "a[href*='logout'], a[href*='member.bilibili.com'], .header-avatar-wrap, "
            ".nav-user-center, .bili-avatar"
        ).count():
            if not _session_cookies(page):
                return False
            return True
    except Exception:
        pass
    return False


def _session_cookies(page) -> bool:
    try:
        cookies = page.context.cookies()
    except Exception:
        return False
    names = set()
    for c in cookies:
        n = str(c.get("name") or "").strip().lower()
        v = str(c.get("value") or "").strip()
        if n in _LOGIN_COOKIE_NAMES and len(v) > 4:
            names.add(n)
    return bool(names & {"sessdata", "dedeuserid", "bili_jct"})


def _parse_iso(raw: str) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _other_next_times(except_id: str) -> list[datetime]:
    skip = (except_id or "").strip()
    out: list[datetime] = []
    for row in db.list_chain_accounts_raw(PLATFORM_ID):
        if str(row.get("id") or "") == skip:
            continue
        parsed = _parse_iso(str(row.get("next_keepalive_at") or ""))
        if parsed:
            out.append(parsed.astimezone(publish_schedule.PUBLISH_TZ))
    return out


def _record_session(
    account_id: str,
    ok: bool,
    code: str,
    row: dict[str, Any],
    *,
    next_keepalive_at: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    last_ok = now if ok else str(row.get("last_ok_at") or "")
    alert_at: str | None = None
    if not ok and code not in {"playwright_missing", "browser_busy", "cancelled", "expired"}:
        last_alert = str(row.get("last_alert_at") or "").strip()
        today = publish_schedule.now_publish_tz().date().isoformat()
        if not last_alert.startswith(today):
            login = str(row.get("login") or row.get("name") or "").strip() or account_id
            notify.send_bilibili_qr_session_alert(
                login=login,
                code=code,
                lang="es",
            )
            alert_at = now
    db.update_chain_browser_session(
        account_id,
        session_ok=ok,
        last_ok_at=now if ok else last_ok,
        last_error="" if ok else code,
        last_alert_at=alert_at,
        next_keepalive_at=next_keepalive_at,
    )


def export_web_session(account: dict[str, Any]) -> tuple[str, str, str]:
    """Cookie + csrf de la sesión QR. El navegador se cierra antes de la subida."""
    oid = str(account.get("id") or "").strip()
    if not oid:
        return "", "", "need_saved_account"
    captured = {"cookie": "", "csrf": ""}

    def body(page) -> tuple[bool, str]:
        ok, code = _ensure_session(page)
        if not ok:
            return False, code
        csrf = ""
        parts: list[str] = []
        try:
            cookies = page.context.cookies()
        except Exception:
            return False, "session_dead"
        for c in cookies:
            name = str(c.get("name") or "").strip()
            value = str(c.get("value") or "")
            if not name:
                continue
            parts.append(f"{name}={value}")
            if name.lower() == "bili_jct":
                csrf = value
        if not csrf or not _session_cookies(page):
            return False, "session_dead"
        captured["cookie"] = "; ".join(parts)
        captured["csrf"] = csrf
        return True, "ok"

    ok, code = _with_browser(oid, body, link_name=str(account.get("name") or ""))
    if not ok:
        return "", "", code or "browser_error"
    return captured["cookie"], captured["csrf"], ""


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

    import bilibili_studio
    from bilibili_publish import VIDEO_EXT

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

    cookie, csrf, err = export_web_session(account)
    if not cookie:
        key = {
            "session_dead": "bilibili_qr.err_session",
            "captcha": "bilibili_qr.err_captcha",
            "website_changed": "bilibili_qr.err_website",
            "browser_busy": "bilibili_qr.err_busy",
            "browser_error": "bilibili_qr.err_browser",
            "playwright_missing": "bilibili_tv.err_playwright",
        }.get((err or "").strip(), "bilibili_qr.err_session")
        return False, t(key, lang)
    try:
        resource_id = bilibili_studio.upload_archive(
            path=path,
            title=title,
            description=description,
            cookie=cookie,
            csrf=csrf,
        )
    except ValueError as e:
        detail = str(e).strip() or "upload"
        if detail == "session_dead":
            return False, t("bilibili_qr.err_session", lang)
        if detail == "website_changed":
            return False, t("bilibili_qr.err_website", lang)
        return False, t("pub.bilibili.upload_fail", lang, error=detail[:180])
    except Exception as e:
        return False, t("pub.bilibili.upload_fail", lang, error=str(e)[:180])
    if not resource_id:
        return False, t("pub.bilibili.upload_fail", lang, error="no id")
    return True, t("pub.bilibili.ok", lang, id=resource_id)
