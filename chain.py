"""Odysee (LBRY) y DTube (Hive): cuentas en Servidores, no hosts PPV."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import dtube
import odysee

PLATFORM_IDS = frozenset({"odysee", "dtube"})

API_KIND = {"odysee": "lbry", "dtube": "hive"}


def extra_field(platform_id: str) -> str:
    return "channel" if (platform_id or "").strip() == "odysee" else ""


def probe_account(platform_id: str, login: str, secret: str, extra: str = "") -> tuple[bool, str]:
    pid = (platform_id or "").strip()
    if pid == "odysee":
        return odysee.probe_account(login, secret, extra)
    if pid == "dtube":
        return dtube.probe_account(login, secret, extra)
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

    return False, t("api.unknown_platform", lang)
