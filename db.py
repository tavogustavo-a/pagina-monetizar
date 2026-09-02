from __future__ import annotations

import os
import random
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt

import db_engine
from db_engine import DATA_DIR, DB_PATH

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "tavo").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "104646")

# Modos para usuarios con role='user'. El role='admin' de la cuenta maestra sigue aparte.
REGULAR_USER_MODES = frozenset({
    "basic",
    "admin",
    "supervisor",
    "videos_only",
    "videos_comments",
    "videos_comments_stats",
})
USER_MODE_LABELS: dict[str, str] = {
    "basic": "Basic mode",
    "admin": "Admin mode",
    "supervisor": "Supervisor mode",
    "videos_only": "Videos only",
    "videos_comments": "Videos & comments",
    "videos_comments_stats": "Videos, comments & stats",
}
USER_MODE_HINTS: dict[str, str] = {
    "basic": "Default: minimal access until permissions are configured.",
    "admin": "High permission level in the app (separate from site administrator account).",
    "supervisor": "Content and workflow oversight.",
    "videos_only": "Publish and manage videos only.",
    "videos_comments": "Videos plus comment interaction.",
    "videos_comments_stats": "Videos, comments, and analytics.",
}
# Backward-compatible aliases
USER_MODE_LABELS_ES = USER_MODE_LABELS
USER_MODE_HINTS_ES = USER_MODE_HINTS
# Orden en formularios (crear / editar).
REGULAR_USER_MODE_ORDER = (
    "basic",
    "admin",
    "supervisor",
    "videos_only",
    "videos_comments",
    "videos_comments_stats",
)
USER_MODES_CAN_UPLOAD_VIDEOS = frozenset({
    "videos_only",
    "videos_comments",
    "videos_comments_stats",
    "supervisor",
    "admin",
})
USER_MODES_CAN_MANAGE_COMMENTS = frozenset({
    "videos_comments",
    "videos_comments_stats",
    "supervisor",
    "admin",
})


def user_has_admin_privileges(user: User) -> bool:
    """Cuenta administrador del sitio o usuario regular en modo admin."""
    if user.role == "admin":
        return True
    return user.role == "user" and user.user_mode == "admin"


def user_is_site_admin(user: User) -> bool:
    return user.role == "admin"


def user_is_admin_mode_user(user: User) -> bool:
    return user.role == "user" and user.user_mode == "admin"


def user_can_manage_member(actor: User, target: User) -> bool:
    """Quién puede editar, desactivar o eliminar a un miembro del equipo."""
    if target.role == "admin":
        return False
    if target.user_mode == "admin":
        return user_is_site_admin(actor)
    return user_has_admin_privileges(actor)


@dataclass
class User:
    id: str
    username: str
    role: str
    display_name: str
    created_at: str
    active: bool = True
    user_mode: str = "basic"
    linked_tiktok_config_id: str | None = None
    can_view_comments: bool = True


_USER_ROW_COLUMNS = (
    "id, username, role, display_name, created_at, active, user_mode, "
    "linked_tiktok_config_id, can_view_comments"
)


@dataclass
class Video:
    id: str
    user_id: str
    title: str
    description: str
    file_name: str
    views: int
    likes: int
    shares: int
    created_at: str


@dataclass
class Comment:
    id: str
    video_id: str
    parent_id: str | None
    author_name: str
    body: str
    is_creator_reply: bool
    created_at: str


def _ensure_users_active_column() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "active" not in cols:
            conn.execute(
                "ALTER TABLE users ADD COLUMN active INTEGER NOT NULL DEFAULT 1"
            )
            conn.commit()
    finally:
        conn.close()


def _ensure_users_mode_column() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "user_mode" not in cols:
            conn.execute(
                "ALTER TABLE users ADD COLUMN user_mode TEXT NOT NULL DEFAULT 'basic'"
            )
            conn.execute(
                "UPDATE users SET user_mode = 'admin' WHERE role = 'admin'"
            )
            conn.commit()
    finally:
        conn.close()


def _ensure_tiktok_oauth_columns() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(tiktok_api_configs)").fetchall()}
        additions = {
            "open_id": "TEXT",
            "tiktok_username": "TEXT",
            "access_token": "TEXT",
            "refresh_token": "TEXT",
            "token_expires_at": "TEXT",
            "oauth_scopes": "TEXT",
        }
        for col, sql_type in additions.items():
            if col not in cols:
                conn.execute(
                    f"ALTER TABLE tiktok_api_configs ADD COLUMN {col} {sql_type}"
                )
        conn.commit()
    finally:
        conn.close()


def _ensure_oauth_accounts_table() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_accounts (
                id TEXT PRIMARY KEY,
                platform_id TEXT NOT NULL,
                open_id TEXT NOT NULL,
                username TEXT,
                display_name TEXT,
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TEXT,
                oauth_scopes TEXT,
                client_id TEXT,
                client_secret TEXT,
                redirect_uri TEXT,
                linked_by_user_id TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (platform_id, open_id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_oauth_accounts_platform ON oauth_accounts(platform_id)"
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_users_linked_tiktok_config_column() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        added = False
        if "linked_tiktok_config_id" not in cols:
            conn.execute(
                """
                ALTER TABLE users ADD COLUMN linked_tiktok_config_id TEXT
                REFERENCES tiktok_api_configs(id) ON DELETE SET NULL
                """
            )
            added = True
        if added:
            rows = conn.execute(
                """
                SELECT id, internal_user_id FROM tiktok_api_configs
                WHERE internal_user_id IS NOT NULL
                """
            ).fetchall()
            for r in rows:
                conn.execute(
                    "UPDATE users SET linked_tiktok_config_id = ? WHERE id = ?",
                    (r["id"], r["internal_user_id"]),
                )
            conn.commit()
    finally:
        conn.close()


def _ensure_users_can_view_comments_column() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "can_view_comments" not in cols:
            conn.execute(
                "ALTER TABLE users ADD COLUMN can_view_comments INTEGER NOT NULL DEFAULT 1"
            )
            conn.execute("UPDATE users SET can_view_comments = 1")
            conn.commit()
            return
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = 'can_view_comments_all_on'"
        ).fetchone()
        if not row:
            conn.execute("UPDATE users SET can_view_comments = 1")
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                VALUES ('can_view_comments_all_on', '1', ?)
                """,
                (now,),
            )
            conn.commit()
    finally:
        conn.close()


def _migrate_legacy_user_modes() -> None:
    conn = _connect()
    try:
        conn.executescript(
            """
            UPDATE users SET user_mode = 'basic' WHERE user_mode = 'viewer';
            UPDATE users SET user_mode = 'videos_comments' WHERE user_mode = 'creator';
            UPDATE users SET user_mode = 'videos_comments_stats' WHERE user_mode = 'manager';
            """
        )
        conn.commit()
    finally:
        conn.close()


def _user_from_row(row: sqlite3.Row) -> User:
    d = dict(row)
    active_v = d.get("active", 1)
    mode = (d.get("user_mode") or "basic").strip() or "basic"
    legacy = {"viewer": "basic", "creator": "videos_comments", "manager": "videos_comments_stats"}
    if mode in legacy:
        mode = legacy[mode]
    ltid = d.get("linked_tiktok_config_id")
    if ltid is not None:
        ltid = str(ltid).strip() or None
    cv = d.get("can_view_comments")
    if cv is None:
        can_view_comments = True
    else:
        can_view_comments = bool(cv)
    return User(
        id=d["id"],
        username=d["username"],
        role=d["role"],
        display_name=d["display_name"],
        created_at=d["created_at"],
        active=bool(active_v),
        user_mode=mode,
        linked_tiktok_config_id=ltid,
        can_view_comments=can_view_comments,
    )


def _sync_user_tiktok_link(
    conn: sqlite3.Connection, user_id: str, config_id: str | None
) -> None:
    """Alinea users.linked_tiktok_config_id y tiktok_api_configs.internal_user_id."""
    if config_id:
        row = conn.execute(
            "SELECT id FROM tiktok_api_configs WHERE id = ?", (config_id,)
        ).fetchone()
        if not row:
            raise ValueError("TikTok configuration not found.")
        conn.execute(
            """
            UPDATE users SET linked_tiktok_config_id = NULL
            WHERE linked_tiktok_config_id = ? AND id != ?
            """,
            (config_id, user_id),
        )
    conn.execute(
        "UPDATE tiktok_api_configs SET internal_user_id = NULL WHERE internal_user_id = ?",
        (user_id,),
    )
    conn.execute(
        "UPDATE users SET linked_tiktok_config_id = ? WHERE id = ?",
        (config_id, user_id),
    )
    if config_id:
        conn.execute(
            "UPDATE tiktok_api_configs SET internal_user_id = ? WHERE id = ?",
            (user_id, config_id),
        )


def _connect():
    return db_engine.connect()


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash BLOB NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                file_name TEXT NOT NULL,
                views INTEGER NOT NULL DEFAULT 0,
                likes INTEGER NOT NULL DEFAULT 0,
                shares INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                parent_id TEXT,
                author_name TEXT NOT NULL,
                body TEXT NOT NULL,
                is_creator_reply INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tiktok_api_configs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                client_key TEXT NOT NULL,
                client_secret TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                internal_user_id TEXT,
                notes TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (internal_user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_credentials (
                platform_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL DEFAULT '',
                client_secret TEXT NOT NULL DEFAULT '',
                access_token TEXT NOT NULL DEFAULT '',
                extra TEXT NOT NULL DEFAULT '',
                last_test_ok INTEGER,
                last_test_at TEXT,
                last_test_message TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS publication_log (
                id TEXT PRIMARY KEY,
                video_id TEXT,
                user_id TEXT NOT NULL,
                platform_id TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'video',
                status TEXT NOT NULL CHECK (status IN ('ok', 'fail', 'skipped')),
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    _ensure_users_active_column()
    _ensure_users_mode_column()
    _migrate_legacy_user_modes()
    _ensure_users_linked_tiktok_config_column()
    _ensure_users_can_view_comments_column()
    _ensure_tiktok_oauth_columns()
    _ensure_oauth_accounts_table()
    _ensure_scheduled_publications_table()
    _ensure_platform_credentials_name_column()
    _ensure_server_groups_tables()
    _ensure_server_accounts_table()
    _ensure_server_accounts_source_columns()
    _ensure_server_account_links_table()
    _ensure_user_account_links_table()
    _ensure_server_group_members_v3()
    _ensure_publication_log_account_link_column()
    _ensure_scheduled_publications_account_link_column()
    _ensure_extractor_tables()
    _pg = _connect()
    try:
        db_engine.ensure_postgres_extras(_pg)
        _pg.commit()
    finally:
        _pg.close()


def _ensure_scheduled_publications_table() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_publications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                platforms_json TEXT NOT NULL,
                tiktok_config_id TEXT NOT NULL DEFAULT '',
                content_type TEXT NOT NULL DEFAULT 'video',
                scheduled_at TEXT NOT NULL,
                lang TEXT NOT NULL DEFAULT 'es',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                processed_at TEXT,
                error_message TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (video_id) REFERENCES videos(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_platform_credentials_name_column() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(platform_credentials)").fetchall()}
        if "name" not in cols:
            conn.execute(
                "ALTER TABLE platform_credentials ADD COLUMN name TEXT NOT NULL DEFAULT ''"
            )
            conn.commit()
    finally:
        conn.close()


def _ensure_server_groups_tables() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS server_groups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS server_group_members (
                group_id TEXT NOT NULL,
                platform_id TEXT NOT NULL,
                PRIMARY KEY (group_id, platform_id),
                FOREIGN KEY (group_id) REFERENCES server_groups(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_server_group_members_account_id() -> None:
    """Legacy v1→v2 migration; superseded by _ensure_server_group_members_v3."""
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(server_group_members)").fetchall()}
        if not cols or "server_account_id" in cols or "account_id" in cols:
            return
        if "platform_id" not in cols:
            return
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS server_group_members_v2 (
                group_id TEXT NOT NULL,
                platform_id TEXT NOT NULL,
                account_id TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (group_id, platform_id, account_id),
                FOREIGN KEY (group_id) REFERENCES server_groups(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            INSERT INTO server_group_members_v2 (group_id, platform_id, account_id)
            SELECT group_id, platform_id, '' FROM server_group_members
            """
        )
        conn.execute("DROP TABLE server_group_members")
        conn.execute("ALTER TABLE server_group_members_v2 RENAME TO server_group_members")
        conn.commit()
    finally:
        conn.close()


def _ensure_server_accounts_table() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS server_accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                platform_id TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_server_accounts_source_columns() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(server_accounts)").fetchall()}
        if "source_kind" not in cols:
            conn.execute(
                "ALTER TABLE server_accounts ADD COLUMN source_kind TEXT NOT NULL DEFAULT 'manual'"
            )
        if "source_ref" not in cols:
            conn.execute(
                "ALTER TABLE server_accounts ADD COLUMN source_ref TEXT NOT NULL DEFAULT ''"
            )
        conn.commit()
    finally:
        conn.close()


