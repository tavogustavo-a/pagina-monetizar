"""Publish uploaded content to selected platforms (when API credentials allow)."""
from __future__ import annotations

from pathlib import Path

import db
import platforms
import tiktok_oauth
import tiktok_publish


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
) -> tuple[bool, str]:
    import proxy_util

    proxy_url = db.get_active_proxy_url_for_account(account_link_id)
    with proxy_util.using_proxy(proxy_url):
        return _publish_to_platform(
            platform_id,
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            tiktok_config_id=tiktok_config_id,
            account_link_id=account_link_id,
        )


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
    pid = (platform_id or "").strip()
    if pid not in platforms.PLATFORM_IDS:
        from i18n import t

        return False, t("api.unknown_platform", lang)

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
    return _publish_generic(pid, content_type=content_type, lang=lang)
