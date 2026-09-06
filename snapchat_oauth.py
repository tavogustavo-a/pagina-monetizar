"""Snapchat Business OAuth 2.0 (Public Profile API). Tokens de cuenta, no pegar access token."""
from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AUTH_URL = "https://accounts.snapchat.com/login/oauth2/authorize"
TOKEN_URL = "https://accounts.snapchat.com/login/oauth2/access_token"
PROFILE_URL = "https://businessapi.snapchat.com/v1/public_profiles/my_profile"
DEFAULT_SCOPES = "snapchat-profile-api"


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("snapchat") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    return (os.environ.get("SNAPCHAT_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    return (
        (os.environ.get("SNAPCHAT_CLIENT_SECRET") or "").strip() or _from_creds("client_secret")
    )


def redirect_uri(request=None) -> str:
    env = (os.environ.get("SNAPCHAT_REDIRECT_URI") or "").strip()
    if env:
        return env
    try:
        from site_config import oauth_callback_url

        return oauth_callback_url("snapchat", request)
    except Exception:
        return "http://127.0.0.1:8000/oauth/snapchat/callback"


def oauth_scopes() -> str:
    return (os.environ.get("SNAPCHAT_SCOPES") or DEFAULT_SCOPES).strip()


def oauth_configured() -> bool:
    return bool(client_id() and client_secret() and redirect_uri())


def new_csrf_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(*, state: str, redirect_uri_value: str | None = None) -> str:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    params = {
        "client_id": client_id(),
        "redirect_uri": ru,
        "response_type": "code",
        "scope": oauth_scopes(),
        "state": state,
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _api_error(data: dict[str, Any], fallback: str) -> str:
    msg = str(
        data.get("display_message")
        or data.get("debug_message")
        or data.get("error_description")
        or data.get("error")
        or data.get("error_code")
        or ""
    ).strip()
    if isinstance(data.get("error"), dict):
        inner = data["error"]
        msg = str(inner.get("message") or inner.get("error_description") or msg).strip()
    return (msg or fallback or "Snapchat API error")[:220]


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 45,
) -> dict[str, Any]:
    hdrs = {"Accept": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        parsed: dict[str, Any] = {}
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            raise ValueError(_api_error(parsed, raw or str(e))) from e
        raise ValueError((raw or str(e))[:220]) from e
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _form_post(url: str, fields: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(fields).encode("utf-8")
    return _request(
        url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def exchange_code_for_tokens(
    code: str, *, redirect_uri_value: str | None = None
) -> dict[str, Any]:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    data = _form_post(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "code": (code or "").strip(),
            "redirect_uri": ru,
        },
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Snapchat did not return an access token."))
    return data


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    token = (refresh_token or "").strip()
    if not token:
        raise ValueError("Snapchat refresh token is missing.")
    data = _form_post(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "refresh_token": token,
        },
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Snapchat token refresh failed."))
    return data


REVOKE_URL = "https://accounts.snapchat.com/accounts/oauth2/revoke"


def revoke_tokens(access_token: str, refresh_token: str | None = None) -> None:
    """Revoca los tokens en Snapchat (mejor esfuerzo)."""
    for token in ((refresh_token or "").strip(), (access_token or "").strip()):
        if not token:
            continue
        try:
            _form_post(
                REVOKE_URL,
                {
                    "client_id": client_id(),
                    "client_secret": client_secret(),
                    "token": token,
                },
            )
            return
        except (ValueError, urllib.error.URLError, OSError):
            continue


def _unwrap_profile(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("public_profile", "profile", "me"):
        inner = data.get(key)
        if isinstance(inner, dict) and (inner.get("id") or inner.get("display_name")):
            return inner
    return data


def fetch_profile(access_token: str) -> dict[str, Any]:
    data = _request(
        PROFILE_URL,
        headers={"Authorization": f"Bearer {(access_token or '').strip()}"},
    )
    if str(data.get("request_status") or "").upper() == "ERROR":
        raise ValueError(_api_error(data, "Snapchat profile request failed."))
    profile = _unwrap_profile(data)
    open_id = str(profile.get("id") or data.get("id") or "").strip()
    name = str(
        profile.get("display_name")
        or profile.get("name")
        or profile.get("snap_user_name")
        or ""
    ).strip()
    username = str(profile.get("snap_user_name") or profile.get("username") or name).strip()
    if not open_id:
        raise ValueError(
            "Snapchat did not return a public profile. Create one in Snap Business Manager."
        )
    return {
        "open_id": open_id,
        "username": username or open_id,
        "display_name": name or username or open_id,
    }
