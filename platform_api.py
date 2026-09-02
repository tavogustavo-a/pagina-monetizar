"""Save and live-test platform API credentials."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import db
import platforms
import tiktok_oauth


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
    client_secret = (draft.get("client_secret") or "").strip()
    if client_secret:
        overlay["client_secret"] = client_secret
    access_token = (draft.get("access_token") or "").strip()
    if access_token:
        overlay["access_token"] = access_token
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
    try:
        if draft is not None:
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
    from i18n import t

    pid = (platform_id or "").strip()
    if pid not in platforms.PLATFORM_IDS:
        return {"ok": False, "message": t("api.unknown_platform", lang)}
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
    return test_platform(pid, lang, save_result=True)


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
        message = t("api.tiktok.token_fail", lang, error=str(e)[:180])
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
        message = t("api.youtube.fail", lang, error=str(e)[:180])
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
        message = t("api.instagram.fail", lang, error=str(e)[:180])
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
        message = t("api.facebook.fail", lang, error=str(e)[:180])
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
        message = t("api.x.fail", lang, error=str(e)[:180])
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
        message = t("api.dailymotion.fail", lang, error=str(e)[:180])
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
        message = t("api.bilibili.fail", lang, error=str(e)[:180])
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
        message = t("api.snapchat.fail", lang, error=str(e)[:180])
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


def _test_tiktok(lang: str) -> tuple[bool, str]:
    from i18n import t

    token = db.get_first_tiktok_access_token()
    if token:
        try:
            user = tiktok_oauth.fetch_user_profile(token)
            name = user.get("username") or user.get("display_name") or "ok"
            return True, t("api.tiktok.token_ok", lang, name=name)
        except Exception as e:
            return False, t("api.tiktok.token_fail", lang, error=str(e)[:180])

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
                return False, t("api.youtube.fail", lang, error=str(e)[:180])

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
    if token:
        status, body = _http(
            "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = _json_body(body)
        if status == 200 and "items" in data:
            return True, t("api.youtube.token_ok", lang)
        err = (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else body[:160]
        return False, t("api.youtube.fail", lang, error=str(err)[:180])
    if api_key:
        q = urllib.parse.urlencode({"part": "id", "id": "jNQXAC9IVRw", "key": api_key})
        status, body = _http(f"https://www.googleapis.com/youtube/v3/videos?{q}")
        data = _json_body(body)
        if status == 200:
            return True, t("api.youtube.key_ok", lang)
        err = (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else body[:160]
        return False, t("api.youtube.fail", lang, error=str(err)[:180])
    if client_id:
        return True, t("api.youtube.client_ok", lang)
    return _need_keys(lang)


def _test_graph(url: str, token: str, lang: str, ok_key: str) -> tuple[bool, str]:
    from i18n import t

    if not token:
        return _need_keys(lang)
    status, body = _http(url + urllib.parse.urlencode({"access_token": token, "fields": "id,name"}))
    data = _json_body(body)
    if status == 200 and data.get("id"):
        name = data.get("name") or data.get("id")
        return True, t(ok_key, lang, name=name)
    err = (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else body[:160]
    return False, t("api.graph_fail", lang, error=str(err)[:180])


def _test_instagram(lang: str) -> tuple[bool, str]:
    from i18n import t

    import instagram_oauth

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
                return False, t("api.instagram.fail", lang, error=str(e)[:180])

    raw = _creds("instagram")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or instagram_oauth.client_id()
    if token:
        try:
            profile = instagram_oauth.fetch_profile(token)
            name = profile.get("username") or profile.get("display_name") or "ok"
            return True, t("api.instagram.ok", lang, name=name)
        except Exception:
            return _test_graph(
                "https://graph.facebook.com/v21.0/me?", token, lang, "api.instagram.ok"
            )
    if client_id:
        return True, t("api.instagram.client_ok", lang)
    return _need_keys(lang)


def _test_facebook(lang: str) -> tuple[bool, str]:
    from i18n import t

    import facebook_oauth

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
                return False, t("api.facebook.fail", lang, error=str(e)[:180])

    raw = _creds("facebook")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or facebook_oauth.client_id()
    if token:
        return _test_graph("https://graph.facebook.com/v21.0/me?", token, lang, "api.facebook.ok")
    if client_id:
        return True, t("api.facebook.client_ok", lang)
    return _need_keys(lang)


def _test_x(lang: str) -> tuple[bool, str]:
    from i18n import t

    import x_oauth

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
                return False, t("api.x.fail", lang, error=str(e)[:180])

    raw = _creds("x")
    token = (raw.get("access_token") or "").strip()
    client_id = (raw.get("client_id") or "").strip() or x_oauth.client_id()
    if token:
        try:
            profile = x_oauth.fetch_profile(token)
            name = profile.get("username") or profile.get("display_name") or "ok"
            return True, t("api.x.ok", lang, name=name)
        except Exception as e:
            return False, t("api.x.fail", lang, error=str(e)[:180])
    if client_id:
        return True, t("api.x.client_ok", lang)
    return _need_keys(lang)


def _test_dailymotion(lang: str) -> tuple[bool, str]:
    from i18n import t

    import dailymotion_oauth

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
                return False, t("api.dailymotion.fail", lang, error=str(e)[:180])

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
            return False, t("api.dailymotion.fail", lang, error=str(e)[:180])
    if client_id and secret:
        return True, t("api.dailymotion.client_ok", lang)
    if client_id:
        return True, t("api.dailymotion.client_ok", lang)
    return _need_keys(lang)


def _test_bilibili(lang: str) -> tuple[bool, str]:
    from i18n import t

    import bilibili_oauth

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
                return False, t("api.bilibili.fail", lang, error=str(e)[:180])

    raw = _creds("bilibili")
    client_id = (raw.get("client_id") or "").strip() or bilibili_oauth.client_id()
    secret = (raw.get("client_secret") or "").strip() or bilibili_oauth.client_secret()
    if client_id and secret:
        return True, t("api.bilibili.client_ok", lang)
    if client_id:
        return True, t("api.bilibili.client_ok", lang)
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
        return False, t("api.rumble.fail", lang, error=str(e)[:180])
    if ok:
        if channel:
            return True, t("api.rumble.ok", lang, channel=channel)
        return True, t("api.rumble.token_ok", lang)
    return False, t("api.rumble.fail", lang, error=detail[:180])


def _test_snapchat(lang: str) -> tuple[bool, str]:
    from i18n import t

    import snapchat_oauth

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
                return False, t("api.snapchat.fail", lang, error=str(e)[:180])

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
            return False, t("api.snapchat.fail", lang, error=str(e)[:180])
    if client_id and secret:
        return True, t("api.snapchat.client_ok", lang)
    if client_id:
        return True, t("api.snapchat.client_ok", lang)
    return _need_keys(lang)
