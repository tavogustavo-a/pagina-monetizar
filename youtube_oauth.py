"""Google OAuth 2.0 para YouTube Data API v3 (conectar cuenta, no pegar tokens)."""
from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

DEFAULT_SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload "
    "https://www.googleapis.com/auth/youtube.readonly"
)


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("youtube") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    return (os.environ.get("YOUTUBE_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    return (os.environ.get("YOUTUBE_CLIENT_SECRET") or "").strip() or _from_creds("client_secret")


def redirect_uri(request=None) -> str:
    env = (os.environ.get("YOUTUBE_REDIRECT_URI") or "").strip()
    if env:
        return env
    try:
        from site_config import oauth_callback_url

        return oauth_callback_url("youtube", request)
    except Exception:
        return "http://127.0.0.1:8000/oauth/youtube/callback"


def oauth_scopes() -> str:
    return (os.environ.get("YOUTUBE_SCOPES") or DEFAULT_SCOPES).strip()


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
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)


def _google_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    desc = data.get("error_description") or ""
    if isinstance(err, dict):
        msg = str(err.get("message") or "").strip()
        if msg:
            return msg[:220]
    if err:
        return f"{err}: {desc}".strip(": ")[:220]
    return (fallback or "Google OAuth error")[:220]


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
        raw = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            raise ValueError(_google_error(parsed, raw or str(e))) from e
        raise ValueError((raw or str(e))[:220]) from e
    return json.loads(raw) if raw else {}


def exchange_code_for_tokens(code: str, redirect_uri_value: str | None = None) -> dict[str, Any]:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    data = _post_form(
        GOOGLE_TOKEN_URL,
        {
            "client_id": client_id(),
            "client_secret": client_secret(),
            "code": (code or "").strip(),
            "grant_type": "authorization_code",
            "redirect_uri": ru,
        },
    )
    if data.get("error") or not data.get("access_token"):
        raise ValueError(_google_error(data, "No access token in Google response."))
    return data


def refresh_access_token(
    refresh_token: str,
    *,
    client_id_value: str | None = None,
    client_secret_value: str | None = None,
) -> dict[str, Any]:
    payload = {
        "client_id": (client_id_value or "").strip() or client_id(),
        "client_secret": (client_secret_value or "").strip() or client_secret(),
        "refresh_token": (refresh_token or "").strip(),
        "grant_type": "refresh_token",
    }
    if not payload["client_id"] or not payload["client_secret"] or not payload["refresh_token"]:
        raise ValueError("YouTube refresh token is missing credentials.")
    data = _post_form(GOOGLE_TOKEN_URL, payload)
    if data.get("error") or not data.get("access_token"):
        raise ValueError(_google_error(data, "YouTube refresh failed."))
    return data


def revoke_tokens(access_token: str, refresh_token: str | None = None) -> None:
    """Revoca el grant en Google (mejor esfuerzo). Revocar el refresh anula todo."""
    token = (refresh_token or "").strip() or (access_token or "").strip()
    if not token:
        return
    try:
        _post_form("https://oauth2.googleapis.com/revoke", {"token": token})
    except (ValueError, urllib.error.URLError, OSError, json.JSONDecodeError):
        return


def fetch_channel_profile(access_token: str) -> dict[str, Any]:
    url = YOUTUBE_CHANNELS_URL + "?" + urllib.parse.urlencode(
        {"part": "snippet", "mine": "true"}
    )
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}
        raise ValueError(_google_error(parsed if isinstance(parsed, dict) else {}, body)) from e
    data = json.loads(raw) if raw else {}
    items = data.get("items") if isinstance(data, dict) else None
    if not items:
        raise ValueError("YouTube did not return a channel for this Google account.")
    ch = items[0] if isinstance(items[0], dict) else {}
    snippet = ch.get("snippet") if isinstance(ch.get("snippet"), dict) else {}
    custom = str(snippet.get("customUrl") or "").strip().lstrip("@")
    title = str(snippet.get("title") or "").strip()
    return {
        "open_id": str(ch.get("id") or "").strip(),
        "username": custom or None,
        "display_name": title or custom or None,
    }
