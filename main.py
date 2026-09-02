from __future__ import annotations

import asyncio
import json
import os
import uuid
import urllib.error
import urllib.request
from urllib.parse import urlencode
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".mov", ".mkv"}
ALLOWED_PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_MEDIA_EXT = ALLOWED_VIDEO_EXT | ALLOWED_PHOTO_EXT
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
COMMENT_INBOX_PER_PAGE = 15

load_dotenv(BASE_DIR / ".env")

import db  # noqa: E402
import extractor  # noqa: E402
import i18n  # noqa: E402
import notify  # noqa: E402
import platform_api  # noqa: E402
import platform_publish  # noqa: E402
import platforms  # noqa: E402
import site_config  # noqa: E402
import tiktok_oauth  # noqa: E402
import youtube_oauth  # noqa: E402
import instagram_oauth  # noqa: E402
import facebook_oauth  # noqa: E402
import x_oauth  # noqa: E402
import dailymotion_oauth  # noqa: E402
import bilibili_oauth  # noqa: E402
import snapchat_oauth  # noqa: E402
import publish_schedule  # noqa: E402
import security_headers  # noqa: E402

SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-cambiar-en-produccion")

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    db.seed_admin_if_missing()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async def scheduled_worker() -> None:
        while True:
            try:
                publish_schedule.process_due_scheduled_publications(upload_dir=UPLOAD_DIR)
            except Exception:
                pass
            await asyncio.sleep(30)

    async def extractor_worker() -> None:
        while True:
            try:
                extractor.process_due_extractor_jobs(upload_dir=UPLOAD_DIR)
            except Exception:
                pass
            await asyncio.sleep(extractor.WORKER_TICK_SECONDS)

    worker = asyncio.create_task(scheduled_worker())
    extractor_task = asyncio.create_task(extractor_worker())
    try:
        yield
    finally:
        for task in (worker, extractor_task):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="tt_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
)


@app.middleware("http")
async def _security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    security_headers.apply_security_headers(request, response)
    return response
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["user_can_access_publicaciones"] = db.user_can_access_publicaciones
templates.env.globals["user_has_admin_privileges"] = db.user_has_admin_privileges
templates.env.globals["user_is_site_admin"] = db.user_is_site_admin
templates.env.globals["format_publish_schedule"] = publish_schedule.format_scheduled_local
templates.env.filters["fromjson"] = json.loads
templates.env.globals.update(site_config.legal_context())
templates.env.globals["platform_select_label"] = platforms.platform_select_label


def _render(request: Request, template: str, ctx: dict | None = None, status_code: int = 200):
    base = {**site_config.legal_context(), **i18n.page_context(request)}
    if ctx:
        base.update(ctx)
    return templates.TemplateResponse(request, template, base, status_code=status_code)


def _msg(request: Request, key: str, **kwargs: object) -> str:
    return i18n.t(key, i18n.resolve_lang(request), **kwargs)


def _render_legal(request: Request, template: str, page_title_key: str):
    lang = i18n.resolve_lang(request)
    page_updated = "29 de mayo de 2026" if lang == "es" else "May 29, 2026"
    return _render(
        request,
        template,
        {
            "page_title": i18n.t(page_title_key, lang),
            "page_updated": page_updated,
        },
    )


def _session_user(request: Request) -> db.User | None:
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.get_user_by_id(str(uid))


def require_user(request: Request) -> db.User:
    user = _session_user(request)
    if not user:
        raise PermissionError("login_required")
    return user


def require_admin(request: Request) -> db.User:
    user = require_user(request)
    if not db.user_is_site_admin(user):
        raise PermissionError("forbidden")
    return user


def require_admin_privileges(request: Request) -> db.User:
    user = require_user(request)
    if not db.user_has_admin_privileges(user):
        raise PermissionError("forbidden")
    return user


class EquipoEstadoBody(BaseModel):
    active: bool


class PlatformApiBody(BaseModel):
    name: str | None = None
    client_id: str = ""
    client_secret: str = ""
    access_token: str = ""
    extra: str = ""


class ServerGroupMemberBody(BaseModel):
    platform_id: str = ""
    account_id: str = ""


class ServerGroupBody(BaseModel):
    name: str = ""
    account_ids: list[str] = []
    members: list[ServerGroupMemberBody] = []
    platform_ids: list[str] = []


class ServerAccountBody(BaseModel):
    name: str = ""
    platform_id: str = ""


class ServerAccountActiveBody(BaseModel):
    active: bool


class AccountLinkBody(BaseModel):
    name: str = ""


class AccountLinkActiveBody(BaseModel):
    active: bool


class ServerGroupActiveBody(BaseModel):
    active: bool


class ExtractorJobBody(BaseModel):
    account_link_id: str = ""
    source_platform_id: str = ""
    target_platform_ids: list[str] = []
    batch_size: int = 1
    interval_minutes: int = 60
    rest_seconds: int = 0


class LogPurgeBody(BaseModel):
    date_from: str = ""
    date_to: str = ""


