"""Dailymotion OAuth 2.0. Tokens de cuenta, no pegar access token."""
from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AUTH_URL = "https://www.dailymotion.com/oauth/authorize"
TOKEN_URL = "https://api.dailymotion.com/oauth/token"
V2 = "https://api.dailymotion.com/v2"

DEFAULT_SCOPES = "video.manage manage_videos userinfo email"


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("dailymotion") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    return (os.environ.get("DAILYMOTION_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    return (
        (os.environ.get("DAILYMOTION_CLIENT_SECRET") or "").strip() or _from_creds("client_secret")
    )


def redirect_uri() -> str:
    env = (os.environ.get("DAILYMOTION_REDIRECT_URI") or "").strip()
    if env:
        return env
    try:
        from site_config import SITE_URL

        return f"{SITE_URL}/oauth/dailymotion/callback"
    except Exception:
        return "http://127.0.0.1:8000/oauth/dailymotion/callback"


def oauth_scopes() -> str:
    return (os.environ.get("DAILYMOTION_SCOPES") or DEFAULT_SCOPES).strip()


def oauth_configured() -> bool:
    return bool(client_id() and client_secret() and redirect_uri())


def new_csrf_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(*, state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "scope": oauth_scopes(),
        "state": state,
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _api_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        msg = str(err.get("message") or err.get("error_user_msg") or "").strip()
        if msg:
            return msg[:220]
    desc = str(data.get("error_description") or data.get("error_message") or "").strip()
    if err or desc:
        return f"{err}: {desc}".strip(": ")[:220]
    return (fallback or "Dailymotion API error")[:220]


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
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
            raise ValueError(_api_error(parsed, raw or str(e))) from e
        raise ValueError((raw or str(e))[:220]) from e
    parsed = json.loads(raw) if raw else {}
    if isinstance(parsed, dict) and parsed.get("error") and not parsed.get("access_token"):
        raise ValueError(_api_error(parsed, raw))
    return parsed if isinstance(parsed, dict) else {}


def _post_form(url: str, fields: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(fields).encode("utf-8")
    return _request(
        url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def bearer_get(path: str, access_token: str) -> dict[str, Any]:
    return _request(
        path if path.startswith("http") else f"{V2}{path}",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )


def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    data = _post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "redirect_uri": redirect_uri(),
            "code": (code or "").strip(),
        },
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Dailymotion did not return an access token."))
    return data


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    token = (refresh_token or "").strip()
    if not token:
        raise ValueError("Dailymotion refresh token is missing.")
    data = _post_form(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "refresh_token": token,
        },
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Dailymotion token refresh failed."))
    return data


def fetch_profile(access_token: str) -> dict[str, Any]:
    token = (access_token or "").strip()
    try:
        data = bearer_get("/profiles", token)
        items = data.get("items") or data.get("data") or data.get("list") or []
        if isinstance(items, list) and items and isinstance(items[0], dict):
            row = items[0]
            pid = str(row.get("id") or "").strip()
            if pid:
                name = str(row.get("name") or row.get("username") or "").strip()
                return {
                    "open_id": pid,
                    "username": name or pid,
                    "display_name": name or pid,
                }
    except ValueError:
        pass
    params = urllib.parse.urlencode({"fields": "id,screenname,username", "access_token": token})
    data = _request(f"https://api.dailymotion.com/me?{params}")
    user_id = str(data.get("id") or "").strip()
    if not user_id:
        raise ValueError("Dailymotion did not return a user id.")
    uname = str(data.get("username") or data.get("screenname") or "").strip() or user_id
    return {"open_id": user_id, "username": uname, "display_name": uname}
