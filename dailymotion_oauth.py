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


def redirect_uri(request=None) -> str:
    from site_config import resolve_oauth_redirect

    return resolve_oauth_redirect(
        "dailymotion", request, os.environ.get("DAILYMOTION_REDIRECT_URI") or ""
    )


def oauth_scopes() -> str:
    return (os.environ.get("DAILYMOTION_SCOPES") or DEFAULT_SCOPES).strip()


def oauth_configured() -> bool:
    return bool(client_id() and client_secret() and redirect_uri())


def new_csrf_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(*, state: str, redirect_uri_value: str | None = None) -> str:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    params = {
        "response_type": "code",
        "client_id": client_id(),
        "redirect_uri": ru,
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


def exchange_code_for_tokens(code: str, redirect_uri_value: str | None = None) -> dict[str, Any]:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    data = _post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "redirect_uri": ru,
            "code": (code or "").strip(),
        },
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Dailymotion did not return an access token."))
    return data


def exchange_client_credentials() -> dict[str, Any]:
    """Token v2 de la clave privada de Studio (client_credentials). No usa /me."""
    cid = client_id()
    secret = client_secret()
    if not cid or not secret:
        raise ValueError("missing_keys")
    last_error = "Dailymotion client credentials failed."
    scopes = (
        "account.read video.manage",
        "video.manage account.read",
        "account.read video.manage bundle.organization",
        "video.manage",
        "bundle.organization",
        "bundle.publisher",
        "video.manage bundle.organization",
    )
    endpoints = (
        "https://oauth2.dailymotion.com/v2/token",
        "https://partner.api.dailymotion.com/oauth/v1/token",
    )
    for url in endpoints:
        for scope in scopes:
            fields = {
                "grant_type": "client_credentials",
                "client_id": cid,
                "client_secret": secret,
                "scope": scope,
            }
            try:
                data = _post_form(url, fields)
            except ValueError as e:
                last_error = str(e)
                continue
            if data.get("access_token"):
                data["scope"] = str(data.get("scope") or scope)
                return data
            last_error = _api_error(data, last_error)
    raise ValueError(last_error)


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


def revoke_tokens(access_token: str, refresh_token: str | None = None) -> None:
    """Revoca la sesión en Dailymotion (mejor esfuerzo)."""
    token = (access_token or "").strip()
    if not token:
        return
    try:
        _request(
            "https://api.dailymotion.com/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
    except (ValueError, urllib.error.URLError, OSError):
        return


def fetch_profile(access_token: str) -> dict[str, Any]:
    token = (access_token or "").strip()
    profiles = list_v2_profiles(token)
    if profiles:
        return profiles[0]
    params = urllib.parse.urlencode({"fields": "id,screenname,username", "access_token": token})
    data = _request(f"https://api.dailymotion.com/me?{params}")
    user_id = str(data.get("id") or "").strip()
    if not user_id:
        raise ValueError("missing_profile")
    uname = str(data.get("username") or data.get("screenname") or "").strip() or user_id
    return {"open_id": user_id, "username": uname, "display_name": uname}


def _profiles_from_payload(data: Any) -> list[dict[str, Any]]:
    rows: list[Any] = []
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("items") or data.get("data") or data.get("list") or data.get("profiles") or []
        if not rows and (data.get("profile_id") or data.get("id")):
            rows = [data]
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("profile_id") or row.get("id") or "").strip()
        if not pid or pid in seen or pid.lower() == "me":
            continue
        seen.add(pid)
        name = str(row.get("name") or row.get("username") or row.get("screenname") or pid).strip()
        out.append({"open_id": pid, "username": name, "display_name": name})
    return out


def list_v2_profiles(access_token: str) -> list[dict[str, Any]]:
    token = (access_token or "").strip()
    if not token:
        return []
    paths = (
        "/me",
        "/profiles",
        "https://partner.api.dailymotion.com/v2/me",
        "https://partner.api.dailymotion.com/v2/profiles",
    )
    for path in paths:
        try:
            data = bearer_get(path, token)
        except ValueError:
            continue
        found = _profiles_from_payload(data)
        if found:
            return found
    return []


def configured_profile_id() -> str:
    env = (
        (os.environ.get("DAILYMOTION_PROFILE_ID") or "").strip()
        or (os.environ.get("DAILYMOTION_USER_ID") or "").strip()
    )
    if env:
        return env
    raw = _from_creds("extra")
    if raw and not raw.lower().startswith("http"):
        return raw
    return ""


def profile_or_key_fallback(access_token: str) -> dict[str, Any]:
    try:
        return fetch_profile(access_token)
    except ValueError:
        pid = configured_profile_id()
        if pid:
            return {"open_id": pid, "username": pid, "display_name": pid}
        cid = client_id() or "dailymotion"
        return {
            "open_id": f"key:{cid}",
            "username": "studio",
            "display_name": "Dailymotion",
        }