def _require_admin_json(request: Request) -> JSONResponse | None:
    try:
        require_admin_privileges(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse(
                {"ok": False, "error": "Sign in as an administrator."},
                status_code=401,
            )
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    return None


def _require_site_admin_json(request: Request) -> JSONResponse | None:
    try:
        require_admin(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse(
                {"ok": False, "error": "Sign in as an administrator."},
                status_code=401,
            )
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    return None


def _admin_redirect_login():
    return RedirectResponse(url="/login?next=/admin/publicaciones", status_code=303)


def _admin_privileges_redirect_login():
    return RedirectResponse(url="/login?next=/admin/panel", status_code=303)


def _panel_redirect_login():
    return RedirectResponse(url="/login?next=/admin/panel", status_code=303)


def _valid_email(value: str) -> bool:
    s = (value or "").strip()
    if len(s) < 5 or "@" not in s:
        return False
    local, _, domain = s.partition("@")
    return bool(local and domain and "." in domain)


def _publicaciones_redirect_login():
    return RedirectResponse(url="/login?next=/admin/publicaciones", status_code=303)


def _publicaciones_comment_scope(user: db.User) -> list[str] | None:
    """None = todos los videos (admin); lista = dueños visibles para el usuario."""
    if db.user_has_admin_privileges(user):
        return None
    allowed = db.allowed_video_owner_ids_for_user(user)
    return list(allowed) if allowed else []


def _publicaciones_comment_user_choices(
    publish_choices: list[dict],
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for c in publish_choices:
        uid = (c.get("internal_user_id") or "").strip()
        if uid and uid not in seen:
            out.append({"id": uid, "name": c.get("name") or uid})
            seen.add(uid)
    return out


def _default_app_home(user: db.User) -> str:
    if db.user_can_access_publicaciones(user):
        return "/admin/publicaciones"
    return "/admin"


def _require_publicaciones_user(request: Request) -> db.User:
    user = require_user(request)
    if not db.user_can_access_publicaciones(user):
        raise PermissionError("forbidden")
    return user




def _error_home_url(request: Request) -> str:
    user = _session_user(request)
    if user:
        return "/admin"
    return "/login"


@app.get("/offline", response_class=HTMLResponse, name="offline_page")
def offline_page(request: Request):
    return _render(
        request,
        "errors/offline.html",
        {"home_url": _error_home_url(request)},
    )


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    path = BASE_DIR / "static" / "sw.js"
    return FileResponse(
        path,
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache",
        },
    )


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools_config():
    """Respuesta vacía para peticiones automáticas de Chrome DevTools."""
    return JSONResponse(content={})


@app.get("/set-language/{lang_code}", name="set_language")
def set_language(request: Request, lang_code: str):
    code = lang_code if lang_code in i18n.LANGUAGES else i18n.DEFAULT_LANG
    request.session["lang"] = code
    referer = request.headers.get("referer", "/")
    from urllib.parse import urlparse

    parsed = urlparse(referer)
    safe_next = parsed.path if parsed.path.startswith("/") else "/"
    if parsed.query:
        safe_next = f"{safe_next}?{parsed.query}"
    return RedirectResponse(url=safe_next, status_code=303)


@app.get("/", response_class=HTMLResponse, name="home")
def home(request: Request):
    user = _session_user(request)
    if user:
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    return _render(request, "landing.html")


@app.get("/about", response_class=HTMLResponse, name="about")
def page_about(request: Request):
    return _render_legal(request, "legal_about.html", "legal.about_title")


@app.get("/privacy-policy", response_class=HTMLResponse, name="privacy")
def page_privacy(request: Request):
    return _render_legal(request, "legal_privacy.html", "legal.privacy_title")


@app.get("/terms-of-service", response_class=HTMLResponse, name="terms")
def page_terms(request: Request):
    return _render_legal(request, "legal_terms.html", "legal.terms_title")


@app.get("/data-deletion", response_class=HTMLResponse, name="data_deletion")
def page_data_deletion(request: Request):
    return _render_legal(request, "legal_deletion.html", "legal.deletion_title")


@app.get("/contact", response_class=HTMLResponse, name="contact")
def page_contact(request: Request):
    return RedirectResponse(url=f"mailto:{site_config.SUPPORT_EMAIL}", status_code=303)


@app.get("/nosotros")
def redirect_nosotros():
    return RedirectResponse(url="/about", status_code=301)


@app.get("/politica-de-privacidad")
def redirect_privacidad():
    return RedirectResponse(url="/privacy-policy", status_code=301)


@app.get("/terminos-de-servicio")
def redirect_terminos():
    return RedirectResponse(url="/terms-of-service", status_code=301)


@app.get("/eliminacion-de-datos")
def redirect_eliminacion():
    return RedirectResponse(url="/data-deletion", status_code=301)


@app.get("/contacto")
def redirect_contacto():
    return RedirectResponse(url="/contact", status_code=301)


@app.get("/login", response_class=HTMLResponse, name="login")
def login_get(request: Request):
    user = _session_user(request)
    if user:
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    next_url = request.query_params.get("next") or "/admin/publicaciones"
    ok = request.session.pop("login_ok", None)
    return _render(
        request,
        "login.html",
        {
            "error": None,
            "success": ok,
            "next_url": next_url,
        },
    )


@app.post("/login", response_class=HTMLResponse, name="login_post")
def login_post(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    next: Annotated[str, Form()] = "/admin/publicaciones",
):
    u = db.verify_login(username, password)
    if not u:
        lang = i18n.resolve_lang(request)
        return _render(
            request,
            "login.html",
            {
                "error": i18n.t("login.error", lang),
                "next_url": next if next.startswith("/") else "/admin/publicaciones",
                "username": username,
            },
            status_code=401,
        )
    request.session["user_id"] = u.id
    safe_next = next if next.startswith("/") else _default_app_home(u)
    if safe_next == "/":
        safe_next = _default_app_home(u)
    return RedirectResponse(url=safe_next, status_code=303)


@app.post("/logout", name="logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=request.url_for("home"), status_code=303)


def _password_reset_url(request: Request, token: str) -> str:
    """Enlace absoluto al formulario de restablecimiento."""
    return f"{request.url_for('admin_panel_reset_get')}?{urlencode({'token': token})}"


def _stats_empty() -> dict[str, int]:
    return {"videos": 0, "comments": 0, "views": 0, "likes": 0, "shares": 0}


def _stats_with_followers(
    creator_user_id: str | None,
    *,
    platform_id: str | None,
    all_creators: bool = False,
    account_link_id: str | None = None,
    account_link_ids: list[str] | None = None,
) -> dict[str, int]:
    del all_creators  # reservado para agregados globales futuros
    return dict(
        db.dashboard_stats(
            creator_user_id,
            platform_id=platform_id,
            account_link_id=account_link_id,
            account_link_ids=account_link_ids,
        )
    )


def _video_stats_bundle(
    video_id: str,
    *,
    owner_user_id: str | None = None,
    platform_id: str | None = None,
    account_link_id: str | None = None,
    account_link_ids: list[str] | None = None,
) -> dict | None:
    v = db.get_video_by_id(video_id)
    if not v:
        return None
    if owner_user_id and v.user_id != owner_user_id:
        return None
    if (account_link_id or account_link_ids) and not db.video_belongs_to_account(
        video_id,
        account_link_id or "",
        platform_id=platform_id,
        account_link_ids=account_link_ids,
    ):
        return None
    if platform_id and not account_link_id and not db.video_has_platform_publication(
        video_id, platform_id
    ):
        return None
    st = {
        "videos": 1,
        "comments": db.count_comments_for_video(video_id),
        "views": v.views,
        "likes": v.likes,
        "shares": v.shares,
    }
    return {"stats": st, "title": v.title}


def _platform_filter(platform_sel: str) -> str | None:
    return None if platform_sel == "all" else platform_sel


def _stats_link_kwargs(selected: dict | None) -> dict:
    if not selected:
        return {}
    link_ids = [str(x).strip() for x in (selected.get("link_ids") or []) if str(x).strip()]
    if not link_ids:
        link_id = str(selected.get("id") or "").strip()
        if link_id and not link_id.startswith(db.STATS_GROUP_PREFIX):
            link_ids = [link_id]
    if not link_ids:
        return {}
    if len(link_ids) == 1:
        return {"account_link_id": link_ids[0]}
    return {"account_link_ids": link_ids}


def _build_platform_breakdown(
    lang: str,
    *,
    account_link_id: str | None = None,
    account_link_ids: list[str] | None = None,
    platform_ids: list[str] | None = None,
) -> list[dict]:
    breakdown: list[dict] = []
    allowed = set(platform_ids or [])
    for p in platforms.PLATFORMS:
        pid = str(p["id"])
        if allowed and pid not in allowed:
            continue
        st = _stats_with_followers(
            None,
            platform_id=pid,
            account_link_id=account_link_id,
            account_link_ids=account_link_ids,
        )
        breakdown.append(
            {
                "platform_id": pid,
                "icon": str(p["icon"]),
                "name": i18n.t(f"platform.{pid}", lang),
                "stats": st,
                "visible_stats": platforms.visible_stats_metrics(pid),
                "publications": db.list_stats_publications(
                    platform_id=pid,
                    account_link_id=account_link_id,
                    account_link_ids=account_link_ids,
                ),
            }
        )
    return breakdown


def _build_server_account_breakdown(
    lang: str,
    accounts: list[dict],
    *,
    platform_id: str | None,
) -> list[dict]:
    breakdown: list[dict] = []
    for acc in accounts:
        aid = str(acc["id"])
        pids = acc.get("platform_ids") or []
        if platform_id and platform_id not in pids:
            continue
        st_b = _stats_with_followers(
            None, platform_id=platform_id or None, account_link_id=aid
        )
        pubs = db.list_stats_publications(
            platform_id=platform_id, account_link_id=aid
        )
        vids = db.list_videos_for_account(aid, platform_id=platform_id)
        by_platform: dict[str, dict] = {}
        if not platform_id:
            for pid in pids:
                by_platform[pid] = {
                    "stats": _stats_with_followers(
                        None, platform_id=pid, account_link_id=aid
                    ),
                    "publications": db.list_stats_publications(
                        platform_id=pid, account_link_id=aid
                    ),
                }
        breakdown.append(
            {
                "config_id": aid,
                "name": acc["name"],
                "stats": st_b,
                "has_user": True,
                "publications": pubs,
                "videos": [{"id": v.id, "title": v.title} for v in vids],
                "platform_ids": pids,
                "by_platform": by_platform,
            }
        )
    return breakdown


@app.get("/admin", response_class=HTMLResponse, name="admin")
def admin_panel(request: Request):
    try:
        u = require_user(request)
    except PermissionError:
        return _admin_redirect_login()

    is_admin = db.user_has_admin_privileges(u)
    lang = i18n.resolve_lang(request)
    all_filter_choices = db.list_stats_filter_choices(u, lang=lang)
    user_platform_ids = sorted(
        {pid for acc in all_filter_choices for pid in (acc.get("platform_ids") or [])}
    )

    platform_sel = (request.query_params.get("platform") or "all").strip()
    if platform_sel not in platforms.PLATFORM_IDS and platform_sel != "all":
        platform_sel = "all"
    if not is_admin and platform_sel != "all" and platform_sel not in user_platform_ids:
        platform_sel = "all"

    platform_choices = platforms.platform_list(lang)
    if not is_admin:
        platform_choices = [p for p in platform_choices if p["id"] in user_platform_ids]

    sel = (
        (request.query_params.get("account") or "").strip()
        or (request.query_params.get("tiktoker") or "").strip()
    )
    video_sel = (request.query_params.get("video") or "").strip()
    visible_stats = platforms.visible_stats_metrics(
        None if platform_sel == "all" else platform_sel
    )
    selected_platform_label = (
        i18n.t("admin.all", lang)
        if platform_sel == "all"
        else next((p["name"] for p in platform_choices if p["id"] == platform_sel), platform_sel)
    )
    selected_platform_icon = (
        ""
        if platform_sel == "all"
        else next((p["icon"] for p in platform_choices if p["id"] == platform_sel), "")
    )
    account_filter_label = (
        i18n.t("admin.accounts", lang)
        if platform_sel == "all"
        else i18n.t("admin.platform_account", lang, platform=selected_platform_label)
    )
    platform_filter = _platform_filter(platform_sel)
    account_choices = db.filter_stats_choices_by_platform(
        all_filter_choices, platform_filter
    )
    choice_ids = {c["id"] for c in account_choices}
    show_account_filter = bool(account_choices)

    if sel not in choice_ids:
        sel = ""
    if not sel and account_choices:
        sel = account_choices[0]["id"]
    elif not sel and not is_admin and len(account_choices) == 1:
        sel = account_choices[0]["id"]
    selected_account = next((c for c in account_choices if c["id"] == sel), None)
    selected_account_name = (selected_account or {}).get("name") or ""
    link_kwargs = _stats_link_kwargs(selected_account)

    show_global_breakdown = False
    platform_breakdown: list[dict] = []
    tiktoker_breakdown: list[dict] = []
    global_summary: dict[str, int] | None = None
    global_video_list: list[dict] = []
    video_options: list[dict[str, str]] = []
    selected_video = ""
    video_title = ""
    stats: dict[str, int] = _stats_empty()

    if selected_account:
        acc_platforms = selected_account.get("platform_ids") or []
        primary_link = link_kwargs.get("account_link_id", "")
        group_links = link_kwargs.get("account_link_ids")
        video_options = [
            {"id": v.id, "title": v.title}
            for v in db.list_videos_for_account(
                primary_link,
                platform_id=platform_filter,
                account_link_ids=group_links,
            )
        ]
        stats = _stats_with_followers(None, platform_id=platform_filter, **link_kwargs)
        if video_sel:
            vb = _video_stats_bundle(
                video_sel,
                platform_id=platform_filter,
                **link_kwargs,
            )
            if vb:
                stats = vb["stats"]
                video_title = vb["title"]
                selected_video = video_sel
            else:
                video_sel = ""
        global_video_list = db.list_stats_publications(
            platform_id=platform_filter,
            **link_kwargs,
        )
        if platform_sel == "all":
            show_global_breakdown = True
            global_summary = dict(stats)
            platform_breakdown = _build_platform_breakdown(
                lang,
                platform_ids=acc_platforms,
                **link_kwargs,
            )
    else:
        stats = _stats_empty()
        sel = ""

    err = request.session.pop("admin_error", None)
    ok = request.session.pop("admin_ok", None)
    ctx = {
        "user": u,
        "stats": stats,
        "error": err,
        "success": ok,
        "nav_active": "admin",
        "tiktok_stat_choices": account_choices,
        "selected_tiktoker": sel,
        "show_global_breakdown": show_global_breakdown,
        "platform_breakdown": platform_breakdown,
        "tiktoker_breakdown": tiktoker_breakdown,
        "global_summary": global_summary,
        "global_video_list": global_video_list,
        "video_options": video_options,
        "selected_video": selected_video,
        "video_title": video_title,
        "platform_choices": platform_choices,
        "selected_platform": platform_sel,
        "selected_platform_label": selected_platform_label,
        "selected_platform_icon": selected_platform_icon,
        "visible_stats": visible_stats,
        "show_account_filter": show_account_filter,
        "account_filter_label": account_filter_label,
        "selected_account_name": selected_account_name,
    }
    return _render(request, "admin.html", ctx)


@app.get("/admin/api/stats-filter-choices")
def api_stats_filter_choices(request: Request, platform: str = "all"):
    try:
        u = require_user(request)
    except PermissionError:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)

    lang = i18n.resolve_lang(request)
    platform_sel = (platform or "all").strip()
    if platform_sel not in platforms.PLATFORM_IDS and platform_sel != "all":
        platform_sel = "all"
    all_choices = db.list_stats_filter_choices(u, lang=lang)
    platform_filter = _platform_filter(platform_sel)
    choices = db.filter_stats_choices_by_platform(all_choices, platform_filter)
    return {"ok": True, "choices": choices}


def _filter_comment_threads(
    threads: list[dict],
    *,
    platform: str = "__all__",
    owner_user_id: str = "__all__",
) -> list[dict]:
    out = threads
    if platform and platform != "__all__":
        out = [t for t in out if platform in (t.get("platform_ids") or [])]
    if owner_user_id and owner_user_id != "__all__":
        out = [t for t in out if (t.get("owner_user_id") or "") == owner_user_id]
    return out


@app.get("/admin/api/publicaciones/comentarios")
def api_publicaciones_comentarios(
    request: Request,
    platform: str = "__all__",
    user: str = "__all__",
):
    try:
        u = _require_publicaciones_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    if not db.user_can_manage_comments(u):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    scope = _publicaciones_comment_scope(u)
    threads = db.list_comment_threads_for_owners(scope)
    filtered = _filter_comment_threads(
        threads,
        platform=(platform or "__all__").strip(),
        owner_user_id=(user or "__all__").strip(),
    )
    return {"ok": True, "threads": filtered}


def _log_purge_bounds(date_from: str, date_to: str, lang: str) -> tuple[str, str] | JSONResponse:
    bounds = publish_schedule.parse_local_date_range(date_from, date_to)
    if not bounds:
        return JSONResponse(
            {"ok": False, "error": i18n.t("log.purge_invalid", lang)},
            status_code=400,
        )
    return bounds


@app.get("/admin/api/publicaciones/logs/count")
def api_publication_logs_count(request: Request, date_from: str = "", date_to: str = ""):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(date_from, date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    return {"ok": True, "count": db.count_publication_logs_in_range(start, end)}


@app.delete("/admin/api/publicaciones/logs")
def api_publication_logs_purge(request: Request, body: LogPurgeBody):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(body.date_from, body.date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    deleted = db.delete_publication_logs_in_range(start, end)
    return {"ok": True, "deleted": deleted}


@app.get("/admin/api/extractor/events/count")
def api_extractor_events_count(request: Request, date_from: str = "", date_to: str = ""):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(date_from, date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    return {"ok": True, "count": db.count_extractor_events_in_range(start, end)}


@app.delete("/admin/api/extractor/events")
def api_extractor_events_purge(request: Request, body: LogPurgeBody):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(body.date_from, body.date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    deleted = db.delete_extractor_events_in_range(start, end)
    return {"ok": True, "deleted": deleted}


@app.get(
    "/admin/publicaciones",
    response_class=HTMLResponse,
    name="admin_publicaciones",
)
def admin_publicaciones(request: Request):
    try:
        u = _require_publicaciones_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return _publicaciones_redirect_login()
        return HTMLResponse("You do not have permission to view Publications.", status_code=403)
    lang = i18n.resolve_lang(request)
    platform_choices = platforms.platform_list(lang)
    account_filter_label = i18n.t("admin.accounts", lang)
    publish_choices = db.publicaciones_tiktoker_choices(u)
    publish_sel = (request.query_params.get("publish_tiktoker") or "").strip()
    choice_ids = {c["id"] for c in publish_choices}
    if publish_sel and publish_sel not in choice_ids:
        publish_sel = ""
    if not publish_sel and len(publish_choices) == 1:
        publish_sel = publish_choices[0]["id"]
    selected_publish_cfg = next(
        (c for c in publish_choices if c["id"] == publish_sel), None
    )
    publish_form_unlocked = bool(
        selected_publish_cfg and selected_publish_cfg.get("internal_user_id")
    )
    has_publish_ready_tiktoker = publish_form_unlocked or any(
        c.get("internal_user_id") for c in publish_choices
    )
    publish_ready_n = sum(1 for c in publish_choices if c.get("internal_user_id"))

    comment_threads: list[dict] = []
    comment_user_choices: list[dict[str, str]] = []
    platform_labels: dict[str, str] = {}
    if db.user_can_manage_comments(u):
        comment_owner_scope = _publicaciones_comment_scope(u)
        comment_threads = db.list_comment_threads_for_owners(comment_owner_scope)
        comment_user_choices = _publicaciones_comment_user_choices(publish_choices)
        platform_labels = {
            p["id"]: i18n.t(f"platform.{p['id']}", lang) for p in platform_choices
        }

    err = request.session.pop("admin_error", None)
    ok = request.session.pop("admin_ok", None)
    is_admin = db.user_has_admin_privileges(u)
    publish_account_choices = db.list_stats_filter_choices(u, lang=lang)
    show_publish_account_picker = is_admin or len(publish_account_choices) > 1
    publish_unlocked = is_admin or len(publish_account_choices) > 0
    pub_account_i18n = {
        "select": i18n.t("pub.select_account", lang),
        "search_ph": i18n.t("pub.publish_account_search_ph", lang),
        "empty": i18n.t("pub.publish_account_empty", lang),
        "select_required": i18n.t("pub.flash.select_account_publish", lang),
    }
    return _render(
        request,
        "admin_publicaciones.html",
        {
            "user": u,
            "comment_threads": comment_threads,
            "comment_user_choices": comment_user_choices,
            "platform_labels": platform_labels,
            "error": err,
            "success": ok,
            "nav_active": "publicaciones",
            "tiktoker_choices": publish_choices,
            "has_publish_ready_tiktoker": has_publish_ready_tiktoker,
            "publish_ready_n": publish_ready_n,
            "publish_sel": publish_sel,
            "publish_form_unlocked": publish_form_unlocked,
            "selected_publish_label": (
                selected_publish_cfg["name"] if selected_publish_cfg else ""
            ),
            "can_upload_videos": db.user_can_upload_videos(u),
            "can_manage_comments": db.user_can_manage_comments(u),
            "publish_platforms": platform_choices,
            "publication_logs": db.list_publication_logs(limit=50),
            "scheduled_publications": db.list_scheduled_publications(limit=30),
            "account_filter_label": account_filter_label,
            "publish_account_choices": publish_account_choices,
            "show_publish_account_picker": show_publish_account_picker,
            "is_publish_admin": is_admin,
            "publish_unlocked": publish_unlocked,
            "pub_account_i18n": pub_account_i18n,
        },
    )


@app.post("/admin/videos", name="admin_upload_video")
async def admin_upload_video(request: Request):
    try:
        u = _require_publicaciones_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return _publicaciones_redirect_login()
        return HTMLResponse("Permission denied.", status_code=403)

    lang = i18n.resolve_lang(request)
    form = await request.form()
    title = (form.get("title") or "").strip()
    description = (form.get("description") or "").strip()
    tiktoker_config_id = (form.get("tiktoker_config_id") or "").strip()
    account_link_id = (form.get("account_link_id") or "").strip()
    selected_platforms = [p for p in form.getlist("platforms") if p in platforms.PLATFORM_IDS]
    upload = form.get("file")

    if not db.user_can_upload_videos(u):
        request.session["admin_error"] = _msg(request, "pub.flash.no_upload")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    is_admin = db.user_has_admin_privileges(u)
    publish_choices = db.list_stats_filter_choices(u, lang=lang)
    choices_by_id = {c["id"]: c for c in publish_choices}
    if is_admin:
        if not account_link_id or account_link_id not in choices_by_id:
            request.session["admin_error"] = _msg(request, "pub.flash.select_account_publish")
            return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)
        acc = choices_by_id[account_link_id]
        allowed_platforms = set(acc.get("platform_ids") or [])
        selected_platforms = [p for p in selected_platforms if p in allowed_platforms]
    else:
        if not choices_by_id:
            request.session["admin_error"] = _msg(request, "pub.flash.no_accounts_registered")
            return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)
        if len(choices_by_id) == 1:
            account_link_id = publish_choices[0]["id"]
        elif account_link_id not in choices_by_id:
            request.session["admin_error"] = _msg(request, "pub.flash.select_account_publish")
            return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)
        acc = choices_by_id.get(account_link_id)
        if acc:
            allowed_platforms = set(acc.get("platform_ids") or [])
            selected_platforms = [p for p in selected_platforms if p in allowed_platforms]

    if not selected_platforms:
        request.session["admin_error"] = _msg(request, "pub.flash.no_platforms")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    if not title:
        request.session["admin_error"] = _msg(request, "pub.flash.missing_title")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    if not description:
        request.session["admin_error"] = _msg(request, "pub.flash.missing_description")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    if "tiktok" in selected_platforms:
        choices = db.publicaciones_tiktoker_choices(u)
        if not choices:
            request.session["admin_error"] = _msg(request, "pub.flash.no_accounts_registered")
            return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)
        owner_user_id = db.resolve_publish_owner_user_id(u, tiktoker_config_id)
        if not owner_user_id:
            cid = tiktoker_config_id
            if cid and db.get_config_internal_user_id(cid) is None:
                request.session["admin_error"] = _msg(request, "pub.flash.no_user_assigned")
            else:
                request.session["admin_error"] = _msg(request, "pub.flash.select_account_publish")
            return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)
    else:
        if u.role == "user":
            owner_user_id = u.id
        else:
            ready = [
                c for c in db.publicaciones_tiktoker_choices(u) if c.get("internal_user_id")
            ]
            owner_user_id = ready[0]["internal_user_id"] if ready else u.id

    if not isinstance(upload, UploadFile) or not upload.filename:
        request.session["admin_error"] = _msg(request, "pub.flash.missing_file")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    raw_name = upload.filename or ""
    suffix = Path(raw_name).suffix.lower()
    if suffix not in ALLOWED_MEDIA_EXT:
        request.session["admin_error"] = _msg(
            request,
            "pub.flash.file_type",
            types=", ".join(sorted(ALLOWED_MEDIA_EXT)),
        )
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    content_type = "photo" if suffix in ALLOWED_PHOTO_EXT else "video"

    contents = await upload.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        request.session["admin_error"] = _msg(request, "pub.flash.file_too_large")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    stored = f"{uuid.uuid4().hex}{suffix}"
    path = UPLOAD_DIR / stored
    path.write_bytes(contents)

    schedule_enabled = (form.get("schedule_enabled") or "").strip() in ("1", "on", "true")
    scheduled_raw = (form.get("scheduled_at") or "").strip()
    scheduled_utc = None
    schedule_for_later = False
    if schedule_enabled:
        scheduled_utc = publish_schedule.parse_scheduled_at_local(scheduled_raw)
        if not scheduled_utc:
            path.unlink(missing_ok=True)
            request.session["admin_error"] = _msg(request, "pub.flash.schedule_invalid")
            return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)
        now_utc = publish_schedule.now_publish_tz().astimezone(timezone.utc)
        schedule_for_later = scheduled_utc > now_utc

    try:
        video = db.create_video(owner_user_id, title, description, stored)
    except Exception:
        path.unlink(missing_ok=True)
        request.session["admin_error"] = _msg(request, "pub.flash.save_fail")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    if schedule_enabled and schedule_for_later and scheduled_utc:
        db.create_scheduled_publication(
            user_id=u.id,
            video_id=video.id,
            platforms=selected_platforms,
            tiktok_config_id=tiktoker_config_id,
            content_type=content_type,
            scheduled_at_utc=scheduled_utc,
            lang=lang,
            account_link_id=account_link_id,
        )
        when_local = publish_schedule.format_scheduled_local(
            scheduled_utc.isoformat(), lang
        )
        request.session["admin_ok"] = _msg(
            request, "pub.flash.scheduled", when=when_local
        )
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    ok_n, fail_n, _ = publish_schedule.execute_video_publish(
        upload_dir=UPLOAD_DIR,
        user_id=u.id,
        video=video,
        selected_platforms=selected_platforms,
        tiktoker_config_id=tiktoker_config_id,
        content_type=content_type,
        lang=lang,
        account_link_id=account_link_id,
    )

    past_schedule_immediate = schedule_enabled and scheduled_utc and not schedule_for_later

    if fail_n and ok_n:
        request.session["admin_ok"] = _msg(
            request, "pub.flash.partial", ok=ok_n, fail=fail_n
        )
    elif fail_n:
        request.session["admin_error"] = _msg(
            request, "pub.flash.partial", ok=ok_n, fail=fail_n
        )
    elif past_schedule_immediate:
        request.session["admin_ok"] = _msg(request, "pub.flash.schedule_past_immediate")
    else:
        request.session["admin_ok"] = _msg(request, "pub.flash.all_ok", n=ok_n)

    return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)


