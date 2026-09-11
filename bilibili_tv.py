"""Bilibili.tv: sesión en navegador interno (Playwright), no OAuth ni API de .com."""
from __future__ import annotations

import re
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import db
import notify
import publish_schedule

PLATFORM_ID = "bilibili_tv"
HOME_URL = "https://www.bilibili.tv/"
LOGIN_URLS = (
    "https://www.bilibili.tv/en/account/login",
    "https://www.bilibili.tv/en/login",
    "https://www.bilibili.tv/login",
)
CHECK_HOUR_LOCAL = 3
LAST_CHECK_KEY = "bilibili_tv_keepalive_day"
NAV_TIMEOUT_MS = 45_000
LOCK_WAIT_S = 180
_BROWSER_LOCK = threading.Lock()

_LOGIN_COOKIE_NAMES = frozenset(
    {
        "sessdata",
        "dedeuserid",
        "bili_jct",
        "bstar_id",
        "bstar_session",
        "access_key",
        "uid",
        "userid",
        "user_id",
    }
)
_CAPTCHA_RE = re.compile(
    r"captcha|recaptcha|geetest|hcaptcha|verify you|sms code|verification code|"
    r"phone code|otp|验证|人机",
    re.I,
)
_LOGGED_IN_RE = re.compile(
    r"log\s*out|sign\s*out|studio|creator|dashboard|my\s+channel|sign\s*out",
    re.I,
)


def profile_dir(account_id: str) -> Path:
    from db_engine import DATA_DIR

    safe = "".join(ch for ch in (account_id or "").strip() if ch.isalnum() or ch in "-_")
    return DATA_DIR / "bilibili_tv_profiles" / (safe or "_invalid")


def remove_profile(account_id: str) -> None:
    path = profile_dir(account_id)
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def playwright_ready() -> tuple[bool, str]:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return False, "playwright_missing"
    return True, ""


def probe_account(login: str, secret: str, extra: str = "", account_id: str = "") -> tuple[bool, str]:
    em = (login or "").strip()
    pw = (secret or "").strip()
    if not em or not pw:
        return False, "email_password_required"
    oid = (account_id or "").strip()
    if not oid:
        return False, "need_saved_account"
    return _with_browser(oid, lambda page: _ensure_session(page, em, pw))


def keep_alive_account(account: dict[str, Any]) -> tuple[bool, str]:
    oid = str(account.get("id") or "").strip()
    em = str(account.get("login") or "").strip()
    pw = str(account.get("secret") or "").strip()
    if not oid:
        return False, "need_saved_account"
    return _with_browser(oid, lambda page: _ensure_session(page, em, pw))


def run_daily_keep_alive_if_due() -> None:
    """A las 3:00 (hora del panel, UTC-5) visita las cuentas una detrás de otra."""
    now = publish_schedule.now_publish_tz()
    if now.hour < CHECK_HOUR_LOCAL:
        return
    last = (db.get_app_setting(LAST_CHECK_KEY) or "").strip()
    today = now.date().isoformat()
    if last == today:
        return
    for row in db.list_chain_accounts_raw(PLATFORM_ID):
        ok, code = keep_alive_account(row)
        _record_session(str(row.get("id") or ""), ok, code, row)
    db.set_app_setting(LAST_CHECK_KEY, today)


