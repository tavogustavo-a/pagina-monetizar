"""Publish uploaded content to selected platforms (when API credentials allow)."""
from __future__ import annotations

from pathlib import Path

import db
import platforms
import tiktok_oauth
import tiktok_publish
import vmos
import filehost
import chain

# Título visible en la red. El resto (TikTok, IG, X, Snapchat, hosts) va solo con el archivo.
TITLE_PLATFORMS = frozenset(
    {
        "youtube",
        "facebook",
        "dailymotion",
        "bilibili",
        "bilibili_tv",
        "rumble",
        "odysee",
        "dtube",
    }
)


def texts_for_platform(platform_id: str, title: str, description: str) -> tuple[str, str]:
    """YouTube es la única con descripción (opcional). El título solo se envía donde la API lo pide."""
    pid = (platform_id or "").strip()
    label = str(title or "").strip()
    desc = str(description or "").strip()
    if pid == "youtube":
        return label, desc
    if pid in TITLE_PLATFORMS:
        return label, ""
    return "", ""


def _has_generic_creds(raw: dict) -> bool:
    return bool(
        (raw.get("client_id") or "").strip()
        or (raw.get("client_secret") or "").strip()
        or (raw.get("access_token") or "").strip()
    )


def _publish_tiktok(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    tiktok_config_id: str | None,
    account_link_id: str | None,
) -> tuple[bool, str]:
    from i18n import t

    if content_type == "photo":
        return False, t("pub.fail_no_photo", lang)

    if not tiktok_oauth.oauth_configured() and not _has_generic_creds(
        db.get_platform_credentials_raw("tiktok") or {}
    ):
        return False, t("pub.fail_no_creds", lang)

    return tiktok_publish.publish_video(
        file_path=file_path,
        title=title,
        description=description,
        lang=lang,
        config_id=tiktok_config_id,
        account_link_id=account_link_id,
    )