@app.post("/admin/comments/reply", name="admin_reply_comment")
def admin_reply_comment(
    request: Request,
    video_id: Annotated[str, Form()],
    parent_id: Annotated[str, Form()],
    body: Annotated[str, Form()],
):
    try:
        u = _require_publicaciones_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return _publicaciones_redirect_login()
        return HTMLResponse("Permission denied.", status_code=403)
    if not db.user_can_manage_comments(u):
        request.session["admin_error"] = _msg(request, "pub.flash.no_comments")
        return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)

    v = db.get_video_by_id(video_id)
    if not v or not db.user_may_act_on_video_owner(u, v.user_id):
        request.session["admin_error"] = _msg(request, "pub.flash.cannot_reply")
    else:
        try:
            db.add_comment(
                video_id,
                u.display_name,
                body,
                parent_id=parent_id,
                is_creator_reply=True,
            )
            request.session["admin_ok"] = _msg(request, "pub.flash.reply_published")
        except ValueError as e:
            request.session["admin_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)


@app.get("/admin/equipo")
def admin_equipo_redirect(request: Request):
    return RedirectResponse(url=request.url_for("admin_panel"), status_code=301)


@app.get("/admin/panel", response_class=HTMLResponse, name="admin_panel")
def admin_panel(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _panel_redirect_login()
    lang = i18n.resolve_lang(request)
    err = request.session.pop("panel_error", None) or request.session.pop("equipo_error", None)
    ok = request.session.pop("panel_ok", None) or request.session.pop("equipo_ok", None)
    admin_email = site_config.notification_email()
    return _render(
        request,
        "admin_panel.html",
        {
            "user": admin,
            "nav_active": "panel",
            "admin_email": admin_email,
            "smtp_configured": notify.smtp_configured(),
            "error": err,
            "success": ok,
            "user_mode_choices": db.regular_user_mode_choices(lang),
            "user_mode_labels": db.user_mode_labels_for_lang(lang),
            "tiktok_config_choices": db.list_team_server_account_choices(lang=lang),
            "team_account_placeholder": i18n.t("team.link_account_placeholder", lang),
            "password_optional_placeholder": i18n.t("team.password_optional", lang),
            "search_accounts_placeholder": i18n.t("team.search_accounts", lang),
        },
    )
@app.get("/admin/servidores", response_class=HTMLResponse, name="admin_servidores")
def admin_servidores(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    err = request.session.pop("tiktok_error", None)
    ok = request.session.pop("tiktok_ok", None)
    lang = i18n.resolve_lang(request)
    youtube_linked = db.list_oauth_accounts_public("youtube")
    instagram_linked = db.list_oauth_accounts_public("instagram")
    facebook_linked = db.list_oauth_accounts_public("facebook")
    x_linked = db.list_oauth_accounts_public("x")
    dailymotion_linked = db.list_oauth_accounts_public("dailymotion")
    bilibili_linked = db.list_oauth_accounts_public("bilibili")
    snapchat_linked = db.list_oauth_accounts_public("snapchat")
    tiktok_linked = db.list_connected_tiktok_accounts()
    import rumble_publish

    rumble_token_set = bool(rumble_publish.access_token())
    rumble_channel = rumble_publish.channel_id()
    return _render(
        request,
        "admin_servidores.html",
        {
            "user": admin,
            "nav_active": "servidores",
            "platforms": platforms.platform_list(lang),
            "linked_accounts": tiktok_linked,
            "youtube_linked": youtube_linked,
            "instagram_linked": instagram_linked,
            "facebook_linked": facebook_linked,
            "x_linked": x_linked,
            "dailymotion_linked": dailymotion_linked,
            "bilibili_linked": bilibili_linked,
            "snapchat_linked": snapchat_linked,
            "oauth_account_counts": {
                "tiktok": len(tiktok_linked),
                "youtube": len(youtube_linked),
                "instagram": len(instagram_linked),
                "facebook": len(facebook_linked),
                "x": len(x_linked),
                "dailymotion": len(dailymotion_linked),
                "bilibili": len(bilibili_linked),
                "snapchat": len(snapchat_linked),
                "rumble": 1 if rumble_token_set else 0,
            },
            "platform_creds": db.list_platform_credentials_public(),
            "group_account_choices": db.list_server_group_account_choices(lang),
            "server_accounts": db.list_server_accounts(lang),
            "oauth_configured": tiktok_oauth.oauth_configured(),
            "oauth_scopes": tiktok_oauth.oauth_scopes(),
            "tiktok_redirect_uri": tiktok_oauth.redirect_uri(),
            "youtube_oauth_configured": youtube_oauth.oauth_configured(),
            "youtube_oauth_scopes": youtube_oauth.oauth_scopes(),
            "youtube_redirect_uri": youtube_oauth.redirect_uri(),
            "instagram_oauth_configured": instagram_oauth.oauth_configured(),
            "instagram_redirect_uri": instagram_oauth.redirect_uri(),
            "facebook_oauth_configured": facebook_oauth.oauth_configured(),
            "facebook_redirect_uri": facebook_oauth.redirect_uri(),
            "x_oauth_configured": x_oauth.oauth_configured(),
            "x_redirect_uri": x_oauth.redirect_uri(),
            "dailymotion_oauth_configured": dailymotion_oauth.oauth_configured(),
            "dailymotion_redirect_uri": dailymotion_oauth.redirect_uri(),
            "bilibili_oauth_configured": bilibili_oauth.oauth_configured(),
            "bilibili_redirect_uri": bilibili_oauth.redirect_uri(),
            "snapchat_oauth_configured": snapchat_oauth.oauth_configured(),
            "snapchat_redirect_uri": snapchat_oauth.redirect_uri(),
            "rumble_token_set": rumble_token_set,
            "rumble_channel": rumble_channel,
            "error": err,
            "success": ok,
        },
    )


@app.get("/admin/api-documento", response_class=HTMLResponse, name="admin_api_documento")
def admin_api_documento(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    return _render(
        request,
        "admin_api_documento.html",
        {
            "user": admin,
            "nav_active": "api_docs",
            "api_docs": platforms.api_document_rows(lang),
        },
    )


@app.get("/admin/extractor", response_class=HTMLResponse, name="admin_extractor")
def admin_extractor_page(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    return _render(
        request,
        "admin_extractor.html",
        {
            "user": admin,
            "nav_active": "extractor",
            "platform_choices": platforms.platform_list(lang),
            "extractor_limits": {
                "batch_min": extractor.MIN_BATCH,
                "batch_max": extractor.MAX_BATCH,
                "interval_min": extractor.MIN_INTERVAL_MINUTES,
                "interval_max": extractor.MAX_INTERVAL_MINUTES,
                "rest_min": extractor.MIN_REST_SECONDS,
                "rest_max": extractor.MAX_REST_SECONDS,
            },
        },
    )


def _extractor_account_choice(
    user: db.User, account_link_id: str, lang: str
) -> dict | None:
    """Cuenta válida para el extractor (solo cuentas, no grupos)."""
    account_id = (account_link_id or "").strip()
    if not account_id:
        return None
    choices = db.list_stats_filter_choices(user, lang=lang)
    return next(
        (
            c
            for c in choices
            if c.get("id") == account_id and c.get("kind") == "link"
        ),
        None,
    )


def _extractor_require_source_api(
    platform_id: str, account_link_id: str, lang: str
) -> JSONResponse | None:
    """Consulta la API de la cuenta/servidor origen antes de buscar videos."""
    result = platform_api.verify_account_platform(platform_id, account_link_id, lang)
    if result.get("ok"):
        return None
    name = i18n.t(f"platform.{platform_id}", lang)
    return JSONResponse(
        {
            "ok": False,
            "error": i18n.t(
                "extractor.err_api",
                lang,
                platform=name,
                detail=str(result.get("message") or "").strip(),
            ),
        },
        status_code=400,
    )


def _extractor_platform_meta(lang: str) -> dict[str, dict]:
    return {
        p["id"]: {"name": p["name"], "icon": p["icon"]}
        for p in platforms.platform_list(lang)
    }


def _extractor_job_public(job: dict, lang: str) -> dict:
    names = _extractor_platform_meta(lang)
    progress = db.extractor_job_progress(job)
    state = job.get("platform_state") or {}
    per_platform = []
    for item in progress["per_platform"]:
        pid = item["platform_id"]
        entry = state.get(pid) if isinstance(state.get(pid), dict) else {}
        meta = names.get(pid, {})
        per_platform.append(
            {
                "platform_id": pid,
                "name": meta.get("name", pid),
                "icon": meta.get("icon", ""),
                "done": item["done"],
                "pending": item["pending"],
                "total": item["total"],
                "disabled": bool(entry.get("disabled")),
                "paused": bool(entry.get("paused")),
                "last_error": str(entry.get("last_error") or ""),
            }
        )
    source_meta = names.get(job["source_platform_id"], {})
    return {
        "id": job["id"],
        "account_link_id": job["account_link_id"],
        "account_name": job["account_name"],
        "source_platform_id": job["source_platform_id"],
        "source_name": source_meta.get("name", job["source_platform_id"]),
        "source_icon": source_meta.get("icon", ""),
        "status": job["status"],
        "status_note": job["status_note"],
        "batch_size": job["batch_size"],
        "effective_batch": job["effective_batch"],
        "interval_minutes": job["interval_minutes"],
        "rest_seconds": job["rest_seconds"],
        "next_action_at": job["next_action_at"],
        "created_at": job["created_at"],
        "source_total": progress["source_total"],
        "total_ops": progress["total_ops"],
        "done_ops": progress["done_ops"],
        "pending_ops": progress["pending_ops"],
        "per_platform": per_platform,
        "events": db.list_extractor_events(job["id"], limit=30),
    }


@app.get("/admin/api/extractor/scan")
def api_extractor_scan(request: Request, platform: str = "", account: str = ""):
    guard = _require_admin_json(request)
    if guard:
        return guard
    user = _session_user(request)
    lang = i18n.resolve_lang(request)
    pid = (platform or "").strip()
    if pid not in platforms.PLATFORM_IDS:
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_platform", lang)},
            status_code=400,
        )
    choice = _extractor_account_choice(user, account, lang)
    if not choice:
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_account", lang)},
            status_code=400,
        )
    if pid not in (choice.get("platform_ids") or []):
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_source_unlinked", lang)},
            status_code=400,
        )
    api_block = _extractor_require_source_api(pid, choice["id"], lang)
    if api_block:
        return api_block
    target_ids = [t for t in (choice.get("platform_ids") or []) if t != pid]
    summary = extractor.scan_summary(choice["id"], pid, target_ids)
    names = _extractor_platform_meta(lang)
    targets = []
    for item in summary["targets"]:
        tid = item["platform_id"]
        meta = names.get(tid, {})
        targets.append(
            {
                "platform_id": tid,
                "name": meta.get("name", tid),
                "icon": meta.get("icon", ""),
                "pending": item["pending"],
                "cycle_cap": extractor.platform_cycle_cap(tid),
            }
        )
    return {
        "ok": True,
        "total": summary["total"],
        "targets": targets,
        "account_name": choice.get("name") or "",
        "conflict": db.extractor_job_conflict_exists(choice["id"], pid),
    }


@app.get("/admin/api/extractor/jobs")
def api_extractor_jobs(request: Request):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    jobs = [_extractor_job_public(j, lang) for j in db.list_extractor_jobs()]
    return {"ok": True, "jobs": jobs}


@app.post("/admin/api/extractor/jobs")
def api_extractor_create_job(request: Request, body: ExtractorJobBody):
    guard = _require_admin_json(request)
    if guard:
        return guard
    user = _session_user(request)
    lang = i18n.resolve_lang(request)

    pid = (body.source_platform_id or "").strip()
    if pid not in platforms.PLATFORM_IDS:
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_platform", lang)},
            status_code=400,
        )
    choice = _extractor_account_choice(user, body.account_link_id, lang)
    if not choice:
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_account", lang)},
            status_code=400,
        )
    if pid not in (choice.get("platform_ids") or []):
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_source_unlinked", lang)},
            status_code=400,
        )

    api_block = _extractor_require_source_api(pid, choice["id"], lang)
    if api_block:
        return api_block

    allowed_targets = [t for t in (choice.get("platform_ids") or []) if t != pid]
    requested = [
        str(t).strip() for t in (body.target_platform_ids or []) if str(t).strip()
    ]
    targets = [t for t in requested if t in allowed_targets] or list(allowed_targets)
    if not targets:
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_no_targets", lang)},
            status_code=400,
        )

    if not (extractor.MIN_BATCH <= body.batch_size <= extractor.MAX_BATCH):
        return JSONResponse(
            {
                "ok": False,
                "error": i18n.t(
                    "extractor.err_batch",
                    lang,
                    min=extractor.MIN_BATCH,
                    max=extractor.MAX_BATCH,
                ),
            },
            status_code=400,
        )
    if not (
        extractor.MIN_INTERVAL_MINUTES
        <= body.interval_minutes
        <= extractor.MAX_INTERVAL_MINUTES
    ):
        return JSONResponse(
            {
                "ok": False,
                "error": i18n.t(
                    "extractor.err_interval",
                    lang,
                    min=extractor.MIN_INTERVAL_MINUTES,
                    max=extractor.MAX_INTERVAL_MINUTES,
                ),
            },
            status_code=400,
        )
    if not (
        extractor.MIN_REST_SECONDS <= body.rest_seconds <= extractor.MAX_REST_SECONDS
    ):
        return JSONResponse(
            {
                "ok": False,
                "error": i18n.t(
                    "extractor.err_rest",
                    lang,
                    min=extractor.MIN_REST_SECONDS,
                    max=extractor.MAX_REST_SECONDS,
                ),
            },
            status_code=400,
        )

    if db.extractor_job_conflict_exists(choice["id"], pid):
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_duplicate", lang)},
            status_code=409,
        )

    total = db.count_extractor_source_videos(choice["id"], pid)
    if total <= 0:
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_no_videos", lang)},
            status_code=400,
        )

    job = db.create_extractor_job(
        owner_user_id=user.id,
        account_link_id=choice["id"],
        account_name=choice.get("name") or "",
        source_platform_id=pid,
        target_platform_ids=targets,
        total_videos=total,
        batch_size=body.batch_size,
        interval_minutes=body.interval_minutes,
        rest_seconds=body.rest_seconds,
        lang=lang,
    )
    names = _extractor_platform_meta(lang)
    target_names = ", ".join(names.get(t, {}).get("name", t) for t in targets)
    db.add_extractor_event(
        job["id"],
        "info",
        i18n.t(
            "extractor.ev_created",
            lang,
            total=total,
            source=names.get(pid, {}).get("name", pid),
            targets=target_names,
        ),
    )
    return {"ok": True, "job": _extractor_job_public(job, lang)}