def _record_session(account_id: str, ok: bool, code: str, row: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    last_ok = now if ok else str(row.get("last_ok_at") or "")
    db.update_chain_browser_session(
        account_id,
        session_ok=ok,
        last_ok_at=last_ok if ok else str(row.get("last_ok_at") or ""),
        last_error="" if ok else code,
    )
    if ok:
        return
    if code in {"playwright_missing", "browser_busy"}:
        return
    last_alert = str(row.get("last_alert_at") or "").strip()
    today = publish_schedule.now_publish_tz().date().isoformat()
    if last_alert.startswith(today):
        return
    login = str(row.get("login") or "").strip() or account_id
    notify.send_bilibili_tv_session_alert(
        login=login,
        code=code,
        lang="es",
    )
    db.update_chain_browser_session(
        account_id,
        session_ok=ok,
        last_ok_at=str(row.get("last_ok_at") or ""),
        last_error=code,
        last_alert_at=now,
    )


def _with_browser(account_id: str, fn) -> tuple[bool, str]:
    ready, err = playwright_ready()
    if not ready:
        return False, err
    got = _BROWSER_LOCK.acquire(timeout=LOCK_WAIT_S)
    if not got:
        return False, "browser_busy"
    try:
        from playwright.sync_api import sync_playwright

        path = profile_dir(account_id)
        path.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(path),
                    headless=True,
                    viewport={"width": 1360, "height": 900},
                    locale="en-US",
                    args=[
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    page.set_default_timeout(NAV_TIMEOUT_MS)
                    return fn(page)
                finally:
                    context.close()
        except Exception as e:
            msg = str(e or "").lower()
            if "executable doesn't exist" in msg or "playwright install" in msg:
                return False, "playwright_missing"
            return False, "browser_error"
    finally:
        _BROWSER_LOCK.release()


def _ensure_session(page, email: str, password: str) -> tuple[bool, str]:
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "website_changed"
    page.wait_for_timeout(1200)
    if _looks_logged_in(page):
        return True, email
    if _looks_captcha(page):
        return False, "captcha"
    if not _open_login(page):
        return False, "website_changed"
    page.wait_for_timeout(800)
    if _looks_captcha(page):
        return False, "captcha"
    if not _fill_credentials(page, email, password):
        return False, "website_changed"
    page.wait_for_timeout(2500)
    if _looks_captcha(page):
        return False, "captcha"
    if _looks_logged_in(page):
        return True, email
    if _looks_bad_password(page):
        return False, "login_failed"
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
    except Exception:
        pass
    if _looks_logged_in(page):
        return True, email
    if _looks_captcha(page):
        return False, "captcha"
    return False, "session_dead"


def _open_login(page) -> bool:
    for url in LOGIN_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(700)
            if _email_input(page) is not None:
                return True
        except Exception:
            continue
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded")
    except Exception:
        return False
    clicked = _click_first(
        page,
        [
            'a[href*="login"]',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'a:has-text("Log in")',
            'a:has-text("Sign in")',
        ],
    )
    if clicked:
        page.wait_for_timeout(1000)
    return _email_input(page) is not None or _password_input(page) is not None


def _fill_credentials(page, email: str, password: str) -> bool:
    email_el = _email_input(page)
    pwd_el = _password_input(page)
    if email_el is None or pwd_el is None:
        return False
    try:
        email_el.click()
        email_el.fill(email)
        pwd_el.click()
        pwd_el.fill(password)
    except Exception:
        return False
    submitted = _click_first(
        page,
        [
            'button[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            'button:has-text("Login")',
            'button:has-text("Continue")',
        ],
    )
    if not submitted:
        try:
            pwd_el.press("Enter")
        except Exception:
            return False
    return True


def _email_input(page):
    return _first_visible(
        page,
        [
            'input[type="email"]',
            'input[name="username"]',
            'input[name="email"]',
            'input[name="account"]',
            'input[autocomplete="username"]',
            'input[placeholder*="mail" i]',
            'input[placeholder*="phone" i]',
        ],
    )


def _password_input(page):
    return _first_visible(
        page,
        [
            'input[type="password"]',
            'input[name="password"]',
            'input[autocomplete="current-password"]',
        ],
    )


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
            ".geetest_holder, input[name*='captcha' i], input[name*='sms' i]"
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
    return bool(_CAPTCHA_RE.search(text) and re.search(r"sms|otp|verify you are human", text, re.I))


def _looks_bad_password(page) -> bool:
    try:
        text = (page.inner_text("body") or "")[:8_000]
    except Exception:
        return False
    return bool(
        re.search(
            r"incorrect|wrong password|invalid (email|password)|account or password|"
            r"contraseña incorrecta|no coincide",
            text,
            re.I,
        )
    )


def _looks_logged_in(page) -> bool:
    if _session_cookies(page):
        return True
    url = (page.url or "").lower()
    host = urlparse(url).hostname or ""
    if "login" in url and "bilibili.tv" in host:
        return False
    try:
        body = (page.inner_text("body") or "")[:12_000]
    except Exception:
        body = ""
    if _LOGGED_IN_RE.search(body) and not re.search(r"\blog in\b|\bsign in\b", body, re.I):
        return True
    try:
        if page.locator('a[href*="logout"], [class*="avatar"], [class*="Avatar"]').count():
            if _email_input(page) is None:
                return True
    except Exception:
        pass
    return False


def _session_cookies(page) -> bool:
    try:
        cookies = page.context.cookies()
    except Exception:
        return False
    names = {str(c.get("name") or "").strip().lower() for c in cookies}
    if names & _LOGIN_COOKIE_NAMES:
        return True
    for c in cookies:
        n = str(c.get("name") or "").lower()
        v = str(c.get("value") or "")
        if "session" in n and len(v) > 12:
            return True
    return False
