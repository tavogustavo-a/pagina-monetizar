"""Bilibili Open Platform OAuth 2.0. Tokens de cuenta, no pegar access token."""
from __future__ import annotations

import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AUTH_URL = "https://account.bilibili.com/pc/account-pc/auth/oauth"
TOKEN_URL = "https://api.bilibili.com/x/account-oauth2/v1/token"
USER_URL = "https://member.bilibili.com/arcopen/fn/user/account/info"
UA = "CreatorHub/1.0 (Bilibili Open Platform)"


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("bilibili") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    return (os.environ.get("BILIBILI_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    return (
        (os.environ.get("BILIBILI_CLIENT_SECRET") or "").strip() or _from_creds("client_secret")
    )


def redirect_uri(request=None) -> str:
    from site_config import resolve_oauth_redirect

    return resolve_oauth_redirect(
        "bilibili", request, os.environ.get("BILIBILI_REDIRECT_URI") or ""
    )


def oauth_scopes() -> str:
    return (os.environ.get("BILIBILI_SCOPES") or "").strip()


def oauth_configured() -> bool:
    return bool(client_id() and client_secret() and redirect_uri())


def new_csrf_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(*, state: str, redirect_uri_value: str | None = None) -> str:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    params = {
        "client_id": client_id(),
        "gourl": ru,
        "state": state,
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _api_error(data: dict[str, Any], fallback: str) -> str:
    msg = str(data.get("message") or data.get("msg") or "").strip()
    if msg and msg not in {"0", "ok", "success"}:
        return msg[:220]
    err = data.get("error")
    if err:
        return str(err)[:220]
    return (fallback or "Bilibili API error")[:220]


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 45,
) -> dict[str, Any]:
    hdrs = {"User-Agent": UA, "Accept": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        parsed = {}
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
    if not isinstance(parsed, dict):
        return {}
    code = parsed.get("code")
    if code not in (None, 0, "0") and not parsed.get("access_token"):
        raise ValueError(_api_error(parsed, raw))
    return parsed


def expires_seconds(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    now = int(time.time())
    if n > 10**12:
        return max(60, n // 1000 - now)
    if n > 10**9:
        return max(60, n - now)
    return n if n > 0 else None


def _unwrap_token(data: dict[str, Any]) -> dict[str, Any]:
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    return inner if isinstance(inner, dict) else data


def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    q = urllib.parse.urlencode(
        {
            "client_id": client_id(),
            "client_secret": client_secret(),
            "grant_type": "authorization_code",
            "code": (code or "").strip(),
        }
    )
    data = _unwrap_token(_request(f"{TOKEN_URL}?{q}", method="POST", data=b""))
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Bilibili did not return an access token."))
    return data


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    token = (refresh_token or "").strip()
    if not token:
        raise ValueError("Bilibili refresh token is missing.")
    q = urllib.parse.urlencode(
        {
            "client_id": client_id(),
            "client_secret": client_secret(),
            "grant_type": "refresh_token",
            "refresh_token": token,
        }
    )
    data = _unwrap_token(_request(f"{TOKEN_URL}?{q}", method="POST", data=b""))
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Bilibili token refresh failed."))
    return data


def fetch_profile(access_token: str) -> dict[str, Any]:
    q = urllib.parse.urlencode(
        {"client_id": client_id(), "access_token": (access_token or "").strip()}
    )
    data = _unwrap_token(_request(f"{USER_URL}?{q}"))
    open_id = str(
        data.get("openid") or data.get("open_id") or data.get("mid") or data.get("uid") or ""
    ).strip()
    name = str(data.get("name") or data.get("uname") or data.get("username") or "").strip()
    if not open_id and not name:
        raise ValueError("Bilibili did not return account info.")
    return {
        "open_id": open_id or name,
        "username": name or open_id,
        "display_name": name or open_id,
    }