@app.post("/admin/api/extractor/jobs/{job_id}/pause")
def api_extractor_pause_job(request: Request, job_id: str):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    job = db.get_extractor_job(job_id)
    if not job:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    if job["status"] == "running":
        db.update_extractor_job(job["id"], status="paused")
        db.add_extractor_event(
            job["id"], "info", i18n.t("extractor.ev_paused", lang)
        )
    job = db.get_extractor_job(job_id)
    return {"ok": True, "job": _extractor_job_public(job, lang)}


@app.post("/admin/api/extractor/jobs/{job_id}/resume")
def api_extractor_resume_job(request: Request, job_id: str):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    job = db.get_extractor_job(job_id)
    if not job:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    if job["status"] in ("paused", "error"):
        state = job.get("platform_state") or {}
        # Al reanudar el trabajo se reintentan los caídos, no los pausados a mano.
        for pid, entry in list(state.items()):
            if isinstance(entry, dict) and entry.get("disabled") and not entry.get("paused"):
                entry["disabled"] = False
                entry["probing"] = True
                entry["fails"] = 0
        db.update_extractor_job(
            job["id"],
            status="running",
            status_note="",
            platform_state=state,
            next_action_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add_extractor_event(
            job["id"], "info", i18n.t("extractor.ev_resumed", lang)
        )
    job = db.get_extractor_job(job_id)
    return {"ok": True, "job": _extractor_job_public(job, lang)}


@app.post("/admin/api/extractor/jobs/{job_id}/targets/{platform_id}/pause")
def api_extractor_pause_target(request: Request, job_id: str, platform_id: str):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    job = extractor.set_target_paused(job_id, platform_id, paused=True, lang=lang)
    if not job:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True, "job": _extractor_job_public(job, lang)}


