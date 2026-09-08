"""Supported publishing platforms (servers) shown in the admin panel."""
from __future__ import annotations

from typing import Any

# video / photo / comment: "yes" | "limited" | "no"
# Capacidades = lo que este panel publica de verdad (no lo que la red podría hacer).
# comment: "no" — las APIs de comentarios no están cableadas; el inbox del panel es local.
PLATFORMS: list[dict[str, Any]] = [
    {
        "id": "tiktok",
        "icon": "🎵",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "youtube",
        "icon": "▶️",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "instagram",
        "icon": "📷",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "limited",
        "photo": "yes",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "facebook",
        "icon": "📘",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "yes",
        "photo": "yes",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "threads",
        "icon": "🧵",
        "has_api": True,
        "api_kind": "vmos",
        "token_renewal": "manual",
        "video": "limited",
        "photo": "yes",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "x",
        "icon": "✖️",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "limited",
        "photo": "yes",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "dailymotion",
        "icon": "🎬",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "bilibili",
        "icon": "📺",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "rumble",
        "icon": "🟢",
        "has_api": True,
        "api_kind": "partner",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": ("access_token", "extra"),
    },
    {
        "id": "snapchat",
        "icon": "👻",
        "has_api": True,
        "api_kind": "oauth",
        "token_renewal": "auto",
        "video": "limited",
        "photo": "limited",
        "comment": "no",
        "fields": ("client_id", "client_secret", "extra"),
    },
    {
        "id": "odysee",
        "icon": "🟠",
        "has_api": True,
        "api_kind": "lbry",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "dtube",
        "icon": "⛓️",
        "has_api": True,
        "api_kind": "hive",
        "token_renewal": "manual",
        # Pausado y oculto en Servidores/Publicaciones. El módulo dtube.py
        # sigue montado: para reactivar pon ui_visible y publish_enabled en True.
        "publish_enabled": False,
        "ui_visible": False,
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "doodstream",
        "icon": "🎬",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "streamwish",
        "icon": "▶️",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "filemoon",
        "icon": "🌙",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "mixdrop",
        "icon": "💧",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "streamtape",
        "icon": "📼",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "voe",
        "icon": "🔷",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "vidoza",
        "icon": "🎞️",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "lulustream",
        "icon": "🟣",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "loadvid",
        "icon": "📥",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "vidsonic",
        "icon": "🔊",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "flyfile",
        "icon": "✈️",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
    {
        "id": "venvo",
        "icon": "🟣",
        "has_api": True,
        "api_kind": "filehost",
        "token_renewal": "manual",
        "video": "yes",
        "photo": "no",
        "comment": "no",
        "fields": (),
    },
]

PLATFORM_IDS = {str(p["id"]) for p in PLATFORMS}

STAT_KEYS = ("views", "likes", "comments", "videos", "shares", "followers")

# Columnas de estadísticas del panel (conteos locales; no hay recolector de APIs).
_LOCAL_STATS = {
    "views": True,
    "likes": True,
    "comments": True,
    "videos": True,
    "shares": False,
    "followers": False,
}
PLATFORM_STATS: dict[str, dict[str, bool]] = {
    "tiktok": {**_LOCAL_STATS, "shares": True},
    "youtube": dict(_LOCAL_STATS),
    "instagram": dict(_LOCAL_STATS),
    "facebook": dict(_LOCAL_STATS),
    "threads": dict(_LOCAL_STATS),
    "x": {**_LOCAL_STATS, "shares": True},
    "dailymotion": dict(_LOCAL_STATS),
    "bilibili": dict(_LOCAL_STATS),
    "rumble": {**_LOCAL_STATS, "comments": False},
    "snapchat": {**_LOCAL_STATS, "likes": False, "comments": False},
    "doodstream": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "streamwish": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "filemoon": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "mixdrop": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "streamtape": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "voe": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "vidoza": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "lulustream": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "loadvid": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "vidsonic": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "flyfile": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
    "venvo": {**_LOCAL_STATS, "comments": False, "likes": False, "shares": False},
}


def visible_stats_metrics(platform_id: str | None) -> dict[str, bool]:
    """Métricas visibles para 'all' (unión) o una plataforma concreta."""
    if not platform_id or platform_id == "all":
        merged = {k: False for k in STAT_KEYS}
        for p in PLATFORMS:
            pid = str(p["id"])
            sm = PLATFORM_STATS.get(pid, {})
            for k in STAT_KEYS:
                if sm.get(k, True):
                    merged[k] = True
        return merged
    sm = PLATFORM_STATS.get(platform_id, {})
    return {k: sm.get(k, True) for k in STAT_KEYS}


def _cap_yes(key: str, platform: dict[str, Any]) -> bool:
    return str(platform.get(key, "no")) in ("yes", "limited")


def pub_capabilities(platform_id: str | None) -> dict[str, bool]:
    """Secciones visibles en Publicaciones según plataforma."""
    keys = ("video", "photo", "comment")
    if not platform_id or platform_id == "all":
        merged = {k: False for k in keys}
        for p in PLATFORMS:
            for k in keys:
                if _cap_yes(k, p):
                    merged[k] = True
        return merged
    p = get_platform(platform_id)
    if not p:
        return {k: False for k in keys}
    return {k: _cap_yes(k, p) for k in keys}


def get_platform(pid: str) -> dict[str, Any] | None:
    for p in PLATFORMS:
        if p["id"] == pid:
            return p
    return None


def is_publish_enabled(platform_id: str) -> bool:
    """False = código montado pero no se publica (p. ej. uploader de DTube caído)."""
    p = get_platform(platform_id)
    if not p:
        return False
    return bool(p.get("publish_enabled", True))


def is_ui_visible(platform_id: str) -> bool:
    """False = no aparece en Servidores, extractor, condiciones ni publicaciones."""
    p = get_platform(platform_id)
    if not p:
        return False
    return bool(p.get("ui_visible", True))


def platform_select_label(platform: dict[str, Any]) -> str:
    icon = str(platform.get("icon") or "").strip()
    name = str(platform.get("name") or "").strip()
    if not icon:
        return name
    if icon.casefold() == name.casefold():
        return name
    return f"{icon}\u00a0{name}"


def _field_label(lang: str, prefix: str, platform_id: str, fallback_key: str) -> str:
    from i18n import MESSAGES, t

    specific = f"{prefix}.{platform_id}"
    if specific in MESSAGES:
        return t(specific, lang)
    return t(fallback_key, lang)


def platform_list(lang: str, *, include_hidden: bool = False) -> list[dict[str, Any]]:
    from i18n import t

    out: list[dict[str, Any]] = []
    for p in PLATFORMS:
        pid = str(p["id"])
        ui_visible = bool(p.get("ui_visible", True))
        if not include_hidden and not ui_visible:
            continue
        out.append(
            {
                "id": pid,
                "icon": str(p["icon"]),
                "has_api": bool(p["has_api"]),
                "name": t(f"platform.{pid}", lang),
                "video": str(p["video"]),
                "photo": str(p["photo"]),
                "comment": str(p["comment"]),
                "fields": list(p["fields"]),
                "publish_enabled": bool(p.get("publish_enabled", True)),
                "ui_visible": ui_visible,
                "note": t(f"limits.note.{pid}", lang),
                "label_client_id": _field_label(lang, "api.field.client_id", pid, "api.field.client_id"),
                "label_client_secret": _field_label(
                    lang, "api.field.client_secret", pid, "api.field.client_secret"
                ),
            }
        )
    return out


def _vmos_platform_ids() -> frozenset[str]:
    import vmos

    return vmos.PLATFORM_IDS


def _vmos_apidoc_row(lang: str) -> dict[str, Any]:
    from i18n import MESSAGES, t

    steps: list[str] = []
    n = 1
    while f"apidoc.vmos.step{n}" in MESSAGES:
        steps.append(t(f"apidoc.vmos.step{n}", lang))
        n += 1
    return {
        "id": "vmos",
        "icon": "☁",
        "name": t("apidoc.vmos.name", lang),
        "api_kind": "vmos",
        "api_label": t("apidoc.api.vmos", lang),
        "video": "yes",
        "photo": "yes",
        "token": "none",
        "token_label": t("apidoc.token.none", lang),
        "setup_steps": steps,
        "extra": t("apidoc.vmos.extra", lang),
    }


def _vmos_conditions_row(lang: str) -> dict[str, Any]:
    from i18n import t

    return {
        "id": "vmos",
        "icon": "☁",
        "name": t("apidoc.vmos.name", lang),
        "api_kind": "vmos",
        "api_label": t("apidoc.api.vmos", lang),
        "cap": t("cond.vmos.cap", lang),
        "window": t("cond.vmos.window", lang),
        "rate": t("cond.vmos.rate", lang),
        "safe": t("cond.vmos.safe", lang),
        "detail": t("cond.vmos.detail", lang),
    }


def api_document_rows(lang: str) -> list[dict[str, Any]]:
    """Filas de la página API Documento (pasos, media y renovación de token)."""
    from i18n import MESSAGES, t

    vmos_ids = _vmos_platform_ids()
    rows: list[dict[str, Any]] = [_vmos_apidoc_row(lang)]
    for p in PLATFORMS:
        if not bool(p.get("ui_visible", True)):
            continue
        pid = str(p["id"])
        steps: list[str] = []
        n = 1
        while f"apidoc.{pid}.step{n}" in MESSAGES:
            steps.append(t(f"apidoc.{pid}.step{n}", lang))
            n += 1
        extra_key = f"apidoc.{pid}.extra"
        extra = t(extra_key, lang) if extra_key in MESSAGES else ""
        kind = str(p.get("api_kind") or ("oauth" if p.get("has_api") else "none"))
        if kind == "filehost":
            if not steps:
                n = 1
                while f"apidoc.filehost.step{n}" in MESSAGES:
                    steps.append(
                        t(f"apidoc.filehost.step{n}", lang, name=t(f"platform.{pid}", lang))
                    )
                    n += 1
            extra = extra or t("apidoc.filehost.extra", lang)
            import filehost as filehost_mod

            if pid in filehost_mod.TRIAL_PAYOUT_IDS:
                trial = t("apidoc.filehost.trial", lang)
                extra = f"{extra} {trial}".strip()
        if pid in vmos_ids:
            alt = t("apidoc.vmos_alt", lang)
            extra = f"{extra} {alt}".strip() if extra else alt
        token = str(p.get("token_renewal") or "manual")
        rows.append(
            {
                "id": pid,
                "icon": str(p.get("icon") or ""),
                "name": t(f"platform.{pid}", lang),
                "api_kind": kind,
                "api_label": t(f"apidoc.api.{kind}", lang),
                "video": str(p.get("video") or "no"),
                "photo": str(p.get("photo") or "no"),
                "token": token,
                "token_label": t(f"apidoc.token.{token}", lang),
                "setup_steps": steps,
                "extra": extra,
            }
        )
    return rows


def server_conditions_rows(lang: str) -> list[dict[str, Any]]:
    """Límites reales de cada API: cuota, ventana de tiempo y uso seguro."""
    from i18n import t

    vmos_ids = _vmos_platform_ids()
    rows: list[dict[str, Any]] = [_vmos_conditions_row(lang)]
    for p in PLATFORMS:
        if not bool(p.get("ui_visible", True)):
            continue
        pid = str(p["id"])
        kind = str(p.get("api_kind") or ("oauth" if p.get("has_api") else "none"))
        if kind == "filehost":
            cap = t("cond.filehost.cap", lang)
            window = t("cond.filehost.window", lang)
            rate = t("cond.filehost.rate", lang)
            safe = t("cond.filehost.safe", lang)
            detail = t("cond.filehost.detail", lang, name=t(f"platform.{pid}", lang))
            import filehost as filehost_mod

            if pid in filehost_mod.TRIAL_PAYOUT_IDS:
                detail = f"{detail} {t('cond.filehost.trial', lang)}".strip()
        else:
            cap = t(f"cond.{pid}.cap", lang)
            window = t(f"cond.{pid}.window", lang)
            rate = t(f"cond.{pid}.rate", lang)
            safe = t(f"cond.{pid}.safe", lang)
            detail = t(f"cond.{pid}.detail", lang)
        if pid in vmos_ids:
            detail = f"{detail} {t('cond.vmos_alt', lang)}".strip()
        rows.append(
            {
                "id": pid,
                "icon": str(p.get("icon") or ""),
                "name": t(f"platform.{pid}", lang),
                "api_kind": kind,
                "api_label": t(f"apidoc.api.{kind}", lang),
                "cap": cap,
                "window": window,
                "rate": rate,
                "safe": safe,
                "detail": detail,
            }
        )
    return rows
