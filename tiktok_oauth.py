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
TIKTOK_REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"
TIKTOK_USERINFO_URL = "https://open.tiktokapis.com/v2/user/info/"

# Primera revisión: Login Kit + subida a bandeja. video.publish (Direct Post) va en una 2ª revisión.
DEFAULT_SCOPES = "user.info.basic,video.upload"


def client_key() -> str:
    env = (os.environ.get("TIKTOK_CLIENT_KEY") or os.environ.get("TIKTOK_CLIENT_ID") or "").strip()
    try:
        import db

        return db.cred_value("tiktok", "client_id", env)
    except Exception:
        if env:
            return env
        return ""


def client_secret() -> str:
    env = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
    try:
        import db

        return db.cred_value("tiktok", "client_secret", env)
    except Exception:
        return env


def redirect_uri(request=None) -> str:
    from site_config import resolve_oauth_redirect

    return resolve_oauth_redirect("tiktok", request, os.environ.get("TIKTOK_REDIRECT_URI") or "")


def oauth_scopes() -> str:
    return (os.environ.get("TIKTOK_SCOPES") or DEFAULT_SCOPES).strip()


def oauth_configured() -> bool:
    return bool(client_key() and client_secret() and redirect_uri())


def new_csrf_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(*, state: str, redirect_uri_value: str | None = None) -> str:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    params = {
        "client_key": client_key(),
        "scope": oauth_scopes(),
        "response_type": "code",
        "redirect_uri": ru,
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


def exchange_code_for_tokens(code: str, redirect_uri_value: str | None = None) -> dict[str, Any]:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    payload = {
        "client_key": client_key(),
        "client_secret": client_secret(),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": ru,
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


def revoke_access_token(token: str) -> None:
    """Revoca el token en TikTok (Login Kit). Si falla, el caller igual puede borrar en local."""
    tok = (token or "").strip()
    if not tok:
        return
    payload = {
        "client_key": client_key(),
        "client_secret": client_secret(),
        "token": tok,
    }
    if not payload["client_key"] or not payload["client_secret"]:
        return
    try:
        _post_form(TIKTOK_REVOKE_URL, payload)
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return