@app.post("/admin/api/extractor/jobs/{job_id}/targets/{platform_id}/resume")
def api_extractor_resume_target(request: Request, job_id: str, platform_id: str):
    guard = _require_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    job = extractor.set_target_paused(job_id, platform_id, paused=False, lang=lang)
    if not job:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True, "job": _extractor_job_public(job, lang)}


@app.delete("/admin/api/extractor/jobs/{job_id}")
def api_extractor_delete_job(request: Request, job_id: str):
    guard = _require_admin_json(request)
    if guard:
        return guard
    if not db.delete_extractor_job(job_id):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True}


@app.post("/admin/panel/email", name="admin_panel_save_email")
def admin_panel_save_email(
    request: Request,
    email: Annotated[str, Form()],
):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _panel_redirect_login()
    addr = (email or "").strip()
    if not _valid_email(addr):
        request.session["panel_error"] = _msg(request, "panel.flash.invalid_email")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    db.set_app_setting("admin_email", addr)
    request.session["panel_ok"] = _msg(request, "panel.flash.email_saved")
    return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)


@app.post("/admin/panel/password-reset", name="admin_panel_password_reset")
def admin_panel_password_reset(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _panel_redirect_login()
    lang = i18n.resolve_lang(request)
    to = site_config.notification_email()
    if not to:
        request.session["panel_error"] = _msg(request, "panel.flash.no_email")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    if not notify.smtp_configured():
        request.session["panel_error"] = _msg(request, "panel.flash.no_smtp")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    token = db.create_password_reset_token(admin.id)
    reset_url = _password_reset_url(request, token)
    if not notify.send_password_reset_email(to=to, reset_url=reset_url, lang=lang):
        request.session["panel_error"] = _msg(request, "panel.flash.mail_fail")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    request.session["panel_ok"] = _msg(request, "panel.flash.reset_sent", email=to)
    return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)


@app.get(
    "/admin/panel/restablecer",
    response_class=HTMLResponse,
    name="admin_panel_reset_get",
)
def admin_panel_reset_get(request: Request):
    token = (request.query_params.get("token") or "").strip()
    lang = i18n.resolve_lang(request)
    if not db.get_password_reset_user_id(token):
        return _render(
            request,
            "admin_panel_reset.html",
            {
                "error": i18n.t("panel.reset.invalid", lang),
                "token_valid": False,
            },
            status_code=400,
        )
    err = request.session.pop("panel_reset_error", None)
    return _render(
        request,
        "admin_panel_reset.html",
        {
            "token": token,
            "token_valid": True,
            "error": err,
        },
    )