def _ensure_server_account_links_table() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS server_account_links (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        _sync_account_links_from_accounts(conn)
    finally:
        conn.close()


def _sync_account_links_from_accounts(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT DISTINCT name FROM server_accounts WHERE trim(name) != ''"
    ).fetchall()
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        name = str(row["name"] or "").strip()
        if not name:
            continue
        exists = conn.execute(
            """
            SELECT 1 AS ok FROM server_account_links
            WHERE lower(trim(name)) = lower(trim(?))
            """,
            (name,),
        ).fetchone()
        if exists:
            continue
        conn.execute(
            """
            INSERT INTO server_account_links (id, name, active, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            """,
            (str(uuid.uuid4()), name, now, now),
        )
    conn.commit()


def _account_name_used_by_group(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1 AS ok
        FROM server_groups
        WHERE lower(trim(name)) = lower(trim(?))
        LIMIT 1
        """,
        (name,),
    ).fetchone()
    return bool(row)


def _ensure_user_account_links_table() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_account_links (
                user_id TEXT NOT NULL,
                account_link_id TEXT NOT NULL,
                PRIMARY KEY (user_id, account_link_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (account_link_id) REFERENCES server_account_links(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _account_link_platform_ids(conn: sqlite3.Connection, link_name: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT platform_id
        FROM server_accounts
        WHERE lower(trim(name)) = lower(trim(?))
          AND active = 1
          AND trim(platform_id) != ''
        ORDER BY platform_id
        """,
        (link_name,),
    ).fetchall()
    return [str(r["platform_id"]) for r in rows]


def list_user_account_link_ids(user_id: str) -> list[str]:
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT account_link_id
            FROM user_account_links
            WHERE user_id = ?
            ORDER BY account_link_id
            """,
            (user_id,),
        ).fetchall()
        return [str(r["account_link_id"]) for r in rows]
    finally:
        conn.close()


def _set_user_account_links_on_conn(
    conn: sqlite3.Connection, user_id: str, link_ids: list[str] | None
) -> None:
    conn.execute("DELETE FROM user_account_links WHERE user_id = ?", (user_id,))
    seen: set[str] = set()
    for raw in link_ids or []:
        lid = (raw or "").strip()
        if not lid or lid in seen:
            continue
        row = conn.execute(
            """
            SELECT id FROM server_account_links
            WHERE id = ? AND active = 1
            """,
            (lid,),
        ).fetchone()
        if not row:
            continue
        conn.execute(
            """
            INSERT INTO user_account_links (user_id, account_link_id)
            VALUES (?, ?)
            """,
            (user_id, lid),
        )
        seen.add(lid)


def set_user_account_links(user_id: str, link_ids: list[str] | None) -> None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        _set_user_account_links_on_conn(conn, user_id, link_ids)
        conn.commit()
    finally:
        conn.close()


def _matches_account_query(search_blob: str, query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True
    tokens = [t for t in q.split() if t]
    if not tokens:
        return True
    return all(token in search_blob for token in tokens)


def list_team_server_account_choices(
    q: str = "",
    selected_ids: list[str] | None = None,
    *,
    lang: str = "es",
) -> list[dict[str, Any]]:
    from platforms import platform_list

    sync_server_accounts_from_links()
    names = {p["id"]: p["name"] for p in platform_list(lang)}
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, name, active
            FROM server_account_links
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            if not row["active"]:
                continue
            link_id = str(row["id"])
            link_name = str(row["name"] or "").strip()
            if not link_name:
                continue
            platform_ids = _account_link_platform_ids(conn, link_name)
            platform_labels = [names.get(pid, pid) for pid in platform_ids]
            items.append(
                {
                    "id": link_id,
                    "name": link_name,
                    "platform_ids": platform_ids,
                    "platform": ", ".join(platform_labels),
                    "_search": f"{link_name} {' '.join(platform_labels)} {link_id}".lower(),
                }
            )
    finally:
        conn.close()

    query = (q or "").strip().lower()
    if query:
        items = [item for item in items if _matches_account_query(item["_search"], query)]

    selected = [s.strip() for s in (selected_ids or []) if (s or "").strip()]
    known = {item["id"] for item in items}
    if selected:
        missing = [sid for sid in selected if sid not in known]
        if missing:
            conn = _connect()
            try:
                for sid in missing:
                    row = conn.execute(
                        "SELECT id, name, active FROM server_account_links WHERE id = ?",
                        (sid,),
                    ).fetchone()
                    if not row:
                        continue
                    link_name = str(row["name"] or "").strip()
                    platform_ids = _account_link_platform_ids(conn, link_name)
                    platform_labels = [names.get(pid, pid) for pid in platform_ids]
                    search_blob = f"{link_name} {' '.join(platform_labels)}".lower()
                    if query and not _matches_account_query(search_blob, query):
                        continue
                    items.append(
                        {
                            "id": str(row["id"]),
                            "name": link_name,
                            "platform_ids": platform_ids,
                            "platform": ", ".join(platform_labels),
                            "_search": search_blob,
                        }
                    )
            finally:
                conn.close()
        items.sort(key=lambda item: item["name"].casefold())

    for item in items:
        item.pop("_search", None)
    return items


def list_user_publish_accounts(user: User, *, lang: str = "es") -> list[dict[str, Any]]:
    if user_has_admin_privileges(user):
        return []
    link_ids = list_user_account_link_ids(user.id)
    if not link_ids:
        return []
    choices = {c["id"]: c for c in list_team_server_account_choices(lang=lang)}
    return [choices[lid] for lid in link_ids if lid in choices]


def list_stats_server_accounts(viewer: User, *, lang: str = "es") -> list[dict[str, Any]]:
    """Cuentas de Servidores visibles en Estadísticas (admin: todas; usuario: asignadas)."""
    if user_has_admin_privileges(viewer):
        return list_team_server_account_choices(lang=lang)
    return list_user_publish_accounts(viewer, lang=lang)


def filter_accounts_by_platform(
    accounts: list[dict[str, Any]], platform_id: str | None
) -> list[dict[str, Any]]:
    if not platform_id:
        return list(accounts)
    return [a for a in accounts if platform_id in (a.get("platform_ids") or [])]


STATS_GROUP_PREFIX = "group:"


def _link_id_for_account_name(conn: sqlite3.Connection, name: str) -> str | None:
    label = (name or "").strip()
    if not label:
        return None
    row = conn.execute(
        """
        SELECT id FROM server_account_links
        WHERE lower(trim(name)) = lower(trim(?)) AND active = 1
        """,
        (label,),
    ).fetchone()
    return str(row["id"]) if row else None


def _group_member_link_ids(group: dict[str, Any], conn: sqlite3.Connection) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for member in group.get("members") or []:
        name = (member.get("name") or "").strip()
        lid = _link_id_for_account_name(conn, name)
        if not lid or lid in seen:
            continue
        seen.add(lid)
        out.append(lid)
    return out


def list_stats_filter_choices(viewer: User, *, lang: str = "es") -> list[dict[str, Any]]:
    """Cuentas y grupos manuales disponibles en el filtro de Estadísticas."""
    from platforms import platform_list

    choices: list[dict[str, Any]] = []
    if user_has_admin_privileges(viewer):
        sync_server_accounts_from_links()
        names = {p["id"]: p["name"] for p in platform_list(lang)}
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT id, name, active
                FROM server_account_links
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
            for row in rows:
                if not row["active"]:
                    continue
                link_id = str(row["id"])
                link_name = str(row["name"] or "").strip()
                if not link_name:
                    continue
                platform_ids = _account_link_platform_ids(conn, link_name)
                platform_labels = [names.get(pid, pid) for pid in platform_ids]
                choices.append(
                    {
                        "id": link_id,
                        "name": link_name,
                        "kind": "link",
                        "platform_ids": list(platform_ids),
                        "platform": ", ".join(platform_labels),
                        "link_ids": [link_id],
                    }
                )
        finally:
            conn.close()
    else:
        for acc in list_user_publish_accounts(viewer, lang=lang):
            link_id = str(acc.get("id") or "").strip()
            if not link_id:
                continue
            choices.append(
                {
                    "id": link_id,
                    "name": acc.get("name") or link_id,
                    "kind": "link",
                    "platform_ids": list(acc.get("platform_ids") or []),
                    "platform": acc.get("platform") or "",
                    "link_ids": [link_id],
                }
            )
    if user_has_admin_privileges(viewer):
        conn = _connect()
        try:
            for group in list_server_groups(lang):
                if not group.get("active"):
                    continue
                members = group.get("members") or []
                link_ids = _group_member_link_ids(group, conn)
                platform_ids = sorted(
                    {
                        str(m.get("platform_id") or "").strip()
                        for m in members
                        if (m.get("platform_id") or "").strip()
                    }
                )
                if not link_ids and not platform_ids:
                    continue
                choices.append(
                    {
                        "id": f"{STATS_GROUP_PREFIX}{group['id']}",
                        "name": group.get("name") or group["id"],
                        "kind": "group",
                        "platform_ids": platform_ids,
                        "link_ids": link_ids,
                    }
                )
        finally:
            conn.close()
    choices.sort(key=lambda item: str(item.get("name") or "").casefold())
    return choices


def filter_stats_choices_by_platform(
    choices: list[dict[str, Any]], platform_id: str | None
) -> list[dict[str, Any]]:
    if not platform_id:
        return list(choices)
    return [c for c in choices if platform_id in (c.get("platform_ids") or [])]


def _account_link_sql_filter(
    account_link_id: str | None,
    account_link_ids: list[str] | None,
    *,
    column: str = "account_link_id",
) -> tuple[str, list[str]]:
    ids = [str(x).strip() for x in (account_link_ids or []) if str(x).strip()]
    if not ids and account_link_id:
        ids = [str(account_link_id).strip()]
    if not ids:
        return "", []
    if len(ids) == 1:
        return f"{column} = ?", ids
    placeholders = ",".join("?" for _ in ids)
    return f"{column} IN ({placeholders})", ids


def _ensure_publication_log_account_link_column() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(publication_log)").fetchall()}
        if "account_link_id" not in cols:
            conn.execute(
                "ALTER TABLE publication_log ADD COLUMN account_link_id TEXT NOT NULL DEFAULT ''"
            )
            conn.commit()
    finally:
        conn.close()


def _ensure_scheduled_publications_account_link_column() -> None:
    conn = _connect()
    try:
        cols = {
            r[1] for r in conn.execute("PRAGMA table_info(scheduled_publications)").fetchall()
        }
        if "account_link_id" not in cols:
            conn.execute(
                "ALTER TABLE scheduled_publications ADD COLUMN account_link_id TEXT NOT NULL DEFAULT ''"
            )
            conn.commit()
    finally:
        conn.close()


def _account_link_name_taken(
    conn: sqlite3.Connection, name: str, *, exclude_id: str = ""
) -> bool:
    label = _normalize_account_name(name)
    if not label:
        return False
    if exclude_id:
        row = conn.execute(
            """
            SELECT 1 AS ok FROM server_account_links
            WHERE lower(trim(name)) = lower(trim(?)) AND id != ?
            """,
            (label, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT 1 AS ok FROM server_account_links
            WHERE lower(trim(name)) = lower(trim(?))
            """,
            (label,),
        ).fetchone()
    return bool(row)


def _list_account_link_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM server_account_links ORDER BY name COLLATE NOCASE"
    ).fetchall()


def create_account_link(name: str, *, lang: str = "es") -> dict[str, Any]:
    seed_admin_if_missing()
    label = _normalize_account_name(name)
    if not label:
        raise ValueError("name_required")
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        if _account_link_name_taken(conn, label):
            raise ValueError("link_name_taken")
        if _account_name_used_by_group(conn, label):
            raise ValueError("group_name_conflict")
        lid = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO server_account_links (id, name, active, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            """,
            (lid, label, now, now),
        )
        conn.commit()
    finally:
        conn.close()
    groups = get_server_account_groups(lang)
    key = label.casefold()
    for group in groups:
        if group.get("key") == key:
            return group
    return {
        "key": key,
        "name": label,
        "accounts": [],
        "active": True,
        "link_id": lid,
        "linked_count": 0,
    }


def delete_account_link(link_id: str) -> None:
    seed_admin_if_missing()
    lid = (link_id or "").strip()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT name FROM server_account_links WHERE id = ?", (lid,)
        ).fetchone()
        if not row:
            raise ValueError("not_found")
        name = str(row["name"] or "").strip()
        _delete_extractor_jobs_on_conn(conn, account_link_id=lid)
        if _has_column(conn, "publication_log", "account_link_id"):
            conn.execute("DELETE FROM publication_log WHERE account_link_id = ?", (lid,))
        if _has_column(conn, "scheduled_publications", "account_link_id"):
            conn.execute(
                "DELETE FROM scheduled_publications WHERE account_link_id = ?", (lid,)
            )
        conn.execute("DELETE FROM user_account_links WHERE account_link_id = ?", (lid,))
        accounts = conn.execute(
            "SELECT id FROM server_accounts WHERE lower(trim(name)) = lower(trim(?))",
            (name,),
        ).fetchall()
        for account in accounts:
            _delete_server_account_on_conn(conn, str(account["id"]))
        conn.execute("DELETE FROM server_account_links WHERE id = ?", (lid,))
        _prune_empty_account_links_on_conn(conn)
        conn.commit()
    finally:
        conn.close()


def set_account_link_active(link_id: str, active: bool, *, lang: str = "es") -> dict[str, Any]:
    seed_admin_if_missing()
    lid = (link_id or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT name FROM server_account_links WHERE id = ?", (lid,)
        ).fetchone()
        if not row:
            raise ValueError("not_found")
        name = str(row["name"] or "").strip()
        conn.execute(
            "UPDATE server_account_links SET active = ?, updated_at = ? WHERE id = ?",
            (1 if active else 0, now, lid),
        )
        account_ids = [
            str(r["id"])
            for r in conn.execute(
                "SELECT id FROM server_accounts WHERE lower(trim(name)) = lower(trim(?))",
                (name,),
            ).fetchall()
        ]
        conn.commit()
    finally:
        conn.close()
    for aid in account_ids:
        set_server_account_active(aid, active, lang=lang)
    groups = get_server_account_groups(lang)
    key = name.casefold()
    for group in groups:
        if group.get("key") == key:
            return group
    raise ValueError("not_found")


def get_server_account_groups(lang: str = "es") -> list[dict[str, Any]]:
    from platforms import platform_list

    seed_admin_if_missing()
    sync_server_accounts_from_links()
    names = {p["id"]: p["name"] for p in platform_list(lang)}
    conn = _connect()
    try:
        links = _list_account_link_rows(conn)
        rows = conn.execute(
            "SELECT * FROM server_accounts ORDER BY name COLLATE NOCASE, created_at"
        ).fetchall()
        accounts = [
            {
                "id": r["id"],
                "name": r["name"],
                "platform_id": r["platform_id"],
                "platform": names.get(r["platform_id"], r["platform_id"]),
                "active": bool(r["active"]),
                "source_kind": (r["source_kind"] or "manual")
                if "source_kind" in r.keys()
                else "manual",
                "source_ref": (r["source_ref"] or "")
                if "source_ref" in r.keys()
                else "",
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()
    return _build_server_account_groups(accounts, links)


def _ensure_server_group_members_v3() -> None:
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(server_group_members)").fetchall()}
        if "server_account_id" in cols:
            return
        conn.execute(
            """
            CREATE TABLE server_group_members_v3 (
                group_id TEXT NOT NULL,
                server_account_id TEXT NOT NULL,
                PRIMARY KEY (group_id, server_account_id),
                FOREIGN KEY (group_id) REFERENCES server_groups(id) ON DELETE CASCADE,
                FOREIGN KEY (server_account_id) REFERENCES server_accounts(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("DROP TABLE IF EXISTS server_group_members")
        conn.execute("ALTER TABLE server_group_members_v3 RENAME TO server_group_members")
        conn.commit()
    finally:
        conn.close()


def _hash_pw(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=12))


def _verify_pw(pw: str, hashed: bytes | memoryview | bytearray | None) -> bool:
    if hashed is None:
        return False
    if isinstance(hashed, memoryview):
        hashed = hashed.tobytes()
    elif not isinstance(hashed, (bytes, bytearray)):
        hashed = bytes(hashed)
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), bytes(hashed))
    except ValueError:
        return False


def seed_admin_if_missing() -> None:
    init_db()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ? COLLATE NOCASE AND role = 'admin'",
            (ADMIN_USERNAME,),
        ).fetchone()
        if row:
            return
        exists_user = conn.execute(
            "SELECT id FROM users WHERE username = ? COLLATE NOCASE",
            (ADMIN_USERNAME,),
        ).fetchone()
        if exists_user:
            return
        uid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO users (id, username, password_hash, role, display_name, created_at, active, user_mode, linked_tiktok_config_id, can_view_comments)
               VALUES (?, ?, ?, 'admin', ?, ?, 1, 'admin', NULL, 1)""",
            (
                uid,
                ADMIN_USERNAME,
                _hash_pw(ADMIN_PASSWORD),
                "Administrator",
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_username(username: str) -> User | None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            f"SELECT {_USER_ROW_COLUMNS} FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()
        if not row:
            return None
        return _user_from_row(row)
    finally:
        conn.close()


def get_user_by_id(uid: str) -> User | None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            f"SELECT {_USER_ROW_COLUMNS} FROM users WHERE id = ?",
            (uid,),
        ).fetchone()
        if not row:
            return None
        return _user_from_row(row)
    finally:
        conn.close()


def verify_login(username: str, password: str) -> User | None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            f"SELECT {_USER_ROW_COLUMNS}, password_hash FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()
        if not row:
            return None
        if not _verify_pw(password, row["password_hash"]):
            return None
        if row["role"] == "user" and not bool(row["active"]):
            return None
        return _user_from_row(row)
    finally:
        conn.close()


def list_users() -> list[User]:
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            f"SELECT {_USER_ROW_COLUMNS} FROM users ORDER BY role DESC, created_at DESC"
        ).fetchall()
        return [_user_from_row(r) for r in rows]
    finally:
        conn.close()


TEAM_MEMBERS_PAGE_SIZE = 10
TEAM_MEMBERS_PER_PAGE_OPTIONS = (10, 20, 30, 50, 100, 200)


def normalize_team_members_per_page(per_page: int | str | None) -> int | None:
    """Return page size, or None to show all members."""
    if per_page is None:
        return TEAM_MEMBERS_PAGE_SIZE
    if isinstance(per_page, str):
        s = per_page.strip().lower()
        if s in ("all", "todos", "0"):
            return None
        try:
            per_page = int(s)
        except ValueError:
            return TEAM_MEMBERS_PAGE_SIZE
    if int(per_page) <= 0:
        return None
    if int(per_page) not in TEAM_MEMBERS_PER_PAGE_OPTIONS:
        return TEAM_MEMBERS_PAGE_SIZE
    return int(per_page)


def _team_member_matches_query(user: User, q: str, mode_labels: dict[str, str]) -> bool:
    if q in user.username.lower():
        return True
    mode_id = (user.user_mode or "basic").lower()
    if q in mode_id or q in mode_id.replace("_", " "):
        return True
    label = mode_labels.get(user.user_mode, user.user_mode).lower()
    return q in label


def list_team_members(
    q: str = "",
    page: int = 1,
    per_page: int | None = TEAM_MEMBERS_PAGE_SIZE,
    lang: str = "en",
    exclude_user_id: str | None = None,
) -> tuple[list[User], int]:
    members = [u for u in list_users() if u.role != "admin"]
    if exclude_user_id:
        members = [u for u in members if u.id != exclude_user_id]
    query = q.strip().lower()
    mode_labels = user_mode_labels_for_lang(lang)
    if query:
        members = [u for u in members if _team_member_matches_query(u, query, mode_labels)]
    total = len(members)
    page = max(1, page)
    if per_page is None:
        return members, total
    per_page = max(1, int(per_page))
    start = (page - 1) * per_page
    return members[start : start + per_page], total


def create_user(
    username: str,
    password: str,
    display_name: str,
    role: str = "user",
    user_mode: str | None = None,
    linked_tiktok_config_id: str | None = None,
    account_link_ids: list[str] | None = None,
    *,
    can_view_comments: bool = True,
) -> User:
    seed_admin_if_missing()
    u = username.strip()
    if len(u) < 2:
        raise ValueError("Username must be at least 2 characters")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters")
    uid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    dn = display_name.strip() or u
    if role == "admin":
        mode = "admin"
    else:
        m = (user_mode or "basic").strip().lower()
        if m not in REGULAR_USER_MODES:
            raise ValueError("Invalid user mode")
        mode = m
    link = (linked_tiktok_config_id or "").strip() or None
    comments_flag = 1 if can_view_comments or role == "admin" else 0
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO users (id, username, password_hash, role, display_name, created_at, active, user_mode, linked_tiktok_config_id, can_view_comments)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?, NULL, ?)""",
            (uid, u, _hash_pw(password), role, dn, now, mode, comments_flag),
        )
        if role != "admin":
            _sync_user_tiktok_link(conn, uid, link)
            _set_user_account_links_on_conn(conn, uid, account_link_ids or [])
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise ValueError("Username already exists") from e
    finally:
        conn.close()
    user = get_user_by_id(uid)
    assert user is not None
    return user


def set_user_active(uid: str, active: bool, *, actor: User | None = None) -> None:
    seed_admin_if_missing()
    target = get_user_by_id(uid)
    if not target:
        raise ValueError("User not found")
    if target.role == "admin":
        raise ValueError("The administrator account is not managed here")
    if actor is not None and not user_can_manage_member(actor, target):
        raise ValueError("Only the site administrator can manage this user")
    conn = _connect()
    try:
        conn.execute(
            "UPDATE users SET active = ? WHERE id = ?",
            ((1 if active else 0), uid),
        )
        conn.commit()
    finally:
        conn.close()


