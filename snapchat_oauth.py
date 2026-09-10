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
API = "https://businessapi.snapchat.com"
PROFILE_URL = f"{API}/v1/public_profiles/my_profile"
ME_ORGS_URL = f"{API}/v1/me/organizations"
DEFAULT_SCOPES = "snapchat-profile-api snapchat-marketing-api"


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("snapchat") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    try:
        import db

        return db.cred_value(
            "snapchat", "client_id", os.environ.get("SNAPCHAT_CLIENT_ID") or ""
        )
    except Exception:
        return (os.environ.get("SNAPCHAT_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    try:
        import db

        return db.cred_value(
            "snapchat",
            "client_secret",
            os.environ.get("SNAPCHAT_CLIENT_SECRET") or "",
        )
    except Exception:
        return (
            (os.environ.get("SNAPCHAT_CLIENT_SECRET") or "").strip()
            or _from_creds("client_secret")
        )


def redirect_uri(request=None) -> str:
    from site_config import resolve_oauth_redirect

    return resolve_oauth_redirect(
        "snapchat", request, os.environ.get("SNAPCHAT_REDIRECT_URI") or ""
    )


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
    hdrs = {
        "Accept": "application/json",
        "User-Agent": "Tuyaho/1.0 (Snapchat OAuth)",
        **(headers or {}),
    }
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


def _token_payload(data: dict[str, Any]) -> dict[str, Any]:
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    return inner if isinstance(inner, dict) else data


def exchange_code_for_tokens(
    code: str, *, redirect_uri_value: str | None = None
) -> dict[str, Any]:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    data = _token_payload(
        _form_post(
            TOKEN_URL,
            {
                "grant_type": "authorization_code",
                "client_id": client_id(),
                "client_secret": client_secret(),
                "code": (code or "").strip(),
                "redirect_uri": ru,
            },
        )
    )
    if not data.get("access_token"):
        raise ValueError(_api_error(data, "Snapchat did not return an access token."))
    return data


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    token = (refresh_token or "").strip()
    if not token:
        raise ValueError("Snapchat refresh token is missing.")
    data = _token_payload(
        _form_post(
            TOKEN_URL,
            {
                "grant_type": "refresh_token",
                "client_id": client_id(),
                "client_secret": client_secret(),
                "refresh_token": token,
            },
        )
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


def _first_profile_dict(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    for key in ("public_profile", "profile", "me"):
        inner = data.get(key)
        if isinstance(inner, dict) and (
            inner.get("id") or inner.get("profile_id") or inner.get("display_name")
        ):
            return inner
    items = data.get("public_profiles")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            inner = item.get("public_profile") if isinstance(item.get("public_profile"), dict) else item
            if isinstance(inner, dict) and (inner.get("id") or inner.get("profile_id")):
                return inner
    return data if data.get("id") or data.get("profile_id") else {}


def _as_profile(profile: dict[str, Any]) -> dict[str, str] | None:
    if not isinstance(profile, dict):
        return None
    open_id = str(profile.get("id") or profile.get("profile_id") or "").strip()
    if not open_id:
        return None
    name = str(
        profile.get("display_name")
        or profile.get("name")
        or profile.get("snap_user_name")
        or ""
    ).strip()
    username = str(profile.get("snap_user_name") or profile.get("username") or name).strip()
    return {
        "open_id": open_id,
        "username": username or open_id,
        "display_name": name or username or open_id,
    }


def _org_ids(data: dict[str, Any]) -> list[str]:
    out: list[str] = []
    rows = data.get("organizations")
    if not isinstance(rows, list):
        rows = data.get("organization") if isinstance(data.get("organization"), list) else []
    for item in rows:
        if not isinstance(item, dict):
            continue
        org = item.get("organization") if isinstance(item.get("organization"), dict) else item
        oid = str((org or {}).get("id") or "").strip()
        if oid:
            out.append(oid)
    return out


def fetch_profile(access_token: str) -> dict[str, Any]:
    token = (access_token or "").strip()
    if not token:
        raise ValueError("missing_token")
    headers = {"Authorization": f"Bearer {token}"}
    last_err = ""

    try:
        data = _request(PROFILE_URL, headers=headers)
        if str(data.get("request_status") or "").upper() == "ERROR":
            raise ValueError(_api_error(data, "Snapchat profile request failed."))
        parsed = _as_profile(_first_profile_dict(data))
        if parsed:
            return parsed
        last_err = "my_profile empty"
    except ValueError as e:
        last_err = str(e)

    try:
        orgs = _request(ME_ORGS_URL, headers=headers)
        if str(orgs.get("request_status") or "").upper() == "ERROR":
            raise ValueError(_api_error(orgs, last_err or "Snapchat organizations failed."))
        for org_id in _org_ids(orgs):
            pdata = _request(
                f"{API}/v1/organizations/{urllib.parse.quote(org_id)}/public_profiles?limit=50",
                headers=headers,
            )
            if str(pdata.get("request_status") or "").upper() == "ERROR":
                last_err = _api_error(pdata, last_err)
                continue
            parsed = _as_profile(_first_profile_dict(pdata))
            if parsed:
                return parsed
    except ValueError as e:
        last_err = str(e)

    low = (last_err or "").lower()
    if "permission" in low or "allowlist" in low or "not authorized" in low:
        raise ValueError("snapchat_need_allowlist")
    raise ValueError("snapchat_no_profile")