@app.post("/admin/panel/restablecer", name="admin_panel_reset_post")
def admin_panel_reset_post(
    request: Request,
    token: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
):
    lang = i18n.resolve_lang(request)
    tok = (token or "").strip()
    pw = (password or "").strip()
    pw2 = (password_confirm or "").strip()
    if not db.get_password_reset_user_id(tok):
        return _render(
            request,
            "admin_panel_reset.html",
            {
                "error": i18n.t("panel.reset.invalid", lang),
                "token_valid": False,
            },
            status_code=400,
        )
    if len(pw) < 4:
        request.session["panel_reset_error"] = i18n.t("panel.reset.too_short", lang)
        return RedirectResponse(
            url=str(request.url_for("admin_panel_reset_get")) + f"?token={tok}",
            status_code=303,
        )
    if pw != pw2:
        request.session["panel_reset_error"] = i18n.t("panel.reset.mismatch", lang)
        return RedirectResponse(
            url=str(request.url_for("admin_panel_reset_get")) + f"?token={tok}",
            status_code=303,
        )
    uid = db.consume_password_reset_token(tok)
    if not uid:
        return _render(
            request,
            "admin_panel_reset.html",
            {
                "error": i18n.t("panel.reset.invalid", lang),
                "token_valid": False,
            },
            status_code=400,
        )
    try:
        db.set_admin_password(uid, pw)
    except ValueError:
        request.session["panel_reset_error"] = i18n.t("panel.reset.fail", lang)
        return RedirectResponse(
            url=str(request.url_for("admin_panel_reset_get")) + f"?token={tok}",
            status_code=303,
        )
    ok_msg = i18n.t("panel.reset.ok", lang)
    request.session.clear()
    request.session["login_ok"] = ok_msg
    return RedirectResponse(url="/login", status_code=303)


@app.get("/admin/tiktokers")
def admin_tiktokers_redirect():
    return RedirectResponse(url="/admin/servidores", status_code=301)


@app.get("/oauth/tiktok/connect", name="tiktok_oauth_connect")
def tiktok_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    if not tiktok_oauth.oauth_configured():
        request.session["tiktok_error"] = (
            "Faltan las credenciales de TikTok. Pon Client Key y Secret en Servidores."
        )
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = tiktok_oauth.new_csrf_state()
    request.session["tiktok_oauth_state"] = state
    request.session["tiktok_oauth_user_id"] = admin.id
    url = tiktok_oauth.build_authorize_url(state=state)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/tiktok/callback", name="tiktok_oauth_callback")
