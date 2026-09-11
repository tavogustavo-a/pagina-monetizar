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
    "dtube": "hive",
    "bilibili_tv": "browser",
    "bilibili_qr": "browser",
}

NO_TEST_IDS = frozenset({"odysee", "bilibili_tv", "bilibili_qr"})

SERVER_PLATFORM = {"bilibili_qr": "bilibili"}


def server_platform_id(platform_id: str) -> str:
    pid = (platform_id or "").strip()
    return SERVER_PLATFORM.get(pid, pid)


def extra_field(platform_id: str) -> str:
    return "channel" if (platform_id or "").strip() == "odysee" else ""


def probe_account(
    platform_id: str,
    login: str,
    secret: str,
    extra: str = "",
    account_id: str = "",
) -> tuple[bool, str]:
    pid = (platform_id or "").strip()
    if pid == "odysee":
        return odysee.probe_account(login, secret, extra)
    if pid == "dtube":
        return dtube.probe_account(login, secret, extra)
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
    if em and pw and "@" in em and len(pw) < 40:
        token, _ = odysee.signin(em, pw)
        return token
    if len(pw) >= 40:
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
        return False, t("pub.bilibili_tv.not_wired", lang)
    if pid == "bilibili_qr":
        return False, t("pub.bilibili_qr.not_wired", lang)
    return False, t("api.unknown_platform", lang)
