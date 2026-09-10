"""Snapchat Business OAuth 2.0 (Public Profile API). Tokens de cuenta, no pegar access token."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AUTH_URL = "https://accounts.snapchat.com/login/oauth2/authorize"
TOKEN_URL = "https://accounts.snapchat.com/login/oauth2/access_token"
API = "https://businessapi.snapchat.com"
ADS_API = "https://adsapi.snapchat.com"
PROFILE_URL = f"{API}/v1/public_profiles/my_profile"
ME_ORGS_URLS = (
    f"{API}/v1/me/organizations",
    f"{ADS_API}/v1/me/organizations",
)
# App Business (Content Management): perfil + orgs. Snap Kit: SNAPCHAT_PROFILE_ONLY=1
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
    """Business Manager: perfil público + orgs (hace falta para listar Kirth Melo).

    Las apps Snap Kit no aceptan marketing-api. En ese caso pon
    SNAPCHAT_PROFILE_ONLY=1 en el servidor.
    """
    raw = (os.environ.get("SNAPCHAT_SCOPES") or DEFAULT_SCOPES).strip()
    parts = [p for p in raw.replace(",", " ").split() if p]
    profile_only = (os.environ.get("SNAPCHAT_PROFILE_ONLY") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if profile_only:
        parts = [p for p in parts if p != "snapchat-marketing-api"]
    elif "snapchat-marketing-api" not in parts:
        parts.append("snapchat-marketing-api")
    if "snapchat-profile-api" not in parts:
        parts.insert(0, "snapchat-profile-api")
    return " ".join(parts)


def oauth_configured() -> bool:
    return bool(client_id() and client_secret() and redirect_uri())


def _debug(message: str) -> None:
    try:
        from db_engine import DATA_DIR

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with (DATA_DIR / "oauth_debug.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} [snapchat] {message}\n")
    except Exception:
        pass


def _shape(data: dict[str, Any]) -> str:
    keys = ",".join(sorted(str(k) for k in data.keys())[:20])
    status = str(data.get("request_status") or data.get("status") or "-")
    msg = str(data.get("display_message") or data.get("debug_message") or "")[:120]
    inner = data.get("public_profile")
    has = "si" if isinstance(inner, dict) and inner else "no"
    nlist = len(data.get("public_profiles") or []) if isinstance(data.get("public_profiles"), list) else 0
    return f"status={status} keys={keys} public_profile={has} profiles_n={nlist} msg={msg or '-'}"


def _state_secret() -> bytes:
    return (os.environ.get("SESSION_SECRET") or "dev-cambiar-en-produccion").encode(
        "utf-8"
    )


def sign_connect_state(
    *,
    user_id: str,
    link_name: str = "",
    redirect_uri_value: str = "",
) -> str:
    payload = {
        "u": (user_id or "").strip(),
        "a": (link_name or "").strip(),
        "r": (redirect_uri_value or "").strip(),
        "n": secrets.token_urlsafe(12),
        "t": int(time.time()),
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    sig = hmac.new(_state_secret(), raw.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{raw}.{sig}"


def read_connect_state(state: str) -> dict[str, str] | None:
    text = (state or "").strip()
    if "." not in text:
        return None
    raw, sig = text.rsplit(".", 1)
    expect = hmac.new(_state_secret(), raw.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expect):
        return None
    try:
        pad = "=" * (-len(raw) % 4)
        data = json.loads(base64.urlsafe_b64decode(raw + pad).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        ts = int(data.get("t") or 0)
    except (TypeError, ValueError):
        return None
    if ts <= 0 or abs(time.time() - ts) > 30 * 60:
        return None
    return {
        "user_id": str(data.get("u") or "").strip(),
        "link_name": str(data.get("a") or "").strip(),
        "redirect_uri": str(data.get("r") or "").strip(),
    }


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


def _unwrap(data: dict[str, Any]) -> dict[str, Any]:
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    return inner if isinstance(inner, dict) else data


def _profile_candidates(data: dict[str, Any]) -> list[dict[str, Any]]:
    data = _unwrap(data)
    out: list[dict[str, Any]] = []
    if not isinstance(data, dict):
        return out
    for key in ("public_profile", "profile"):
        inner = data.get(key)
        if isinstance(inner, dict):
            out.append(inner)
    items = data.get("public_profiles")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            inner = (
                item.get("public_profile")
                if isinstance(item.get("public_profile"), dict)
                else item
            )
            if isinstance(inner, dict):
                out.append(inner)
    return out


def _parse_any_profile(data: dict[str, Any]) -> dict[str, str] | None:
    for cand in _profile_candidates(data):
        parsed = _as_profile(cand)
        if parsed:
            return parsed
    return None


def _as_profile(profile: dict[str, Any]) -> dict[str, str] | None:
    if not isinstance(profile, dict):
        return None
    open_id = str(
        profile.get("id")
        or profile.get("profile_id")
        or profile.get("public_profile_id")
        or ""
    ).strip()
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
    data = _unwrap(data)
    out: list[str] = []
    rows = data.get("organizations")
    if not isinstance(rows, list):
        one = data.get("organization")
        rows = one if isinstance(one, list) else ([one] if isinstance(one, dict) else [])
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
    cid = (client_id() or "")[:8]
    _debug(f"fetch_profile client={cid}… scope={oauth_scopes()}")

    try:
        data = _unwrap(_request(PROFILE_URL, headers=headers))
        _debug(f"my_profile {_shape(data)}")
        if str(data.get("request_status") or "").upper() == "ERROR":
            raise ValueError(_api_error(data, "Snapchat profile request failed."))
        parsed = _parse_any_profile(data)
        if parsed:
            return parsed
        last_err = str(data.get("display_message") or data.get("debug_message") or "my_profile empty")
    except ValueError as e:
        last_err = str(e)
        _debug(f"my_profile error: {last_err[:180]}")

    for path in ME_ORGS_URLS:
        try:
            orgs = _unwrap(_request(path, headers=headers))
            _debug(f"{path.split('/')[-1]} {_shape(orgs)}")
            if str(orgs.get("request_status") or "").upper() == "ERROR":
                last_err = _api_error(orgs, last_err)
                continue
            org_ids = _org_ids(orgs)
            _debug(f"orgs n={len(org_ids)}")
            for org_id in org_ids:
                pdata = _unwrap(
                    _request(
                        f"{API}/v1/organizations/{urllib.parse.quote(org_id)}/public_profiles?limit=50",
                        headers=headers,
                    )
                )
                _debug(f"org {org_id[:8]}… {_shape(pdata)}")
                if str(pdata.get("request_status") or "").upper() == "ERROR":
                    last_err = _api_error(pdata, last_err)
                    continue
                parsed = _parse_any_profile(pdata)
                if parsed:
                    return parsed
        except ValueError as e:
            last_err = str(e)
            _debug(f"orgs error: {last_err[:180]}")

    low = (last_err or "").lower()
    if "permission" in low or "allowlist" in low or "not authorized" in low:
        raise ValueError("snapchat_need_allowlist")
    raise ValueError("snapchat_no_profile")