def tiktok_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    saved_state = request.session.pop("tiktok_oauth_state", None)
    linked_by = request.session.pop("tiktok_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        request.session["tiktok_error"] = f"TikTok authorization denied: {err_param}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = "Invalid OAuth state. Please try again."
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = "TikTok did not return an authorization code."
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = tiktok_oauth.exchange_code_for_tokens(code)
        access = token_data.get("access_token") or ""
        refresh = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in TikTok response.")
        profile = tiktok_oauth.fetch_user_profile(access)
        open_id = profile.get("open_id") or token_data.get("open_id") or ""
        db.save_tiktok_oauth_connection(
            open_id=str(open_id),
            tiktok_username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=int(expires_in) if expires_in is not None else None,
            scopes=tiktok_oauth.oauth_scopes(),
            client_key=tiktok_oauth.client_key(),
            client_secret=tiktok_oauth.client_secret(),
            redirect_uri=tiktok_oauth.redirect_uri(),
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        uname = profile.get("username") or "account"
        request.session["tiktok_ok"] = f"Connected @{uname} successfully."
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.delete("/admin/api/tiktokers/{config_id}")
def api_tiktok_delete(request: Request, config_id: str):
    deny = _require_admin_json(request)
    if deny:
        return deny
    try:
        db.delete_tiktok_api_config(config_id)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=404)
    return {"ok": True, "message": "Account disconnected."}


@app.get("/oauth/youtube/connect", name="youtube_oauth_connect")
def youtube_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    if not youtube_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.youtube_oauth_missing", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = youtube_oauth.new_csrf_state()
    request.session["youtube_oauth_state"] = state
    request.session["youtube_oauth_user_id"] = admin.id
    url = youtube_oauth.build_authorize_url(state=state)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/youtube/callback", name="youtube_oauth_callback")
def youtube_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("youtube_oauth_state", None)
    linked_by = request.session.pop("youtube_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"YouTube: {desc}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.youtube_no_code", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = youtube_oauth.exchange_code_for_tokens(code)
        access = token_data.get("access_token") or ""
        refresh = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in Google response.")
        profile = youtube_oauth.fetch_channel_profile(access)
        open_id = profile.get("open_id") or ""
        if not open_id:
            raise ValueError("YouTube did not return a channel id.")
        db.save_oauth_connection(
            platform_id="youtube",
            open_id=str(open_id),
            username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=int(expires_in) if expires_in is not None else None,
            scopes=youtube_oauth.oauth_scopes(),
            client_id=youtube_oauth.client_id(),
            client_secret=youtube_oauth.client_secret(),
            redirect_uri=youtube_oauth.redirect_uri(),
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        label = profile.get("display_name") or profile.get("username") or "YouTube"
        request.session["tiktok_ok"] = i18n.t("servers.youtube_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.get("/oauth/instagram/connect", name="instagram_oauth_connect")
def instagram_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    if not instagram_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.instagram_oauth_missing", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = instagram_oauth.new_csrf_state()
    request.session["instagram_oauth_state"] = state
    request.session["instagram_oauth_user_id"] = admin.id
    url = instagram_oauth.build_authorize_url(state=state)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/instagram/callback", name="instagram_oauth_callback")
def instagram_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("instagram_oauth_state", None)
    linked_by = request.session.pop("instagram_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Instagram: {desc}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.instagram_no_code", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = instagram_oauth.exchange_code_for_tokens(code)
        access = str(token_data.get("access_token") or "").strip()
        if not access:
            raise ValueError("No access token in Instagram response.")
        expires_in = token_data.get("expires_in")
        try:
            long_lived = instagram_oauth.exchange_long_lived(access)
            access = str(long_lived.get("access_token") or access).strip()
            if long_lived.get("expires_in") is not None:
                expires_in = long_lived.get("expires_in")
        except ValueError:
            if expires_in is None:
                expires_in = 3600
        profile = instagram_oauth.fetch_profile(access)
        open_id = profile.get("open_id") or token_data.get("user_id") or ""
        if not open_id:
            raise ValueError("Instagram did not return a user id.")
        db.save_oauth_connection(
            platform_id="instagram",
            open_id=str(open_id),
            username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=access,
            expires_in=int(expires_in) if expires_in is not None else None,
            scopes=instagram_oauth.oauth_scopes(),
            client_id=instagram_oauth.client_id(),
            client_secret=instagram_oauth.client_secret(),
            redirect_uri=instagram_oauth.redirect_uri(),
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        label = profile.get("username") or profile.get("display_name") or "Instagram"
        request.session["tiktok_ok"] = i18n.t("servers.instagram_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.get("/oauth/facebook/connect", name="facebook_oauth_connect")
def facebook_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    if not facebook_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.facebook_oauth_missing", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = facebook_oauth.new_csrf_state()
    request.session["facebook_oauth_state"] = state
    request.session["facebook_oauth_user_id"] = admin.id
    url = facebook_oauth.build_authorize_url(state=state)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/facebook/callback", name="facebook_oauth_callback")
def facebook_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("facebook_oauth_state", None)
    linked_by = request.session.pop("facebook_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Facebook: {desc}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.facebook_no_code", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = facebook_oauth.exchange_code_for_tokens(code)
        access = str(token_data.get("access_token") or "").strip()
        if not access:
            raise ValueError("No access token in Facebook response.")
        expires_in = token_data.get("expires_in")
        try:
            long_lived = facebook_oauth.exchange_long_lived(access)
            access = str(long_lived.get("access_token") or access).strip()
            if long_lived.get("expires_in") is not None:
                expires_in = long_lived.get("expires_in")
        except ValueError:
            if expires_in is None:
                expires_in = 3600
        pages = facebook_oauth.list_pages(access)
        if not pages:
            raise ValueError(i18n.t("servers.facebook_no_pages", lang))
        for page in pages:
            db.save_oauth_connection(
                platform_id="facebook",
                open_id=page["open_id"],
                username=page.get("username"),
                display_name=page.get("display_name"),
                access_token=page["access_token"],
                refresh_token=access,
                expires_in=int(expires_in) if expires_in is not None else None,
                scopes=facebook_oauth.oauth_scopes(),
                client_id=facebook_oauth.client_id(),
                client_secret=facebook_oauth.client_secret(),
                redirect_uri=facebook_oauth.redirect_uri(),
                linked_by_user_id=str(linked_by) if linked_by else None,
            )
        request.session["tiktok_ok"] = i18n.t(
            "servers.facebook_connected", lang, n=len(pages)
        )
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.get("/oauth/x/connect", name="x_oauth_connect")
def x_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    if not x_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.x_oauth_missing", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = x_oauth.new_csrf_state()
    verifier, challenge = x_oauth.pkce_pair()
    request.session["x_oauth_state"] = state
    request.session["x_oauth_verifier"] = verifier
    request.session["x_oauth_user_id"] = admin.id
    url = x_oauth.build_authorize_url(state=state, code_challenge=challenge)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/x/callback", name="x_oauth_callback")
def x_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("x_oauth_state", None)
    verifier = request.session.pop("x_oauth_verifier", None)
    linked_by = request.session.pop("x_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"X: {desc}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state or not verifier:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.x_no_code", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = x_oauth.exchange_code_for_tokens(code, code_verifier=str(verifier))
        access = str(token_data.get("access_token") or "").strip()
        refresh = str(token_data.get("refresh_token") or "").strip() or None
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in X response.")
        profile = x_oauth.fetch_profile(access)
        open_id = profile.get("open_id") or ""
        if not open_id:
            raise ValueError("X did not return a user id.")
        db.save_oauth_connection(
            platform_id="x",
            open_id=str(open_id),
            username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=int(expires_in) if expires_in is not None else 7200,
            scopes=x_oauth.oauth_scopes(),
            client_id=x_oauth.client_id(),
            client_secret=x_oauth.client_secret(),
            redirect_uri=x_oauth.redirect_uri(),
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        label = profile.get("username") or profile.get("display_name") or "X"
        request.session["tiktok_ok"] = i18n.t("servers.x_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.get("/oauth/dailymotion/connect", name="dailymotion_oauth_connect")
def dailymotion_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    if not dailymotion_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.dailymotion_oauth_missing", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = dailymotion_oauth.new_csrf_state()
    request.session["dailymotion_oauth_state"] = state
    request.session["dailymotion_oauth_user_id"] = admin.id
    url = dailymotion_oauth.build_authorize_url(state=state)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/dailymotion/callback", name="dailymotion_oauth_callback")
def dailymotion_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("dailymotion_oauth_state", None)
    linked_by = request.session.pop("dailymotion_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Dailymotion: {desc}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.dailymotion_no_code", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = dailymotion_oauth.exchange_code_for_tokens(code)
        access = str(token_data.get("access_token") or "").strip()
        refresh = str(token_data.get("refresh_token") or "").strip() or None
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in Dailymotion response.")
        profile = dailymotion_oauth.fetch_profile(access)
        open_id = profile.get("open_id") or ""
        if not open_id:
            raise ValueError("Dailymotion did not return a user id.")
        db.save_oauth_connection(
            platform_id="dailymotion",
            open_id=str(open_id),
            username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=int(expires_in) if expires_in is not None else None,
            scopes=dailymotion_oauth.oauth_scopes(),
            client_id=dailymotion_oauth.client_id(),
            client_secret=dailymotion_oauth.client_secret(),
            redirect_uri=dailymotion_oauth.redirect_uri(),
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        label = profile.get("username") or profile.get("display_name") or "Dailymotion"
        request.session["tiktok_ok"] = i18n.t("servers.dailymotion_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.get("/oauth/bilibili/connect", name="bilibili_oauth_connect")
def bilibili_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    if not bilibili_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.bilibili_oauth_missing", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = bilibili_oauth.new_csrf_state()
    request.session["bilibili_oauth_state"] = state
    request.session["bilibili_oauth_user_id"] = admin.id
    url = bilibili_oauth.build_authorize_url(state=state)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/bilibili/callback", name="bilibili_oauth_callback")
def bilibili_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("bilibili_oauth_state", None)
    linked_by = request.session.pop("bilibili_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Bilibili: {desc}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.bilibili_no_code", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = bilibili_oauth.exchange_code_for_tokens(code)
        access = str(token_data.get("access_token") or "").strip()
        refresh = str(token_data.get("refresh_token") or "").strip() or None
        if not access:
            raise ValueError("No access token in Bilibili response.")
        profile = bilibili_oauth.fetch_profile(access)
        open_id = (
            profile.get("open_id")
            or token_data.get("openid")
            or token_data.get("open_id")
            or ""
        )
        if not open_id:
            raise ValueError("Bilibili did not return an openid.")
        db.save_oauth_connection(
            platform_id="bilibili",
            open_id=str(open_id),
            username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=bilibili_oauth.expires_seconds(token_data.get("expires_in")),
            scopes=bilibili_oauth.oauth_scopes(),
            client_id=bilibili_oauth.client_id(),
            client_secret=bilibili_oauth.client_secret(),
            redirect_uri=bilibili_oauth.redirect_uri(),
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        label = profile.get("username") or profile.get("display_name") or "Bilibili"
        request.session["tiktok_ok"] = i18n.t("servers.bilibili_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.get("/oauth/snapchat/connect", name="snapchat_oauth_connect")
def snapchat_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    if not snapchat_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.snapchat_oauth_missing", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = snapchat_oauth.new_csrf_state()
    request.session["snapchat_oauth_state"] = state
    request.session["snapchat_oauth_user_id"] = admin.id
    url = snapchat_oauth.build_authorize_url(state=state)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/snapchat/callback", name="snapchat_oauth_callback")
def snapchat_oauth_callback(request: Request):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("snapchat_oauth_state", None)
    linked_by = request.session.pop("snapchat_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Snapchat: {desc}"
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.snapchat_no_code", lang)
        return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)
    try:
        token_data = snapchat_oauth.exchange_code_for_tokens(code)
        access = str(token_data.get("access_token") or "").strip()
        refresh = str(token_data.get("refresh_token") or "").strip() or None
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in Snapchat response.")
        profile = snapchat_oauth.fetch_profile(access)
        open_id = profile.get("open_id") or ""
        if not open_id:
            raise ValueError("Snapchat did not return a public profile id.")
        db.save_oauth_connection(
            platform_id="snapchat",
            open_id=str(open_id),
            username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=int(expires_in) if expires_in is not None else 3600,
            scopes=snapchat_oauth.oauth_scopes(),
            client_id=snapchat_oauth.client_id(),
            client_secret=snapchat_oauth.client_secret(),
            redirect_uri=snapchat_oauth.redirect_uri(),
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        label = profile.get("username") or profile.get("display_name") or "Snapchat"
        request.session["tiktok_ok"] = i18n.t("servers.snapchat_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_servidores"), status_code=303)


@app.delete("/admin/api/oauth/{account_id}")
def api_oauth_delete(request: Request, account_id: str):
    deny = _require_admin_json(request)
    if deny:
        return deny
    try:
        db.delete_oauth_account(account_id)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=404)
    return {"ok": True, "message": "Account disconnected."}


@app.post("/admin/api/platforms/{platform_id}/credentials")
def api_save_platform_credentials(request: Request, platform_id: str, body: PlatformApiBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    if platform_id not in platforms.PLATFORM_IDS:
        return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
    lang = i18n.resolve_lang(request)
    try:
        public = db.upsert_platform_credentials(
            platform_id,
            name=body.name,
            client_id=body.client_id,
            client_secret=body.client_secret or None,
            access_token=body.access_token or None,
            extra=body.extra,
        )
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(str(e), lang)},
            status_code=400,
        )
    return {"ok": True, "message": i18n.t("api.saved", lang), **public}


@app.post("/admin/api/platforms/{platform_id}/test")
def api_test_platform(request: Request, platform_id: str, body: PlatformApiBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    return platform_api.test_platform(
        platform_id,
        lang,
        draft=body.model_dump(),
        save_result=False,
    )


@app.post("/admin/api/platforms/test-all")
def api_test_all_platforms(request: Request):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    results = platform_api.test_all_platforms(lang)
    return {"ok": True, "results": results}


def _server_group_error_message(code: str, lang: str) -> str:
    keys = {
        "name_required": "servers.groups_name_required",
        "platforms_required": "servers.groups_platforms_required",
        "name_taken": "servers.groups_name_taken",
        "account_name_conflict": "servers.groups_name_account_conflict",
        "members_not_linked": "servers.groups_members_not_linked",
        "not_found": "servers.groups_not_found",
        "save_fail": "servers.groups_save_fail",
    }
    return i18n.t(keys.get(code, "servers.network_error"), lang)


def _server_account_error_message(code: str, lang: str) -> str:
    keys = {
        "name_required": "servers.accounts_name_required",
        "platform_required": "servers.accounts_platform_required",
        "not_found": "servers.accounts_not_found",
        "save_fail": "servers.accounts_save_fail",
        "name_taken": "servers.accounts_name_taken",
        "link_name_taken": "servers.accounts_link_name_taken",
        "group_name_conflict": "servers.accounts_group_name_conflict",
    }
    return i18n.t(keys.get(code, "servers.network_error"), lang)


@app.post("/admin/api/server-account-links")
def api_create_account_link(request: Request, body: AccountLinkBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        group = db.create_account_link(body.name, lang=lang)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(str(e), lang)},
            status_code=400,
        )
    return {
        "ok": True,
        "group": group,
        "message": i18n.t("servers.accounts_saved", lang),
        "choices": db.list_server_group_account_choices(lang),
    }


@app.delete("/admin/api/server-account-links/{link_id}")
def api_delete_account_link(request: Request, link_id: str):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        db.delete_account_link(link_id)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(str(e), lang)},
            status_code=404,
        )
    return {
        "ok": True,
        "message": i18n.t("servers.accounts_deleted", lang),
        "choices": db.list_server_group_account_choices(lang),
    }


@app.post("/admin/api/server-account-links/{link_id}/active")
def api_set_account_link_active(
    request: Request, link_id: str, body: AccountLinkActiveBody
):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        group = db.set_account_link_active(link_id, body.active, lang=lang)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(str(e), lang)},
            status_code=404,
        )
    return {
        "ok": True,
        "group": group,
        "choices": db.list_server_group_account_choices(lang),
    }


@app.get("/admin/api/server-accounts")
def api_list_server_accounts(request: Request):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    accounts = db.list_server_accounts(lang)
    return {
        "ok": True,
        "accounts": accounts,
        "auto_groups": db.list_auto_account_groups(lang),
        "choices": db.list_server_group_account_choices(lang),
    }


@app.get("/admin/api/server-account-groups")
def api_list_server_account_groups(
    request: Request, q: str = "", page: int = 1, per_page: str = "10"
):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    page_size = db.normalize_team_members_per_page(per_page)
    page = max(1, page)
    groups, total = db.list_server_account_groups(q, page, page_size, lang=lang)
    if page_size is None:
        total_pages = 1
        page = 1
        per_page_out: int | str = "all"
    else:
        total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
        if page > total_pages:
            page = total_pages
            groups, total = db.list_server_account_groups(
                q, page, page_size, lang=lang
            )
        per_page_out = page_size
    return {
        "ok": True,
        "groups": groups,
        "page": page,
        "per_page": per_page_out,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1 and page_size is not None,
        "has_next": page < total_pages and page_size is not None,
    }


@app.post("/admin/api/server-accounts")
def api_create_server_account(request: Request, body: ServerAccountBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        account = db.create_server_account(body.name, body.platform_id, lang=lang)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(str(e), lang)},
            status_code=400,
        )
    return {
        "ok": True,
        "message": i18n.t("servers.accounts_saved", lang),
        "account": account,
        "choices": db.list_server_group_account_choices(lang),
    }


@app.put("/admin/api/server-accounts/{account_id}")
def api_update_server_account(request: Request, account_id: str, body: ServerAccountBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        account = db.update_server_account(
            account_id, body.name, body.platform_id, lang=lang
        )
    except ValueError as e:
        code = str(e)
        status = 404 if code == "not_found" else 400
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(code, lang)},
            status_code=status,
        )
    return {
        "ok": True,
        "message": i18n.t("servers.accounts_saved", lang),
        "account": account,
        "choices": db.list_server_group_account_choices(lang),
    }


@app.post("/admin/api/server-accounts/{account_id}/active")
def api_set_server_account_active(
    request: Request, account_id: str, body: ServerAccountActiveBody
):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        account = db.set_server_account_active(account_id, body.active, lang=lang)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(str(e), lang)},
            status_code=404,
        )
    return {
        "ok": True,
        "account": account,
        "choices": db.list_server_group_account_choices(lang),
    }


@app.delete("/admin/api/server-accounts/{account_id}")
def api_delete_server_account(request: Request, account_id: str):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        db.delete_server_account(account_id)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(str(e), lang)},
            status_code=404,
        )
    return {
        "ok": True,
        "message": i18n.t("servers.accounts_deleted", lang),
        "choices": db.list_server_group_account_choices(lang),
    }


@app.get("/admin/api/server-groups")
def api_list_server_groups(request: Request):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    return {"ok": True, "groups": db.list_all_server_groups(lang)}


@app.get("/admin/api/server-groups/list")
def api_list_server_groups_page(
    request: Request, q: str = "", page: int = 1, per_page: str = "10"
):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    page_size = db.normalize_team_members_per_page(per_page)
    page = max(1, page)
    try:
        groups, total = db.list_server_groups_page(q, page, page_size, lang=lang)
    except Exception:
        return JSONResponse(
            {"ok": False, "error": i18n.t("servers.network_error", lang)},
            status_code=500,
        )
    if page_size is None:
        total_pages = 1
        page = 1
        per_page_out: int | str = "all"
    else:
        total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
        if page > total_pages:
            page = total_pages
            groups, total = db.list_server_groups_page(
                q, page, page_size, lang=lang
            )
        per_page_out = page_size
    return {
        "ok": True,
        "groups": groups,
        "page": page,
        "per_page": per_page_out,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1 and page_size is not None,
        "has_next": page < total_pages and page_size is not None,
    }


@app.post("/admin/api/server-groups")
def api_create_server_group(request: Request, body: ServerGroupBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    members = [m.model_dump() for m in body.members] if body.members else None
    account_ids = body.account_ids or None
    try:
        group = db.create_server_group(
            body.name,
            members,
            account_ids=account_ids,
            platform_ids=body.platform_ids or None,
            lang=lang,
        )
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_group_error_message(str(e), lang)},
            status_code=400,
        )
    return {
        "ok": True,
        "message": i18n.t("servers.groups_saved", lang),
        "group": group,
    }


@app.put("/admin/api/server-groups/{group_id}")
def api_update_server_group(request: Request, group_id: str, body: ServerGroupBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    members = [m.model_dump() for m in body.members] if body.members else None
    account_ids = body.account_ids or None
    try:
        group = db.update_server_group(
            group_id,
            body.name,
            members,
            account_ids=account_ids,
            platform_ids=body.platform_ids or None,
            lang=lang,
        )
    except ValueError as e:
        code = str(e)
        status = 404 if code == "not_found" else 400
        return JSONResponse(
            {"ok": False, "error": _server_group_error_message(code, lang)},
            status_code=status,
        )
    return {
        "ok": True,
        "message": i18n.t("servers.groups_saved", lang),
        "group": group,
    }


@app.post("/admin/api/server-groups/{group_id}/active")
def api_set_server_group_active(
    request: Request, group_id: str, body: ServerGroupActiveBody
):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        group = db.set_server_group_active(group_id, body.active)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_group_error_message(str(e), lang)},
            status_code=404,
        )
    return {"ok": True, "group": group}


@app.delete("/admin/api/server-groups/{group_id}")
def api_delete_server_group(request: Request, group_id: str):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        db.delete_server_group(group_id)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _server_group_error_message(str(e), lang)},
            status_code=404,
        )
    return {"ok": True, "message": i18n.t("servers.groups_deleted", lang)}


@app.get("/admin/api/equipo/cuentas")
def api_equipo_cuentas(request: Request, q: str = "", selected: str = ""):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    selected_ids = [s.strip() for s in (selected or "").split(",") if s.strip()]
    accounts = db.list_team_server_account_choices(q, selected_ids, lang=lang)
    return {
        "ok": True,
        "accounts": accounts,
        "placeholder": i18n.t("team.link_account_placeholder", lang),
    }


@app.get("/admin/api/equipo/miembros")
def api_equipo_miembros(request: Request, q: str = "", page: int = 1, per_page: str = "10"):
    deny = _require_admin_json(request)
    if deny:
        return deny
    me = require_admin_privileges(request)
    lang = i18n.resolve_lang(request)
    mode_labels = db.user_mode_labels_for_lang(lang)
    page_size = db.normalize_team_members_per_page(per_page)
    page = max(1, page)
    exclude_id = me.id if me.role == "user" else None
    users, total = db.list_team_members(
        q, page, page_size, lang, exclude_user_id=exclude_id
    )
    if page_size is None:
        total_pages = 1
        page = 1
        per_page_out: int | str = "all"
    else:
        total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
        if page > total_pages:
            page = total_pages
            users, total = db.list_team_members(
                q, page, page_size, lang, exclude_user_id=exclude_id
            )
        per_page_out = page_size
    return {
        "ok": True,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "display_name": u.display_name,
                "user_mode": u.user_mode,
                "user_mode_label": mode_labels.get(u.user_mode, u.user_mode),
                "can_view_comments": u.can_view_comments,
                "active": u.active,
                "linked_tiktok_config_id": u.linked_tiktok_config_id or "",
                "linked_account_link_ids": db.list_user_account_link_ids(u.id),
                "can_manage": db.user_can_manage_member(me, u),
            }
            for u in users
        ],
        "page": page,
        "per_page": per_page_out,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1 and page_size is not None,
        "has_next": page < total_pages and page_size is not None,
    }


