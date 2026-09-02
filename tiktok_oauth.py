"""TikTok Login Kit / OAuth 2.0 (credentials from environment only)."""
from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_USERINFO_URL = "https://open.tiktokapis.com/v2/user/info/"

DEFAULT_SCOPES = "user.info.basic,video.upload,video.publish"


def client_key() -> str:
    env = (os.environ.get("TIKTOK_CLIENT_KEY") or os.environ.get("TIKTOK_CLIENT_ID") or "").strip()
    if env:
        return env
    try:
        import db

        raw = db.get_platform_credentials_raw("tiktok") or {}
        return (raw.get("client_id") or "").strip()
    except Exception:
        return ""


def client_secret() -> str:
    env = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
    if env:
        return env
    try:
        import db

        raw = db.get_platform_credentials_raw("tiktok") or {}
        return (raw.get("client_secret") or "").strip()
    except Exception:
        return ""


def redirect_uri() -> str:
    env = os.environ.get("TIKTOK_REDIRECT_URI", "").strip()
    if env:
        return env
    try:
        import db

        raw = db.get_platform_credentials_raw("tiktok") or {}
        extra = (raw.get("extra") or "").strip()
        if extra:
            return extra
    except Exception:
        pass
    try:
        from site_config import SITE_URL

        return f"{SITE_URL}/oauth/tiktok/callback"
    except Exception:
        return "http://127.0.0.1:8000/oauth/tiktok/callback"


def oauth_scopes() -> str:
    return (os.environ.get("TIKTOK_SCOPES") or DEFAULT_SCOPES).strip()


def oauth_configured() -> bool:
    return bool(client_key() and client_secret() and redirect_uri())


def new_csrf_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(*, state: str) -> str:
    params = {
        "client_key": client_key(),
        "scope": oauth_scopes(),
        "response_type": "code",
        "redirect_uri": redirect_uri(),
        "state": state,
    }
    return TIKTOK_AUTH_URL + "?" + urllib.parse.urlencode(params)


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    payload = {
        "client_key": client_key(),
        "client_secret": client_secret(),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri(),
    }
    data = _post_form(TIKTOK_TOKEN_URL, payload)
    if "error" in data or data.get("error_code"):
        msg = data.get("error_description") or data.get("description") or str(data)
        raise ValueError(f"TikTok token error: {msg}")
    return data.get("data") or data


def refresh_access_token(
    refresh_token: str,
    *,
    client_key_value: str | None = None,
    client_secret_value: str | None = None,
) -> dict[str, Any]:
    payload = {
        "client_key": (client_key_value or "").strip() or client_key(),
        "client_secret": (client_secret_value or "").strip() or client_secret(),
        "grant_type": "refresh_token",
        "refresh_token": (refresh_token or "").strip(),
    }
    if not payload["client_key"] or not payload["client_secret"] or not payload["refresh_token"]:
        raise ValueError("TikTok refresh token is missing credentials.")
    data = _post_form(TIKTOK_TOKEN_URL, payload)
    if "error" in data or data.get("error_code"):
        msg = data.get("error_description") or data.get("description") or str(data)
        raise ValueError(f"TikTok refresh error: {msg}")
    return data.get("data") or data


def fetch_user_profile(access_token: str) -> dict[str, Any]:
    fields = "open_id,union_id,avatar_url,display_name,username"
    url = TIKTOK_USERINFO_URL + "?" + urllib.parse.urlencode({"fields": fields})
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise ValueError(f"TikTok user info failed: {body}") from e
    data = json.loads(raw)
    user = (data.get("data") or {}).get("user") or {}
    if not user:
        raise ValueError("TikTok did not return user profile data.")
    return user
