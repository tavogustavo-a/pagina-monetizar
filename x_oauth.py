"""X (Twitter) OAuth 2.0 con PKCE. Tokens de cuenta, no pegar access token."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
ME_URL = "https://api.twitter.com/2/users/me"

DEFAULT_SCOPES = "tweet.read tweet.write users.read offline.access media.write"


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("x") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    return (os.environ.get("X_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    return (os.environ.get("X_CLIENT_SECRET") or "").strip() or _from_creds("client_secret")


def redirect_uri() -> str:
    env = (os.environ.get("X_REDIRECT_URI") or "").strip()
    if env:
        return env
    try:
        from site_config import SITE_URL

        return f"{SITE_URL}/oauth/x/callback"
    except Exception:
        return "http://127.0.0.1:8000/oauth/x/callback"


def oauth_scopes() -> str:
    return (os.environ.get("X_SCOPES") or DEFAULT_SCOPES).strip()


def oauth_configured() -> bool:
    return bool(client_id() and client_secret() and redirect_uri())


def new_csrf_state() -> str:
    return secrets.token_urlsafe(32)


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_authorize_url(*, state: str, code_challenge: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "scope": oauth_scopes(),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _api_error(data: dict[str, Any], fallback: str) -> str:
    if data.get("error_description"):
        return str(data.get("error_description"))[:220]
    if data.get("detail"):
        return str(data.get("detail"))[:220]
    if data.get("title"):
        return str(data.get("title"))[:220]
    errs = data.get("errors")
    if isinstance(errs, list) and errs:
        first = errs[0]
        if isinstance(first, dict):
            msg = str(first.get("message") or first.get("detail") or "").strip()
            if msg:
                return msg[:220]
        return str(first)[:220]
    err = data.get("error")
    if err:
        return str(err)[:220]
    return (fallback or "X API error")[:220]


def _basic_auth_header() -> str:
    raw = f"{client_id()}:{client_secret()}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": _basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
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
            raise ValueError(_api_error(parsed, raw or str(e))) from e
        raise ValueError((raw or str(e))[:220]) from e
    parsed = json.loads(raw) if raw else {}
    if isinstance(parsed, dict) and (parsed.get("error") or parsed.get("errors")):
        if not parsed.get("access_token"):
            raise ValueError(_api_error(parsed, raw))
    return parsed if isinstance(parsed, dict) else {}


def _get(url: str, access_token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {access_token}"},
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
            raise ValueError(_api_error(parsed, raw or str(e))) from e
        raise ValueError((raw or str(e))[:220]) from e
    parsed = json.loads(raw) if raw else {}
    if isinstance(parsed, dict) and parsed.get("errors") and not parsed.get("data"):
        raise ValueError(_api_error(parsed, raw))
    return parsed if isinstance(parsed, dict) else {}


def exchange_code_for_tokens(code: str, *, code_verifier: str) -> dict[str, Any]:
    data = _post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "code": (code or "").strip(),
            "redirect_uri": redirect_uri(),
            "code_verifier": (code_verifier or "").strip(),
            "client_id": client_id(),
        },
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "X did not return an access token."))
    return data


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    token = (refresh_token or "").strip()
    if not token:
        raise ValueError("X refresh token is missing.")
    data = _post_form(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": token,
            "client_id": client_id(),
        },
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "X token refresh failed."))
    return data


def fetch_profile(access_token: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"user.fields": "username,name"})
    data = _get(f"{ME_URL}?{params}", access_token)
    user = data.get("data") if isinstance(data.get("data"), dict) else {}
    user_id = str(user.get("id") or "").strip()
    if not user_id:
        raise ValueError("X did not return a user id.")
    username = str(user.get("username") or "").strip().lstrip("@") or None
    name = str(user.get("name") or "").strip() or None
    return {
        "open_id": user_id,
        "username": username,
        "display_name": name or (f"@{username}" if username else None),
    }