def update_user_record(
    uid: str,
    username: str,
    display_name: str,
    new_password: str | None,
    user_mode: str | None = None,
    linked_tiktok_config_id: str | None = None,
    account_link_ids: list[str] | None = None,
    *,
    can_view_comments: bool | None = None,
    actor: User | None = None,
) -> User:
    seed_admin_if_missing()
    target = get_user_by_id(uid)
    if not target:
        raise ValueError("User not found")
    if target.role == "admin":
        raise ValueError("The administrator account cannot be edited here")
    if actor is not None and not user_can_manage_member(actor, target):
        raise ValueError("Only the site administrator can manage this user")
    u = username.strip()
    if len(u) < 2:
        raise ValueError("Username must be at least 2 characters")
    dn = display_name.strip() or u
    if user_mode is None or not str(user_mode).strip():
        mode = target.user_mode
        if mode not in REGULAR_USER_MODES:
            mode = "basic"
    else:
        m = str(user_mode).strip().lower()
        if m not in REGULAR_USER_MODES:
            raise ValueError("Invalid user mode")
        mode = m
    comments_flag = (
        target.can_view_comments if can_view_comments is None else bool(can_view_comments)
    )
    conn = _connect()
    try:
        clash = conn.execute(
            "SELECT id FROM users WHERE username = ? COLLATE NOCASE AND id != ?",
            (u, uid),
        ).fetchone()
        if clash:
            raise ValueError("That username is already taken")
        if new_password is not None and new_password != "":
            if len(new_password) < 4:
                raise ValueError("Password must be at least 4 characters")
            conn.execute(
                "UPDATE users SET username = ?, display_name = ?, password_hash = ?, user_mode = ?, can_view_comments = ? WHERE id = ?",
                (u, dn, _hash_pw(new_password), mode, (1 if comments_flag else 0), uid),
            )
        else:
            conn.execute(
                "UPDATE users SET username = ?, display_name = ?, user_mode = ?, can_view_comments = ? WHERE id = ?",
                (u, dn, mode, (1 if comments_flag else 0), uid),
            )
        if linked_tiktok_config_id is not None:
            link = (linked_tiktok_config_id or "").strip() or None
            _sync_user_tiktok_link(conn, uid, link)
        if account_link_ids is not None:
            _set_user_account_links_on_conn(conn, uid, account_link_ids)
        conn.commit()
    finally:
        conn.close()
    out = get_user_by_id(uid)
    assert out is not None
    return out


def regular_user_mode_choices(lang: str = "en") -> list[dict[str, str]]:
    from i18n import t

    return [
        {
            "id": mid,
            "label": t(f"mode.{mid}", lang),
            "hint": t(f"mode.{mid}.hint", lang),
        }
        for mid in REGULAR_USER_MODE_ORDER
    ]


def user_mode_labels_for_lang(lang: str = "en") -> dict[str, str]:
    from i18n import t

    return {mid: t(f"mode.{mid}", lang) for mid in REGULAR_USER_MODE_ORDER}


def _sql_in(ids: list[str]) -> tuple[str, list[str]]:
    clean = [str(x).strip() for x in ids if str(x).strip()]
    if not clean:
        return "", []
    return ",".join("?" * len(clean)), clean


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return column in {r[1] for r in rows}


def _delete_extractor_jobs_on_conn(
    conn: sqlite3.Connection,
    *,
    owner_user_id: str | None = None,
    account_link_id: str | None = None,
) -> None:
    where: list[str] = []
    params: list[str] = []
    if owner_user_id:
        where.append("owner_user_id = ?")
        params.append(owner_user_id)
    if account_link_id:
        where.append("account_link_id = ?")
        params.append(account_link_id)
    if not where:
        return
    clause = " AND ".join(where)
    rows = conn.execute(
        f"SELECT id FROM extractor_jobs WHERE {clause}", params
    ).fetchall()
    job_ids = [str(r["id"]) for r in rows]
    if not job_ids:
        return
    ph, vals = _sql_in(job_ids)
    conn.execute(f"DELETE FROM extractor_events WHERE job_id IN ({ph})", vals)
    conn.execute(f"DELETE FROM extractor_jobs WHERE id IN ({ph})", vals)


def _delete_videos_on_conn(conn: sqlite3.Connection, video_ids: list[str]) -> None:
    ph, vals = _sql_in(video_ids)
    if not ph:
        return
    if _has_column(conn, "comments", "parent_id"):
        conn.execute(
            f"DELETE FROM comments WHERE video_id IN ({ph}) AND parent_id IS NOT NULL",
            vals,
        )
    conn.execute(f"DELETE FROM comments WHERE video_id IN ({ph})", vals)
    if _has_column(conn, "scheduled_publications", "video_id"):
        conn.execute(
            f"DELETE FROM scheduled_publications WHERE video_id IN ({ph})", vals
        )
    conn.execute(f"DELETE FROM publication_log WHERE video_id IN ({ph})", vals)
    conn.execute(f"DELETE FROM videos WHERE id IN ({ph})", vals)


def _prune_empty_account_links_on_conn(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT l.id FROM server_account_links l
        WHERE NOT EXISTS (
            SELECT 1 FROM server_accounts a
            WHERE lower(trim(a.name)) = lower(trim(l.name))
        )
        """
    ).fetchall()
    for row in rows:
        lid = str(row["id"])
        _delete_extractor_jobs_on_conn(conn, account_link_id=lid)
        if _has_column(conn, "publication_log", "account_link_id"):
            conn.execute("DELETE FROM publication_log WHERE account_link_id = ?", (lid,))
        if _has_column(conn, "scheduled_publications", "account_link_id"):
            conn.execute(
                "DELETE FROM scheduled_publications WHERE account_link_id = ?", (lid,)
            )
        conn.execute("DELETE FROM user_account_links WHERE account_link_id = ?", (lid,))
        conn.execute("DELETE FROM server_account_links WHERE id = ?", (lid,))


def _delete_tiktok_config_on_conn(conn: sqlite3.Connection, config_id: str) -> None:
    cid = (config_id or "").strip()
    if not cid:
        return
    conn.execute(
        "UPDATE users SET linked_tiktok_config_id = NULL WHERE linked_tiktok_config_id = ?",
        (cid,),
    )
    if _has_column(conn, "scheduled_publications", "tiktok_config_id"):
        conn.execute(
            "UPDATE scheduled_publications SET tiktok_config_id = '' WHERE tiktok_config_id = ?",
            (cid,),
        )
    member_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(server_group_members)").fetchall()
    }
    if "server_account_id" in member_cols:
        conn.execute(
            """
            DELETE FROM server_group_members
            WHERE server_account_id IN (
                SELECT id FROM server_accounts
                WHERE source_kind = 'tiktok' AND source_ref = ?
            )
            """,
            (cid,),
        )
    conn.execute(
        "DELETE FROM server_accounts WHERE source_kind = 'tiktok' AND source_ref = ?",
        (cid,),
    )
    conn.execute("DELETE FROM tiktok_api_configs WHERE id = ?", (cid,))


def _delete_oauth_account_on_conn(conn: sqlite3.Connection, account_id: str) -> None:
    oid = (account_id or "").strip()
    if not oid:
        return
    member_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(server_group_members)").fetchall()
    }
    if "server_account_id" in member_cols:
        conn.execute(
            """
            DELETE FROM server_group_members
            WHERE server_account_id IN (
                SELECT id FROM server_accounts
                WHERE source_kind = 'oauth' AND source_ref = ?
            )
            """,
            (oid,),
        )
    conn.execute(
        "DELETE FROM server_accounts WHERE source_kind = 'oauth' AND source_ref = ?",
        (oid,),
    )
    conn.execute("DELETE FROM oauth_accounts WHERE id = ?", (oid,))


def _delete_server_account_on_conn(conn: sqlite3.Connection, account_id: str) -> None:
    aid = (account_id or "").strip()
    if not aid:
        return
    row = conn.execute(
        "SELECT source_kind, source_ref FROM server_accounts WHERE id = ?", (aid,)
    ).fetchone()
    if not row:
        raise ValueError("not_found")
    keys = row.keys()
    kind = str(row["source_kind"] or "manual") if "source_kind" in keys else "manual"
    ref = str(row["source_ref"] or "") if "source_ref" in keys else ""
    member_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(server_group_members)").fetchall()
    }
    if "server_account_id" in member_cols:
        conn.execute(
            "DELETE FROM server_group_members WHERE server_account_id = ?", (aid,)
        )
    if kind == "tiktok" and ref:
        _delete_tiktok_config_on_conn(conn, ref)
        leftover = conn.execute(
            "SELECT 1 AS ok FROM server_accounts WHERE id = ?", (aid,)
        ).fetchone()
        if leftover:
            conn.execute("DELETE FROM server_accounts WHERE id = ?", (aid,))
        return
    if kind == "oauth" and ref:
        _delete_oauth_account_on_conn(conn, ref)
        leftover = conn.execute(
            "SELECT 1 AS ok FROM server_accounts WHERE id = ?", (aid,)
        ).fetchone()
        if leftover:
            conn.execute("DELETE FROM server_accounts WHERE id = ?", (aid,))
        return
    if kind == "platform" and ref:
        conn.execute("DELETE FROM platform_credentials WHERE platform_id = ?", (ref,))
    cur = conn.execute("DELETE FROM server_accounts WHERE id = ?", (aid,))
    if cur.rowcount == 0:
        raise ValueError("not_found")


def delete_user_by_id(uid: str, *, actor: User | None = None) -> list[str]:
    """Elimina un usuario que no sea admin y todo lo que depende de él.
    Devuelve los nombres de archivo en uploads/ que habría que borrar en disco.
    """
    seed_admin_if_missing()
    target = get_user_by_id(uid)
    if not target:
        raise ValueError("User not found")
    if target.role == "admin":
        raise ValueError("The administrator account cannot be deleted")
    if actor is not None and not user_can_manage_member(actor, target):
        raise ValueError("Only the site administrator can manage this user")
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, file_name FROM videos WHERE user_id = ?", (uid,)
        ).fetchall()
        file_names = [str(r["file_name"]) for r in rows]
        video_ids = [str(r["id"]) for r in rows]
        _delete_extractor_jobs_on_conn(conn, owner_user_id=uid)
        conn.execute("DELETE FROM scheduled_publications WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM publication_log WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM user_account_links WHERE user_id = ?", (uid,))
        if _has_column(conn, "tiktok_api_configs", "internal_user_id"):
            conn.execute(
                "UPDATE tiktok_api_configs SET internal_user_id = NULL WHERE internal_user_id = ?",
                (uid,),
            )
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        if "oauth_accounts" in tables:
            conn.execute(
                "UPDATE oauth_accounts SET linked_by_user_id = NULL WHERE linked_by_user_id = ?",
                (uid,),
            )
        _delete_videos_on_conn(conn, video_ids)
        cur = conn.execute("DELETE FROM users WHERE id = ?", (uid,))
        if cur.rowcount == 0:
            raise ValueError("User not found")
        conn.commit()
        return file_names
    finally:
        conn.close()


def _fmt_metric(n: int) -> str:
    if n >= 1_000_000:
        s = f"{n / 1_000_000:.1f}M"
        return s.replace(".0M", "M")
    if n >= 1_000:
        s = f"{n / 1_000:.1f}k"
        return s.replace(".0k", "k")
    return str(n)


def create_video(
    user_id: str, title: str, description: str, stored_filename: str
) -> Video:
    seed_admin_if_missing()
    vid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    views = random.randint(120, 8_000)
    lo = max(1, int(views * 0.02))
    hi = max(lo + 1, int(views * 0.18))
    likes = random.randint(lo, hi)
    shares = random.randint(5, max(20, likes // 10))
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO videos (id, user_id, title, description, file_name, views, likes, shares, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (vid, user_id, title.strip(), description.strip(), stored_filename, views, likes, shares, now),
        )
        conn.commit()
    finally:
        conn.close()
    v = get_video_by_id(vid)
    assert v is not None
    return v


def get_video_by_id(vid: str) -> Video | None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (vid,)).fetchone()
        if not row:
            return None
        return _row_to_video(row)
    finally:
        conn.close()


def _row_to_video(row: sqlite3.Row) -> Video:
    return Video(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        description=row["description"],
        file_name=row["file_name"],
        views=int(row["views"]),
        likes=int(row["likes"]),
        shares=int(row["shares"]),
        created_at=row["created_at"],
    )


def list_videos_newest() -> list[Video]:
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM videos ORDER BY created_at DESC"
        ).fetchall()
        return [_row_to_video(r) for r in rows]
    finally:
        conn.close()


def list_videos_for_user(user_id: str) -> list[Video]:
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM videos WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [_row_to_video(r) for r in rows]
    finally:
        conn.close()


def list_videos_for_account(
    account_link_id: str,
    *,
    platform_id: str | None = None,
    account_link_ids: list[str] | None = None,
) -> list[Video]:
    seed_admin_if_missing()
    link_sql, link_vals = _account_link_sql_filter(account_link_id, account_link_ids)
    if not link_sql:
        return []
    conn = _connect()
    try:
        where = [link_sql, "pl.status = 'ok'", "pl.video_id IS NOT NULL"]
        params: list[Any] = list(link_vals)
        if platform_id:
            where.append("pl.platform_id = ?")
            params.append(platform_id)
        rows = conn.execute(
            f"""
            SELECT v.*
            FROM videos v
            WHERE v.id IN (
                SELECT DISTINCT pl.video_id
                FROM publication_log pl
                WHERE {" AND ".join(where)}
            )
            ORDER BY v.created_at DESC
            """,
            params,
        ).fetchall()
        return [_row_to_video(r) for r in rows]
    finally:
        conn.close()


def video_belongs_to_account(
    video_id: str,
    account_link_id: str,
    *,
    platform_id: str | None = None,
    account_link_ids: list[str] | None = None,
) -> bool:
    seed_admin_if_missing()
    vid = (video_id or "").strip()
    link_sql, link_vals = _account_link_sql_filter(account_link_id, account_link_ids)
    if not vid or not link_sql:
        return False
    conn = _connect()
    try:
        where = ["video_id = ?", link_sql, "status = 'ok'"]
        params: list[Any] = [vid, *link_vals]
        if platform_id:
            where.append("platform_id = ?")
            params.append(platform_id)
        row = conn.execute(
            f"SELECT 1 AS ok FROM publication_log WHERE {' AND '.join(where)} LIMIT 1",
            params,
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def list_stats_publications(
    *,
    platform_id: str | None = None,
    creator_user_id: str | None = None,
    config_id: str | None = None,
    account_link_id: str | None = None,
    account_link_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Publicaciones por plataforma (publication_log) con métricas del video."""
    seed_admin_if_missing()
    if config_id and not creator_user_id:
        creator_user_id = get_config_internal_user_id(config_id)

    conn = _connect()
    try:
        pub_where = ["pl.status = 'ok'", "pl.video_id IS NOT NULL"]
        pub_params: list[Any] = []
        if platform_id:
            pub_where.append("pl.platform_id = ?")
            pub_params.append(platform_id)
        if creator_user_id:
            pub_where.append("v.user_id = ?")
            pub_params.append(creator_user_id)
        link_sql, link_vals = _account_link_sql_filter(
            account_link_id, account_link_ids, column="pl.account_link_id"
        )
        if link_sql:
            pub_where.append(link_sql)
            pub_params.extend(link_vals)

        pub_sql = f"""
            SELECT
                pl.id AS publication_id,
                pl.platform_id,
                pl.created_at AS published_at,
                pl.account_link_id,
                sal.name AS account_link_name,
                v.id,
                v.title,
                v.views,
                v.likes,
                v.shares,
                v.created_at,
                u.username AS owner_username,
                tc.id AS config_id,
                tc.name AS config_name,
                tc.tiktok_username,
                (
                    SELECT COUNT(*) FROM comments c WHERE c.video_id = v.id
                ) AS comment_count
            FROM publication_log pl
            JOIN videos v ON v.id = pl.video_id
            JOIN users u ON u.id = v.user_id
            LEFT JOIN tiktok_api_configs tc ON tc.internal_user_id = v.user_id
            LEFT JOIN server_account_links sal ON sal.id = pl.account_link_id
            WHERE {" AND ".join(pub_where)}
            ORDER BY pl.created_at DESC
        """
        pub_rows = conn.execute(pub_sql, pub_params).fetchall()

        seen_video_ids = {str(r["id"]) for r in pub_rows}
        out: list[dict[str, Any]] = []
        for r in pub_rows:
            out.append(_stats_publication_row(r, platform_id=str(r["platform_id"] or "")))

        if not platform_id and not creator_user_id and not link_sql:
            local_where = ["1=1"]
            local_params: list[Any] = []
            if seen_video_ids:
                placeholders = ",".join("?" for _ in seen_video_ids)
                local_where.append(f"v.id NOT IN ({placeholders})")
                local_params.extend(sorted(seen_video_ids))

            local_sql = f"""
                SELECT
                    v.id,
                    v.title,
                    v.views,
                    v.likes,
                    v.shares,
                    v.created_at,
                    u.username AS owner_username,
                    tc.id AS config_id,
                    tc.name AS config_name,
                    tc.tiktok_username,
                    (
                        SELECT COUNT(*) FROM comments c WHERE c.video_id = v.id
                    ) AS comment_count
                FROM videos v
                JOIN users u ON u.id = v.user_id
                LEFT JOIN tiktok_api_configs tc ON tc.internal_user_id = v.user_id
                WHERE {" AND ".join(local_where)}
                ORDER BY v.created_at DESC
            """
            for r in conn.execute(local_sql, local_params).fetchall():
                out.append(_stats_publication_row(r, platform_id=""))

        return out
    finally:
        conn.close()


def _stats_publication_row(row: sqlite3.Row, *, platform_id: str) -> dict[str, Any]:
    views = int(row["views"] or 0)
    likes = int(row["likes"] or 0)
    shares = int(row["shares"] or 0)
    comments = int(row["comment_count"] or 0)
    if "account_link_name" in row.keys() and row["account_link_name"]:
        account = str(row["account_link_name"])
        config_id = str(row["account_link_id"] or "") if "account_link_id" in row.keys() else ""
    elif row["config_id"]:
        account = _config_display_label(row)
        config_id = str(row["config_id"])
    else:
        account = str(row["owner_username"] or "—")
        config_id = ""
    return {
        "id": str(row["id"]),
        "publication_id": str(row["publication_id"]) if "publication_id" in row.keys() and row["publication_id"] else "",
        "platform_id": platform_id,
        "title": str(row["title"] or ""),
        "config_id": config_id,
        "account_link_id": str(row["account_link_id"]) if "account_link_id" in row.keys() and row["account_link_id"] else "",
        "account": account,
        "views": views,
        "likes": likes,
        "shares": shares,
        "comments": comments,
        "views_label": _fmt_metric(views),
        "likes_label": _fmt_metric(likes),
        "shares_label": _fmt_metric(shares),
        "comments_label": _fmt_metric(comments) if comments >= 1000 else str(comments),
        "created_at": str(row["created_at"] or ""),
        "published_at": str(row["published_at"]) if "published_at" in row.keys() and row["published_at"] else "",
    }


def count_comments_for_video(video_id: str) -> int:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM comments WHERE video_id = ?", (video_id,)
        ).fetchone()
        return int(row["c"]) if row else 0
    finally:
        conn.close()


