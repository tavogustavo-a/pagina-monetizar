"""Chromium persistente (Playwright) con proxy del panel. Un navegador a la vez."""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Callable

import proxy_util

LOCK_WAIT_S = 240
NAV_TIMEOUT_MS = 45_000
NAV_TIMEOUT_PROXY_MS = 90_000
_BROWSER_LOCK = threading.Lock()


def _prefer_user_browsers() -> None:
    """Si Cursor apunta a un cache vacío, usa el Chromium de AppData."""
    raw = (os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "").strip()
    if not raw:
        return
    root = Path(raw)
    has_browser = any(root.glob("chromium*")) if root.is_dir() else False
    if not has_browser:
        os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)


def playwright_ready() -> tuple[bool, str]:
    _prefer_user_browsers()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright_missing"
    try:
        with sync_playwright() as p:
            exe = (p.chromium.executable_path or "").strip()
            if not exe or not Path(exe).is_file():
                return False, "playwright_missing"
    except Exception:
        return False, "playwright_missing"
    return True, ""


def classify_launch_error(exc: BaseException, *, proxy: bool = False) -> str:
    msg = str(exc or "").lower()
    if (
        "executable doesn't exist" in msg
        or "executable does not exist" in msg
        or "playwright install" in msg
        or ("executable" in msg and "exist" in msg)
    ):
        return "playwright_missing"
    if (
        "timeout" in msg
        or "timed out" in msg
        or "proxy" in msg
        or "err_proxy" in msg
        or "tunnel" in msg
        or "err_socks" in msg
        or "err_connection" in msg
    ):
        return "proxy_slow" if proxy else "timeout"
    return "browser_error"


def is_nav_timeout(exc: BaseException) -> bool:
    return classify_launch_error(exc, proxy=True) in {"proxy_slow", "timeout"}


def playwright_proxy(proxy_url: str) -> dict[str, str] | None:
    text = (proxy_url or "").strip()
    if not text:
        return None
    try:
        data = proxy_util.parse_proxy_line(text)
    except ValueError:
        return None
    proto = proxy_util.normalize_protocol(str(data.get("protocol") or "http"))
    if proto == "https":
        proto = "http"
    host = str(data.get("host") or "").strip()
    port = int(data.get("port") or 0)
    if not host or port <= 0:
        return None
    out: dict[str, str] = {"server": f"{proto}://{host}:{port}"}
    user = str(data.get("username") or "").strip()
    if user:
        out["username"] = user
        out["password"] = str(data.get("password") or "")
    return out


def with_persistent_browser(
    profile_path: Path,
    fn: Callable[[Any], tuple[bool, str]],
    *,
    proxy_url: str = "",
    locale: str = "en-US",
    lock_wait_s: int = LOCK_WAIT_S,
) -> tuple[bool, str]:
    ready, err = playwright_ready()
    if not ready:
        return False, err
    got = _BROWSER_LOCK.acquire(timeout=lock_wait_s)
    if not got:
        return False, "browser_busy"
    try:
        from playwright.sync_api import sync_playwright

        profile_path.mkdir(parents=True, exist_ok=True)
        kwargs: dict[str, Any] = {
            "user_data_dir": str(profile_path),
            "headless": True,
            "viewport": {"width": 1360, "height": 900},
            "locale": locale,
            "args": [
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        }
        proxy = playwright_proxy(proxy_url)
        if proxy:
            kwargs["proxy"] = proxy
        nav_ms = NAV_TIMEOUT_PROXY_MS if proxy else NAV_TIMEOUT_MS
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(**kwargs)
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    page.set_default_timeout(nav_ms)
                    page.set_default_navigation_timeout(nav_ms)
                    return fn(page)
                finally:
                    context.close()
        except Exception as e:
            return False, classify_launch_error(e, proxy=bool(proxy))
    finally:
        _BROWSER_LOCK.release()
