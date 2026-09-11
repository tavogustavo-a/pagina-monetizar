"""Odysee: login LBRY (email/contraseña → auth_token) y publicación real por TUS + asynqueries."""
from __future__ import annotations

import base64
import hashlib
import http.cookiejar
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

UA = "Tuyaho/1.0 (Odysee LBRY publish)"
INTERNAL = "https://api.odysee.com"
SDK = "https://api.na-backend.odysee.com"
BROWSER_HEADERS = {
    "Origin": "https://odysee.com",
    "Referer": "https://odysee.com/",
    "Accept": "application/json",
}
_TLS = threading.local()
VIDEO_EXT = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".m4v"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TUS_CHUNK = 50 * 1024 * 1024
FILE_PATH_RE = re.compile(r"^https?://([^/]+)/.+/([a-zA-Z0-9+_.\-]{32,})$")
CLAIM_ID_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class OdyseeError(ValueError):
    pass


def _parse(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_error(exc: urllib.error.HTTPError) -> str:
    raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
    data = _parse(raw)
    msg = str(
        data.get("error")
        or data.get("message")
        or (data.get("data") if isinstance(data.get("data"), str) else "")
        or raw
        or exc.reason
        or f"HTTP {exc.code}"
    ).strip()
    return msg[:280]


def _flatten_error(err: Any) -> str:
    if err is None or err is False:
        return ""
    if isinstance(err, dict):
        parts = []
        for key, val in err.items():
            if val in (None, "", False):
                continue
            parts.append(f"{key}: {val}")
        return "; ".join(parts)[:280]
    text = str(err).strip()
    return text[:280]


def _debug(message: str) -> None:
    try:
        from datetime import datetime, timezone

        from db_engine import DATA_DIR

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with (DATA_DIR / "oauth_debug.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} [odysee] {message}\n")
    except Exception:
        pass


def _opener() -> urllib.request.OpenerDirector:
    op = getattr(_TLS, "opener", None)
    if op is None:
        op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        _TLS.opener = op
    return op


def _reset_http_session() -> None:
    _TLS.opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )


def _request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> tuple[int, dict[str, str], bytes]:
    hdrs = {"User-Agent": UA}
    hdrs.update(BROWSER_HEADERS)
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with _opener().open(req, timeout=timeout) as resp:
            body = resp.read()
            return int(resp.status), {k.lower(): v for k, v in resp.headers.items()}, body
    except urllib.error.HTTPError as e:
        raw = e.read() if e.fp else b""
        return int(e.code), {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}, raw


