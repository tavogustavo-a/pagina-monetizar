"""Odysee (LBRY), DTube (Hive), Bilibili.tv y sesión QR de Bilibili.com."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import bilibili_tv
import dtube
import odysee

QR_PLATFORM_IDS = frozenset({"bilibili_qr"})
PLATFORM_IDS = frozenset({"odysee", "dtube", "bilibili_tv", "bilibili_qr"})

API_KIND = {
    "odysee": "lbry",
    "dtube": "browser",
    "bilibili_tv": "browser",
    "bilibili_qr": "browser",
}

NO_TEST_IDS = frozenset({"odysee", "dtube", "bilibili_tv", "bilibili_qr"})

SERVER_PLATFORM = {"bilibili_qr": "bilibili"}


def server_platform_id(platform_id: str) -> str:
    pid = (platform_id or "").strip()
    return SERVER_PLATFORM.get(pid, pid)


def extra_field(platform_id: str) -> str:
    return "channel" if (platform_id or "").strip() == "odysee" else ""


def _account_proxy(platform_id: str, account_id: str, link_name: str = ""):
    """Contexto con el proxy vinculado a la cuenta (o sin proxy si no hay)."""
    import db
    import proxy_util

    proxy_url = ""
    try:
        proxy_url = db.get_active_proxy_url_for_chain(account_id, link_name)
    except Exception:
        proxy_url = ""
    return proxy_util.using_proxy(proxy_url)


def probe_account(
    platform_id: str,
    login: str,
    secret: str,
    extra: str = "",
    account_id: str = "",
    link_name: str = "",
) -> tuple[bool, str]:
    pid = (platform_id or "").strip()
    if pid == "odysee":
        with _account_proxy(pid, account_id, link_name) as proxy_url:
            ok, detail = odysee.probe_account(login, secret, extra)
            if ok:
                return True, detail
            if not (proxy_url or "").strip():
                return False, "need_proxy"
            return False, "proxy_rejected"
    if pid == "dtube":
        with _account_proxy(pid, account_id, link_name):
            return dtube.probe_account(login, secret, extra, account_id=account_id)
    if pid == "bilibili_tv":
        return bilibili_tv.probe_account(login, secret, extra, account_id=account_id)
    return False, "unknown_platform"


def persist_secret(platform_id: str, login: str, secret: str, previous: str = "") -> str:
    """Odysee guarda la contraseña; el auth_token va en chain_accounts.auth_token."""
    incoming = (secret or "").strip()
    prev = (previous or "").strip()
    return incoming or prev


def odysee_auth_token_for_save(login: str, secret: str, previous_token: str = "") -> str:
    em = (login or "").strip()
    pw = (secret or "").strip()
    prev = (previous_token or "").strip()
    if em and pw and "@" in em:
        try:
            token, _ = odysee.signin(em, pw)
            return token
        except odysee.OdyseeError:
            if odysee._try_cached_token(pw):
                return pw
            raise
    if odysee._try_cached_token(pw):
        return pw
    return prev


def publish_video(
    *,
    platform_id: str,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account: dict[str, Any],
) -> tuple[bool, str]:
    pid = (platform_id or "").strip()
    if pid == "odysee":
        return odysee.publish_video(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account=account,
        )
    if pid == "dtube":
        return dtube.publish_video(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account=account,
        )
    from i18n import t

    if pid == "bilibili_tv":
        return bilibili_tv.publish_video(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account=account,
        )
    if pid == "bilibili_qr":
        import bilibili_web

        return bilibili_web.publish_video(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account=account,
        )
    return False, t("api.unknown_platform", lang)