def dashboard_stats(
    creator_user_id: str | None = None,
    *,
    platform_id: str | None = None,
    account_link_id: str | None = None,
    account_link_ids: list[str] | None = None,
) -> dict[str, int]:
    """Totales globales, por usuario, cuenta de servidores y/o por plataforma."""
    seed_admin_if_missing()
    conn = _connect()
    try:
        where_parts: list[str] = []
        params: list[Any] = []
        log_filters: list[str] = ["status = 'ok'", "video_id IS NOT NULL"]
        log_params: list[Any] = []

        if platform_id:
            log_filters.append("platform_id = ?")
            log_params.append(platform_id)
        link_sql, link_vals = _account_link_sql_filter(
            account_link_id, account_link_ids
        )
        if link_sql:
            log_filters.append(link_sql)
            log_params.extend(link_vals)

        if platform_id or link_sql:
            where_parts.append(
                f"""
                v.id IN (
                    SELECT DISTINCT video_id FROM publication_log
                    WHERE {" AND ".join(log_filters)}
                )
                """
            )
            params.extend(log_params)

        if creator_user_id:
            where_parts.append("v.user_id = ?")
            params.append(creator_user_id)

        where_sql = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""

        if creator_user_id or platform_id or link_sql:
            nv = conn.execute(
                f"SELECT COUNT(*) AS c FROM videos v{where_sql}",
                params,
            ).fetchone()
            nc = conn.execute(
                f"""
                SELECT COUNT(*) AS c FROM comments c
                JOIN videos v ON v.id = c.video_id
                {where_sql}
                """,
                params,
            ).fetchone()
            agg = conn.execute(
                f"""
                SELECT COALESCE(SUM(v.views),0) AS v, COALESCE(SUM(v.likes),0) AS l,
                       COALESCE(SUM(v.shares),0) AS s
                FROM videos v
                {where_sql}
                """,
                params,
            ).fetchone()
        else:
            nv = conn.execute("SELECT COUNT(*) AS c FROM videos").fetchone()
            nc = conn.execute("SELECT COUNT(*) AS c FROM comments").fetchone()
            agg = conn.execute(
                "SELECT COALESCE(SUM(views),0) AS v, COALESCE(SUM(likes),0) AS l, COALESCE(SUM(shares),0) AS s FROM videos"
            ).fetchone()
        return {
            "videos": int(nv["c"] if nv else 0),
            "comments": int(nc["c"] if nc else 0),
            "views": int(agg["v"] if agg else 0),
            "likes": int(agg["l"] if agg else 0),
            "shares": int(agg["s"] if agg else 0),
        }
    finally:
        conn.close()


def video_has_platform_publication(video_id: str, platform_id: str) -> bool:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT 1 FROM publication_log
            WHERE video_id = ? AND platform_id = ? AND status = 'ok'
            LIMIT 1
            """,
            (video_id, platform_id),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def add_comment(
    video_id: str,
    author_name: str,
    body: str,
    parent_id: str | None = None,
    is_creator_reply: bool = False,
) -> Comment:
    seed_admin_if_missing()
    if not body.strip():
        raise ValueError("Comment cannot be empty")
    cid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        if parent_id:
            prow = conn.execute(
                "SELECT id FROM comments WHERE id = ? AND video_id = ?",
                (parent_id, video_id),
            ).fetchone()
            if not prow:
                raise ValueError("Invalid parent comment")
        conn.execute(
            """INSERT INTO comments (id, video_id, parent_id, author_name, body, is_creator_reply, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                cid,
                video_id,
                parent_id,
                author_name.strip(),
                body.strip(),
                1 if is_creator_reply else 0,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    c = get_comment_by_id(cid)
    assert c is not None
    return c


def get_comment_by_id(cid: str) -> Comment | None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM comments WHERE id = ?", (cid,)).fetchone()
        if not row:
            return None
        return Comment(
            id=row["id"],
            video_id=row["video_id"],
            parent_id=row["parent_id"],
            author_name=row["author_name"],
            body=row["body"],
            is_creator_reply=bool(row["is_creator_reply"]),
            created_at=row["created_at"],
        )
    finally:
        conn.close()


def list_comments_with_video() -> list[tuple[Comment, str]]:
    """Comments newest first, with video title (sin límite; preferir list_comments_with_video_page)."""
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT c.*, v.title AS video_title
            FROM comments c
            JOIN videos v ON v.id = c.video_id
            ORDER BY c.created_at DESC
            """
        ).fetchall()
        out: list[tuple[Comment, str]] = []
        for r in rows:
            c = Comment(
                id=r["id"],
                video_id=r["video_id"],
                parent_id=r["parent_id"],
                author_name=r["author_name"],
                body=r["body"],
                is_creator_reply=bool(r["is_creator_reply"]),
                created_at=r["created_at"],
            )
            out.append((c, r["video_title"]))
        return out
    finally:
        conn.close()


def count_comments() -> int:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM comments").fetchone()
        return int(row["c"] if row else 0)
    finally:
        conn.close()


def list_comments_with_video_page(page: int, per_page: int) -> list[tuple[Comment, str]]:
    """Comentarios más recientes primero, con título del vídeo; paginado."""
    seed_admin_if_missing()
    page = max(1, int(page))
    per_page = max(1, min(int(per_page), 100))
    offset = (page - 1) * per_page
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT c.*, v.title AS video_title
            FROM comments c
            JOIN videos v ON v.id = c.video_id
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        ).fetchall()
        out: list[tuple[Comment, str]] = []
        for r in rows:
            c = Comment(
                id=r["id"],
                video_id=r["video_id"],
                parent_id=r["parent_id"],
                author_name=r["author_name"],
                body=r["body"],
                is_creator_reply=bool(r["is_creator_reply"]),
                created_at=r["created_at"],
            )
            out.append((c, r["video_title"]))
        return out
    finally:
        conn.close()


def count_comments_for_video_owners(owner_ids: list[str] | None) -> int:
    """None = todos; lista vacía = ninguno."""
    seed_admin_if_missing()
    if owner_ids is not None and len(owner_ids) == 0:
        return 0
    conn = _connect()
    try:
        if owner_ids is None:
            row = conn.execute("SELECT COUNT(*) AS c FROM comments").fetchone()
        else:
            ph = ",".join("?" * len(owner_ids))
            row = conn.execute(
                f"""
                SELECT COUNT(*) AS c FROM comments c
                JOIN videos v ON v.id = c.video_id
                WHERE v.user_id IN ({ph})
                """,
                owner_ids,
            ).fetchone()
        return int(row["c"] if row else 0)
    finally:
        conn.close()


def list_comments_with_video_page_for_owners(
    page: int,
    per_page: int,
    owner_ids: list[str] | None,
) -> list[tuple[Comment, str]]:
    seed_admin_if_missing()
    if owner_ids is not None and len(owner_ids) == 0:
        return []
    page = max(1, int(page))
    per_page = max(1, min(int(per_page), 100))
    offset = (page - 1) * per_page
    conn = _connect()
    try:
        if owner_ids is None:
            rows = conn.execute(
                """
                SELECT c.*, v.title AS video_title
                FROM comments c
                JOIN videos v ON v.id = c.video_id
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, offset),
            ).fetchall()
        else:
            ph = ",".join("?" * len(owner_ids))
            rows = conn.execute(
                f"""
                SELECT c.*, v.title AS video_title
                FROM comments c
                JOIN videos v ON v.id = c.video_id
                WHERE v.user_id IN ({ph})
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (*owner_ids, per_page, offset),
            ).fetchall()
        out: list[tuple[Comment, str]] = []
        for r in rows:
            c = Comment(
                id=r["id"],
                video_id=r["video_id"],
                parent_id=r["parent_id"],
                author_name=r["author_name"],
                body=r["body"],
                is_creator_reply=bool(r["is_creator_reply"]),
                created_at=r["created_at"],
            )
            out.append((c, r["video_title"]))
        return out
    finally:
        conn.close()


def list_comment_threads_for_owners(
    owner_ids: list[str] | None,
) -> list[dict[str, Any]]:
    """Comentarios agrupados por video, con plataformas publicadas y actividad reciente."""
    seed_admin_if_missing()
    if owner_ids is not None and len(owner_ids) == 0:
        return []
    conn = _connect()
    try:
        if owner_ids is None:
            rows = conn.execute(
                """
                SELECT c.*, v.title AS video_title, v.user_id AS owner_user_id,
                       u.username AS owner_username
                FROM comments c
                JOIN videos v ON v.id = c.video_id
                LEFT JOIN users u ON u.id = v.user_id
                ORDER BY c.created_at ASC
                """
            ).fetchall()
        else:
            ph = ",".join("?" * len(owner_ids))
            rows = conn.execute(
                f"""
                SELECT c.*, v.title AS video_title, v.user_id AS owner_user_id,
                       u.username AS owner_username
                FROM comments c
                JOIN videos v ON v.id = c.video_id
                LEFT JOIN users u ON u.id = v.user_id
                WHERE v.user_id IN ({ph})
                ORDER BY c.created_at ASC
                """,
                owner_ids,
            ).fetchall()

        video_ids = list({r["video_id"] for r in rows})
        platforms_by_video: dict[str, list[str]] = {}
        if video_ids:
            phv = ",".join("?" * len(video_ids))
            pl_rows = conn.execute(
                f"""
                SELECT DISTINCT video_id, platform_id
                FROM publication_log
                WHERE video_id IN ({phv}) AND status = 'ok' AND video_id IS NOT NULL
                """,
                video_ids,
            ).fetchall()
            for pr in pl_rows:
                vid = pr["video_id"]
                if vid:
                    platforms_by_video.setdefault(vid, []).append(pr["platform_id"])

        threads_map: dict[str, dict[str, Any]] = {}
        for r in rows:
            vid = r["video_id"]
            if vid not in threads_map:
                threads_map[vid] = {
                    "video_id": vid,
                    "video_title": r["video_title"] or "—",
                    "owner_user_id": r["owner_user_id"] or "",
                    "owner_username": r["owner_username"] or "—",
                    "platform_ids": sorted(set(platforms_by_video.get(vid, []))),
                    "comments": [],
                    "latest_at": r["created_at"],
                }
            thread = threads_map[vid]
            thread["comments"].append(
                {
                    "id": r["id"],
                    "parent_id": r["parent_id"],
                    "author_name": r["author_name"],
                    "body": r["body"],
                    "is_creator_reply": bool(r["is_creator_reply"]),
                    "created_at": r["created_at"],
                }
            )
            if r["created_at"] > thread["latest_at"]:
                thread["latest_at"] = r["created_at"]

        threads = list(threads_map.values())
        threads.sort(key=lambda t: t["latest_at"], reverse=True)
        return threads
    finally:
        conn.close()


def build_feed_clips() -> list[dict[str, Any]]:
    """Videos subidos en el feed (más recientes primero)."""
    seed_admin_if_missing()
    out: list[dict[str, Any]] = []
    for v in list_videos_newest():
        u = get_user_by_id(v.user_id)
        uname = u.username if u else "user"
        cc = count_comments_for_video(v.id)
        out.append(
            {
                "id": v.id,
                "title": v.title,
                "user": f"@{uname}",
                "src": f"/uploads/{v.file_name}",
                "views": v.views,
                "likes": v.likes,
                "shares": v.shares,
                "views_label": _fmt_metric(v.views),
                "likes_label": _fmt_metric(v.likes),
                "shares_label": _fmt_metric(v.shares),
                "comments_label": _fmt_metric(cc) if cc >= 1000 else str(cc),
            }
        )
    return out


def _mask_client_secret(secret: str) -> str:
    s = (secret or "").strip()
    if not s:
        return "(empty)"
    if len(s) <= 4:
        return "••••"
    return "••••••••" + s[-4:]


def _validate_tiktok_redirect_uri(uri: str) -> None:
    from urllib.parse import urlparse

    u = urlparse((uri or "").strip())
    if u.scheme not in ("http", "https"):
        raise ValueError("Redirect URL must start with http:// or https://")
    if not u.netloc:
        raise ValueError("Redirect URL is not valid.")


def list_tiktok_configs_for_stats_dropdown() -> list[dict[str, Any]]:
    """Registros TikTok con OAuth conectado."""
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, name, internal_user_id, tiktok_username, open_id, access_token
            FROM tiktok_api_configs
            WHERE access_token IS NOT NULL AND TRIM(access_token) != ''
            ORDER BY name COLLATE NOCASE ASC
            """
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            iu = r["internal_user_id"]
            if iu is not None:
                iu = str(iu).strip() or None
            out.append(
                {
                    "id": str(r["id"]),
                    "name": _config_display_label(r),
                    "internal_user_id": iu,
                    "tiktok_username": r["tiktok_username"],
                    "oauth_connected": True,
                }
            )
        return out
    finally:
        conn.close()


def get_config_internal_user_id(config_id: str) -> str | None:
    """Usuario interno (dueño de videos) para un registro TikToker, o None."""
    seed_admin_if_missing()
    cid = (config_id or "").strip()
    if not cid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT internal_user_id FROM tiktok_api_configs WHERE id = ?",
            (cid,),
        ).fetchone()
        if not row or row["internal_user_id"] is None:
            return None
        s = str(row["internal_user_id"]).strip()
        return s or None
    finally:
        conn.close()


