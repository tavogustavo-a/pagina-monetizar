"""Business Login for Instagram (OAuth). Tokens de cuenta, no pegar access token."""
from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AUTH_URL = "https://www.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
LONG_LIVED_URL = "https://graph.instagram.com/access_token"
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"
GRAPH_ME = "https://graph.instagram.com/v21.0/me"

DEFAULT_SCOPES = (
    "instagram_business_basic,"
    "instagram_business_content_publish"
)


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("instagram") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    return (os.environ.get("INSTAGRAM_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    return (
        (os.environ.get("INSTAGRAM_CLIENT_SECRET") or "").strip() or _from_creds("client_secret")
    )


def redirect_uri(request=None) -> str:
    env = (os.environ.get("INSTAGRAM_REDIRECT_URI") or "").strip()
    if env:
        return env
    try:
        from site_config import oauth_callback_url

        return oauth_callback_url("instagram", request)
    except Exception:
        return "http://127.0.0.1:8000/oauth/instagram/callback"


def oauth_scopes() -> str:
    return (os.environ.get("INSTAGRAM_SCOPES") or DEFAULT_SCOPES).strip()


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
        "force_reauth": "true",
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _graph_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        msg = str(err.get("message") or err.get("error_user_msg") or "").strip()
        if msg:
            return msg[:220]
    desc = str(data.get("error_message") or data.get("error_description") or "").strip()
    if err or desc:
        return f"{err}: {desc}".strip(": ")[:220]
    return (fallback or "Instagram OAuth error")[:220]


def _read_http_error(exc: urllib.error.HTTPError) -> dict[str, Any]:
    raw = exc.read().decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw) if raw else {}
        return parsed if isinstance(parsed, dict) else {"error": raw[:220]}
    except json.JSONDecodeError:
        return {"error": raw[:220] or str(exc)}


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        parsed = _read_http_error(e)
        raise ValueError(_graph_error(parsed, str(e))) from e
    return json.loads(raw) if raw else {}


def _post_json(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        parsed = _read_http_error(e)
        raise ValueError(_graph_error(parsed, str(e))) from e
    return json.loads(raw) if raw else {}


def _get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        parsed = _read_http_error(e)
        raise ValueError(_graph_error(parsed, str(e))) from e
    return json.loads(raw) if raw else {}


def revoke_tokens(access_token: str, refresh_token: str | None = None) -> None:
    """Intenta revocar la autorización en Instagram (mejor esfuerzo, sin garantía)."""
    token = (access_token or "").strip()
    if not token:
        return
    params = urllib.parse.urlencode({"access_token": token})
    req = urllib.request.Request(
        f"https://graph.instagram.com/v21.0/me/permissions?{params}",
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=30):
            return
    except (urllib.error.URLError, OSError, ValueError):
        return


def _unwrap_token_payload(data: dict[str, Any]) -> dict[str, Any]:
    inner = data.get("data")
    if isinstance(inner, list) and inner and isinstance(inner[0], dict):
        merged = dict(data)
        merged.update(inner[0])
        return merged
    if isinstance(inner, dict):
        merged = dict(data)
        merged.update(inner)
        return merged
    return data


def exchange_code_for_tokens(code: str, redirect_uri_value: str | None = None) -> dict[str, Any]:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    payload = {
        "client_id": client_id(),
        "client_secret": client_secret(),
        "grant_type": "authorization_code",
        "redirect_uri": ru,
        "code": (code or "").strip().split("#", 1)[0],
    }
    try:
        data = _unwrap_token_payload(_post_form(TOKEN_URL, payload))
    except ValueError:
        data = _unwrap_token_payload(_post_json(TOKEN_URL, payload))
    if not data.get("access_token"):
        raise ValueError(_graph_error(data, "Instagram did not return an access token."))
    return data


def exchange_long_lived(short_lived_token: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "grant_type": "ig_exchange_token",
            "client_secret": client_secret(),
            "access_token": (short_lived_token or "").strip(),
        }
    )
    data = _get(f"{LONG_LIVED_URL}?{params}")
    if not data.get("access_token"):
        raise ValueError(_graph_error(data, "Could not exchange Instagram long-lived token."))
    return data


def refresh_access_token(long_lived_token: str) -> dict[str, Any]:
    token = (long_lived_token or "").strip()
    if not token:
        raise ValueError("Instagram refresh token is missing.")
    params = urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": token}
    )
    data = _get(f"{REFRESH_URL}?{params}")
    if not data.get("access_token"):
        raise ValueError(_graph_error(data, "Instagram token refresh failed."))
    return data


def fetch_profile(access_token: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "fields": "user_id,id,username,name,account_type",
            "access_token": (access_token or "").strip(),
        }
    )
    data = _get(f"{GRAPH_ME}?{params}")
    if data.get("error"):
        raise ValueError(_graph_error(data, "Instagram profile failed."))
    user_id = str(data.get("user_id") or data.get("id") or "").strip()
    if not user_id:
        raise ValueError("Instagram did not return a user id.")
    username = str(data.get("username") or "").strip().lstrip("@") or None
    name = str(data.get("name") or "").strip() or None
    return {
        "open_id": user_id,
        "username": username,
        "display_name": name or (f"@{username}" if username else None),
        "account_type": str(data.get("account_type") or "").strip(),
    }