def _publish_youtube(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import youtube_publish

    return youtube_publish.publish_video(
        file_path=file_path,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_instagram(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import instagram_publish

    return instagram_publish.publish_media(
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_facebook(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import facebook_publish

    return facebook_publish.publish_media(
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_x(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import x_publish

    return x_publish.publish_media(
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_dailymotion(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import dailymotion_publish

    return dailymotion_publish.publish_video(
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_bilibili(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import bilibili_publish

    oauth_id = db.resolve_oauth_account_id("bilibili", account_link_id=account_link_id)
    if oauth_id:
        return bilibili_publish.publish_video(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    qr = db.resolve_chain_account_for_publish("bilibili", account_link_id)
    if qr:
        from i18n import t

        return False, t("pub.bilibili_qr.not_wired", lang)
    return bilibili_publish.publish_video(
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_rumble(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import rumble_publish

    return rumble_publish.publish_video(
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_snapchat(
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    import snapchat_publish

    return snapchat_publish.publish_video(
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        account_link_id=account_link_id,
    )


def _publish_generic(
    platform_id: str,
    *,
    content_type: str,
    lang: str,
) -> tuple[bool, str]:
    from i18n import t

    p = platforms.get_platform(platform_id)
    if not p:
        return False, t("api.unknown_platform", lang)

    cap_key = "video" if content_type == "video" else "photo"
    cap = str(p.get(cap_key, "no"))
    if cap == "no":
        return False, t("pub.fail_not_supported", lang, kind=cap_key)

    raw = db.get_platform_credentials_raw(platform_id) or {}
    if not _has_generic_creds(raw):
        return False, t("pub.fail_no_creds", lang)

    if raw.get("last_test_ok") is not True:
        return False, t("pub.fail_api_test", lang)

    return False, t("pub.fail_no_api", lang)


def publish_to_platform(
    platform_id: str,
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str = "es",
    tiktok_config_id: str | None = None,
    account_link_id: str | None = None,
    x_use_funding: bool = False,
) -> tuple[str, str]:
    import proxy_util
    import publish_pending
    from i18n import t

    publish_pending.clear()
    pid = (platform_id or "").strip()
    if not platforms.is_publish_enabled(pid):
        return "fail", t("pub.platform_paused", lang, platform=t(f"platform.{pid}", lang))
    if not platforms.supports_content(pid, content_type):
        kind = "photo" if (content_type or "").strip().lower() == "photo" else "video"
        return "skipped", t(
            "pub.skipped_unsupported",
            lang,
            platform=t(f"platform.{pid}", lang),
            kind=t(f"pub.kind.{kind}", lang),
        )

    kwargs = dict(
        platform_id=platform_id,
        file_path=file_path,
        content_type=content_type,
        title=title,
        description=description,
        lang=lang,
        tiktok_config_id=tiktok_config_id,
        account_link_id=account_link_id,
    )
    name = db.get_account_link_name(account_link_id) if account_link_id else ""
    x_mode = "auto"
    if pid == "x":
        x_mode = "funding" if x_use_funding else "own"
        if x_mode == "funding" and not db.resolve_active_x_funding_source():
            from i18n import t as _t

            return "fail", _t("pub.x.need_funding_api", lang)
    with db.using_credentials_account(name):
        with db.using_x_app_mode(x_mode):
            if pid in vmos.PLATFORM_IDS and db.resolve_vmos_account_for_publish(
                pid, account_link_id
            ):
                ok, message = _publish_to_platform(**kwargs)
                return _final_status(ok), message

            proxy_url = db.get_active_proxy_url_for_account(account_link_id)
            with proxy_util.using_proxy(proxy_url):
                ok, message = _publish_to_platform(**kwargs)
                return _final_status(ok), message


def _final_status(ok: bool) -> str:
    """La plataforma aceptó el envío pero sigue revisándolo → estado 'pending'."""
    import publish_pending

    if not ok:
        publish_pending.clear()
        return "fail"
    return "pending" if publish_pending.has_pending() else "ok"


def _publish_to_platform(
    platform_id: str,
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str = "es",
    tiktok_config_id: str | None = None,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    from i18n import t

    pid = (platform_id or "").strip()
    if pid not in platforms.PLATFORM_IDS:
        return False, t("api.unknown_platform", lang)

    send_path = Path(file_path)
    temps: list[Path] = []
    try:
        if pid == "snapchat" and content_type != "photo":
            import snapchat_publish

            try:
                send_path, snap_tmp = snapchat_publish.clip_for_snapchat(
                    send_path, content_type
                )
            except ValueError:
                return False, t("pub.snapchat.trim_fail", lang)
            if snap_tmp:
                temps.append(snap_tmp)

        import video_compress

        kind = "photo" if content_type == "photo" else "video"
        try:
            send_path, size_tmp = video_compress.ensure_under_bytes(
                send_path,
                video_compress.max_bytes_for(pid, content_type),
                kind=kind,
            )
        except ValueError:
            return False, t("pub.flash.compress_fail", lang)
        if size_tmp:
            temps.append(size_tmp)

        send_title, send_desc = texts_for_platform(pid, title, description)
        return _dispatch_platform(
            pid,
            file_path=send_path,
            content_type=content_type,
            title=send_title,
            description=send_desc,
            lang=lang,
            tiktok_config_id=tiktok_config_id,
            account_link_id=account_link_id,
        )
    finally:
        for tmp in temps:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass


def _dispatch_platform(
    pid: str,
    *,
    file_path: Path,
    content_type: str,
    title: str,
    description: str,
    lang: str,
    tiktok_config_id: str | None,
    account_link_id: str | None,
) -> tuple[bool, str]:
    if pid in vmos.PLATFORM_IDS:
        vmos_row = db.resolve_vmos_account_for_publish(pid, account_link_id)
        if vmos_row:
            import vmos_publish

            return vmos_publish.publish(
                file_path=file_path,
                title=title,
                description=description,
                lang=lang,
                account=vmos_row,
            )

    if pid == "tiktok":
        return _publish_tiktok(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            tiktok_config_id=tiktok_config_id,
            account_link_id=account_link_id,
        )
    if pid == "youtube":
        return _publish_youtube(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid == "instagram":
        return _publish_instagram(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid == "facebook":
        return _publish_facebook(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid == "x":
        return _publish_x(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid == "dailymotion":
        return _publish_dailymotion(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid == "bilibili":
        return _publish_bilibili(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid == "rumble":
        return _publish_rumble(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid == "snapchat":
        return _publish_snapchat(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account_link_id=account_link_id,
        )
    if pid in filehost.PLATFORM_IDS:
        row = db.resolve_filehost_account_for_publish(pid, account_link_id)
        if not row:
            from i18n import t

            return False, t("pub.filehost.no_key", lang)
        return filehost.publish_video(
            platform_id=pid,
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account=row,
        )
    if pid in chain.PLATFORM_IDS:
        row = db.resolve_chain_account_for_publish(pid, account_link_id)
        if not row:
            from i18n import t

            return False, t("pub.chain.no_account", lang)
        return chain.publish_video(
            platform_id=pid,
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account=row,
        )
    if pid == "threads":
        from i18n import t

        return False, t("pub.fail_vmos_pending", lang)
    return _publish_generic(pid, content_type=content_type, lang=lang)