def tiktok_config_id_exists(config_id: str) -> bool:
    seed_admin_if_missing()
    cid = (config_id or "").strip()
    if not cid:
        return False
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT 1 AS ok FROM tiktok_api_configs WHERE id = ?",
            (cid,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def publicaciones_tiktoker_choices(viewer: User) -> list[dict[str, Any]]:
    """Cuentas OAuth para selects en Publicaciones."""
    all_c = list_tiktok_configs_for_stats_dropdown()
    if user_has_admin_privileges(viewer):
        return all_c
    uid = viewer.id
    link = viewer.linked_tiktok_config_id
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in all_c:
        cid = c["id"]
        if cid in seen:
            continue
        iu = c.get("internal_user_id")
        if iu == uid or cid == link:
            out.append(c)
            seen.add(cid)
    return out


def tiktok_stat_choices_for_viewer(viewer: User) -> list[dict[str, Any]]:
    """Admin: todos los TikTokers. Usuario: solo los vinculados a su cuenta."""
    all_c = list_tiktok_configs_for_stats_dropdown()
    if user_has_admin_privileges(viewer):
        return all_c
    uid = viewer.id
    link = viewer.linked_tiktok_config_id
    picked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in all_c:
        cid = c["id"]
        if cid in seen:
            continue
        iu = c.get("internal_user_id")
        if iu == uid or cid == link:
            picked.append(c)
            seen.add(cid)
    return picked


def user_can_access_publicaciones(user: User) -> bool:
    if user_has_admin_privileges(user):
        return True
    if user.role != "user":
        return False
    m = user.user_mode
    return m in USER_MODES_CAN_UPLOAD_VIDEOS or m in USER_MODES_CAN_MANAGE_COMMENTS


def user_can_upload_videos(user: User) -> bool:
    if user_has_admin_privileges(user):
        return True
    if user.role != "user":
        return False
    return user.user_mode in USER_MODES_CAN_UPLOAD_VIDEOS


def user_can_manage_comments(user: User) -> bool:
    return bool(user.can_view_comments)


def tiktoker_choices_for_publish(viewer: User) -> list[dict[str, Any]]:
    """Configs con usuario interno (dueño del vídeo al publicar)."""
    all_c = list_tiktok_configs_for_stats_dropdown()
    with_user = [c for c in all_c if c.get("internal_user_id")]
    if user_has_admin_privileges(viewer):
        return with_user
    uid = viewer.id
    link = viewer.linked_tiktok_config_id
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in with_user:
        cid = c["id"]
        if cid in seen:
            continue
        iu = c.get("internal_user_id")
        if iu == uid or cid == link:
            out.append(c)
            seen.add(cid)
    return out


def allowed_video_owner_ids_for_user(viewer: User) -> set[str]:
    return {
        str(c["internal_user_id"])
        for c in tiktoker_choices_for_publish(viewer)
        if c.get("internal_user_id")
    }


def resolve_publish_owner_user_id(viewer: User, config_id: str) -> str | None:
    cfg_id = (config_id or "").strip()
    if not cfg_id:
        return None
    owner = get_config_internal_user_id(cfg_id)
    if not owner:
        return None
    if user_has_admin_privileges(viewer):
        return owner
    allowed = allowed_video_owner_ids_for_user(viewer)
    return owner if owner in allowed else None


def user_may_act_on_video_owner(viewer: User, video_owner_user_id: str) -> bool:
    if user_has_admin_privileges(viewer):
        return True
    return str(video_owner_user_id) in allowed_video_owner_ids_for_user(viewer)


def list_tiktok_equipo_choices() -> list[dict[str, str]]:
    """Cuentas TikTok OAuth para selects en Equipo."""
    return list_equipo_account_choices()


def list_equipo_account_choices(
    q: str = "",
    selected_id: str = "",
) -> list[dict[str, str]]:
    """Cuentas conectadas para vincular en Equipo (filtrable)."""
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.name, t.tiktok_username,
                   (
                     SELECT u.username FROM users u
                     WHERE u.linked_tiktok_config_id = t.id
                        OR u.id = t.internal_user_id
                     ORDER BY u.username COLLATE NOCASE ASC
                     LIMIT 1
                   ) AS linked_username
            FROM tiktok_api_configs t
            WHERE access_token IS NOT NULL AND TRIM(access_token) != ''
            ORDER BY name COLLATE NOCASE ASC, updated_at DESC
            """
        ).fetchall()
        items = []
        for r in rows:
            label = _config_display_label(r)
            linked = (r["linked_username"] or "").strip()
            if linked:
                label = f"{label} → {linked}"
            items.append(
                {
                    "id": str(r["id"]),
                    "name": label,
                    "_search": " ".join(
                        filter(
                            None,
                            [
                                str(r["name"] or ""),
                                str(r["tiktok_username"] or ""),
                                _config_display_label(r),
                                linked,
                            ],
                        )
                    ).lower(),
                }
            )
    finally:
        conn.close()
    query = q.strip().lower()
    selected = selected_id.strip()
    if query:
        items = [c for c in items if query in c["_search"]]
    if selected and not any(c["id"] == selected for c in items):
        conn = _connect()
        try:
            row = conn.execute(
                """
                SELECT t.id, t.name, t.tiktok_username,
                       (
                         SELECT u.username FROM users u
                         WHERE u.linked_tiktok_config_id = t.id
                            OR u.id = t.internal_user_id
                         ORDER BY u.username COLLATE NOCASE ASC
                         LIMIT 1
                       ) AS linked_username
                FROM tiktok_api_configs t
                WHERE t.id = ? AND access_token IS NOT NULL AND TRIM(access_token) != ''
                """,
                (selected,),
            ).fetchone()
            if row:
                label = _config_display_label(row)
                linked = (row["linked_username"] or "").strip()
                if linked:
                    label = f"{label} → {linked}"
                items.insert(
                    0,
                    {
                        "id": str(row["id"]),
                        "name": label,
                        "_search": "",
                    },
                )
        finally:
            conn.close()
    return [{"id": c["id"], "name": c["name"]} for c in items]


def list_tiktok_api_configs() -> list[dict[str, Any]]:
    """Listado para el panel (client_secret enmascarado)."""
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT t.*, u.username AS internal_username, u.display_name AS internal_display_name
            FROM tiktok_api_configs t
            LEFT JOIN users u ON u.id = t.internal_user_id
            ORDER BY t.updated_at DESC
            """
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "client_key": r["client_key"],
                    "client_secret_masked": _mask_client_secret(r["client_secret"]),
                    "redirect_uri": r["redirect_uri"],
                    "internal_user_id": r["internal_user_id"],
                    "internal_username": r["internal_username"],
                    "internal_display_name": r["internal_display_name"],
                    "notes": r["notes"] or "",
                    "active": bool(r["active"]),
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                }
            )
        return out
    finally:
        conn.close()


def get_tiktok_api_config(config_id: str) -> dict[str, Any] | None:
    """Registro completo (incluye client_secret) para edición vía API."""
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT t.*, u.username AS internal_username
            FROM tiktok_api_configs t
            LEFT JOIN users u ON u.id = t.internal_user_id
            WHERE t.id = ?
            """,
            (config_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "client_key": row["client_key"],
            "client_secret": row["client_secret"],
            "redirect_uri": row["redirect_uri"],
            "internal_user_id": row["internal_user_id"],
            "internal_username": row["internal_username"],
            "notes": row["notes"] or "",
            "active": bool(row["active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def create_tiktok_api_config(
    name: str,
    client_key: str,
    client_secret: str,
    redirect_uri: str,
    internal_user_id: str | None,
    notes: str,
    active: bool,
) -> dict[str, Any]:
    seed_admin_if_missing()
    n = (name or "").strip()
    ck = (client_key or "").strip()
    cs = (client_secret or "").strip()
    ru = (redirect_uri or "").strip()
    if len(n) < 1:
        raise ValueError("Name is required.")
    if len(ck) < 2:
        raise ValueError("Client key is too short.")
    if len(cs) < 4:
        raise ValueError("Client secret must be at least 4 characters.")
    _validate_tiktok_redirect_uri(ru)
    uid_clean = (internal_user_id or "").strip() or None
    if uid_clean and not get_user_by_id(uid_clean):
        raise ValueError("Internal user does not exist.")
    now = datetime.now(timezone.utc).isoformat()
    cid = str(uuid.uuid4())
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO tiktok_api_configs
            (id, name, client_key, client_secret, redirect_uri, internal_user_id, notes, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                n,
                ck,
                cs,
                ru,
                uid_clean,
                (notes or "").strip(),
                1 if active else 0,
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    out = get_tiktok_api_config(cid)
    assert out is not None
    return out


def update_tiktok_api_config(
    config_id: str,
    name: str,
    client_key: str,
    client_secret: str | None,
    redirect_uri: str,
    internal_user_id: str | None,
    notes: str,
    active: bool,
) -> None:
    seed_admin_if_missing()
    existing = get_tiktok_api_config(config_id)
    if not existing:
        raise ValueError("Configuration not found.")
    n = (name or "").strip()
    ck = (client_key or "").strip()
    ru = (redirect_uri or "").strip()
    if len(n) < 1:
        raise ValueError("Name is required.")
    if len(ck) < 2:
        raise ValueError("Client key is too short.")
    _validate_tiktok_redirect_uri(ru)
    uid_clean = (internal_user_id or "").strip() or None
    if uid_clean and not get_user_by_id(uid_clean):
        raise ValueError("Internal user does not exist.")
    cs_final = existing["client_secret"]
    if client_secret is not None:
        cs_new = client_secret.strip()
        if cs_new:
            if len(cs_new) < 4:
                raise ValueError("Client secret must be at least 4 characters.")
            cs_final = cs_new
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE tiktok_api_configs SET
              name = ?, client_key = ?, client_secret = ?, redirect_uri = ?,
              internal_user_id = ?, notes = ?, active = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                n,
                ck,
                cs_final,
                ru,
                uid_clean,
                (notes or "").strip(),
                1 if active else 0,
                now,
                config_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_tiktok_api_config(config_id: str) -> None:
    seed_admin_if_missing()
    cid = (config_id or "").strip()
    conn = _connect()
    try:
        cur = conn.execute("SELECT 1 AS ok FROM tiktok_api_configs WHERE id = ?", (cid,))
        if not cur.fetchone():
            raise ValueError("Configuration not found.")
        _delete_tiktok_config_on_conn(conn, cid)
        _prune_empty_account_links_on_conn(conn)
        conn.commit()
    finally:
        conn.close()
    sync_server_accounts_from_links()


def _config_display_label(row: sqlite3.Row | dict[str, Any]) -> str:
    if isinstance(row, sqlite3.Row):
        d = dict(row)
    else:
        d = row
    uname = (d.get("tiktok_username") or "").strip()
    if uname:
        return f"@{uname.lstrip('@')}"
    return str(d.get("name") or "TikTok account")


def list_connected_tiktok_accounts() -> list[dict[str, Any]]:
    """Cuentas vinculadas vía OAuth (con token)."""
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT t.*, u.username AS internal_username, u.display_name AS internal_display_name
            FROM tiktok_api_configs t
            LEFT JOIN users u ON u.id = t.internal_user_id
            WHERE t.access_token IS NOT NULL AND TRIM(t.access_token) != ''
            ORDER BY t.updated_at DESC
            """
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            label = _config_display_label(r)
            out.append(
                {
                    "id": r["id"],
                    "name": label,
                    "tiktok_username": r["tiktok_username"],
                    "display_name": r["name"],
                    "open_id": r["open_id"],
                    "internal_user_id": r["internal_user_id"],
                    "internal_username": r["internal_username"],
                    "active": bool(r["active"]),
                    "connected_at": r["updated_at"],
                    "has_token": True,
                }
            )
        return out
    finally:
        conn.close()


def get_tiktok_by_open_id(open_id: str) -> dict[str, Any] | None:
    seed_admin_if_missing()
    oid = (open_id or "").strip()
    if not oid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM tiktok_api_configs WHERE open_id = ?",
            (oid,),
        ).fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def save_tiktok_oauth_connection(
    *,
    open_id: str,
    tiktok_username: str | None,
    display_name: str | None,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
    scopes: str,
    client_key: str,
    client_secret: str,
    redirect_uri: str,
    linked_by_user_id: str | None = None,
) -> str:
    """Crea o actualiza cuenta OAuth; devuelve config id."""
    seed_admin_if_missing()
    oid = open_id.strip()
    if not oid:
        raise ValueError("open_id missing from TikTok.")
    uname = (tiktok_username or "").strip().lstrip("@") or None
    label = display_name.strip() if display_name else None
    if not label and uname:
        label = f"@{uname}"
    if not label:
        label = "TikTok account"
    now = datetime.now(timezone.utc).isoformat()
    expires_at: str | None = None
    if expires_in and expires_in > 0:
        from datetime import timedelta

        exp = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        expires_at = exp.isoformat()
    conn = _connect()
    try:
        existing = conn.execute(
            "SELECT id, internal_user_id FROM tiktok_api_configs WHERE open_id = ?",
            (oid,),
        ).fetchone()
        if existing:
            cid = str(existing["id"])
            iu = existing["internal_user_id"]
            if not iu and linked_by_user_id:
                iu = linked_by_user_id
            conn.execute(
                """
                UPDATE tiktok_api_configs SET
                  name = ?, tiktok_username = ?, access_token = ?, refresh_token = ?,
                  token_expires_at = ?, oauth_scopes = ?, client_key = ?, client_secret = ?,
                  redirect_uri = ?, internal_user_id = COALESCE(?, internal_user_id),
                  active = 1, updated_at = ?
                WHERE id = ?
                """,
                (
                    label,
                    uname,
                    access_token,
                    refresh_token,
                    expires_at,
                    scopes,
                    client_key,
                    client_secret,
                    redirect_uri,
                    linked_by_user_id,
                    now,
                    cid,
                ),
            )
        else:
            cid = str(uuid.uuid4())
            iu = linked_by_user_id
            conn.execute(
                """
                INSERT INTO tiktok_api_configs (
                  id, name, client_key, client_secret, redirect_uri, internal_user_id,
                  notes, active, created_at, updated_at, open_id, tiktok_username,
                  access_token, refresh_token, token_expires_at, oauth_scopes
                ) VALUES (?, ?, ?, ?, ?, ?, '', 1, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    label,
                    client_key,
                    client_secret,
                    redirect_uri,
                    iu,
                    now,
                    now,
                    oid,
                    uname,
                    access_token,
                    refresh_token,
                    expires_at,
                    scopes,
                ),
            )
        conn.commit()
    finally:
        conn.close()
    sync_server_accounts_from_links()
    return cid


def list_oauth_accounts_public(platform_id: str) -> list[dict[str, Any]]:
    seed_admin_if_missing()
    pid = (platform_id or "").strip()
    if not pid:
        return []
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT o.*, u.username AS internal_username
            FROM oauth_accounts o
            LEFT JOIN users u ON u.id = o.linked_by_user_id
            WHERE o.platform_id = ?
              AND o.access_token IS NOT NULL AND TRIM(o.access_token) != ''
            ORDER BY o.updated_at DESC
            """,
            (pid,),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            uname = str(r["username"] or "").strip()
            label = str(r["display_name"] or "").strip()
            if uname and not label:
                label = f"@{uname}"
            if not label:
                label = pid
            out.append(
                {
                    "id": r["id"],
                    "name": label,
                    "username": uname,
                    "open_id": r["open_id"],
                    "internal_username": r["internal_username"],
                    "active": bool(r["active"]),
                    "connected_at": r["updated_at"],
                    "has_token": True,
                }
            )
        return out
    finally:
        conn.close()


def get_oauth_account_row(account_id: str) -> dict[str, Any] | None:
    seed_admin_if_missing()
    oid = (account_id or "").strip()
    if not oid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM oauth_accounts WHERE id = ?", (oid,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_oauth_connection(
    *,
    platform_id: str,
    open_id: str,
    username: str | None,
    display_name: str | None,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
    scopes: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    linked_by_user_id: str | None = None,
) -> str:
    seed_admin_if_missing()
    pid = (platform_id or "").strip()
    oid = (open_id or "").strip()
    token = (access_token or "").strip()
    if not pid or not oid or not token:
        raise ValueError("OAuth account data is incomplete.")
    uname = (username or "").strip().lstrip("@") or None
    label = (display_name or "").strip() if display_name else None
    if not label and uname:
        label = f"@{uname}"
    if not label:
        label = pid
    now = datetime.now(timezone.utc).isoformat()
    expires_at: str | None = None
    if expires_in and int(expires_in) > 0:
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        ).isoformat()
    conn = _connect()
    try:
        existing = conn.execute(
            "SELECT id, linked_by_user_id FROM oauth_accounts WHERE platform_id = ? AND open_id = ?",
            (pid, oid),
        ).fetchone()
        if existing:
            cid = str(existing["id"])
            conn.execute(
                """
                UPDATE oauth_accounts SET
                  username = ?, display_name = ?, access_token = ?, refresh_token = COALESCE(?, refresh_token),
                  token_expires_at = ?, oauth_scopes = ?, client_id = ?, client_secret = ?,
                  redirect_uri = ?, linked_by_user_id = COALESCE(?, linked_by_user_id),
                  active = 1, updated_at = ?
                WHERE id = ?
                """,
                (
                    uname,
                    label,
                    token,
                    (refresh_token or "").strip() or None,
                    expires_at,
                    scopes,
                    client_id,
                    client_secret,
                    redirect_uri,
                    linked_by_user_id,
                    now,
                    cid,
                ),
            )
        else:
            cid = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO oauth_accounts (
                  id, platform_id, open_id, username, display_name, access_token, refresh_token,
                  token_expires_at, oauth_scopes, client_id, client_secret, redirect_uri,
                  linked_by_user_id, active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    cid,
                    pid,
                    oid,
                    uname,
                    label,
                    token,
                    (refresh_token or "").strip() or None,
                    expires_at,
                    scopes,
                    client_id,
                    client_secret,
                    redirect_uri,
                    linked_by_user_id,
                    now,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()
    sync_server_accounts_from_links()
    return cid


def update_oauth_tokens(
    account_id: str,
    *,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
) -> None:
    seed_admin_if_missing()
    cid = (account_id or "").strip()
    token = (access_token or "").strip()
    if not cid or not token:
        return
    now = datetime.now(timezone.utc)
    expires_at = None
    if expires_in and int(expires_in) > 0:
        expires_at = (now + timedelta(seconds=int(expires_in))).isoformat()
    conn = _connect()
    try:
        if refresh_token:
            conn.execute(
                """
                UPDATE oauth_accounts
                SET access_token = ?, refresh_token = ?, token_expires_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (token, refresh_token, expires_at, now.isoformat(), cid),
            )
        else:
            conn.execute(
                """
                UPDATE oauth_accounts
                SET access_token = ?, token_expires_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (token, expires_at, now.isoformat(), cid),
            )
        conn.commit()
    finally:
        conn.close()


def delete_oauth_account(account_id: str) -> None:
    seed_admin_if_missing()
    oid = (account_id or "").strip()
    if not oid:
        raise ValueError("not_found")
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id FROM oauth_accounts WHERE id = ?", (oid,)
        ).fetchone()
        if not row:
            raise ValueError("not_found")
        _delete_oauth_account_on_conn(conn, oid)
        conn.commit()
    finally:
        conn.close()
    sync_server_accounts_from_links()


def get_oauth_account_id_for_account_name(platform_id: str, account_name: str) -> str | None:
    seed_admin_if_missing()
    pid = (platform_id or "").strip()
    label = (account_name or "").strip().lstrip("@")
    if not pid or not label:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id FROM oauth_accounts
            WHERE platform_id = ?
              AND access_token IS NOT NULL AND TRIM(access_token) != ''
              AND (
                lower(trim(display_name)) = lower(trim(?))
                OR lower(trim(username)) = lower(trim(?))
                OR lower(trim(username)) = lower(trim(?))
              )
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (pid, label, label, f"@{label}"),
        ).fetchone()
        return str(row["id"]) if row else None
    finally:
        conn.close()


def resolve_oauth_account_id(
    platform_id: str,
    *,
    account_id: str | None = None,
    account_link_id: str | None = None,
) -> str | None:
    pid = (platform_id or "").strip()
    cid = (account_id or "").strip()
    if cid:
        row = get_oauth_account_row(cid)
        if row and str(row.get("platform_id") or "") == pid:
            return cid
    lid = (account_link_id or "").strip()
    if lid:
        row = get_account_platform_row(lid, pid)
        if row and str(row.get("source_kind") or "") == "oauth":
            ref = str(row.get("source_ref") or "").strip()
            if ref:
                return ref
        name = get_account_link_name(lid) or ""
        found = get_oauth_account_id_for_account_name(pid, name)
        if found:
            return found
        return None
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id FROM oauth_accounts
            WHERE platform_id = ?
              AND access_token IS NOT NULL AND TRIM(access_token) != ''
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (pid,),
        ).fetchone()
        return str(row["id"]) if row else None
    finally:
        conn.close()


