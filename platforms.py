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
        "fields": ("client_id", "client_secret"),
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
        "fields": ("client_id", "client_secret"),
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
        "fields": ("client_id", "client_secret"),
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
        "fields": ("client_id", "client_secret"),
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
        "fields": ("client_id", "client_secret"),
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
        "fields": ("client_id", "client_secret"),
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
        "fields": ("client_id", "client_secret"),
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
    "x": {**_LOCAL_STATS, "shares": True},
    "dailymotion": dict(_LOCAL_STATS),
    "bilibili": dict(_LOCAL_STATS),
    "rumble": {**_LOCAL_STATS, "comments": False},
    "snapchat": {**_LOCAL_STATS, "likes": False, "comments": False},
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


def platform_list(lang: str) -> list[dict[str, Any]]:
    from i18n import t

    out: list[dict[str, Any]] = []
    for p in PLATFORMS:
        pid = str(p["id"])
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
                "note": t(f"limits.note.{pid}", lang),
                "label_client_id": _field_label(lang, "api.field.client_id", pid, "api.field.client_id"),
                "label_client_secret": _field_label(
                    lang, "api.field.client_secret", pid, "api.field.client_secret"
                ),
            }
        )
    return out


def api_document_rows(lang: str) -> list[dict[str, Any]]:
    """Filas de la página API Documento (pasos, media y renovación de token)."""
    from i18n import MESSAGES, t

    rows: list[dict[str, Any]] = []
    for p in PLATFORMS:
        pid = str(p["id"])
        steps: list[str] = []
        n = 1
        while f"apidoc.{pid}.step{n}" in MESSAGES:
            steps.append(t(f"apidoc.{pid}.step{n}", lang))
            n += 1
        extra_key = f"apidoc.{pid}.extra"
        extra = t(extra_key, lang) if extra_key in MESSAGES else ""
        kind = str(p.get("api_kind") or ("oauth" if p.get("has_api") else "none"))
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

    rows: list[dict[str, Any]] = []
    for p in PLATFORMS:
        pid = str(p["id"])
        kind = str(p.get("api_kind") or ("oauth" if p.get("has_api") else "none"))
        rows.append(
            {
                "id": pid,
                "icon": str(p.get("icon") or ""),
                "name": t(f"platform.{pid}", lang),
                "api_kind": kind,
                "api_label": t(f"apidoc.api.{kind}", lang),
                "cap": t(f"cond.{pid}.cap", lang),
                "window": t(f"cond.{pid}.window", lang),
                "rate": t(f"cond.{pid}.rate", lang),
                "safe": t(f"cond.{pid}.safe", lang),
                "detail": t(f"cond.{pid}.detail", lang),
            }
        )
    return rows
