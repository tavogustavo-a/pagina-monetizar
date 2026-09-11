"""Bilibili.com: sesión web con código QR (estudio member.bilibili.com), no Open Platform."""
from __future__ import annotations

import base64
import json
import random
import re
import shutil
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import db
import notify
import playwright_session
import publish_schedule

PLATFORM_ID = "bilibili_qr"
SERVER_PLATFORM_ID = "bilibili"
QR_SECRET = "qr-session"
HOME_URL = "https://www.bilibili.com/"
LOGIN_URL = "https://passport.bilibili.com/login"
MEMBER_URL = "https://member.bilibili.com/"
QR_WAIT_S = 12 * 60
QR_TICK_MS = 900
KEEP_DAYS_MIN = 3
KEEP_DAYS_MAX = 5
RETRY_HOURS_MIN = 8
RETRY_HOURS_MAX = 20
ACCOUNT_GAP_HOURS_MIN = 2
ACCOUNT_GAP_HOURS_MAX = 7
JOB_TTL_S = 20 * 60

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
_QR_EXPIRED_RE = re.compile(
    r"二维码已失效|二维码过期|二维码失效|点击刷新|click to refresh qr",
    re.I,
)

_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()

_QR_IMG_SELECTORS = [
    ".login-scan img",
    ".qrcode-img img",
    ".login-panel img",
    "img[src*='qrcode']",
    "img[src*='qr']",
    ".qr-code img",
    ".scan-code img",
    "canvas",
]
_QR_BOX_SELECTORS = [
    ".login-scan",
    ".qrcode-img",
    ".login-scan-box",
    ".qr-code",
    ".scan-code",
]


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
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "account_id": oid,
        "link_name": name,
        "is_new": is_new,
        "status": "starting",
        "qr_png": "",
        "message": "",
        "nickname": "",
        "error": "",
        "cancel": False,
        "created_at": time.time(),
    }
    with _jobs_lock:
        _jobs[job_id] = job
        _persist_job(job)
    thread = threading.Thread(target=_run_qr_job, args=(job_id,), daemon=True)
    thread.start()
    return {"ok": True, "job_id": job_id, "account_id": oid}


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
    return _with_browser(oid, _ensure_session)


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
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        candidate = (now_local + timedelta(days=days)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        if candidate <= now_local:
            candidate += timedelta(days=1)
    others = _other_next_times(except_id)
    gap = timedelta(hours=random.randint(ACCOUNT_GAP_HOURS_MIN, ACCOUNT_GAP_HOURS_MAX))
    for _ in range(36):
        if all(abs((candidate - other).total_seconds()) >= gap.total_seconds() for other in others):
            break
        candidate += gap
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
    stored = db.get_chain_account_raw(oid) or {}

    def body(page) -> tuple[bool, str]:
        return _qr_login_flow(page, job_id)

    ok, code = _with_browser(oid, body, link_name=link_name)
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
            if code and code not in {"ok"}:
                job["nickname"] = code
        else:
            job["status"] = code or "error"
            job["error"] = code or "error"
            job["qr_png"] = job.get("qr_png") or ""
        _persist_job(job)
    nick = ""
    with _jobs_lock:
        nick = str((_jobs.get(job_id) or {}).get("nickname") or "")
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


def _qr_login_flow(page, job_id: str) -> tuple[bool, str]:
    _set_job(job_id, status="waiting")
    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "website_changed"
    page.wait_for_timeout(800)
    _open_qr_tab(page)
    try:
        page.wait_for_selector(
            ".login-scan img, .qrcode-img img, img[src*='qrcode'], img[src*='qr'], canvas",
            timeout=20_000,
        )
    except Exception:
        pass
    page.wait_for_timeout(400)
    if _looks_logged_in(page):
        nick = _nickname(page)
        _set_job(job_id, nickname=nick)
        return True, nick or "ok"
    if _looks_captcha(page):
        return False, "captcha"
    deadline = time.time() + QR_WAIT_S
    last_png = b""
    saw_qr = False
    while time.time() < deadline:
        if _job_cancelled(job_id):
            return False, "cancelled"
        if _looks_captcha(page):
            return False, "captcha"
        if _looks_logged_in(page):
            nick = _nickname(page)
            _set_job(job_id, nickname=nick)
            return True, nick or "ok"
        if _qr_expired(page):
            _click_qr_refresh(page)
            page.wait_for_timeout(500)
        png = _qr_png(page)
        if png:
            saw_qr = True
            if png != last_png:
                last_png = png
                _set_job(
                    job_id,
                    status="waiting",
                    qr_png=base64.b64encode(png).decode("ascii"),
                )
        page.wait_for_timeout(QR_TICK_MS)
    if not saw_qr:
        return False, "website_changed"
    return False, "expired"


def _open_qr_tab(page) -> None:
    _click_first(
        page,
        [
            'div.login-tab:has-text("二维码")',
            'li:has-text("二维码登录")',
            'div:has-text("二维码登录")',
            ".qrcode-login",
            ".login-scan",
        ],
    )


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


def _qr_png(page) -> bytes:
    frames = [page]
    try:
        frames.extend(page.frames)
    except Exception:
        pass
    seen: set[int] = set()
    for fr in frames:
        if id(fr) in seen:
            continue
        seen.add(id(fr))
        for sel in _QR_IMG_SELECTORS:
            el = _first_visible(fr, [sel])
            if el is None:
                continue
            try:
                data = el.screenshot()
                if data and len(data) > 80:
                    return data
            except Exception:
                continue
        for sel in _QR_BOX_SELECTORS:
            el = _first_visible(fr, [sel])
            if el is None:
                continue
            try:
                data = el.screenshot()
                if data and len(data) > 80:
                    return data
            except Exception:
                continue
    return b""


def _qr_expired(page) -> bool:
    try:
        text = (page.inner_text("body") or "")[:4_000]
    except Exception:
        return False
    return bool(_QR_EXPIRED_RE.search(text))


def _click_qr_refresh(page) -> None:
    _click_first(
        page,
        [
            'button:has-text("刷新")',
            'a:has-text("刷新")',
            'button:has-text("Refresh")',
            ".login-scan",
            ".qrcode-img",
        ],
    )


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


def _click_first(page, selectors: list[str]) -> bool:
    el = _first_visible(page, selectors)
    if el is None:
        return False
    try:
        el.click()
        return True
    except Exception:
        return False


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
