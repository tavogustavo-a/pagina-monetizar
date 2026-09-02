"""Public site configuration (legal, TikTok app review)."""
from __future__ import annotations

import os

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
SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465") or "465")
SMTP_USER = os.environ.get("SMTP_USER", "").strip()
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").strip().replace(" ", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or CONTACT_EMAIL).strip()
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "0").strip().lower() in ("1", "true", "yes")
SITE_DESCRIPTION = (
    "Manage scheduled posts, track performance statistics, and grow your audience "
    "from a single, powerful dashboard powered by the official TikTok API."
)
HERO_TITLE = os.environ.get(
    "HERO_TITLE", "Optimize Your TikTok Content & Analytics"
)
HERO_SUBTITLE = os.environ.get(
    "HERO_SUBTITLE",
    "Manage scheduled posts, track performance statistics, and grow your audience "
    "from a single, powerful dashboard.",
)


def notification_email() -> str:
    """Correo del admin guardado en Panel (app_settings)."""
    try:
        import db

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
    }