@app.post("/admin/api/equipo/usuario/{user_id}/estado")
def api_equipo_usuario_estado(request: Request, user_id: str, body: EquipoEstadoBody):
    deny = _require_admin_json(request)
    if deny:
        return deny
    me = require_admin_privileges(request)
    try:
        db.set_user_active(user_id, body.active, actor=me)
    except ValueError as e:
        lang = i18n.resolve_lang(request)
        return JSONResponse(
            {"ok": False, "error": _equipo_user_form_error(str(e), lang)},
            status_code=400,
        )
    return {"ok": True, "active": body.active}


def _form_checkbox_on(form, key: str) -> bool:
    val = form.get(key)
    if val is None:
        return False
    if isinstance(val, list):
        val = val[-1] if val else ""
    return str(val).strip().lower() in ("1", "true", "on", "yes")


def _equipo_user_form_error(message: str, lang: str) -> str:
    keys = {
        "Username already exists": "team.err.username_exists",
        "Username must be at least 2 characters": "team.err.username_short",
        "Password must be at least 4 characters": "team.err.password_short",
        "Invalid user mode": "team.err.invalid_mode",
        "Only the site administrator can manage this user": "team.err.site_admin_only",
    }
    key = keys.get((message or "").strip())
    return i18n.t(key, lang) if key else message


@app.post("/admin/api/equipo/usuario")
async def api_equipo_create_user(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    user_mode: Annotated[str, Form()] = "basic",
):
    deny = _require_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    form = await request.form()
    account_link_ids = [
        str(x).strip() for x in form.getlist("account_link_ids") if str(x).strip()
    ]
    can_view_comments = True
    try:
        user = db.create_user(
            username,
            password,
            username.strip(),
            "user",
            user_mode.strip(),
            account_link_ids=account_link_ids,
            can_view_comments=can_view_comments,
        )
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _equipo_user_form_error(str(e), lang)},
            status_code=400,
        )
    link_ids = db.list_user_account_link_ids(user.id)
    link_names = [
        c["name"]
        for c in db.list_team_server_account_choices(selected_ids=link_ids, lang=lang)
    ]
    return {
        "ok": True,
        "message": i18n.t("team.js.user_created", lang),
        "user": {
            "id": user.id,
            "username": user.username,
            "user_mode": user.user_mode,
            "can_view_comments": user.can_view_comments,
            "linked_account_link_ids": link_ids,
            "linked_account_names": link_names,
        },
    }


@app.post("/admin/api/equipo/usuario/{user_id}/edit")
async def api_equipo_usuario_edit(
    request: Request,
    user_id: str,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()] = "",
    user_mode: Annotated[str, Form()] = "basic",
):
    deny = _require_admin_json(request)
    if deny:
        return deny
    me = require_admin_privileges(request)
    target = db.get_user_by_id(user_id)
    if not target or target.role == "admin":
        return JSONResponse(
            {"ok": False, "error": "You cannot edit that user."},
            status_code=400,
        )
    pw = password.strip()
    u = username.strip()
    lang = i18n.resolve_lang(request)
    form = await request.form()
    account_link_ids = [
        str(x).strip() for x in form.getlist("account_link_ids") if str(x).strip()
    ]
    can_view_comments = _form_checkbox_on(form, "can_view_comments")
    try:
        updated = db.update_user_record(
            user_id,
            u,
            u,
            pw if pw else None,
            user_mode.strip(),
            account_link_ids=account_link_ids,
            can_view_comments=can_view_comments,
            actor=me,
        )
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _equipo_user_form_error(str(e), lang)},
            status_code=400,
        )
    link_ids = db.list_user_account_link_ids(updated.id)
    link_names = [
        c["name"]
        for c in db.list_team_server_account_choices(selected_ids=link_ids, lang=lang)
    ]
    return {
        "ok": True,
        "username": updated.username,
        "display_name": updated.display_name,
        "user_mode": updated.user_mode,
        "can_view_comments": updated.can_view_comments,
        "linked_account_link_ids": link_ids,
        "linked_account_names": link_names,
        "message": i18n.t("team.js.user_updated", lang),
    }


@app.delete("/admin/api/equipo/usuario/{user_id}")
def api_equipo_delete_user(request: Request, user_id: str):
    try:
        me = require_admin_privileges(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse(
                {"ok": False, "error": "Sign in as an administrator."},
                status_code=401,
            )
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    if me.id == user_id:
        return JSONResponse(
            {"ok": False, "error": "You cannot delete your own account."},
            status_code=400,
        )
    lang = i18n.resolve_lang(request)
    try:
        files = db.delete_user_by_id(user_id, actor=me)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _equipo_user_form_error(str(e), lang)},
            status_code=400,
        )
    for name in files:
        (UPLOAD_DIR / name).unlink(missing_ok=True)
    return {"ok": True, "message": "User deleted. Their videos and comments were removed from the database."}


@app.post("/admin/users", name="admin_create_user")
def admin_create_user(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    user_mode: Annotated[str, Form()] = "basic",
    linked_tiktok_config_id: Annotated[str, Form()] = "",
    can_view_comments: Annotated[str, Form()] = "1",
):
    try:
        require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login()
    comments_on = str(can_view_comments).strip().lower() in ("1", "true", "on", "yes")
    try:
        db.create_user(
            username,
            password,
            username.strip(),
            "user",
            user_mode.strip(),
            linked_tiktok_config_id.strip(),
            can_view_comments=comments_on,
        )
        request.session["panel_ok"] = "User created successfully"
    except ValueError as e:
        request.session["panel_error"] = str(e)
    return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