def _mask_secret(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    if len(s) <= 4:
        return "••••"
    return "••••" + s[-4:]


def get_platform_credentials_raw(platform_id: str) -> dict[str, Any] | None:
    seed_admin_if_missing()
    pid = (platform_id or "").strip()
    if not pid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM platform_credentials WHERE platform_id = ?",
            (pid,),
        ).fetchone()
        if not row:
            return None
        data = {k: row[k] for k in row.keys()}
        # SQLite guarda booleanos como 0/1; normalizar para comparaciones `is True`.
        if data.get("last_test_ok") is not None:
            data["last_test_ok"] = bool(data["last_test_ok"])
        return data
    finally:
        conn.close()


def get_platform_credentials_public(platform_id: str) -> dict[str, Any]:
    raw = get_platform_credentials_raw(platform_id) or {}
    ok = raw.get("last_test_ok")
    return {
        "platform_id": platform_id,
        "name": (raw.get("name") or "").strip(),
        "client_id": raw.get("client_id") or "",
        "client_secret_set": bool((raw.get("client_secret") or "").strip()),
        "client_secret_mask": _mask_secret(raw.get("client_secret") or ""),
        "access_token_set": bool((raw.get("access_token") or "").strip()),
        "access_token_mask": _mask_secret(raw.get("access_token") or ""),
        "extra": raw.get("extra") or "",
        "last_test_ok": None if ok is None else bool(ok),
        "last_test_at": raw.get("last_test_at") or "",
        "last_test_message": raw.get("last_test_message") or "",
        "configured": bool(
            (raw.get("client_id") or "").strip()
            or (raw.get("client_secret") or "").strip()
            or (raw.get("access_token") or "").strip()
            or (raw.get("extra") or "").strip()
        ),
    }


def list_platform_credentials_public() -> dict[str, dict[str, Any]]:
    from platforms import PLATFORM_IDS

    return {pid: get_platform_credentials_public(pid) for pid in PLATFORM_IDS}


def upsert_platform_credentials(
    platform_id: str,
    *,
    name: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    access_token: str | None = None,
    extra: str | None = None,
) -> dict[str, Any]:
    seed_admin_if_missing()
    pid = (platform_id or "").strip()
    existing = get_platform_credentials_raw(pid) or {}
    now = datetime.now(timezone.utc).isoformat()

    cred_name = existing.get("name") or ""
    if name is not None:
        cred_name = name.strip()

    cid = existing.get("client_id") or ""
    if client_id is not None:
        cid = client_id.strip()

    secret = existing.get("client_secret") or ""
    if client_secret is not None and client_secret.strip() and client_secret.strip() != "unchanged":
        secret = client_secret.strip()

    token = existing.get("access_token") or ""
    if access_token is not None and access_token.strip() and access_token.strip() != "unchanged":
        token = access_token.strip()

    extra_val = existing.get("extra") or ""
    if extra is not None:
        extra_val = extra.strip()

    conn = _connect()
    try:
        if cred_name:
            has_link = conn.execute(
                """
                SELECT 1 AS ok FROM server_account_links
                WHERE lower(trim(name)) = lower(trim(?))
                """,
                (cred_name,),
            ).fetchone()
            if not has_link and _account_name_used_by_group(conn, cred_name):
                raise ValueError("group_name_conflict")
        conn.execute(
            """
            INSERT INTO platform_credentials (
                platform_id, name, client_id, client_secret, access_token, extra,
                last_test_ok, last_test_at, last_test_message, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform_id) DO UPDATE SET
                name = excluded.name,
                client_id = excluded.client_id,
                client_secret = excluded.client_secret,
                access_token = excluded.access_token,
                extra = excluded.extra,
                updated_at = excluded.updated_at
            """,
            (
                pid,
                cred_name,
                cid,
                secret,
                token,
                extra_val,
                existing.get("last_test_ok"),
                existing.get("last_test_at") or "",
                existing.get("last_test_message") or "",
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    sync_server_accounts_from_links()
    return get_platform_credentials_public(pid)


def save_platform_test_result(platform_id: str, ok: bool, message: str) -> None:
    seed_admin_if_missing()
    now = datetime.now(timezone.utc).isoformat()
    pid = (platform_id or "").strip()
    conn = _connect()
    try:
        existing = conn.execute(
            "SELECT platform_id FROM platform_credentials WHERE platform_id = ?",
            (pid,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE platform_credentials
                SET last_test_ok = ?, last_test_at = ?, last_test_message = ?, updated_at = ?
                WHERE platform_id = ?
                """,
                (1 if ok else 0, now, (message or "")[:400], now, pid),
            )
        else:
            conn.execute(
                """
                INSERT INTO platform_credentials (
                    platform_id, name, client_id, client_secret, access_token, extra,
                    last_test_ok, last_test_at, last_test_message, updated_at
                ) VALUES (?, '', '', '', '', '', ?, ?, ?, ?)
                """,
                (pid, 1 if ok else 0, now, (message or "")[:400], now),
            )
        conn.commit()
    finally:
        conn.close()


def get_account_link_name(link_id: str) -> str | None:
    seed_admin_if_missing()
    lid = (link_id or "").strip()
    if not lid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT name FROM server_account_links WHERE id = ?", (lid,)
        ).fetchone()
        name = str(row["name"] or "").strip() if row else ""
        return name or None
    finally:
        conn.close()


def get_account_platform_row(account_link_id: str, platform_id: str) -> dict[str, Any] | None:
    """Fila de server_accounts de esa cuenta en ese servidor."""
    seed_admin_if_missing()
    name = get_account_link_name(account_link_id)
    pid = (platform_id or "").strip()
    if not name or not pid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT * FROM server_accounts
            WHERE lower(trim(name)) = lower(trim(?))
              AND platform_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (name, pid),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_tiktok_access_token_for_config(config_id: str) -> str | None:
    seed_admin_if_missing()
    cid = (config_id or "").strip()
    if not cid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT access_token FROM tiktok_api_configs
            WHERE id = ? AND access_token IS NOT NULL AND TRIM(access_token) != ''
            """,
            (cid,),
        ).fetchone()
        if row and row["access_token"]:
            return str(row["access_token"])
        return None
    finally:
        conn.close()


def get_tiktok_access_token_for_account_name(account_name: str) -> str | None:
    """Token TikTok de la cuenta cuyo nombre o @usuario coincide."""
    seed_admin_if_missing()
    label = (account_name or "").strip().lstrip("@")
    if not label:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT access_token FROM tiktok_api_configs
            WHERE access_token IS NOT NULL AND TRIM(access_token) != ''
              AND (
                lower(trim(name)) = lower(trim(?))
                OR lower(trim(tiktok_username)) = lower(trim(?))
                OR lower(trim(tiktok_username)) = lower(trim(?))
              )
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (label, label, f"@{label}"),
        ).fetchone()
        if row and row["access_token"]:
            return str(row["access_token"])
        return None
    finally:
        conn.close()


def get_tiktok_config_id_for_account_name(account_name: str) -> str | None:
    seed_admin_if_missing()
    label = (account_name or "").strip().lstrip("@")
    if not label:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id FROM tiktok_api_configs
            WHERE access_token IS NOT NULL AND TRIM(access_token) != ''
              AND (
                lower(trim(name)) = lower(trim(?))
                OR lower(trim(tiktok_username)) = lower(trim(?))
                OR lower(trim(tiktok_username)) = lower(trim(?))
              )
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (label, label, f"@{label}"),
        ).fetchone()
        return str(row["id"]) if row else None
    finally:
        conn.close()


def get_tiktok_oauth_row(config_id: str) -> dict[str, Any] | None:
    """Fila OAuth completa (tokens) para publicar."""
    seed_admin_if_missing()
    cid = (config_id or "").strip()
    if not cid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM tiktok_api_configs WHERE id = ?", (cid,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_tiktok_oauth_tokens(
    config_id: str,
    *,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
) -> None:
    seed_admin_if_missing()
    cid = (config_id or "").strip()
    token = (access_token or "").strip()
    if not cid or not token:
        return
    now = datetime.now(timezone.utc)
    expires_at = None
    if expires_in and int(expires_in) > 0:
        expires_at = (now + timedelta(seconds=int(expires_in))).isoformat()
    conn = _connect()
    try:
        if refresh_token:
            conn.execute(
                """
                UPDATE tiktok_api_configs
                SET access_token = ?, refresh_token = ?, token_expires_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (token, refresh_token, expires_at, now.isoformat(), cid),
            )
        else:
            conn.execute(
                """
                UPDATE tiktok_api_configs
                SET access_token = ?, token_expires_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (token, expires_at, now.isoformat(), cid),
            )
        conn.commit()
    finally:
        conn.close()


def resolve_tiktok_config_id(
    *,
    config_id: str | None = None,
    account_link_id: str | None = None,
) -> str | None:
    """Elige la cuenta TikTok OAuth de esa publicación o extracción."""
    cid = (config_id or "").strip()
    if cid and get_tiktok_oauth_row(cid):
        return cid
    lid = (account_link_id or "").strip()
    if lid:
        row = get_account_platform_row(lid, "tiktok")
        if row and str(row.get("source_kind") or "") == "tiktok":
            ref = str(row.get("source_ref") or "").strip()
            if ref:
                return ref
        name = get_account_link_name(lid) or ""
        found = get_tiktok_config_id_for_account_name(name)
        if found:
            return found
    return None


def get_first_tiktok_access_token() -> str | None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT access_token FROM tiktok_api_configs
            WHERE access_token IS NOT NULL AND TRIM(access_token) != ''
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ).fetchone()
        if row and row["access_token"]:
            return str(row["access_token"])
        return None
    finally:
        conn.close()


def _platform_cred_is_configured(raw: dict[str, Any] | None) -> bool:
    if not raw:
        return False
    return bool(
        (raw.get("client_id") or "").strip()
        or (raw.get("client_secret") or "").strip()
        or (raw.get("access_token") or "").strip()
        or (raw.get("extra") or "").strip()
    )


def _normalize_account_name(name: str) -> str:
    return (name or "").strip()