def _form(url: str, fields: dict[str, str], *, headers: dict[str, str] | None = None) -> dict[str, Any]:
    payload = urllib.parse.urlencode({k: v for k, v in fields.items() if v is not None}).encode()
    hdrs = {"Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        hdrs.update(headers)
    code, _, body = _request(url, method="POST", data=payload, headers=hdrs, timeout=45)
    raw = body.decode("utf-8", errors="replace")
    data = _parse(raw)
    if code >= 400 and not data:
        raise OdyseeError(f"HTTP {code}")
    if code == 417:
        raise OdyseeError("2fa_required")
    if code == 409:
        msg = (
            _flatten_error(data.get("error"))
            or _flatten_error(data.get("message"))
            or raw[:180]
            or "HTTP 409"
        )
        low = msg.lower()
        if "verif" in low or "unverified" in low or "confirm" in low:
            raise OdyseeError("email_unverified")
        raise OdyseeError(msg)
    if code >= 400:
        msg = (
            _flatten_error(data.get("error"))
            or _flatten_error(data.get("message"))
            or f"HTTP {code}"
        )
        raise OdyseeError(msg)
    return data


def _json(
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    method: str = "POST",
    headers: dict[str, str] | None = None,
    timeout: int = 90,
) -> tuple[int, dict[str, Any], bytes]:
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    raw = json.dumps(payload).encode("utf-8") if payload is not None else None
    code, _, body = _request(url, method=method, data=raw, headers=hdrs, timeout=timeout)
    return code, _parse(body.decode("utf-8", errors="replace")), body


def status_ok() -> tuple[bool, str]:
    code, data, body = _json(f"{SDK}/api/v2/status", None, method="GET", timeout=20)
    state = ""
    if isinstance(data.get("general_state"), str):
        state = data["general_state"]
    elif isinstance(data.get("status"), dict):
        state = str(data["status"].get("general_state") or "")
    ok = code == 200 and (state.lower() == "ok" or bool(data))
    return ok, state or (body.decode("utf-8", errors="replace")[:120] if body else f"HTTP {code}")


def _inner_data(data: dict[str, Any]) -> dict[str, Any]:
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    return inner if isinstance(inner, dict) else {}


def _raise_if_api_error(data: dict[str, Any], fallback: str) -> None:
    err = _flatten_error(data.get("error"))
    if err:
        raise OdyseeError(err)
    if data.get("success") is False:
        raise OdyseeError(_flatten_error(data.get("message")) or fallback)


def _extract_auth_token(data: dict[str, Any]) -> str:
    inner = _inner_data(data)
    for key in ("auth_token", "authToken", "legacy_auth_token"):
        val = str(inner.get(key) or data.get(key) or "").strip()
        if val:
            return val
    return ""


def _guest_auth_token() -> str:
    """Odysee exige un auth_token anónimo (user/new) antes de user/signin."""
    app_id = hashlib.sha1(uuid.uuid4().bytes).hexdigest()
    last_err: OdyseeError | None = None
    for fields in (
        {"language": "en", "app_id": app_id, "auth_token": ""},
        {"language": "en", "auth_token": ""},
    ):
        try:
            data = _form(f"{INTERNAL}/user/new", fields)
            _raise_if_api_error(data, "user/new failed")
        except OdyseeError as e:
            last_err = e
            _debug(f"user/new fallo: {e}")
            continue
        token = _extract_auth_token(data)
        if token:
            return token
        keys = sorted({*data.keys(), *_inner_data(data).keys()})
        _debug("user/new sin auth_token keys=" + ",".join(keys)[:180])
        last_err = OdyseeError("user/new did not return auth_token")
    raise last_err or OdyseeError("user/new did not return auth_token")


def signin(email: str, password: str) -> tuple[str, str]:
    em = (email or "").strip()
    pw = (password or "").strip()
    if not em or not pw:
        raise OdyseeError("email_password_required")
    _reset_http_session()
    guest = _guest_auth_token()
    data = _form(
        f"{INTERNAL}/user/signin",
        {"email": em, "password": pw, "auth_token": guest},
        headers={"X-Lbry-Auth-Token": guest},
    )
    _raise_if_api_error(data, "signin failed")
    token = _extract_auth_token(data) or guest
    inner = _inner_data(data)
    name = str(inner.get("name") or inner.get("primary_email") or em).strip()
    return token, name


def _resolve_channel_claim_id(channel_name: str) -> str:
    name = (channel_name or "").strip()
    if not name:
        return ""
    if not name.startswith("@"):
        name = "@" + name.lstrip("@")
    payload = {"method": "resolve", "params": {"urls": f"lbry://{name}"}}
    code, data, _ = _json(f"{SDK}/api/v1/proxy", payload, method="POST", timeout=25)
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    if code >= 400 or not result:
        return ""
    for value in result.values():
        if not isinstance(value, dict):
            continue
        cid = str(value.get("claim_id") or "").strip()
        if CLAIM_ID_RE.fullmatch(cid) and str(value.get("value_type") or "") == "channel":
            return cid.lower()
        if CLAIM_ID_RE.fullmatch(cid):
            return cid.lower()
    return ""


def normalize_channel_id(extra: str) -> str:
    """Acepta claim_id de 40 hex, URL de Odysee o @canal; devuelve claim_id."""
    raw = (extra or "").strip()
    if not raw:
        return ""
    if CLAIM_ID_RE.fullmatch(raw):
        return raw.lower()
    text = raw
    lower = text.lower()
    if "odysee.com/" in lower:
        text = text.split("odysee.com/", 1)[1]
    text = text.split("?")[0].strip().strip("/")
    if text.startswith("lbry://"):
        text = text[7:]
    if "#" in text:
        hid = text.split("#")[-1]
        if CLAIM_ID_RE.fullmatch(hid):
            return hid.lower()
        text = text.split("#", 1)[0]
    if ":" in text:
        left, right = text.rsplit(":", 1)
        if CLAIM_ID_RE.fullmatch(right):
            return right.lower()
        text = left
    name = text.strip()
    if not name:
        return ""
    return _resolve_channel_claim_id(name)


def user_me(auth_token: str) -> dict[str, Any]:
    token = (auth_token or "").strip()
    if not token:
        raise OdyseeError("missing_token")
    data = _form(
        f"{INTERNAL}/user/me",
        {"auth_token": token},
        headers={"X-Lbry-Auth-Token": token},
    )
    _raise_if_api_error(data, "user/me empty")
    inner = _inner_data(data)
    if not inner or inner is data:
        # Sin "data" anidado, exige al menos un id de usuario.
        if not (inner.get("id") or inner.get("primary_email")):
            raise OdyseeError("user/me empty")
        return inner
    return inner


def _looks_like_password(login: str, secret: str) -> bool:
    """Email + secreto = contraseña. El token va en auth_token, no en secret."""
    return bool((login or "").strip() and "@" in login and (secret or "").strip())


def _is_bad_credentials(message: str) -> bool:
    low = (message or "").lower()
    return any(
        x in low
        for x in (
            "incorrect email",
            "incorrect password",
            "email and/or password",
            "invalid password",
            "wrong password",
        )
    )


def _try_cached_token(token: str) -> str | None:
    tok = (token or "").strip()
    if not tok:
        return None
    try:
        user_me(tok)
        return tok
    except OdyseeError:
        return None


def probe_account(email: str, secret: str, extra: str = "") -> tuple[bool, str]:
    """secret = contraseña al conectar; también acepta auth_token legado en secret."""
    login = (email or "").strip()
    sec = (secret or "").strip()
    if not login or not sec:
        return False, "missing_fields"
    try:
        token = ""
        name = login
        if _looks_like_password(login, sec):
            try:
                token, name = signin(login, sec)
            except OdyseeError:
                if _try_cached_token(sec):
                    token = sec
                else:
                    raise
        else:
            token = sec
        me = user_me(token)
        email_ok = str(me.get("primary_email") or "").strip()
        if not email_ok and not me.get("has_verified_email"):
            raise OdyseeError("signin_not_logged_in")
        shown = str(me.get("name") or me.get("primary_email") or name or login).strip()
        return True, shown
    except OdyseeError as e:
        _debug(f"probe fallo: {e}")
        return False, str(e)
    except Exception as e:
        return False, str(e)[:280]


def resolve_account_auth_token(account: dict[str, Any]) -> str:
    """Usa auth_token en caché; si caducó, hace signin con email/contraseña guardados."""
    import db

    account_id = str(account.get("id") or "").strip()
    login = str(account.get("login") or "").strip()
    secret = str(account.get("secret") or "").strip()
    cached = str(account.get("auth_token") or "").strip()

    hit = _try_cached_token(cached)
    if hit:
        return hit

    if _looks_like_password(login, secret):
        try:
            token, _ = signin(login, secret)
            if account_id:
                db.update_chain_auth_token(account_id, token)
            return token
        except OdyseeError:
            hit = _try_cached_token(secret)
            if hit:
                return hit
            raise

    hit = _try_cached_token(secret)
    if hit:
        return hit

    raise OdyseeError("session_expired_reconnect")


def _claim_name(title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (title or "video").lower()).strip("-")[:40]
    if not base or base[0].isdigit():
        base = f"v-{base or 'video'}"
    return f"{base}-{uuid.uuid4().hex[:8]}"


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _create_upload(auth_token: str) -> tuple[str, str]:
    code, data, body = _json(
        f"{SDK}/api/v1/asynqueries/uploads/",
        {},
        headers={"X-Lbry-Auth-Token": auth_token},
        timeout=45,
    )
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else data
    token = str((payload or {}).get("token") or "").strip()
    location = str((payload or {}).get("location") or "").strip()
    if data.get("status") == "upload_token_created" and token and location:
        return token, location
    if token and location:
        return token, location
    raise OdyseeError(
        str(data.get("error") or data.get("message") or body.decode("utf-8", errors="replace")[:200] or f"HTTP {code}")
    )


def _tus_headers(upload_token: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    hdrs = {
        "Tus-Resumable": "1.0.0",
        "Authorization": f"Bearer {upload_token}",
        "User-Agent": UA,
    }
    if extra:
        hdrs.update(extra)
    return hdrs


def _tus_offset(location: str, upload_token: str) -> int:
    code, headers, _ = _request(
        location,
        method="HEAD",
        headers=_tus_headers(upload_token),
        timeout=45,
    )
    if code in (404, 410):
        return 0
    raw = headers.get("upload-offset") or "0"
    try:
        return int(raw)
    except ValueError:
        return 0


def _tus_upload(location: str, upload_token: str, file_path: Path) -> None:
    size = file_path.stat().st_size
    meta = f"filename {_b64(file_path.name)},filetype {_b64('video/mp4')}"
    code, headers, body = _request(
        location,
        method="POST",
        data=b"",
        headers=_tus_headers(
            upload_token,
            {
                "Upload-Length": str(size),
                "Upload-Metadata": meta,
                "Content-Length": "0",
            },
        ),
        timeout=45,
    )
    loc = headers.get("location") or location
    if code not in (201, 204, 409, 200) and code >= 400:
        text = body.decode("utf-8", errors="replace")[:200]
        if code not in (404, 405):
            raise OdyseeError(text or f"TUS POST HTTP {code}")
        loc = location
    offset = _tus_offset(loc, upload_token)
    with file_path.open("rb") as fh:
        if offset:
            fh.seek(offset)
        while offset < size:
            chunk = fh.read(min(TUS_CHUNK, size - offset))
            if not chunk:
                break
            p_code, p_headers, p_body = _request(
                loc,
                method="PATCH",
                data=chunk,
                headers=_tus_headers(
                    upload_token,
                    {
                        "Upload-Offset": str(offset),
                        "Content-Type": "application/offset+octet-stream",
                        "Content-Length": str(len(chunk)),
                    },
                ),
                timeout=300,
            )
            if p_code not in (204, 200):
                raise OdyseeError(
                    p_body.decode("utf-8", errors="replace")[:200] or f"TUS PATCH HTTP {p_code}"
                )
            nxt = p_headers.get("upload-offset")
            offset = int(nxt) if nxt and nxt.isdigit() else offset + len(chunk)
    if offset < size:
        raise OdyseeError("TUS upload incomplete")


def _asynquery(auth_token: str, params: dict[str, Any]) -> str:
    payload = {
        "jsonrpc": "2.0",
        "method": "stream_create",
        "params": params,
        "id": int(time.time()),
    }
    code, data, body = _json(
        f"{SDK}/api/v1/asynqueries/",
        payload,
        headers={"X-Lbry-Auth-Token": auth_token},
        timeout=60,
    )
    payload_id = ""
    inner_payload = data.get("payload")
    if isinstance(inner_payload, dict):
        payload_id = str(inner_payload.get("id") or "").strip()
    qid = str(data.get("id") or payload_id or data.get("query_id") or "").strip()
    if data.get("status") == "query_created" and qid:
        return qid
    if qid:
        return qid
    inner = data.get("result") if isinstance(data.get("result"), dict) else {}
    qid = str((inner or {}).get("id") or "").strip()
    if qid:
        return qid
    raise OdyseeError(
        str(data.get("error") or data.get("message") or body.decode("utf-8", errors="replace")[:220] or f"HTTP {code}")
    )


def _poll(auth_token: str, query_id: str, timeout_s: int = 420) -> dict[str, Any]:
    url = f"{SDK}/api/v1/asynqueries/{urllib.parse.quote(query_id)}"
    deadline = time.time() + timeout_s
    last = b""
    while time.time() < deadline:
        code, headers, body = _request(
            url,
            method="GET",
            headers={"X-Lbry-Auth-Token": auth_token, "Accept": "application/json"},
            timeout=45,
        )
        last = body
        if code == 204:
            time.sleep(3)
            continue
        if code == 404:
            time.sleep(2)
            continue
        data = _parse(body.decode("utf-8", errors="replace"))
        if code >= 400:
            raise OdyseeError(str(data.get("error") or data.get("message") or f"HTTP {code}")[:280])
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            raise OdyseeError(str(err.get("message"))[:280])
        if isinstance(err, str) and err.strip():
            raise OdyseeError(err[:280])
        result = data.get("result") if isinstance(data.get("result"), dict) else data
        if result.get("outputs") or result.get("claim_id") or result.get("lbry_url") or result.get("txid"):
            return result if isinstance(result, dict) else data
        status = str(data.get("status") or "").lower()
        if status in {"succeeded", "complete", "completed"}:
            return result if isinstance(result, dict) else data
        if status in {"failed", "error"}:
            raise OdyseeError(str(data.get("message") or status)[:280])
        time.sleep(3)
    raise OdyseeError(last.decode("utf-8", errors="replace")[:200] or "asynquery timeout")


def _watch_url(result: dict[str, Any], claim_name: str) -> str:
    for key in ("canonical_url", "permanent_url", "lbry_url", "short_url"):
        raw = str(result.get(key) or "").strip()
        if raw.startswith("lbry://"):
            path = raw.replace("lbry://", "").lstrip("/")
            return f"https://odysee.com/{path}"
        if raw.startswith("http"):
            return raw
    outputs = result.get("outputs")
    if isinstance(outputs, list) and outputs:
        first = outputs[0] if isinstance(outputs[0], dict) else {}
        cid = str(first.get("claim_id") or "").strip()
        name = str(first.get("name") or claim_name).strip()
        if cid:
            return f"https://odysee.com/{name}:{cid}"
    cid = str(result.get("claim_id") or "").strip()
    if cid:
        return f"https://odysee.com/{claim_name}:{cid}"
    return f"https://odysee.com/{claim_name}"


def publish_video(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account: dict[str, Any],
) -> tuple[bool, str]:
    from i18n import t

    path = Path(file_path)
    if content_type == "photo" or path.suffix.lower() in PHOTO_EXT:
        return False, t("pub.odysee.no_photo", lang)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.odysee.file_missing", lang)
    if path.suffix.lower() not in VIDEO_EXT:
        return False, t("pub.odysee.bad_video", lang)
    channel = normalize_channel_id(str(account.get("extra") or "").strip())
    if not str(account.get("secret") or "").strip() and not str(account.get("auth_token") or "").strip():
        return False, t("pub.odysee.no_account", lang)
    try:
        token = resolve_account_auth_token(account)
        upload_token, location = _create_upload(token)
        if not FILE_PATH_RE.match(location):
            raise OdyseeError("upload location is not a TUS URL")
        name = _claim_name(title)
        params: dict[str, Any] = {
            "name": name,
            "bid": "0.01",
            "file_path": location,
            "title": (title or path.stem)[:255],
            "description": description or "",
            "languages": ["en"],
            "tags": ["video"],
            "_defer": True,
        }
        if channel:
            params["channel_id"] = channel
        qid = _asynquery(token, params)
        _tus_upload(location, upload_token, path)
        params.pop("_defer", None)
        qid = _asynquery(token, params) or qid
        result = _poll(token, qid)
        url = _watch_url(result, name)
        return True, t("pub.odysee.ok", lang, url=url)
    except OdyseeError as e:
        code = str(e)
        low = code.lower()
        if code == "email_unverified" or "unverified" in low:
            return False, t("odysee.err_unverified", lang)
        if code == "2fa_required" or "2fa" in low:
            return False, t("odysee.err_2fa", lang)
        if code == "session_expired_reconnect" or _is_bad_credentials(code):
            return False, t("odysee.err_auth", lang)
        return False, t("pub.odysee.upload_fail", lang, error=code[:180])
    except Exception as e:
        return False, t("pub.odysee.upload_fail", lang, error=str(e)[:180])
