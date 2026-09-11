"""Bilibili.tv: sesión en navegador interno (Playwright), no OAuth ni API de .com."""
from __future__ import annotations

import random
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import db
import notify
import playwright_session
import publish_schedule

PLATFORM_ID = "bilibili_tv"
HOME_URL = "https://www.bilibili.tv/"
STUDIO_NEW_URL = "https://studio.bilibili.tv/archive/new"
VIDEO_EXT = {".mp4", ".flv", ".avi", ".wmv", ".mov", ".mkv", ".webm"}
UPLOAD_WAIT_S = 15 * 60
PUBLISH_LOCK_S = 20 * 60
LOGIN_URLS = (
    "https://www.bilibili.tv/en/account/login",
    "https://www.bilibili.tv/en/login",
    "https://www.bilibili.tv/login",
)
KEEP_DAYS_MIN = 3
KEEP_DAYS_MAX = 5
RETRY_HOURS_MIN = 8
RETRY_HOURS_MAX = 20
ACCOUNT_GAP_HOURS_MIN = 2
ACCOUNT_GAP_HOURS_MAX = 7
NAV_TIMEOUT_MS = playwright_session.NAV_TIMEOUT_MS

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
    return playwright_session.playwright_ready()


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
    oid = str(account.get("id") or "").strip()
    em = str(account.get("login") or "").strip()
    pw = str(account.get("secret") or "").strip()
    if not oid or not em or not pw:
        return False, t("pub.chain.no_account", lang)
    label = (title or "").strip() or path.stem
    desc = (description or "").strip()

    def body(page) -> tuple[bool, str]:
        ok, code = _ensure_session(page, em, pw)
        if not ok:
            return False, code
        return _studio_upload(page, path, label, desc)

    ok, code = _with_browser(oid, body, lock_wait_s=PUBLISH_LOCK_S)
    if ok and code and code not in {"ok", "email"}:
        return True, t("pub.bilibili_tv.ok", lang, id=code)
    key = {
        "session_dead": "bilibili_tv.err_session",
        "captcha": "bilibili_tv.err_captcha",
        "website_changed": "bilibili_tv.err_website",
        "browser_busy": "bilibili_tv.err_busy",
        "browser_error": "bilibili_tv.err_browser",
        "playwright_missing": "bilibili_tv.err_playwright",
        "login_failed": "bilibili_tv.err_login",
    }.get((code or "").strip())
    if key:
        return False, t(key, lang)
    return False, t("pub.bilibili.upload_fail", lang, error=(code or "upload")[:180])


def schedule_next_visit(account_id: str, *, soon: bool = False) -> str:
    """Próxima visita: 3–5 días a hora aleatoria, o reintento en horas si la sesión cayó."""
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


def run_daily_keep_alive_if_due() -> None:
    """Visita como máximo una cuenta por ciclo: 3–5 días, horas distintas; relogin si caducó."""
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
    soon = (not ok) and code in {"session_dead", "login_failed", "browser_error"}
    next_at = pick_next_keepalive(except_id=oid, soon=soon)
    _record_session(oid, ok, code, row, next_keepalive_at=next_at)


