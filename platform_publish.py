"""Publish uploaded content to selected platforms (when API credentials allow)."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import threading
import time
from pathlib import Path

import db
import platforms
import tiktok_oauth
import tiktok_publish
import vmos
import filehost
import chain

# Un envío por proxy (misma IP = un hueco). Redes de navegador usan proxy fijo.
_PUBLISH_GATE_WAIT_S = 45 * 60
_MAX_PROXY_PARALLEL = 8
_DIRECT_SLOT = "__direct__"
_slot_locks: dict[str, threading.RLock] = {}
_slot_guard = threading.Lock()
_slot_rr = 0
_pub_log_id: ContextVar[str] = ContextVar("pub_log_id", default="")
_pub_log_lang: ContextVar[str] = ContextVar("pub_log_lang", default="es")

BROWSER_STICKY_PLATFORMS = frozenset(
    {"bilibili", "bilibili_tv", "odysee", "dtube"}
)

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
    if pid in {"bilibili", "bilibili_tv"}:
        return label, desc
    if pid in TITLE_PLATFORMS:
        return label, ""
    return "", ""


def is_browser_sticky_platform(platform_id: str) -> bool:
    pid = platforms.canonical_platform_id(str(platform_id or "").strip())
    return pid in BROWSER_STICKY_PLATFORMS or str(platform_id or "").strip() == "bilibili_qr"


def bind_publish_log(log_id: str, lang: str) -> tuple[object, object]:
    return _pub_log_id.set(str(log_id or "")), _pub_log_lang.set(lang or "es")


def reset_publish_log(tokens: tuple[object, object] | None) -> None:
    if not tokens:
        return
    try:
        _pub_log_id.reset(tokens[0])  # type: ignore[arg-type]
        _pub_log_lang.reset(tokens[1])  # type: ignore[arg-type]
    except Exception:
        pass


def note_waiting_browser() -> None:
    lid = (_pub_log_id.get() or "").strip()
    if not lid:
        return
    from i18n import t

    db.update_publication_log_entry(
        lid,
        status="pending",
        message=t("pub.waiting_browser", _pub_log_lang.get() or "es"),
    )


def _slot_key(proxy: dict) -> str:
    ip = str(proxy.get("last_check_ip") or "").strip()
    if ip:
        return f"ip:{ip.lower()}"
    return f"id:{str(proxy.get('id') or '').strip()}"


def _unique_slots(proxies: list[dict]) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for item in proxies:
        key = _slot_key(item)
        if not key or key in seen:
            continue
        url = str(item.get("url") or "").strip()
        pid = str(item.get("id") or "").strip()
        if not url or not pid:
            continue
        seen.add(key)
        out.append((key, url, pid))
    return out


def publish_parallelism(account_link_id: str | None) -> int:
    """Cuántas redes API a la vez: 1 por IP/proxy distinto (mínimo 1)."""
    slots = _unique_slots(db.list_active_proxies_for_account(account_link_id))
    return max(1, min(_MAX_PROXY_PARALLEL, len(slots) if slots else 1))


def _lock_for_slot(key: str) -> threading.RLock:
    with _slot_guard:
        lock = _slot_locks.get(key)
        if lock is None:
            lock = threading.RLock()
            _slot_locks[key] = lock
        return lock


def _key_for_proxy_url(proxy_url: str) -> str:
    """Misma clave que acquire_publish_slot (IP o id), no otra por URL."""
    url = (proxy_url or "").strip()
    if not url:
        return _DIRECT_SLOT
    try:
        items = db.list_all_active_proxies()
    except Exception:
        items = []
    for item in items:
        if str(item.get("url") or "").strip() == url:
            return _slot_key(item)
    return f"url:{url}"


def _candidates_for_platform(
    account_link_id: str | None, platform_id: str
) -> list[tuple[str, str]]:
    proxies = db.list_active_proxies_for_account(account_link_id)
    if not proxies:
        return [(_DIRECT_SLOT, "")]
    if is_browser_sticky_platform(platform_id):
        sticky = db.ensure_sticky_proxy(account_link_id)
        if sticky:
            return [(_slot_key(sticky), str(sticky.get("url") or ""))]
    slots = _unique_slots(proxies)[:_MAX_PROXY_PARALLEL]
    pid = platforms.canonical_platform_id(str(platform_id or "").strip())
    ranked: list[tuple[int, str, str]] = []
    for key, url, proxy_id in slots:
        check = db.proxy_platform_check_ok(proxy_id, pid) if pid else None
        rank = 0 if check is True else (1 if check is None else 2)
        ranked.append((rank, key, url))
    ranked.sort(key=lambda row: row[0])
    if any(row[0] < 2 for row in ranked):
        ranked = [row for row in ranked if row[0] < 2]
    return [(key, url) for _, key, url in ranked]


def acquire_publish_slot(
    account_link_id: str | None,
    *,
    platform_id: str = "",
    timeout: float = _PUBLISH_GATE_WAIT_S,
) -> tuple[str | None, threading.RLock | None]:
    """Toma un proxy libre. Navegador = sticky; APIs = round-robin por IP."""
    global _slot_rr
    keys = _candidates_for_platform(account_link_id, platform_id)
    with _slot_guard:
        start = _slot_rr
        _slot_rr += 1
    n = len(keys)
    deadline = time.monotonic() + max(0.1, float(timeout))
    while True:
        for i in range(n):
            key, url = keys[(start + i) % n]
            lock = _lock_for_slot(key)
            if lock.acquire(blocking=False):
                return url, lock
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None, None
        time.sleep(min(0.25, remaining))


@contextmanager
def hold_named_proxy(proxy_url: str, *, timeout: float = 15.0):
    """Candado del mismo hueco que las subidas (keep-alive / test). Reentrante."""
    url = (proxy_url or "").strip()
    if not url:
        yield True
        return
    lock = _lock_for_slot(_key_for_proxy_url(url))
    if not lock.acquire(timeout=timeout):
        yield False
        return
    try:
        yield True
    finally:
        lock.release()


@contextmanager
def using_held_proxy(proxy_url: str, *, timeout: float = 15.0):
    """Hueco + using_proxy. Si el hueco está ocupado, igual usa el proxy (tras esperar)."""
    import proxy_util

    with hold_named_proxy(proxy_url, timeout=timeout):
        with proxy_util.using_proxy(proxy_url) as u:
            yield u


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
        import bilibili_web

        return bilibili_web.publish_video(
            file_path=file_path,
            content_type=content_type,
            title=title,
            description=description,
            lang=lang,
            account=qr,
        )
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
        x_mode = "own" if db.account_wants_own_x_api(account_link_id) else "funding"
        if x_mode == "funding" and not db.resolve_active_x_funding_source():
            from i18n import t as _t

            return "fail", _t("pub.x.need_funding_api", lang)
    if pid in vmos.PLATFORM_IDS and db.resolve_vmos_account_for_publish(
        pid, account_link_id
    ):
        return _publish_to_platform_locked(
            pid,
            lang=lang,
            name=name,
            x_mode=x_mode,
            kwargs=kwargs,
            account_link_id=account_link_id,
            proxy_url="",
        )
    proxy_url, slot_lock = acquire_publish_slot(
        account_link_id, platform_id=pid
    )
    if slot_lock is None:
        return "fail", t("pub.publish_busy", lang)
    try:
        return _publish_to_platform_locked(
            pid,
            lang=lang,
            name=name,
            x_mode=x_mode,
            kwargs=kwargs,
            account_link_id=account_link_id,
            proxy_url=proxy_url or "",
        )
    finally:
        slot_lock.release()


def _publish_to_platform_locked(
    pid: str,
    *,
    lang: str,
    name: str,
    x_mode: str,
    kwargs: dict,
    account_link_id: str | None,
    proxy_url: str = "",
) -> tuple[str, str]:
    import proxy_util
    from i18n import t

    with db.using_credentials_account(name):
        with db.using_x_app_mode(x_mode):
            if pid in vmos.PLATFORM_IDS and db.resolve_vmos_account_for_publish(
                pid, account_link_id
            ):
                ok, message = _publish_to_platform(**kwargs)
                return _final_status(ok), message

            with proxy_util.using_proxy(proxy_url):
                ping_ok = True
                if (proxy_url or "").strip():
                    ping_ok = proxy_util.ping_platform(pid, attempts=2)
                try:
                    ok, message = proxy_util.run_upload_retry(
                        lambda: _publish_to_platform(**kwargs),
                        attempts=2,
                    )
                except Exception as e:
                    if not ping_ok:
                        return "fail", t(
                            "pub.proxy.platform_unreachable",
                            lang,
                            platform=t(f"platform.{pid}", lang),
                        )
                    nice = proxy_util.humanize_network_failure(e, lang)
                    return "fail", nice or t("pub.publish_crash", lang, error=str(e)[:180])
                if not ok and not ping_ok:
                    return "fail", t(
                        "pub.proxy.platform_unreachable",
                        lang,
                        platform=t(f"platform.{pid}", lang),
                    )
                if not ok:
                    nice = proxy_util.humanize_network_failure(message, lang)
                    if nice and proxy_util.classify_proxy_error(message) in {
                        "timeout",
                        "reset",
                        "refused",
                        "unreachable",
                        "auth",
                        "ssl",
                        "socks_fail",
                        "host_unresolved",
                    }:
                        message = nice
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
        try:
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
        except Exception as e:
            import proxy_util

            nice = proxy_util.humanize_network_failure(e, lang)
            return False, nice or t("pub.publish_crash", lang, error=str(e)[:180])
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