def _server_account_name_in_use(
    conn: sqlite3.Connection,
    platform_id: str,
    name: str,
    *,
    exclude_id: str = "",
) -> bool:
    label = _normalize_account_name(name)
    pid = (platform_id or "").strip()
    if not label or not pid:
        return False
    if exclude_id:
        row = conn.execute(
            """
            SELECT 1 AS ok FROM server_accounts
            WHERE platform_id = ? AND lower(trim(name)) = lower(trim(?)) AND id != ?
            """,
            (pid, label, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT 1 AS ok FROM server_accounts
            WHERE platform_id = ? AND lower(trim(name)) = lower(trim(?))
            """,
            (pid, label),
        ).fetchone()
    return bool(row)


def _resolve_account_name(
    conn: sqlite3.Connection,
    platform_id: str,
    desired_name: str,
    *,
    exclude_id: str = "",
    keep_existing_on_conflict: bool = False,
) -> str:
    label = _normalize_account_name(desired_name)
    if not label:
        raise ValueError("name_required")
    if _server_account_name_in_use(conn, platform_id, label, exclude_id=exclude_id):
        if keep_existing_on_conflict and exclude_id:
            row = conn.execute(
                "SELECT name FROM server_accounts WHERE id = ?", (exclude_id,)
            ).fetchone()
            if row and row["name"]:
                return str(row["name"])
        raise ValueError("name_taken")
    return label


def _ensure_account_link(
    conn: sqlite3.Connection, name: str, *, active: bool = True
) -> str:
    label = _normalize_account_name(name)
    if not label:
        return ""
    row = conn.execute(
        """
        SELECT id FROM server_account_links
        WHERE lower(trim(name)) = lower(trim(?))
        """,
        (label,),
    ).fetchone()
    if row:
        return str(row["id"])
    if _account_name_used_by_group(conn, label):
        raise ValueError("group_name_conflict")
    now = datetime.now(timezone.utc).isoformat()
    lid = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO server_account_links (id, name, active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (lid, label, 1 if active else 0, now, now),
    )
    return lid


def _upsert_linked_server_account(
    conn: sqlite3.Connection,
    *,
    source_kind: str,
    source_ref: str,
    name: str,
    platform_id: str,
    active: bool,
) -> str:
    now = datetime.now(timezone.utc).isoformat()
    row = conn.execute(
        """
        SELECT id FROM server_accounts
        WHERE source_kind = ? AND source_ref = ?
        """,
        (source_kind, source_ref),
    ).fetchone()
    if row:
        aid = str(row["id"])
        safe_name = _resolve_account_name(
            conn,
            platform_id,
            name,
            exclude_id=aid,
            keep_existing_on_conflict=True,
        )
        conn.execute(
            """
            UPDATE server_accounts
            SET name = ?, platform_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (safe_name, platform_id, now, aid),
        )
        _ensure_account_link(conn, safe_name, active=active)
        return aid
    safe_name = _resolve_account_name(conn, platform_id, name)
    aid = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO server_accounts (
            id, name, platform_id, active, created_at, updated_at, source_kind, source_ref
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (aid, safe_name, platform_id, 1 if active else 0, now, now, source_kind, source_ref),
    )
    _ensure_account_link(conn, safe_name, active=active)
    return aid


def sync_server_accounts_from_links() -> None:
    """Refleja en server_accounts las cuentas vinculadas de cada servidor."""
    from platforms import PLATFORM_IDS, platform_list

    seed_admin_if_missing()
    names = {p["id"]: p["name"] for p in platform_list("es")}
    conn = _connect()
    try:
        tiktok_rows = conn.execute(
            """
            SELECT id, name, tiktok_username, active, updated_at
            FROM tiktok_api_configs
            WHERE access_token IS NOT NULL AND TRIM(access_token) != ''
            """
        ).fetchall()
        live_tiktok: set[str] = set()
        for row in tiktok_rows:
            cid = str(row["id"])
            live_tiktok.add(cid)
            label = _config_display_label(row)
            _upsert_linked_server_account(
                conn,
                source_kind="tiktok",
                source_ref=cid,
                name=label,
                platform_id="tiktok",
                active=bool(row["active"]),
            )

        live_oauth: set[str] = set()
        oauth_platforms: set[str] = set()
        oauth_rows = conn.execute(
            """
            SELECT id, platform_id, username, display_name, active
            FROM oauth_accounts
            WHERE access_token IS NOT NULL AND TRIM(access_token) != ''
            """
        ).fetchall()
        for row in oauth_rows:
            oid = str(row["id"])
            pid = str(row["platform_id"] or "")
            live_oauth.add(oid)
            if pid:
                oauth_platforms.add(pid)
            uname = str(row["username"] or "").strip()
            label = str(row["display_name"] or "").strip() or (f"@{uname}" if uname else pid)
            _upsert_linked_server_account(
                conn,
                source_kind="oauth",
                source_ref=oid,
                name=label,
                platform_id=pid,
                active=bool(row["active"]),
            )

        live_platform: set[str] = set()
        for pid in PLATFORM_IDS:
            if pid in oauth_platforms:
                continue
            row = conn.execute(
                "SELECT * FROM platform_credentials WHERE platform_id = ?",
                (pid,),
            ).fetchone()
            raw = {k: row[k] for k in row.keys()} if row else None
            if not _platform_cred_is_configured(raw):
                continue
            live_platform.add(pid)
            cred_name = (raw.get("name") or "").strip() if raw else ""
            label = cred_name or names.get(pid, pid)
            _upsert_linked_server_account(
                conn,
                source_kind="platform",
                source_ref=pid,
                name=label,
                platform_id=pid,
                active=True,
            )

        for row in conn.execute(
            "SELECT id, source_kind, source_ref FROM server_accounts WHERE source_kind != 'manual'"
        ).fetchall():
            kind = str(row["source_kind"] or "")
            ref = str(row["source_ref"] or "")
            stale = (
                (kind == "tiktok" and ref not in live_tiktok)
                or (kind == "oauth" and ref not in live_oauth)
                or (kind == "platform" and ref not in live_platform)
            )
            if stale:
                conn.execute("DELETE FROM server_accounts WHERE id = ?", (row["id"],))

        conn.commit()
    finally:
        conn.close()


def list_server_accounts(lang: str = "es") -> list[dict[str, Any]]:
    from platforms import platform_list

    sync_server_accounts_from_links()
    names = {p["id"]: p["name"] for p in platform_list(lang)}
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM server_accounts ORDER BY name COLLATE NOCASE, created_at"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "platform_id": r["platform_id"],
                "platform": names.get(r["platform_id"], r["platform_id"]),
                "active": bool(r["active"]),
                "source_kind": (r["source_kind"] or "manual") if "source_kind" in r.keys() else "manual",
                "source_ref": (r["source_ref"] or "") if "source_ref" in r.keys() else "",
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def _build_server_account_groups(
    accounts: list[dict[str, Any]],
    links: list[sqlite3.Row] | None = None,
) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for account in accounts:
        key = (account.get("name") or "").strip().casefold()
        if not key:
            continue
        by_name.setdefault(key, []).append(account)
    groups: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    if links:
        for link in links:
            name = str(link["name"] or "").strip()
            key = name.casefold()
            if not key:
                continue
            seen_keys.add(key)
            members_sorted = sorted(
                by_name.get(key, []),
                key=lambda item: (item.get("platform") or "").casefold(),
            )
            groups.append(
                {
                    "key": key,
                    "name": name,
                    "link_id": str(link["id"]),
                    "accounts": members_sorted,
                    "linked_count": len(members_sorted),
                    "active": bool(link["active"]),
                }
            )
    for key, members in by_name.items():
        if key in seen_keys:
            continue
        members_sorted = sorted(
            members,
            key=lambda item: (item.get("platform") or "").casefold(),
        )
        groups.append(
            {
                "key": key,
                "name": members_sorted[0]["name"],
                "link_id": "",
                "accounts": members_sorted,
                "linked_count": len(members_sorted),
                "active": all(item.get("active") for item in members_sorted),
            }
        )
    groups.sort(key=lambda item: item["name"].casefold())
    return groups


def _server_account_group_matches_query(group: dict[str, Any], query: str) -> bool:
    q = (query or "").strip().casefold()
    if not q:
        return True
    if q in (group.get("name") or "").casefold():
        return True
    for account in group.get("accounts") or []:
        if q in (account.get("platform") or "").casefold():
            return True
        if q in (account.get("platform_id") or "").casefold():
            return True
    return False


def list_server_account_groups(
    q: str = "",
    page: int = 1,
    per_page: int | None = TEAM_MEMBERS_PAGE_SIZE,
    *,
    lang: str = "es",
) -> tuple[list[dict[str, Any]], int]:
    groups = get_server_account_groups(lang)
    if (q or "").strip():
        groups = [g for g in groups if _server_account_group_matches_query(g, q)]
    total = len(groups)
    if per_page is None:
        return groups, total
    page = max(1, int(page))
    per_page = max(1, int(per_page))
    start = (page - 1) * per_page
    return groups[start : start + per_page], total


def _server_account_public(
    conn: sqlite3.Connection, account_id: str, *, lang: str = "es"
) -> dict[str, Any] | None:
    from platforms import platform_list

    row = conn.execute(
        "SELECT * FROM server_accounts WHERE id = ?", (account_id,)
    ).fetchone()
    if not row:
        return None
    names = {p["id"]: p["name"] for p in platform_list(lang)}
    return {
        "id": row["id"],
        "key": row["id"],
        "account_id": row["id"],
        "name": row["name"],
        "platform_id": row["platform_id"],
        "platform": names.get(row["platform_id"], row["platform_id"]),
        "active": bool(row["active"]),
        "source_kind": (row["source_kind"] or "manual") if "source_kind" in row.keys() else "manual",
        "source_ref": (row["source_ref"] or "") if "source_ref" in row.keys() else "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_server_account(name: str, platform_id: str, *, lang: str = "es") -> dict[str, Any]:
    from platforms import PLATFORM_IDS

    seed_admin_if_missing()
    label = (name or "").strip()
    pid = (platform_id or "").strip()
    if not label:
        raise ValueError("name_required")
    if pid not in PLATFORM_IDS:
        raise ValueError("platform_required")
    aid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        safe_name = _resolve_account_name(conn, pid, label)
        if _account_name_used_by_group(conn, safe_name):
            raise ValueError("group_name_conflict")
        conn.execute(
            """
            INSERT INTO server_accounts (
                id, name, platform_id, active, created_at, updated_at, source_kind, source_ref
            )
            VALUES (?, ?, ?, 1, ?, ?, 'manual', '')
            """,
            (aid, safe_name, pid, now, now),
        )
        _ensure_account_link(conn, safe_name, active=True)
        conn.commit()
        created = _server_account_public(conn, aid, lang=lang)
    finally:
        conn.close()
    if not created:
        raise ValueError("save_fail")
    return created


def update_server_account(
    account_id: str, name: str, platform_id: str, *, lang: str = "es"
) -> dict[str, Any]:
    from platforms import PLATFORM_IDS

    seed_admin_if_missing()
    aid = (account_id or "").strip()
    label = (name or "").strip()
    pid = (platform_id or "").strip()
    if not aid:
        raise ValueError("not_found")
    if not label:
        raise ValueError("name_required")
    if pid not in PLATFORM_IDS:
        raise ValueError("platform_required")
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        safe_name = _resolve_account_name(conn, pid, label, exclude_id=aid)
        cur = conn.execute(
            """
            UPDATE server_accounts
            SET name = ?, platform_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (safe_name, pid, now, aid),
        )
        if cur.rowcount == 0:
            raise ValueError("not_found")
        conn.commit()
        updated = _server_account_public(conn, aid, lang=lang)
    finally:
        conn.close()
    if not updated:
        raise ValueError("not_found")
    return updated


def set_server_account_active(account_id: str, active: bool, *, lang: str = "es") -> dict[str, Any]:
    seed_admin_if_missing()
    aid = (account_id or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT source_kind, source_ref FROM server_accounts WHERE id = ?", (aid,)
        ).fetchone()
        if not row:
            raise ValueError("not_found")
        cur = conn.execute(
            "UPDATE server_accounts SET active = ?, updated_at = ? WHERE id = ?",
            (1 if active else 0, now, aid),
        )
        if cur.rowcount == 0:
            raise ValueError("not_found")
        kind = str(row["source_kind"] or "manual")
        ref = str(row["source_ref"] or "")
        if kind == "tiktok" and ref:
            conn.execute(
                "UPDATE tiktok_api_configs SET active = ?, updated_at = ? WHERE id = ?",
                (1 if active else 0, now, ref),
            )
        conn.commit()
        row = _server_account_public(conn, aid, lang=lang)
    finally:
        conn.close()
    if not row:
        raise ValueError("not_found")
    return row


def delete_server_account(account_id: str) -> None:
    seed_admin_if_missing()
    aid = (account_id or "").strip()
    conn = _connect()
    try:
        _delete_server_account_on_conn(conn, aid)
        _prune_empty_account_links_on_conn(conn)
        conn.commit()
    finally:
        conn.close()


def list_auto_account_groups(lang: str = "es") -> list[dict[str, Any]]:
    accounts = [a for a in list_server_accounts(lang) if a.get("active")]
    buckets: dict[str, list[dict[str, Any]]] = {}
    for account in accounts:
        key = _normalize_account_name(account.get("name", "")).lower()
        if not key:
            continue
        buckets.setdefault(key, []).append(account)
    groups: list[dict[str, Any]] = []
    for key in sorted(buckets, key=lambda k: buckets[k][0]["name"].lower()):
        members = buckets[key]
        groups.append(
            {
                "id": f"auto:{key}",
                "name": members[0]["name"],
                "auto": True,
                "active": True,
                "members": members,
                "platforms": [
                    {
                        "id": m["platform_id"],
                        "account_id": m["id"],
                        "cred_name": m["name"],
                        "platform": m["platform"],
                    }
                    for m in members
                ],
                "account_count": len(members),
                "platform_count": len({m["platform_id"] for m in members}),
            }
        )
    return groups


def list_server_group_account_choices(lang: str = "es") -> list[dict[str, Any]]:
    """Cuentas disponibles para unir en grupos manuales (con o sin servidores)."""
    choices: list[dict[str, Any]] = []
    for group in get_server_account_groups(lang):
        if not group.get("active", True):
            continue
        name = (group.get("name") or "").strip()
        key = (group.get("key") or name.casefold()).strip()
        if not name or not key:
            continue
        accounts = [a for a in (group.get("accounts") or []) if a.get("active", True)]
        platform_ids = sorted(
            {str(a["platform_id"]) for a in accounts if (a.get("platform_id") or "").strip()}
        )
        account_ids = [str(a["id"]) for a in accounts if (a.get("id") or "").strip()]
        platform_labels = sorted(
            {str(a.get("platform") or "") for a in accounts if (a.get("platform") or "").strip()}
        )
        choices.append(
            {
                "key": f"link:{key}",
                "name": name,
                "link_id": str(group.get("link_id") or ""),
                "account_ids": account_ids,
                "platform_ids": platform_ids,
                "platforms": platform_labels,
                "platform": ", ".join(platform_labels),
                "platform_id": platform_ids[0] if platform_ids else "",
                "account_id": account_ids[0] if account_ids else "",
                "selectable": bool(platform_ids),
            }
        )
    choices.sort(key=lambda item: str(item.get("name") or "").casefold())
    return choices


def _normalize_group_account_ids(
    members: list[dict[str, str]] | None = None,
    *,
    account_ids: list[str] | None = None,
) -> list[str]:
    raw: list[str] = []
    if members:
        for m in members:
            aid = (m.get("account_id") or m.get("id") or "").strip()
            if aid:
                raw.append(aid)
    elif account_ids:
        raw = [a.strip() for a in account_ids if (a or "").strip()]
    if not raw:
        return []
    conn = _connect()
    try:
        out: list[str] = []
        seen: set[str] = set()
        for aid in raw:
            if aid in seen:
                continue
            row = conn.execute(
                "SELECT id FROM server_accounts WHERE id = ?", (aid,)
            ).fetchone()
            if row:
                seen.add(aid)
                out.append(aid)
        return out
    finally:
        conn.close()


def _server_group_name_taken(conn: sqlite3.Connection, name: str, *, exclude_id: str = "") -> bool:
    if exclude_id:
        row = conn.execute(
            "SELECT 1 AS ok FROM server_groups WHERE lower(name) = lower(?) AND id != ?",
            (name, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 AS ok FROM server_groups WHERE lower(name) = lower(?)",
            (name,),
        ).fetchone()
    return bool(row)


def _server_group_name_used_by_account(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1 AS ok
        FROM server_account_links
        WHERE lower(trim(name)) = lower(trim(?))
        LIMIT 1
        """,
        (name,),
    ).fetchone()
    if row:
        return True
    row = conn.execute(
        """
        SELECT 1 AS ok
        FROM server_accounts
        WHERE lower(trim(name)) = lower(trim(?))
        LIMIT 1
        """,
        (name,),
    ).fetchone()
    return bool(row)


def _validate_group_member_accounts_linked(
    conn: sqlite3.Connection, account_ids: list[str]
) -> None:
    if not account_ids:
        raise ValueError("platforms_required")
    for aid in account_ids:
        row = conn.execute(
            """
            SELECT platform_id FROM server_accounts
            WHERE id = ? AND trim(platform_id) != ''
            """,
            (aid,),
        ).fetchone()
        if not row:
            raise ValueError("members_not_linked")


def _server_group_row(
    conn: sqlite3.Connection, group_id: str, *, lang: str = "es"
) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM server_groups WHERE id = ?", (group_id,)).fetchone()
    if not row:
        return None
    members = conn.execute(
        """
        SELECT server_account_id
        FROM server_group_members
        WHERE group_id = ?
        ORDER BY server_account_id
        """,
        (group_id,),
    ).fetchall()
    member_rows = [
        acc
        for m in members
        if (acc := _server_account_public(conn, m["server_account_id"], lang=lang))
    ]
    return {
        "id": row["id"],
        "name": row["name"],
        "active": bool(row["active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "members": member_rows,
        "platforms": [
            {
                "id": m["platform_id"],
                "account_id": m["id"],
                "cred_name": m["name"],
            }
            for m in member_rows
        ],
    }


def _list_manual_server_groups(lang: str = "es") -> list[dict[str, Any]]:
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id FROM server_groups ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [
            g for gid in rows if (g := _server_group_row(conn, gid["id"], lang=lang))
        ]
    finally:
        conn.close()


def list_server_groups(lang: str = "es") -> list[dict[str, Any]]:
    manual = _list_manual_server_groups(lang)
    for group in manual:
        group["auto"] = False
    return manual


def _manual_server_group_matches_query(group: dict[str, Any], query: str) -> bool:
    q = (query or "").strip().casefold()
    if not q:
        return True
    if q in (group.get("name") or "").casefold():
        return True
    for member in group.get("members") or []:
        if q in (member.get("name") or "").casefold():
            return True
        if q in (member.get("platform") or "").casefold():
            return True
        if q in (member.get("platform_id") or "").casefold():
            return True
    return False


def list_server_groups_page(
    q: str = "",
    page: int = 1,
    per_page: int | None = TEAM_MEMBERS_PAGE_SIZE,
    *,
    lang: str = "es",
) -> tuple[list[dict[str, Any]], int]:
    groups = list_server_groups(lang)
    if (q or "").strip():
        groups = [g for g in groups if _manual_server_group_matches_query(g, q)]
    total = len(groups)
    if per_page is None:
        return groups, total
    page = max(1, int(page))
    per_page = max(1, int(per_page))
    start = (page - 1) * per_page
    return groups[start : start + per_page], total


def list_all_server_groups(lang: str = "es") -> list[dict[str, Any]]:
    return list_auto_account_groups(lang) + _list_manual_server_groups(lang)


def create_server_group(
    name: str,
    members: list[dict[str, str]] | None = None,
    *,
    account_ids: list[str] | None = None,
    platform_ids: list[str] | None = None,
    lang: str = "es",
) -> dict[str, Any]:
    seed_admin_if_missing()
    label = (name or "").strip()
    if not label:
        raise ValueError("name_required")
    aids = _normalize_group_account_ids(members, account_ids=account_ids)
    if not aids:
        raise ValueError("platforms_required")
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        if _server_group_name_taken(conn, label):
            raise ValueError("name_taken")
        if _server_group_name_used_by_account(conn, label):
            raise ValueError("account_name_conflict")
        _validate_group_member_accounts_linked(conn, aids)
        conn.execute(
            """
            INSERT INTO server_groups (id, name, active, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            """,
            (sid, label, now, now),
        )
        conn.executemany(
            """
            INSERT INTO server_group_members (group_id, server_account_id)
            VALUES (?, ?)
            """,
            [(sid, aid) for aid in aids],
        )
        conn.commit()
        created = _server_group_row(conn, sid, lang=lang)
    finally:
        conn.close()
    if not created:
        raise ValueError("save_fail")
    return created


def update_server_group(
    group_id: str,
    name: str,
    members: list[dict[str, str]] | None = None,
    *,
    account_ids: list[str] | None = None,
    platform_ids: list[str] | None = None,
    lang: str = "es",
) -> dict[str, Any]:
    seed_admin_if_missing()
    label = (name or "").strip()
    if not label:
        raise ValueError("name_required")
    aids = _normalize_group_account_ids(members, account_ids=account_ids)
    if not aids:
        raise ValueError("platforms_required")
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        existing = conn.execute(
            "SELECT id FROM server_groups WHERE id = ?", (group_id,)
        ).fetchone()
        if not existing:
            raise ValueError("not_found")
        if _server_group_name_taken(conn, label, exclude_id=group_id):
            raise ValueError("name_taken")
        if _server_group_name_used_by_account(conn, label):
            raise ValueError("account_name_conflict")
        _validate_group_member_accounts_linked(conn, aids)
        conn.execute(
            "UPDATE server_groups SET name = ?, updated_at = ? WHERE id = ?",
            (label, now, group_id),
        )
        conn.execute(
            "DELETE FROM server_group_members WHERE group_id = ?", (group_id,)
        )
        conn.executemany(
            """
            INSERT INTO server_group_members (group_id, server_account_id)
            VALUES (?, ?)
            """,
            [(group_id, aid) for aid in aids],
        )
        conn.commit()
        updated = _server_group_row(conn, group_id, lang=lang)
    finally:
        conn.close()
    if not updated:
        raise ValueError("not_found")
    return updated


def set_server_group_active(group_id: str, active: bool) -> dict[str, Any]:
    seed_admin_if_missing()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cur = conn.execute(
            "UPDATE server_groups SET active = ?, updated_at = ? WHERE id = ?",
            (1 if active else 0, now, group_id),
        )
        if cur.rowcount == 0:
            raise ValueError("not_found")
        conn.commit()
        row = _server_group_row(conn, group_id, lang="es")
    finally:
        conn.close()
    if not row:
        raise ValueError("not_found")
    return row


def delete_server_group(group_id: str) -> None:
    seed_admin_if_missing()
    conn = _connect()
    try:
        conn.execute("DELETE FROM server_group_members WHERE group_id = ?", (group_id,))
        tables = {
            str(r[0])
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        if "server_group_members_v2" in tables:
            conn.execute(
                "DELETE FROM server_group_members_v2 WHERE group_id = ?", (group_id,)
            )
        cur = conn.execute("DELETE FROM server_groups WHERE id = ?", (group_id,))
        if cur.rowcount == 0:
            raise ValueError("not_found")
        conn.commit()
    finally:
        conn.close()


def insert_publication_log(
    *,
    user_id: str,
    platform_id: str,
    status: str,
    message: str,
    content_type: str = "video",
    video_id: str | None = None,
    account_link_id: str = "",
) -> str:
    seed_admin_if_missing()
    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO publication_log (
                id, video_id, user_id, platform_id, content_type, status, message, created_at,
                account_link_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                video_id,
                user_id,
                platform_id,
                content_type,
                status,
                (message or "")[:500],
                now,
                (account_link_id or "").strip(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return log_id


def create_scheduled_publication(
    *,
    user_id: str,
    video_id: str,
    platforms: list[str],
    tiktok_config_id: str,
    content_type: str,
    scheduled_at_utc: datetime,
    lang: str = "es",
    account_link_id: str = "",
) -> str:
    import json

    seed_admin_if_missing()
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    sched = scheduled_at_utc.astimezone(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO scheduled_publications (
                id, user_id, video_id, platforms_json, tiktok_config_id,
                content_type, scheduled_at, lang, status, created_at, account_link_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                sid,
                user_id,
                video_id,
                json.dumps(platforms),
                (tiktok_config_id or "").strip(),
                content_type,
                sched,
                lang,
                now,
                (account_link_id or "").strip(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return sid


def list_scheduled_publications(*, limit: int = 30) -> list[dict[str, Any]]:
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT sp.*, v.title AS video_title
            FROM scheduled_publications sp
            LEFT JOIN videos v ON v.id = sp.video_id
            WHERE sp.status = 'pending'
            ORDER BY sp.scheduled_at ASC
            LIMIT ?
            """,
            (max(1, min(limit, 100)),),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_due_scheduled_publications(*, limit: int = 20) -> list[dict[str, Any]]:
    seed_admin_if_missing()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM scheduled_publications
            WHERE status = 'pending' AND scheduled_at <= ?
            ORDER BY scheduled_at ASC
            LIMIT ?
            """,
            (now, max(1, min(limit, 50))),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_scheduled_processing(sched_id: str) -> bool:
    seed_admin_if_missing()
    conn = _connect()
    try:
        cur = conn.execute(
            """
            UPDATE scheduled_publications
            SET status = 'processing'
            WHERE id = ? AND status = 'pending'
            """,
            (sched_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def complete_scheduled_publication(
    sched_id: str, status: str, error_message: str | None = None
) -> None:
    seed_admin_if_missing()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE scheduled_publications
            SET status = ?, processed_at = ?, error_message = ?
            WHERE id = ?
            """,
            (status, now, (error_message or "")[:500], sched_id),
        )
        conn.commit()
    finally:
        conn.close()


def list_publication_logs(*, limit: int = 40) -> list[dict[str, Any]]:
    seed_admin_if_missing()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT pl.*, v.title AS video_title
            FROM publication_log pl
            LEFT JOIN videos v ON v.id = pl.video_id
            ORDER BY pl.created_at DESC
            LIMIT ?
            """,
            (max(1, min(limit, 200)),),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def count_publication_logs_in_range(start_iso: str, end_iso: str) -> int:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n FROM publication_log
            WHERE created_at >= ? AND created_at <= ?
            """,
            (start_iso, end_iso),
        ).fetchone()
        return int(row["n"] or 0)
    finally:
        conn.close()


def delete_publication_logs_in_range(start_iso: str, end_iso: str) -> int:
    seed_admin_if_missing()
    conn = _connect()
    try:
        cur = conn.execute(
            """
            DELETE FROM publication_log
            WHERE created_at >= ? AND created_at <= ?
            """,
            (start_iso, end_iso),
        )
        conn.commit()
        return int(cur.rowcount or 0)
    finally:
        conn.close()


def count_extractor_events_in_range(start_iso: str, end_iso: str) -> int:
    seed_admin_if_missing()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n FROM extractor_events
            WHERE created_at >= ? AND created_at <= ?
            """,
            (start_iso, end_iso),
        ).fetchone()
        return int(row["n"] or 0)
    finally:
        conn.close()


def delete_extractor_events_in_range(start_iso: str, end_iso: str) -> int:
    seed_admin_if_missing()
    conn = _connect()
    try:
        cur = conn.execute(
            """
            DELETE FROM extractor_events
            WHERE created_at >= ? AND created_at <= ?
            """,
            (start_iso, end_iso),
        )
        conn.commit()
        return int(cur.rowcount or 0)
    finally:
        conn.close()


def get_app_setting(key: str) -> str | None:
    seed_admin_if_missing()
    k = (key or "").strip()
    if not k:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (k,),
        ).fetchone()
        if not row:
            return None
        v = str(row["value"]).strip()
        return v or None
    finally:
        conn.close()


def set_app_setting(key: str, value: str) -> None:
    seed_admin_if_missing()
    k = (key or "").strip()
    if not k:
        raise ValueError("Invalid setting key")
    v = (value or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (k, v, now),
        )
        conn.commit()
    finally:
        conn.close()


def create_password_reset_token(user_id: str, *, ttl_hours: int = 2) -> str:
    seed_admin_if_missing()
    uid = (user_id or "").strip()
    if not uid:
        raise ValueError("Invalid user")
    token = uuid.uuid4().hex + uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    expires = now.timestamp() + max(1, ttl_hours) * 3600
    expires_at = datetime.fromtimestamp(expires, tz=timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (uid,))
        conn.execute(
            """
            INSERT INTO password_reset_tokens (token, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, uid, expires_at, now.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    return token


def get_password_reset_user_id(token: str) -> str | None:
    seed_admin_if_missing()
    tok = (token or "").strip()
    if not tok:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at FROM password_reset_tokens WHERE token = ?",
            (tok,),
        ).fetchone()
        if not row:
            return None
        expires_at = datetime.fromisoformat(str(row["expires_at"]))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            conn.execute("DELETE FROM password_reset_tokens WHERE token = ?", (tok,))
            conn.commit()
            return None
        uid = str(row["user_id"]).strip()
        user = get_user_by_id(uid)
        if not user or not user_has_admin_privileges(user):
            return None
        return uid
    finally:
        conn.close()


def consume_password_reset_token(token: str) -> str | None:
    uid = get_password_reset_user_id(token)
    if not uid:
        return None
    tok = (token or "").strip()
    conn = _connect()
    try:
        conn.execute("DELETE FROM password_reset_tokens WHERE token = ?", (tok,))
        conn.commit()
    finally:
        conn.close()
    return uid


def set_admin_password(user_id: str, new_password: str) -> None:
    seed_admin_if_missing()
    uid = (user_id or "").strip()
    pw = (new_password or "").strip()
    if len(pw) < 4:
        raise ValueError("Password must be at least 4 characters")
    user = get_user_by_id(uid)
    if not user or not user_has_admin_privileges(user):
        raise ValueError("Invalid administrator account")
    conn = _connect()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_pw(pw), uid),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Extractor: repartir videos de un servidor origen hacia los demás vinculados
# ---------------------------------------------------------------------------

EXTRACTOR_ACTIVE_STATUSES = ("running", "paused", "error")
EXTRACTOR_EVENTS_KEEP = 200

_EXTRACTOR_JOB_FIELDS = {
    "account_name",
    "total_videos",
    "batch_size",
    "effective_batch",
    "interval_minutes",
    "rest_seconds",
    "status",
    "status_note",
    "platform_state",
    "cycle_remaining",
    "good_cycles",
    "next_action_at",
    "last_cycle_at",
}


def _ensure_extractor_tables() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS extractor_jobs (
                id TEXT PRIMARY KEY,
                owner_user_id TEXT NOT NULL,
                account_link_id TEXT NOT NULL,
                account_name TEXT NOT NULL DEFAULT '',
                source_platform_id TEXT NOT NULL,
                target_platform_ids TEXT NOT NULL DEFAULT '[]',
                total_videos INTEGER NOT NULL DEFAULT 0,
                batch_size INTEGER NOT NULL DEFAULT 1,
                effective_batch INTEGER NOT NULL DEFAULT 1,
                interval_minutes INTEGER NOT NULL DEFAULT 60,
                rest_seconds INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'running'
                    CHECK (status IN ('running', 'paused', 'done', 'error')),
                status_note TEXT NOT NULL DEFAULT '',
                platform_state TEXT NOT NULL DEFAULT '{}',
                cycle_remaining INTEGER NOT NULL DEFAULT 0,
                good_cycles INTEGER NOT NULL DEFAULT 0,
                next_action_at TEXT NOT NULL DEFAULT '',
                last_cycle_at TEXT NOT NULL DEFAULT '',
                lang TEXT NOT NULL DEFAULT 'es',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS extractor_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                level TEXT NOT NULL DEFAULT 'info',
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES extractor_jobs(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_extractor_events_job"
            " ON extractor_events(job_id, id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_publication_log_account_platform"
            " ON publication_log(account_link_id, platform_id, status)"
        )
        cols = {r[1] for r in conn.execute("PRAGMA table_info(extractor_jobs)").fetchall()}
        if "lang" not in cols:
            conn.execute(
                "ALTER TABLE extractor_jobs ADD COLUMN lang TEXT NOT NULL DEFAULT 'es'"
            )
        conn.commit()
    finally:
        conn.close()


def _extractor_job_from_row(row: sqlite3.Row) -> dict[str, Any]:
    import json as _json

    try:
        targets = _json.loads(row["target_platform_ids"] or "[]")
    except ValueError:
        targets = []
    try:
        platform_state = _json.loads(row["platform_state"] or "{}")
    except ValueError:
        platform_state = {}
    return {
        "id": str(row["id"]),
        "owner_user_id": str(row["owner_user_id"]),
        "account_link_id": str(row["account_link_id"]),
        "account_name": str(row["account_name"] or ""),
        "source_platform_id": str(row["source_platform_id"]),
        "target_platform_ids": [str(t) for t in targets if str(t).strip()],
        "total_videos": int(row["total_videos"] or 0),
        "batch_size": int(row["batch_size"] or 1),
        "effective_batch": int(row["effective_batch"] or 1),
        "interval_minutes": int(row["interval_minutes"] or 1),
        "rest_seconds": int(row["rest_seconds"] or 0),
        "status": str(row["status"] or "paused"),
        "status_note": str(row["status_note"] or ""),
        "platform_state": platform_state if isinstance(platform_state, dict) else {},
        "cycle_remaining": int(row["cycle_remaining"] or 0),
        "good_cycles": int(row["good_cycles"] or 0),
        "next_action_at": str(row["next_action_at"] or ""),
        "last_cycle_at": str(row["last_cycle_at"] or ""),
        "lang": str(row["lang"] or "es"),
        "created_at": str(row["created_at"] or ""),
        "updated_at": str(row["updated_at"] or ""),
    }


def extractor_job_conflict_exists(
    account_link_id: str, source_platform_id: str
) -> bool:
    """Ya existe una extracción activa (no terminada) para la misma cuenta+origen."""
    conn = _connect()
    try:
        placeholders = ",".join("?" for _ in EXTRACTOR_ACTIVE_STATUSES)
        row = conn.execute(
            f"""
            SELECT 1 FROM extractor_jobs
            WHERE account_link_id = ? AND source_platform_id = ?
              AND status IN ({placeholders})
            LIMIT 1
            """,
            (account_link_id, source_platform_id, *EXTRACTOR_ACTIVE_STATUSES),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def create_extractor_job(
    *,
    owner_user_id: str,
    account_link_id: str,
    account_name: str,
    source_platform_id: str,
    target_platform_ids: list[str],
    total_videos: int,
    batch_size: int,
    interval_minutes: int,
    rest_seconds: int,
    lang: str = "es",
) -> dict[str, Any]:
    import json as _json

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO extractor_jobs (
                id, owner_user_id, account_link_id, account_name,
                source_platform_id, target_platform_ids, total_videos,
                batch_size, effective_batch, interval_minutes, rest_seconds,
                status, status_note, platform_state, cycle_remaining,
                good_cycles, next_action_at, last_cycle_at, lang,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', '', '{}', 0, 0, ?, '', ?, ?, ?)
            """,
            (
                job_id,
                owner_user_id,
                account_link_id,
                (account_name or "").strip(),
                source_platform_id,
                _json.dumps(list(target_platform_ids)),
                int(total_videos),
                int(batch_size),
                int(batch_size),
                int(interval_minutes),
                int(rest_seconds),
                now,
                lang if lang in ("es", "en") else "es",
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    job = get_extractor_job(job_id)
    assert job is not None
    return job


def get_extractor_job(job_id: str) -> dict[str, Any] | None:
    jid = (job_id or "").strip()
    if not jid:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM extractor_jobs WHERE id = ?", (jid,)
        ).fetchone()
        return _extractor_job_from_row(row) if row else None
    finally:
        conn.close()


def list_extractor_jobs() -> list[dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM extractor_jobs ORDER BY created_at DESC"
        ).fetchall()
        return [_extractor_job_from_row(r) for r in rows]
    finally:
        conn.close()


def list_due_extractor_jobs(now_iso: str) -> list[dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM extractor_jobs
            WHERE status = 'running' AND next_action_at <= ?
            ORDER BY next_action_at ASC
            """,
            (now_iso,),
        ).fetchall()
        return [_extractor_job_from_row(r) for r in rows]
    finally:
        conn.close()


def update_extractor_job(job_id: str, **fields: Any) -> None:
    import json as _json

    jid = (job_id or "").strip()
    clean: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in _EXTRACTOR_JOB_FIELDS:
            raise ValueError(f"Invalid extractor job field: {key}")
        if key == "platform_state" and not isinstance(value, str):
            value = _json.dumps(value)
        clean[key] = value
    if not jid or not clean:
        return
    clean["updated_at"] = datetime.now(timezone.utc).isoformat()
    sets = ", ".join(f"{k} = ?" for k in clean)
    conn = _connect()
    try:
        conn.execute(
            f"UPDATE extractor_jobs SET {sets} WHERE id = ?",
            (*clean.values(), jid),
        )
        conn.commit()
    finally:
        conn.close()


def delete_extractor_job(job_id: str) -> bool:
    jid = (job_id or "").strip()
    if not jid:
        return False
    conn = _connect()
    try:
        cur = conn.execute("SELECT 1 AS ok FROM extractor_jobs WHERE id = ?", (jid,))
        if not cur.fetchone():
            return False
        conn.execute("DELETE FROM extractor_events WHERE job_id = ?", (jid,))
        conn.execute("DELETE FROM extractor_jobs WHERE id = ?", (jid,))
        conn.commit()
        return True
    finally:
        conn.close()


def add_extractor_event(job_id: str, level: str, message: str) -> None:
    jid = (job_id or "").strip()
    if not jid:
        return
    now = datetime.now(timezone.utc).isoformat()
    lvl = level if level in ("info", "warn", "error") else "info"
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO extractor_events (job_id, level, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (jid, lvl, (message or "")[:500], now),
        )
        conn.execute(
            """
            DELETE FROM extractor_events
            WHERE job_id = ? AND id NOT IN (
                SELECT id FROM extractor_events
                WHERE job_id = ? ORDER BY id DESC LIMIT ?
            )
            """,
            (jid, jid, EXTRACTOR_EVENTS_KEEP),
        )
        conn.commit()
    finally:
        conn.close()


def list_extractor_events(job_id: str, *, limit: int = 30) -> list[dict[str, Any]]:
    jid = (job_id or "").strip()
    if not jid:
        return []
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT level, message, created_at FROM extractor_events
            WHERE job_id = ? ORDER BY id DESC LIMIT ?
            """,
            (jid, int(limit)),
        ).fetchall()
        return [
            {
                "level": str(r["level"]),
                "message": str(r["message"]),
                "created_at": str(r["created_at"]),
            }
            for r in rows
        ]
    finally:
        conn.close()


def count_extractor_source_videos(
    account_link_id: str, source_platform_id: str
) -> int:
    """Videos publicados OK en el servidor origen para esa cuenta."""
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT video_id) AS n FROM publication_log
            WHERE account_link_id = ? AND platform_id = ?
              AND status = 'ok' AND video_id IS NOT NULL
            """,
            (account_link_id, source_platform_id),
        ).fetchone()
        return int(row["n"] or 0)
    finally:
        conn.close()


def count_extractor_pending(
    account_link_id: str, source_platform_id: str, target_platform_id: str
) -> int:
    """Videos del origen que aún no se han resuelto (ok/omitido) en el destino."""
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT pl.video_id) AS n FROM publication_log pl
            WHERE pl.account_link_id = ? AND pl.platform_id = ?
              AND pl.status = 'ok' AND pl.video_id IS NOT NULL
              AND pl.video_id NOT IN (
                  SELECT video_id FROM publication_log
                  WHERE account_link_id = ? AND platform_id = ?
                    AND status IN ('ok', 'skipped') AND video_id IS NOT NULL
              )
            """,
            (
                account_link_id,
                source_platform_id,
                account_link_id,
                target_platform_id,
            ),
        ).fetchone()
        return int(row["n"] or 0)
    finally:
        conn.close()


def list_extractor_pending_videos(
    account_link_id: str,
    source_platform_id: str,
    target_platform_id: str,
    *,
    limit: int = 10,
) -> list[Video]:
    """Videos del origen pendientes de publicar en el destino (más antiguos primero)."""
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT v.* FROM videos v
            WHERE v.id IN (
                SELECT DISTINCT pl.video_id FROM publication_log pl
                WHERE pl.account_link_id = ? AND pl.platform_id = ?
                  AND pl.status = 'ok' AND pl.video_id IS NOT NULL
            )
            AND v.id NOT IN (
                SELECT video_id FROM publication_log
                WHERE account_link_id = ? AND platform_id = ?
                  AND status IN ('ok', 'skipped') AND video_id IS NOT NULL
            )
            ORDER BY v.created_at ASC
            LIMIT ?
            """,
            (
                account_link_id,
                source_platform_id,
                account_link_id,
                target_platform_id,
                int(limit),
            ),
        ).fetchall()
        return [_row_to_video(r) for r in rows]
    finally:
        conn.close()


def extractor_job_progress(job: dict[str, Any]) -> dict[str, Any]:
    """Progreso del trabajo: operaciones hechas/pendientes por servidor destino."""
    account_link_id = job["account_link_id"]
    source = job["source_platform_id"]
    total_source = count_extractor_source_videos(account_link_id, source)
    per_platform: list[dict[str, Any]] = []
    total_ops = 0
    pending_ops = 0
    for pid in job.get("target_platform_ids") or []:
        pending = count_extractor_pending(account_link_id, source, pid)
        done = max(0, total_source - pending)
        per_platform.append(
            {
                "platform_id": pid,
                "total": total_source,
                "done": done,
                "pending": pending,
            }
        )
        total_ops += total_source
        pending_ops += pending
    return {
        "source_total": total_source,
        "total_ops": total_ops,
        "done_ops": max(0, total_ops - pending_ops),
        "pending_ops": pending_ops,
        "per_platform": per_platform,
    }
