"""Save and live-test platform API credentials."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import db
import filehost
import chain
import platforms
import tiktok_oauth
import vmos


def _http(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    form: dict[str, str] | None = None,
    timeout: int = 18,
) -> tuple[int, str]:
    data = None
    hdrs = dict(headers or {})
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body


def _json_body(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _creds(pid: str) -> dict[str, Any]:
    raw = dict(db.get_platform_credentials_raw(pid) or {})
    overlay = _test_overlay.get(pid)
    if not overlay:
        return raw
    merged = {**raw, **overlay}
    return merged


_test_overlay: dict[str, dict[str, Any]] = {}


def _set_test_overlay(pid: str, draft: dict[str, Any] | None) -> None:
    if not draft:
        _test_overlay.pop(pid, None)
        return
    overlay: dict[str, Any] = {}
    if draft.get("client_id") is not None:
        overlay["client_id"] = (draft.get("client_id") or "").strip()
    if "client_secret" in draft:
        secret = (draft.get("client_secret") or "").strip()
        if secret not in ("unchanged", "x" * 19):
            overlay["client_secret"] = secret
    if "access_token" in draft:
        token = (draft.get("access_token") or "").strip()
        if token not in ("unchanged", "x" * 19):
            overlay["access_token"] = token
    if draft.get("extra") is not None:
        overlay["extra"] = (draft.get("extra") or "").strip()
    _test_overlay[pid] = overlay


def _tiktok_keys() -> tuple[str, str, str]:
    raw = _creds("tiktok")
    key = (raw.get("client_id") or "").strip() or tiktok_oauth.client_key()
    secret = (raw.get("client_secret") or "").strip() or tiktok_oauth.client_secret()
    redirect = (raw.get("extra") or "").strip() or tiktok_oauth.redirect_uri()
    return key, secret, redirect


def test_platform(
    platform_id: str,
    lang: str = "en",
    *,
    draft: dict[str, Any] | None = None,
    save_result: bool = True,
) -> dict[str, Any]:
    from i18n import t

    pid = (platform_id or "").strip()
    if pid not in platforms.PLATFORM_IDS:
        return {"ok": False, "message": t("api.unknown_platform", lang)}

    testers = {
        "tiktok": _test_tiktok,
        "youtube": _test_youtube,
        "instagram": _test_instagram,
        "x": _test_x,
        "dailymotion": _test_dailymotion,
        "bilibili": _test_bilibili,
        "rumble": _test_rumble,
        "snapchat": _test_snapchat,
        "facebook": _test_facebook,
    }
    for hid in filehost.PLATFORM_IDS:
        testers[hid] = lambda lang, p=hid: _test_filehost(p, lang)
    for cid in chain.PLATFORM_IDS:
        testers[cid] = lambda lang, p=cid: _test_chain(p, lang)
    if pid not in testers:
        return {"ok": False, "message": t("api.unknown_platform", lang)}
    try:
        if draft is not None:
            db.set_credentials_account_name(str(draft.get("name") or ""))
            _set_test_overlay(pid, draft)
        ok, message = testers[pid](lang)
        if save_result:
            db.save_platform_test_result(pid, ok, message)
        return {"ok": ok, "message": message, **db.get_platform_credentials_public(pid)}
    finally:
        if draft is not None:
            _set_test_overlay(pid, None)


def verify_account_platform(
    platform_id: str,
    account_link_id: str,
    lang: str = "es",
) -> dict[str, Any]:
    """Consulta la API de esa cuenta/servidor antes de buscar o extraer videos."""
    import proxy_util

    name = db.get_account_link_name(account_link_id) or ""
    with db.using_credentials_account(name):
        return _verify_account_platform_with_proxy(
            platform_id, account_link_id, lang, proxy_util
        )


def _verify_account_platform_with_proxy(
    platform_id: str,
    account_link_id: str,
    lang: str,
    proxy_util: Any,
) -> dict[str, Any]:
    pid = (platform_id or "").strip()
    if pid in vmos.PLATFORM_IDS and db.resolve_vmos_account_for_publish(
        pid, account_link_id
    ):
        return _verify_account_platform_inner(platform_id, account_link_id, lang)

    proxy_url = db.get_active_proxy_url_for_account(account_link_id)
    with proxy_util.using_proxy(proxy_url):
        return _verify_account_platform_inner(platform_id, account_link_id, lang)


def _verify_account_platform_inner(
    platform_id: str,
    account_link_id: str,
    lang: str = "es",
) -> dict[str, Any]:
    from i18n import t

    pid = (platform_id or "").strip()
    if pid not in platforms.PLATFORM_IDS:
        return {"ok": False, "message": t("api.unknown_platform", lang)}
    if pid in vmos.PLATFORM_IDS:
        vmos_row = db.resolve_vmos_account_for_publish(pid, account_link_id)
        if vmos_row:
            return _verify_vmos_account(vmos_row, lang)
    if pid == "tiktok":
        return _verify_tiktok_account(account_link_id, lang)
    if pid == "youtube":
        return _verify_youtube_account(account_link_id, lang)
    if pid == "instagram":
        return _verify_instagram_account(account_link_id, lang)
    if pid == "facebook":
        return _verify_facebook_account(account_link_id, lang)
    if pid == "x":
        return _verify_x_account(account_link_id, lang)
    if pid == "dailymotion":
        return _verify_dailymotion_account(account_link_id, lang)
    if pid == "bilibili":
        return _verify_bilibili_account(account_link_id, lang)
    if pid == "rumble":
        return _verify_rumble_account(account_link_id, lang)
    if pid == "snapchat":
        return _verify_snapchat_account(account_link_id, lang)
    if pid in filehost.PLATFORM_IDS:
        return _verify_filehost_account(pid, account_link_id, lang)
    if pid in chain.PLATFORM_IDS:
        return _verify_chain_account(pid, account_link_id, lang)
    return test_platform(pid, lang, save_result=True)


def _verify_vmos_account(account: dict[str, Any], lang: str) -> dict[str, Any]:
    from i18n import t

    try:
        data = vmos.pad_info(
            str(account.get("access_key") or ""),
            str(account.get("secret_key") or ""),
            str(account.get("pad_code") or ""),
            lang=lang,
        )
    except vmos.VmosError as e:
        return {"ok": False, "message": str(e)[:300]}
    info = data.get("data") if isinstance(data.get("data"), dict) else {}
    pad = str((info or {}).get("padCode") or account.get("pad_code") or "").strip()
    return {"ok": True, "message": t("servers.vmos_test_ok", lang, pad=pad or "ok")}


def _verify_filehost_account(
    platform_id: str, account_link_id: str, lang: str
) -> dict[str, Any]:
    from i18n import t

    row = db.resolve_filehost_account_for_publish(platform_id, account_link_id)
    if not row:
        return {"ok": False, "message": t("api.filehost.need_account", lang)}
    ok, detail = filehost.probe_account(
        platform_id,
        str(row.get("api_key") or ""),
        str(row.get("extra") or ""),
    )
    if ok:
        message = t("api.filehost.ok", lang, name=detail)
        db.save_platform_test_result(platform_id, True, message)
        return {"ok": True, "message": message}
    message = t("api.filehost.fail", lang, error=detail)
    db.save_platform_test_result(platform_id, False, message)
    return {"ok": False, "message": message}


def _verify_chain_account(
    platform_id: str, account_link_id: str, lang: str
) -> dict[str, Any]:
    from i18n import t

    row = db.resolve_chain_account_for_publish(platform_id, account_link_id)
    if not row:
        return {"ok": False, "message": t("api.chain.need_account", lang)}
    ok, detail = chain.probe_account(
        platform_id,
        str(row.get("login") or ""),
        str(row.get("secret") or ""),
        str(row.get("extra") or ""),
        account_id=str(row.get("id") or ""),
    )
    if ok:
        message = t("api.chain.ok", lang, name=detail)
        db.save_platform_test_result(platform_id, True, message)
        return {"ok": True, "message": message}
    message = t("api.chain.fail", lang, error=detail)
    db.save_platform_test_result(platform_id, False, message)
    return {"ok": False, "message": message}


def _verify_tiktok_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    token = None
    row = db.get_account_platform_row(account_link_id, "tiktok")
    if row and str(row.get("source_kind") or "") == "tiktok":
        token = db.get_tiktok_access_token_for_config(str(row.get("source_ref") or ""))
    if not token:
        name = db.get_account_link_name(account_link_id) or ""
        token = db.get_tiktok_access_token_for_account_name(name)
    if not token:
        return test_platform("tiktok", lang, save_result=True)
    try:
        user = tiktok_oauth.fetch_user_profile(token)
        name = user.get("username") or user.get("display_name") or "ok"
        message = t("api.tiktok.token_ok", lang, name=name)
        db.save_platform_test_result("tiktok", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "tiktok", str(e))
        db.save_platform_test_result("tiktok", False, message)
        return {"ok": False, "message": message}


def _verify_youtube_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    import youtube_oauth

    oid = db.resolve_oauth_account_id("youtube", account_link_id=account_link_id)
    token = ""
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
    if not token:
        return test_platform("youtube", lang, save_result=True)
    try:
        profile = youtube_oauth.fetch_channel_profile(token)
        name = profile.get("display_name") or profile.get("username") or "ok"
        message = t("api.youtube.token_ok", lang) + f" ({name})"
        db.save_platform_test_result("youtube", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "youtube", str(e))
        db.save_platform_test_result("youtube", False, message)
        return {"ok": False, "message": message}


def _verify_instagram_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    import instagram_oauth

    oid = db.resolve_oauth_account_id("instagram", account_link_id=account_link_id)
    token = ""
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
    if not token:
        return test_platform("instagram", lang, save_result=True)
    try:
        profile = instagram_oauth.fetch_profile(token)
        name = profile.get("username") or profile.get("display_name") or "ok"
        message = t("api.instagram.ok", lang, name=name)
        db.save_platform_test_result("instagram", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "instagram", str(e))
        db.save_platform_test_result("instagram", False, message)
        return {"ok": False, "message": message}


def _verify_facebook_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    import facebook_oauth

    oid = db.resolve_oauth_account_id("facebook", account_link_id=account_link_id)
    token = ""
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
    if not token:
        return test_platform("facebook", lang, save_result=True)
    try:
        profile = facebook_oauth.fetch_page_profile(token)
        name = profile.get("display_name") or profile.get("open_id") or "ok"
        message = t("api.facebook.ok", lang, name=name)
        db.save_platform_test_result("facebook", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "facebook", str(e))
        db.save_platform_test_result("facebook", False, message)
        return {"ok": False, "message": message}


def _verify_x_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    import x_oauth

    oid = db.resolve_oauth_account_id("x", account_link_id=account_link_id)
    token = ""
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
    if not token:
        return test_platform("x", lang, save_result=True)
    try:
        profile = x_oauth.fetch_profile(token)
        name = profile.get("username") or profile.get("display_name") or "ok"
        message = t("api.x.ok", lang, name=name)
        db.save_platform_test_result("x", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "x", str(e))
        db.save_platform_test_result("x", False, message)
        return {"ok": False, "message": message}


def _verify_dailymotion_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    import dailymotion_oauth

    oid = db.resolve_oauth_account_id("dailymotion", account_link_id=account_link_id)
    token = ""
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
    if not token:
        return test_platform("dailymotion", lang, save_result=True)
    try:
        profile = dailymotion_oauth.fetch_profile(token)
        name = profile.get("username") or profile.get("display_name") or "ok"
        message = t("api.dailymotion.ok", lang, name=name)
        db.save_platform_test_result("dailymotion", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "dailymotion", str(e))
        db.save_platform_test_result("dailymotion", False, message)
        return {"ok": False, "message": message}


def _verify_bilibili_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    import bilibili_oauth

    oid = db.resolve_oauth_account_id("bilibili", account_link_id=account_link_id)
    token = ""
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
    if not token:
        return test_platform("bilibili", lang, save_result=True)
    try:
        profile = bilibili_oauth.fetch_profile(token)
        name = profile.get("username") or profile.get("display_name") or "ok"
        message = t("api.bilibili.ok", lang, name=name)
        db.save_platform_test_result("bilibili", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "bilibili", str(e))
        db.save_platform_test_result("bilibili", False, message)
        return {"ok": False, "message": message}


def _verify_rumble_account(account_link_id: str, lang: str) -> dict[str, Any]:
    _ = account_link_id
    return test_platform("rumble", lang, save_result=True)


def _verify_snapchat_account(account_link_id: str, lang: str) -> dict[str, Any]:
    from i18n import t

    import snapchat_oauth

    oid = db.resolve_oauth_account_id("snapchat", account_link_id=account_link_id)
    token = ""
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
    if not token:
        return test_platform("snapchat", lang, save_result=True)
    try:
        profile = snapchat_oauth.fetch_profile(token)
        name = profile.get("username") or profile.get("display_name") or "ok"
        message = t("api.snapchat.ok", lang, name=name)
        db.save_platform_test_result("snapchat", True, message)
        return {"ok": True, "message": message}
    except Exception as e:
        message = _fail_message(lang, "snapchat", str(e))
        db.save_platform_test_result("snapchat", False, message)
        return {"ok": False, "message": message}


def test_all_platforms(lang: str = "en") -> list[dict[str, Any]]:
    results = []
    for p in platforms.PLATFORMS:
        r = test_platform(str(p["id"]), lang)
        r["platform_id"] = p["id"]
        results.append(r)
    return results


def _need_keys(lang: str) -> tuple[bool, str]:
    from i18n import t

    return False, t("api.need_credentials", lang)


def _looks_like_placeholder(value: str) -> bool:
    s = (value or "").strip().lower()
    if len(s) < 8:
        return True
    if s in {"test", "demo", "example", "changeme", "password", "secret"}:
        return True
    if s.isdigit() and len(set(s)) <= 2:
        return True
    return False


def _platform_label(lang: str, platform_id: str) -> str:
    from i18n import t

    key = f"platform.{platform_id}"
    label = t(key, lang)
    return label if label != key else platform_id


def _humanize_api_error(lang: str, platform_id: str, raw: str) -> str:
    from i18n import t

    text = (raw or "").strip()
    if not text:
        return t("api.err.generic", lang)
    low = text.lower()
    platform = _platform_label(lang, platform_id)
    checks: tuple[tuple[tuple[str, ...], str], ...] = (
        (
            (
                "invalid authentication credentials",
                "invalid_grant",
                "token has been expired",
                "token expired",
                "expired token",
                "unauthorized",
                "autherror",
            ),
            "api.err.token_expired",
        ),
        (
            (
                "invalid_client",
                "unauthorized_client",
                "client authentication failed",
                "invalid client",
            ),
            "api.err.bad_client",
        ),
        (
            ("access_denied", "insufficient permission", "insufficient_permissions", "forbidden"),
            "api.err.permission_denied",
        ),
        (("redirect_uri_mismatch", "redirect uri"), "api.err.redirect_mismatch"),
        (("quota", "rate limit", "ratelimit", "too many requests"), "api.err.rate_limit"),
        (
            ("ssl", "certificate", "connection refused", "timed out", "timeout", "network"),
            "api.err.network",
        ),
    )
    for needles, key in checks:
        if any(n in low for n in needles):
            if key in {"api.err.token_expired", "api.err.bad_client", "api.err.permission_denied"}:
                return t(key, lang, platform=platform)
            return t(key, lang)
    detail = text.replace("https://", "").replace("http://", "")
    if len(detail) > 140:
        detail = detail[:137].rstrip() + "…"
    return t("api.err.detail", lang, detail=detail)


def _testing_draft_credentials(platform_id: str) -> bool:
    overlay = _test_overlay.get(platform_id) or {}
    return bool((overlay.get("client_id") or "").strip())


def _draft_client_pair(platform_id: str) -> tuple[str, str]:
    raw = _creds(platform_id)
    client_id = (raw.get("client_id") or "").strip()
    client_secret = (raw.get("client_secret") or "").strip()
    return client_id, client_secret


def _validate_draft_client_credentials(lang: str, platform_id: str) -> tuple[bool, str] | None:
    """Valida credenciales del formulario (panel). None = seguir con prueba normal."""
    from i18n import t

    if not _testing_draft_credentials(platform_id):
        return None
    client_id, client_secret = _draft_client_pair(platform_id)
    if not client_id:
        return False, t("api.need_credentials", lang)
    if _looks_like_placeholder(client_id):
        return False, t("api.err.invalid_credentials", lang)
    if (
        platform_id
        in {"dailymotion", "x", "instagram", "facebook", "youtube", "snapchat", "bilibili"}
        and not client_secret
    ):
        return False, t("api.err.need_secret", lang)
    if client_secret and _looks_like_placeholder(client_secret):
        return False, t("api.err.invalid_credentials", lang)
    return None


_PROBE_CODE = "credential-probe"
_PROBE_REDIRECT = "https://example.com/oauth/callback"
_PROBE_VERIFIER = "credential-probe-verifier-credential-probe-verifier-0123456789"

_BAD_CLIENT_NEEDLES = (
    "invalid_client",
    "unauthorized_client",
    "client authentication failed",
    "invalid client",
    "unknown client",
    "invalid app id",
    "invalid client id",
    "invalid platform app",
    "error validating application",
    "invalid application",
    "incorrect client credentials",
    "invalid api key",
    "app not found",
)

_CLIENT_OK_NEEDLES = (
    "invalid_grant",
    "authorization code",
    "authorization_code",
    "auth code",
    "invalid code",
    "code was invalid",
    "expired code",
    "malformed auth code",
    "matching code was not found",
    "invalid oauth code",
    "code has been used",
    "invalid_request",
)


def _classify_client_probe(status: int, body: str) -> str:
    """'ok' = client válido (solo falló el code falso); 'bad' = client inválido."""
    data = _json_body(body)
    blob = (json.dumps(data) if data else (body or "")[:400]).lower()
    if any(n in blob for n in _BAD_CLIENT_NEEDLES):
        return "bad"
    if any(n in blob for n in _CLIENT_OK_NEEDLES):
        return "ok"
    if status >= 500:
        return "network"
    return "unknown"


def _probe_error_detail(body: str, status: int) -> str:
    data = _json_body(body)
    if data:
        err = data.get("error")
        if isinstance(err, dict):
            msg = str(err.get("message") or err.get("error_description") or "").strip()
            if msg:
                return msg[:200]
        for key in ("error_description", "message", "error_message", "error", "msg"):
            val = str(data.get(key) or "").strip()
            if val:
                return val[:200]
    return (body or f"HTTP {status}")[:200]


def _probe_draft_credentials(
    platform_id: str, client_id: str, client_secret: str
) -> tuple[str, str]:
    """Prueba real de Client ID/Secret contra el proveedor. (veredicto, detalle)."""
    try:
        if platform_id == "facebook":
            q = urllib.parse.urlencode(
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials",
                }
            )
            status, body = _http(f"https://graph.facebook.com/v21.0/oauth/access_token?{q}")
            data = _json_body(body)
            if status == 200 and data.get("access_token"):
                return "ok", ""
            verdict = "bad" if status in (400, 401, 403) else _classify_client_probe(status, body)
            return verdict, _probe_error_detail(body, status)

        if platform_id == "dailymotion":
            import dailymotion_oauth

            status, body = _http(
                dailymotion_oauth.TOKEN_URL,
                method="POST",
                form={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            data = _json_body(body)
            if status == 200 and data.get("access_token"):
                return "ok", ""
            verdict = "bad" if status in (400, 401, 403) else _classify_client_probe(status, body)
            return verdict, _probe_error_detail(body, status)

        if platform_id == "youtube":
            import youtube_oauth

            status, body = _http(
                youtube_oauth.GOOGLE_TOKEN_URL,
                method="POST",
                form={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": _PROBE_CODE,
                    "grant_type": "authorization_code",
                    "redirect_uri": _PROBE_REDIRECT,
                },
            )
            return _classify_client_probe(status, body), _probe_error_detail(body, status)

        if platform_id == "instagram":
            import instagram_oauth

            status, body = _http(
                instagram_oauth.TOKEN_URL,
                method="POST",
                form={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": _PROBE_REDIRECT,
                    "code": _PROBE_CODE,
                },
            )
            return _classify_client_probe(status, body), _probe_error_detail(body, status)

        if platform_id == "x":
            import x_oauth

            basic = base64.b64encode(
                f"{client_id}:{client_secret}".encode("utf-8")
            ).decode("ascii")
            status, body = _http(
                x_oauth.TOKEN_URL,
                method="POST",
                form={
                    "grant_type": "authorization_code",
                    "code": _PROBE_CODE,
                    "redirect_uri": _PROBE_REDIRECT,
                    "client_id": client_id,
                    "code_verifier": _PROBE_VERIFIER,
                },
                headers={"Authorization": f"Basic {basic}"},
            )
            return _classify_client_probe(status, body), _probe_error_detail(body, status)

        if platform_id == "snapchat":
            import snapchat_oauth

            status, body = _http(
                snapchat_oauth.TOKEN_URL,
                method="POST",
                form={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": _PROBE_CODE,
                    "redirect_uri": _PROBE_REDIRECT,
                },
            )
            return _classify_client_probe(status, body), _probe_error_detail(body, status)

        if platform_id == "bilibili":
            import bilibili_oauth

            q = urllib.parse.urlencode(
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "code": _PROBE_CODE,
                }
            )
            status, body = _http(
                f"{bilibili_oauth.TOKEN_URL}?{q}",
                method="POST",
                headers={"User-Agent": bilibili_oauth.UA, "Accept": "application/json"},
            )
            return _classify_client_probe(status, body), _probe_error_detail(body, status)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return "network", str(e)[:200]
    return "unknown", ""


def _client_probe_result(
    lang: str, platform_id: str, ok_key: str, client_id: str, client_secret: str
) -> tuple[bool, str]:
    """Resultado del probe real de Client ID/Secret contra el proveedor."""
    from i18n import t

    if not client_id:
        return _need_keys(lang)
    verdict, detail = _probe_draft_credentials(platform_id, client_id, client_secret)
    if verdict == "ok":
        return True, t(ok_key, lang)
    if verdict == "bad":
        return False, t(
            "api.err.bad_client", lang, platform=_platform_label(lang, platform_id)
        )
    if detail:
        return False, _fail_message(lang, platform_id, detail)
    if verdict == "network":
        return False, t("api.err.network", lang)
    return False, t("api.err.generic", lang)


def _finish_draft_credentials_test(
    lang: str, platform_id: str, ok_key: str
) -> tuple[bool, str] | None:
    if not _testing_draft_credentials(platform_id):
        return None
    client_id, client_secret = _draft_client_pair(platform_id)
    if not client_id:
        return _need_keys(lang)
    return _client_probe_result(lang, platform_id, ok_key, client_id, client_secret)


def _fail_message(lang: str, platform_id: str, raw: str) -> str:
    return _humanize_api_error(lang, platform_id, raw)


def _test_tiktok(lang: str) -> tuple[bool, str]:
    from i18n import t

    token = db.get_first_tiktok_access_token()
    if token:
        try:
            user = tiktok_oauth.fetch_user_profile(token)
            name = user.get("username") or user.get("display_name") or "ok"
            return True, t("api.tiktok.token_ok", lang, name=name)
        except Exception as e:
            return False, _fail_message(lang, "tiktok", str(e))

    key, secret, redirect = _tiktok_keys()
    if not (key and secret):
        return _need_keys(lang)
    if _looks_like_placeholder(key) or _looks_like_placeholder(secret):
        return False, t("api.tiktok.dummy", lang)

    status, body = _http(
        tiktok_oauth.TIKTOK_TOKEN_URL,
        method="POST",
        form={
            "client_key": key,
            "client_secret": secret,
            "grant_type": "authorization_code",
            "code": "credential-probe",
            "redirect_uri": redirect or "https://example.com/callback",
        },
    )
    data = _json_body(body)
    err = str(data.get("error") or data.get("error_code") or "")
    desc = str(data.get("error_description") or data.get("description") or body[:160])
    blob = f"{err} {desc}".lower()
    if "invalid_client" in blob or err in ("10002", "10013"):
        return False, t("api.tiktok.bad_client", lang)
    if status in (200, 400, 401) and (
        "invalid_grant" in blob or "authorization_code" in blob or "authorization code" in blob
    ):
        return True, t("api.tiktok.client_ok", lang)
    if status >= 500:
        return False, t("api.http_fail", lang, status=status)
    detail = (desc or err or body[:160] or f"HTTP {status}").strip()
    return False, t("api.tiktok.probe_fail", lang, error=detail[:180])


def _test_youtube(lang: str) -> tuple[bool, str]:
    from i18n import t

    import youtube_oauth

    draft_check = _validate_draft_client_credentials(lang, "youtube")
    if draft_check is not None:
        return draft_check
    draft_ok = _finish_draft_credentials_test(lang, "youtube", "api.youtube.client_ok")
    if draft_ok is not None:
        return draft_ok

    oid = db.resolve_oauth_account_id("youtube")
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
        if token:
            try:
                profile = youtube_oauth.fetch_channel_profile(token)
                name = profile.get("display_name") or profile.get("username") or "ok"
                return True, t("api.youtube.token_ok", lang) + f" ({name})"
            except Exception as e:
                return False, _fail_message(lang, "youtube", str(e))

    raw = _creds("youtube")
    extra = str(raw.get("extra") or "").strip()
    api_key = extra
    if extra.startswith("{") or extra.startswith("1/"):
        api_key = ""
        if extra.startswith("{"):
            try:
                parsed = json.loads(extra)
                if isinstance(parsed, dict):
                    api_key = str(parsed.get("api_key") or parsed.get("key") or "").strip()
            except json.JSONDecodeError:
                api_key = ""
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or youtube_oauth.client_id()
    client_secret = (raw.get("client_secret") or "").strip() or youtube_oauth.client_secret()
    if token:
        status, body = _http(
            "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = _json_body(body)
        if status == 200 and "items" in data:
            return True, t("api.youtube.token_ok", lang)
        err = (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else body[:160]
        return False, _fail_message(lang, "youtube", str(err))
    if api_key:
        q = urllib.parse.urlencode({"part": "id", "id": "jNQXAC9IVRw", "key": api_key})
        status, body = _http(f"https://www.googleapis.com/youtube/v3/videos?{q}")
        data = _json_body(body)
        if status == 200:
            return True, t("api.youtube.key_ok", lang)
        err = (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else body[:160]
        return False, _fail_message(lang, "youtube", str(err))
    if client_id:
        return _client_probe_result(lang, "youtube", "api.youtube.client_ok", client_id, client_secret)
    return _need_keys(lang)


def _test_graph(
    url: str, token: str, lang: str, ok_key: str, platform_id: str = "facebook"
) -> tuple[bool, str]:
    from i18n import t

    if not token:
        return _need_keys(lang)
    status, body = _http(url + urllib.parse.urlencode({"access_token": token, "fields": "id,name"}))
    data = _json_body(body)
    if status == 200 and data.get("id"):
        name = data.get("name") or data.get("id")
        return True, t(ok_key, lang, name=name)
    err = (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else body[:160]
    return False, _fail_message(lang, platform_id, str(err))


def _test_instagram(lang: str) -> tuple[bool, str]:
    from i18n import t

    import instagram_oauth

    draft_check = _validate_draft_client_credentials(lang, "instagram")
    if draft_check is not None:
        return draft_check
    draft_ok = _finish_draft_credentials_test(lang, "instagram", "api.instagram.client_ok")
    if draft_ok is not None:
        return draft_ok

    oid = db.resolve_oauth_account_id("instagram")
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
        if token:
            try:
                profile = instagram_oauth.fetch_profile(token)
                name = profile.get("username") or profile.get("display_name") or "ok"
                return True, t("api.instagram.ok", lang, name=name)
            except Exception as e:
                return False, _fail_message(lang, "instagram", str(e))

    raw = _creds("instagram")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or instagram_oauth.client_id()
    client_secret = (raw.get("client_secret") or "").strip() or instagram_oauth.client_secret()
    if token:
        try:
            profile = instagram_oauth.fetch_profile(token)
            name = profile.get("username") or profile.get("display_name") or "ok"
            return True, t("api.instagram.ok", lang, name=name)
        except Exception:
            return _test_graph(
                "https://graph.facebook.com/v21.0/me?", token, lang, "api.instagram.ok", "instagram"
            )
    if client_id:
        return _client_probe_result(
            lang, "instagram", "api.instagram.client_ok", client_id, client_secret
        )
    return _need_keys(lang)


def _test_facebook(lang: str) -> tuple[bool, str]:
    from i18n import t

    import facebook_oauth

    draft_check = _validate_draft_client_credentials(lang, "facebook")
    if draft_check is not None:
        return draft_check
    draft_ok = _finish_draft_credentials_test(lang, "facebook", "api.facebook.client_ok")
    if draft_ok is not None:
        return draft_ok

    oid = db.resolve_oauth_account_id("facebook")
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
        if token:
            try:
                profile = facebook_oauth.fetch_page_profile(token)
                name = profile.get("display_name") or profile.get("open_id") or "ok"
                return True, t("api.facebook.ok", lang, name=name)
            except Exception as e:
                return False, _fail_message(lang, "facebook", str(e))

    raw = _creds("facebook")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or facebook_oauth.client_id()
    client_secret = (raw.get("client_secret") or "").strip() or facebook_oauth.client_secret()
    if token:
        return _test_graph("https://graph.facebook.com/v21.0/me?", token, lang, "api.facebook.ok", "facebook")
    if client_id:
        return _client_probe_result(
            lang, "facebook", "api.facebook.client_ok", client_id, client_secret
        )
    return _need_keys(lang)


def _test_x(lang: str) -> tuple[bool, str]:
    from i18n import t

    import x_oauth

    draft_check = _validate_draft_client_credentials(lang, "x")
    if draft_check is not None:
        return draft_check
    draft_ok = _finish_draft_credentials_test(lang, "x", "api.x.client_ok")
    if draft_ok is not None:
        return draft_ok

    oid = db.resolve_oauth_account_id("x")
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
        if token:
            try:
                profile = x_oauth.fetch_profile(token)
                name = profile.get("username") or profile.get("display_name") or "ok"
                return True, t("api.x.ok", lang, name=name)
            except Exception as e:
                return False, _fail_message(lang, "x", str(e))

    raw = _creds("x")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or x_oauth.client_id()
    client_secret = (raw.get("client_secret") or "").strip() or x_oauth.client_secret()
    if token:
        try:
            profile = x_oauth.fetch_profile(token)
            name = profile.get("username") or profile.get("display_name") or "ok"
            return True, t("api.x.ok", lang, name=name)
        except Exception as e:
            return False, _fail_message(lang, "x", str(e))
    if client_id:
        return _client_probe_result(lang, "x", "api.x.client_ok", client_id, client_secret)
    return _need_keys(lang)


def _test_dailymotion(lang: str) -> tuple[bool, str]:
    from i18n import t

    import dailymotion_oauth

    draft_check = _validate_draft_client_credentials(lang, "dailymotion")
    if draft_check is not None:
        return draft_check
    draft_ok = _finish_draft_credentials_test(lang, "dailymotion", "api.dailymotion.client_ok")
    if draft_ok is not None:
        return draft_ok

    oid = db.resolve_oauth_account_id("dailymotion")
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
        if token:
            try:
                profile = dailymotion_oauth.fetch_profile(token)
                name = profile.get("username") or profile.get("display_name") or "ok"
                return True, t("api.dailymotion.ok", lang, name=name)
            except Exception as e:
                return False, _fail_message(lang, "dailymotion", str(e))

    raw = _creds("dailymotion")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or dailymotion_oauth.client_id()
    secret = (raw.get("client_secret") or "").strip() or dailymotion_oauth.client_secret()
    if token:
        try:
            profile = dailymotion_oauth.fetch_profile(token)
            name = profile.get("username") or profile.get("display_name") or "ok"
            return True, t("api.dailymotion.ok", lang, name=name)
        except Exception as e:
            return False, _fail_message(lang, "dailymotion", str(e))
    if client_id:
        return _client_probe_result(
            lang, "dailymotion", "api.dailymotion.client_ok", client_id, secret
        )
    return _need_keys(lang)


def _test_bilibili(lang: str) -> tuple[bool, str]:
    from i18n import t

    import bilibili_oauth

    draft_check = _validate_draft_client_credentials(lang, "bilibili")
    if draft_check is not None:
        return draft_check
    draft_ok = _finish_draft_credentials_test(lang, "bilibili", "api.bilibili.client_ok")
    if draft_ok is not None:
        return draft_ok

    oid = db.resolve_oauth_account_id("bilibili")
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
        if token:
            try:
                profile = bilibili_oauth.fetch_profile(token)
                name = profile.get("username") or profile.get("display_name") or "ok"
                return True, t("api.bilibili.ok", lang, name=name)
            except Exception as e:
                return False, _fail_message(lang, "bilibili", str(e))

    raw = _creds("bilibili")
    client_id = (raw.get("client_id") or "").strip() or bilibili_oauth.client_id()
    secret = (raw.get("client_secret") or "").strip() or bilibili_oauth.client_secret()
    if client_id:
        return _client_probe_result(
            lang, "bilibili", "api.bilibili.client_ok", client_id, secret
        )
    return _need_keys(lang)


def _test_rumble(lang: str) -> tuple[bool, str]:
    from i18n import t

    import rumble_publish

    raw = _creds("rumble")
    token = (raw.get("access_token") or "").strip() or rumble_publish.access_token()
    channel = (raw.get("extra") or "").strip() or rumble_publish.channel_id()
    if not token:
        return _need_keys(lang)
    try:
        ok, detail = rumble_publish.probe_token(token=token, channel=channel)
    except Exception as e:
        return False, _fail_message(lang, "rumble", str(e))
    if ok:
        if channel:
            return True, t("api.rumble.ok", lang, channel=channel)
        return True, t("api.rumble.token_ok", lang)
    return False, _fail_message(lang, "rumble", detail)


def _test_snapchat(lang: str) -> tuple[bool, str]:
    from i18n import t

    import snapchat_oauth

    draft_check = _validate_draft_client_credentials(lang, "snapchat")
    if draft_check is not None:
        return draft_check
    draft_ok = _finish_draft_credentials_test(lang, "snapchat", "api.snapchat.client_ok")
    if draft_ok is not None:
        return draft_ok

    oid = db.resolve_oauth_account_id("snapchat")
    if oid:
        row = db.get_oauth_account_row(oid) or {}
        token = str(row.get("access_token") or "").strip()
        if token:
            try:
                profile = snapchat_oauth.fetch_profile(token)
                name = profile.get("username") or profile.get("display_name") or "ok"
                return True, t("api.snapchat.ok", lang, name=name)
            except Exception as e:
                return False, _fail_message(lang, "snapchat", str(e))

    raw = _creds("snapchat")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or snapchat_oauth.client_id()
    secret = (raw.get("client_secret") or "").strip() or snapchat_oauth.client_secret()
    if token:
        try:
            profile = snapchat_oauth.fetch_profile(token)
            name = profile.get("username") or profile.get("display_name") or "ok"
            return True, t("api.snapchat.ok", lang, name=name)
        except Exception as e:
            return False, _fail_message(lang, "snapchat", str(e))
    if client_id:
        return _client_probe_result(
            lang, "snapchat", "api.snapchat.client_ok", client_id, secret
        )
    return _need_keys(lang)


def _test_filehost(platform_id: str, lang: str) -> tuple[bool, str]:
    from i18n import t

    rows = db.list_filehost_accounts_public(platform_id)
    if not rows:
        return False, t("api.filehost.need_account", lang)
    raw = db.get_filehost_account_raw(str(rows[0].get("id") or ""))
    if not raw:
        return False, t("api.filehost.need_account", lang)
    ok, detail = filehost.probe_account(
        platform_id,
        str(raw.get("api_key") or ""),
        str(raw.get("extra") or ""),
    )
    if ok:
        return True, t("api.filehost.ok", lang, name=detail)
    return False, t("api.filehost.fail", lang, error=detail)


def _test_chain(platform_id: str, lang: str) -> tuple[bool, str]:
    from i18n import t

    rows = db.list_chain_accounts_public(platform_id)
    if not rows:
        return False, t("api.chain.need_account", lang)
    raw = db.get_chain_account_raw(str(rows[0].get("id") or ""))
    if not raw:
        return False, t("api.chain.need_account", lang)
    ok, detail = chain.probe_account(
        platform_id,
        str(raw.get("login") or ""),
        str(raw.get("secret") or ""),
        str(raw.get("extra") or ""),
        account_id=str(raw.get("id") or ""),
    )
    if ok:
        return True, t("api.chain.ok", lang, name=detail)
    return False, t("api.chain.fail", lang, error=detail)
