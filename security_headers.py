"""Cabeceras de seguridad (mismo CSP que Nginx).

En producción las pone Nginx (`add_header`). Aquí se replican en local
cuando RELOAD=1 o CONTENT_SECURITY_POLICY_FROM_APP=1, como en el proyecto IMAP.
"""
from __future__ import annotations

import os

from starlette.requests import Request
from starlette.responses import Response

# Dominios de login OAuth (navegación / form-action / connect). Las APIs
# de publicación van por el servidor, no por el navegador.
_OAUTH_HOSTS = (
    "https://www.tiktok.com https://tiktok.com "
    "https://accounts.google.com https://www.youtube.com "
    "https://www.instagram.com https://api.instagram.com "
    "https://www.facebook.com https://facebook.com "
    "https://twitter.com https://x.com "
    "https://www.dailymotion.com "
    "https://account.bilibili.com https://passport.bilibili.com https://www.bilibili.com "
    "https://accounts.snapchat.com https://www.snapchat.com "
    "https://rumble.com https://www.rumble.com"
)

_SITE_HOSTS = "https://tuyaho.com https://www.tuyaho.com"

# Avatares / thumbs si el panel muestra fotos de las cuentas conectadas.
_IMG_CDNS = (
    "https://*.tiktokcdn.com https://*.tiktokcdn-us.com https://*.tiktok.com "
    "https://*.googleusercontent.com https://yt3.ggpht.com https://i.ytimg.com "
    "https://*.fbcdn.net https://*.cdninstagram.com https://*.facebook.com "
    "https://*.twimg.com "
    "https://*.dmcdn.net "
    "https://*.hdslb.com "
    "https://*.snapchat.com https://*.sc-cdn.net "
    "https://*.rumble.com https://*.rmbl.ws"
)

# Estilos inline (login, stats, extractor). JS inline del panel: 'unsafe-inline'
# en script-src hasta extraer esos <script> a archivos (IMAP ya lo hizo).
_CSP_DEFAULT = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "worker-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    f"font-src 'self' https://fonts.gstatic.com; "
    f"img-src 'self' data: blob: {_IMG_CDNS}; "
    "media-src 'self' blob: data:; "
    f"connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com {_OAUTH_HOSTS} {_SITE_HOSTS}; "
    f"form-action 'self' {_OAUTH_HOSTS} {_SITE_HOSTS}; "
    "frame-ancestors 'self'; "
    "base-uri 'self'; "
    "object-src 'none';"
)

CONTENT_SECURITY_POLICY = (os.getenv("CONTENT_SECURITY_POLICY") or "").strip() or _CSP_DEFAULT

X_FRAME_OPTIONS = "SAMEORIGIN"
X_CONTENT_TYPE_OPTIONS = "nosniff"
REFERRER_POLICY = "strict-origin-when-cross-origin"
PERMISSIONS_POLICY = (
    "geolocation=(), microphone=(), camera=(), payment=(), usb=(), serial=(), bluetooth=()"
)
HSTS = "max-age=31536000"


def content_security_policy_from_app() -> bool:
    flag = (os.getenv("CONTENT_SECURITY_POLICY_FROM_APP") or "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    if flag in ("0", "false", "no", "off"):
        return False
    reload_on = os.environ.get("RELOAD", "1").lower() in ("1", "true", "yes")
    site = (os.environ.get("SITE_URL") or "").strip().lower()
    local_site = ("127.0.0.1" in site) or ("localhost" in site)
    return reload_on or local_site


def apply_security_headers(request: Request, response: Response) -> None:
    if not content_security_policy_from_app():
        return
    headers = response.headers
    if CONTENT_SECURITY_POLICY and not headers.get("Content-Security-Policy"):
        headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
    if not headers.get("X-Frame-Options"):
        headers["X-Frame-Options"] = X_FRAME_OPTIONS
    if not headers.get("X-Content-Type-Options"):
        headers["X-Content-Type-Options"] = X_CONTENT_TYPE_OPTIONS
    if not headers.get("Referrer-Policy"):
        headers["Referrer-Policy"] = REFERRER_POLICY
    if not headers.get("Permissions-Policy"):
        headers["Permissions-Policy"] = PERMISSIONS_POLICY
    https = request.url.scheme == "https"
    forwarded = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    if (https or forwarded == "https") and not headers.get("Strict-Transport-Security"):
        headers["Strict-Transport-Security"] = HSTS
