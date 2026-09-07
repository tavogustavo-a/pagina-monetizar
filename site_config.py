"""Public site configuration (legal, app review)."""
from __future__ import annotations

import os
from datetime import datetime

SITE_NAME = os.environ.get("SITE_NAME", "Creator Hub").strip() or "Creator Hub"
COMPANY_NAME = os.environ.get("COMPANY_NAME", SITE_NAME).strip() or SITE_NAME
CONTACT_EMAIL = (
    os.environ.get("CONTACT_EMAIL", "support@yourdomain.com").strip()
    or "support@yourdomain.com"
)
SUPPORT_EMAIL = (
    os.environ.get("SUPPORT_EMAIL", CONTACT_EMAIL).strip() or CONTACT_EMAIL
)
SITE_URL = os.environ.get("SITE_URL", "https://yourdomain.com").strip().rstrip("/")


def is_local_host(host: str | None) -> bool:
    h = (host or "").strip().lower()
    if not h:
        return False
    if h in ("127.0.0.1", "localhost", "::1"):
        return True
    if h.startswith("127.") or h.endswith(".local"):
        return True
    return False


def effective_site_url(request=None) -> str:
    """URL pública del panel (SITE_URL). La callback OAuth debe coincidir con la consola del proveedor."""
    return SITE_URL


def oauth_callback_url(platform_id: str, request=None) -> str:
    pid = (platform_id or "").strip().lower()
    if not pid:
        return SITE_URL
    return f"{SITE_URL}/oauth/{pid}/callback"


def resolve_oauth_redirect(
    platform_id: str,
    request=None,
    env_value: str = "",
) -> str:
    """Env → Callback guardada (https pública) → SITE_URL/oauth/{plataforma}/callback."""
    env = (env_value or "").strip()
    if env:
        return env
    extra = oauth_redirect_from_credentials(platform_id)
    if extra:
        return extra
    try:
        return oauth_callback_url(platform_id, request)
    except Exception:
        pid = (platform_id or "").strip().lower() or "oauth"
        return f"{SITE_URL}/oauth/{pid}/callback"


def oauth_redirect_from_credentials(platform_id: str) -> str:
    """Si en Servidores guardaron una Callback/Redirect URI pública (campo extra), usarla."""
    pid = (platform_id or "").strip().lower()
    if not pid:
        return ""
    try:
        import db
        from urllib.parse import urlparse

        raw = db.get_platform_credentials_raw(pid) or {}
        extra = str(raw.get("extra") or "").strip()
        low = extra.lower()
        if not (low.startswith("http://") or low.startswith("https://")):
            return ""
        host = urlparse(extra).hostname
        if is_local_host(host):
            return ""
        return extra
    except Exception:
        pass
    return ""


SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465") or "465")
SMTP_USER = os.environ.get("SMTP_USER", "").strip()
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").strip().replace(" ", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or CONTACT_EMAIL).strip()
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "0").strip().lower() in ("1", "true", "yes")
SITE_DESCRIPTION = (
    "Grow on social media from one dashboard: schedule posts, track performance, "
    "and engage your audience with official, permission-based connections."
)
HERO_TITLE = os.environ.get(
    "HERO_TITLE", "Grow your presence on social media"
)
HERO_SUBTITLE = os.environ.get(
    "HERO_SUBTITLE",
    "Schedule posts, track performance statistics, and grow your audience "
    "from a single, powerful dashboard.",
)


def notification_email() -> str:
    """Correo del admin del sitio (por usuario; fallback legacy)."""
    try:
        import db

        conn = db._connect()
        try:
            row = conn.execute(
                """
                SELECT notification_email FROM users
                WHERE role = 'admin' AND trim(notification_email) != ''
                ORDER BY created_at LIMIT 1
                """
            ).fetchone()
            if row and str(row["notification_email"] or "").strip():
                return str(row["notification_email"]).strip()
        finally:
            conn.close()
        stored = db.get_app_setting("admin_email")
        if stored:
            return stored
    except Exception:
        pass
    return ""


def legal_context() -> dict[str, str]:
    return {
        "site_name": SITE_NAME,
        "company_name": COMPANY_NAME,
        "contact_email": CONTACT_EMAIL,
        "support_email": SUPPORT_EMAIL,
        "site_url": SITE_URL,
        "site_description": SITE_DESCRIPTION,
        "hero_title": HERO_TITLE,
        "hero_subtitle": HERO_SUBTITLE,
        "current_year": str(datetime.now().year),
    }
