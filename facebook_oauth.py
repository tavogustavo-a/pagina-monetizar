"""Facebook Login (OAuth) para Páginas. Tokens de página, no pegar access token."""
from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

GRAPH = "https://graph.facebook.com/v21.0"
AUTH_URL = "https://www.facebook.com/v21.0/dialog/oauth"
TOKEN_URL = f"{GRAPH}/oauth/access_token"

DEFAULT_SCOPES = "pages_show_list,pages_manage_posts"


def _from_creds(key: str) -> str:
    try:
        import db

        raw = db.get_platform_credentials_raw("facebook") or {}
        return str(raw.get(key) or "").strip()
    except Exception:
        return ""


def client_id() -> str:
    return (os.environ.get("FACEBOOK_CLIENT_ID") or "").strip() or _from_creds("client_id")


def client_secret() -> str:
    return (
        (os.environ.get("FACEBOOK_CLIENT_SECRET") or "").strip() or _from_creds("client_secret")
    )


def redirect_uri(request=None) -> str:
    env = (os.environ.get("FACEBOOK_REDIRECT_URI") or "").strip()
    if env:
        return env
    try:
        from site_config import oauth_callback_url

        return oauth_callback_url("facebook", request)
    except Exception:
        return "http://127.0.0.1:8000/oauth/facebook/callback"


def oauth_scopes() -> str:
    return (os.environ.get("FACEBOOK_SCOPES") or DEFAULT_SCOPES).strip()


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
        "auth_type": "rerequest",
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _graph_error(data: dict[str, Any], fallback: str) -> str:
    err = data.get("error")
    if isinstance(err, dict):
        msg = str(err.get("message") or err.get("error_user_msg") or "").strip()
        if msg:
            return msg[:220]
    desc = str(data.get("error_description") or "").strip()
    if err or desc:
        return f"{err}: {desc}".strip(": ")[:220]
    return (fallback or "Facebook OAuth error")[:220]


def _get(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
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
            raise ValueError(_graph_error(parsed, raw or str(e))) from e
        raise ValueError((raw or str(e))[:220]) from e
    data = json.loads(raw) if raw else {}
    if isinstance(data, dict) and data.get("error"):
        raise ValueError(_graph_error(data, raw))
    return data if isinstance(data, dict) else {}


def exchange_code_for_tokens(code: str, redirect_uri_value: str | None = None) -> dict[str, Any]:
    ru = (redirect_uri_value or "").strip() or redirect_uri()
    params = urllib.parse.urlencode(
        {
            "client_id": client_id(),
            "client_secret": client_secret(),
            "redirect_uri": ru,
            "code": (code or "").strip().split("#", 1)[0],
        }
    )
    data = _get(f"{TOKEN_URL}?{params}")
    if not data.get("access_token"):
        raise ValueError(_graph_error(data, "Facebook did not return an access token."))
    return data


def exchange_long_lived(short_lived_token: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "grant_type": "fb_exchange_token",
            "client_id": client_id(),
            "client_secret": client_secret(),
            "fb_exchange_token": (short_lived_token or "").strip(),
        }
    )
    data = _get(f"{TOKEN_URL}?{params}")
    if not data.get("access_token"):
        raise ValueError(_graph_error(data, "Could not exchange Facebook long-lived token."))
    return data


def list_pages(user_token: str) -> list[dict[str, str]]:
    params = urllib.parse.urlencode(
        {
            "fields": "id,name,access_token,tasks",
            "limit": "100",
            "access_token": (user_token or "").strip(),
        }
    )
    data = _get(f"{GRAPH}/me/accounts?{params}")
    items = data.get("data") if isinstance(data.get("data"), list) else []
    out: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        page_id = str(item.get("id") or "").strip()
        token = str(item.get("access_token") or "").strip()
        if not page_id or not token:
            continue
        tasks = item.get("tasks") if isinstance(item.get("tasks"), list) else []
        if tasks:
            allowed = {str(t).upper() for t in tasks}
            if not allowed.intersection({"CREATE_CONTENT", "MANAGE", "MODERATE"}):
                continue
        name = str(item.get("name") or "").strip() or page_id
        out.append(
            {
                "open_id": page_id,
                "username": page_id,
                "display_name": name,
                "access_token": token,
            }
        )
    return out


def fetch_page_profile(page_token: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "fields": "id,name",
            "access_token": (page_token or "").strip(),
        }
    )
    data = _get(f"{GRAPH}/me?{params}")
    page_id = str(data.get("id") or "").strip()
    if not page_id:
        raise ValueError("Facebook did not return a Page id.")
    name = str(data.get("name") or "").strip() or page_id
    return {"open_id": page_id, "username": page_id, "display_name": name}