def _record_session(
    account_id: str,
    ok: bool,
    code: str,
    row: dict[str, Any],
    *,
    next_keepalive_at: str = "",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    last_ok = now if ok else str(row.get("last_ok_at") or "")
    alert_at: str | None = None
    if not ok and code not in {"playwright_missing", "browser_busy"}:
        last_alert = str(row.get("last_alert_at") or "").strip()
        today = publish_schedule.now_publish_tz().date().isoformat()
        if not last_alert.startswith(today):
            login = str(row.get("login") or "").strip() or account_id
            notify.send_bilibili_tv_session_alert(
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
        next_keepalive_at=next_keepalive_at or None,
    )


def _with_browser(account_id: str, fn, *, lock_wait_s: int | None = None) -> tuple[bool, str]:
    proxy_url = db.get_active_proxy_url_for_source("chain", account_id)
    kwargs: dict[str, Any] = {
        "proxy_url": proxy_url,
        "locale": "en-US",
    }
    if lock_wait_s is not None:
        kwargs["lock_wait_s"] = lock_wait_s
    return playwright_session.with_persistent_browser(profile_dir(account_id), fn, **kwargs)


def _ensure_session(page, email: str, password: str) -> tuple[bool, str]:
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "website_changed"
    page.wait_for_timeout(1200)
    _dismiss_noise(page)
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
    page.wait_for_timeout(2800)
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


def _studio_upload(page, path: Path, title: str, description: str) -> tuple[bool, str]:
    found: dict[str, str] = {"id": ""}

    def on_response(resp) -> None:
        url = (resp.url or "").lower()
        if not any(x in url for x in ("submit", "publish", "add/v3", "/add", "archive/add")):
            return
        try:
            data = resp.json()
        except Exception:
            return
        vid = _id_from_payload(data)
        if vid:
            found["id"] = vid

    try:
        page.on("response", on_response)
    except Exception:
        pass
    try:
        page.goto(STUDIO_NEW_URL, wait_until="domcontentloaded")
    except Exception:
        return False, "website_changed"
    page.wait_for_timeout(1500)
    if _looks_captcha(page):
        return False, "captcha"
    file_input = None
    try:
        loc = page.locator("input[type='file']")
        if loc.count():
            file_input = loc.first
    except Exception:
        file_input = None
    if file_input is None:
        return False, "website_changed"
    try:
        file_input.set_input_files(str(path))
    except Exception:
        return False, "website_changed"
    if not _wait_upload_ready(page):
        return False, "website_changed"
    _fill_studio_title(page, title)
    if description:
        _fill_studio_desc(page, description)
    _attach_cover(page, path)
    _pick_first_category(page)
    found["id"] = ""
    if not _click_first(
        page,
        [
            'button:has-text("Publish")',
            'button:has-text("Submit")',
            'button:has-text("Post")',
            'button:has-text("发布")',
            'button:has-text("投稿")',
            'button[type="submit"]',
        ],
    ):
        return False, "website_changed"
    deadline = datetime.now(timezone.utc).timestamp() + 90
    while datetime.now(timezone.utc).timestamp() < deadline:
        if found["id"]:
            return True, found["id"]
        url = (page.url or "").lower()
        m = re.search(r"/video/(\d+)", url)
        if m:
            return True, m.group(1)
        if "archive-list" in url and found["id"]:
            return True, found["id"]
        page.wait_for_timeout(1500)
    if found["id"]:
        return True, found["id"]
    return False, "website_changed"


def _id_from_payload(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    inner = data.get("data")
    blobs: list[dict[str, Any]] = [data]
    if isinstance(inner, dict):
        blobs.append(inner)
    for blob in blobs:
        for key in ("bvid", "aid", "avid", "resource_id", "video_id"):
            val = str(blob.get(key) or "").strip()
            if val and val.lower() not in {"0", "ok", "success", "true"}:
                return val
        val = str(blob.get("id") or "").strip()
        if val.isdigit() and len(val) >= 6:
            return val
    code = data.get("code")
    if code not in (None, 0, "0"):
        return ""
    return ""


def _wait_upload_ready(page) -> bool:
    deadline = datetime.now(timezone.utc).timestamp() + UPLOAD_WAIT_S
    while datetime.now(timezone.utc).timestamp() < deadline:
        if _looks_captcha(page):
            return False
        try:
            body = (page.inner_text("body") or "")[:4000]
        except Exception:
            body = ""
        low = body.lower()
        if any(x in low for x in ("100%", "upload complete", "uploaded", "processing", "cover")):
            if _studio_title_box(page) is not None:
                return True
        if _studio_title_box(page) is not None and not re.search(r"\b([1-9]\d?%)\b", low):
            return True
        page.wait_for_timeout(2000)
    return _studio_title_box(page) is not None


def _studio_title_box(page):
    return _first_visible(
        page,
        [
            'input[placeholder*="title" i]',
            'textarea[placeholder*="title" i]',
            'input[name="title"]',
            'textarea[name="title"]',
            'input[maxlength="80"]',
            'input[maxlength="100"]',
        ],
    )


def _fill_studio_title(page, title: str) -> None:
    el = _studio_title_box(page)
    if el is None:
        return
    try:
        el.click()
        el.fill(title[:80])
    except Exception:
        pass


def _fill_studio_desc(page, description: str) -> None:
    el = _first_visible(
        page,
        [
            'textarea[placeholder*="desc" i]',
            'textarea[placeholder*="intro" i]',
            'textarea[name="description"]',
            'textarea[name="desc"]',
        ],
    )
    if el is None:
        return
    try:
        el.fill(description[:2000])
    except Exception:
        pass


def _attach_cover(page, video_path: Path) -> None:
    try:
        from bilibili_publish import _extract_cover
    except Exception:
        return
    try:
        cover = _extract_cover(video_path)
    except Exception:
        cover = None
    if not cover:
        return
    try:
        loc = page.locator(
            "input[type='file'][accept*='image'], input[type='file'][accept*='jpg']"
        )
        if loc.count():
            loc.last.set_input_files(str(cover))
    except Exception:
        pass
    try:
        cover.unlink(missing_ok=True)
    except OSError:
        pass


def _pick_first_category(page) -> None:
    _click_first(
        page,
        [
            '[class*="select"]',
            '[class*="category"]',
            '[class*="partition"]',
            'div[role="combobox"]',
        ],
    )
    page.wait_for_timeout(400)
    _click_first(
        page,
        [
            '[class*="option"]:visible',
            '[role="option"]',
            "li[class*='option']",
        ],
    )


def _dismiss_noise(page) -> None:
    _click_first(
        page,
        [
            'button:has-text("Accept")',
            'button:has-text("Agree")',
            'button:has-text("I agree")',
            'button:has-text("Got it")',
            'button:has-text("OK")',
            '[aria-label="Close"]',
            'button:has-text("Close")',
        ],
    )


def _open_login(page) -> bool:
    for url in LOGIN_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(700)
            _dismiss_noise(page)
            if _reveal_email_login(page):
                return True
        except Exception:
            continue
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded")
    except Exception:
        return False
    page.wait_for_timeout(800)
    _dismiss_noise(page)
    _click_first(
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
    page.wait_for_timeout(900)
    _reveal_email_login(page)
    return _email_input(page) is not None or _password_input(page) is not None


def _reveal_email_login(page) -> bool:
    if _email_input(page) is not None or _password_input(page) is not None:
        return True
    _click_first(
        page,
        [
            'button:has-text("Log in with Email")',
            'button:has-text("Login with Email")',
            'button:has-text("Sign in with Email")',
            'a:has-text("Log in with Email")',
            'button:has-text("Email")',
            'a:has-text("Email")',
            '[class*="email"]',
        ],
    )
    page.wait_for_timeout(800)
    return _email_input(page) is not None or _password_input(page) is not None


def _fill_credentials(page, email: str, password: str) -> bool:
    email_el = _email_input(page)
    pwd_el = _password_input(page)
    if email_el is None and pwd_el is None:
        return False
    try:
        if email_el is not None:
            email_el.click()
            email_el.fill(email)
        if pwd_el is None:
            _click_first(
                page,
                [
                    'button:has-text("Continue")',
                    'button:has-text("Next")',
                    'button[type="submit"]',
                ],
            )
            page.wait_for_timeout(900)
            pwd_el = _password_input(page)
        if pwd_el is None:
            return False
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
            'input[name="email"]',
            'input[name="username"]',
            'input[name="account"]',
            'input[autocomplete="username"]',
            'input[placeholder*="mail" i]',
            'input[placeholder*="phone" i]',
            'input[type="text"]',
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
    scopes = [page]
    try:
        scopes.extend(list(page.frames))
    except Exception:
        pass
    for scope in scopes:
        for sel in selectors:
            try:
                loc = scope.locator(sel)
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
