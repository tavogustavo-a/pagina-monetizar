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
    """Odysee guarda auth_token, no la contraseña. DTube guarda el posting WIF."""
    pid = (platform_id or "").strip()
    incoming = (secret or "").strip()
    prev = (previous or "").strip()
    if pid == "odysee":
        if incoming and "@" in (login or "") and len(incoming) < 40:
            token, _ = odysee.signin(login, incoming)
            return token
        return incoming or prev
    return incoming or prev


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
