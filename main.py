from __future__ import annotations

import asyncio
import json
import os
import uuid
import urllib.error
import urllib.request
from urllib.parse import quote, urlencode
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
from jinja2 import FileSystemBytecodeCache
from markupsafe import Markup
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".mov", ".mkv", ".m4v"}
ALLOWED_PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_MEDIA_EXT = ALLOWED_VIDEO_EXT | ALLOWED_PHOTO_EXT
VIDEO_MIME_EXT = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-matroska": ".mkv",
    "video/mkv": ".mkv",
    "video/x-m4v": ".m4v",
}
def _read_max_upload_mb() -> int:
    raw = (os.environ.get("MAX_UPLOAD_MB") or "500").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 500


MAX_UPLOAD_MB = _read_max_upload_mb()
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
PUBLISHER_MIN_VIDEO_SECONDS = 60
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
import vmos  # noqa: E402
import filehost  # noqa: E402
import chain  # noqa: E402
import x_funding  # noqa: E402
import publish_schedule  # noqa: E402
import publish_pending  # noqa: E402
import proxy_util  # noqa: E402
import membership  # noqa: E402
import video_temp_util  # noqa: E402
import video_probe  # noqa: E402
import video_compress  # noqa: E402
import security_headers  # noqa: E402

SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-cambiar-en-produccion")
_SCHEDULER_LOCK_FH = None


def _try_hold_scheduler_lock():
    """Un solo proceso uvicorn corre programador + extractor (el resto solo atiende HTTP)."""
    from db_engine import DATA_DIR

    path = DATA_DIR / "scheduler.lock"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+", encoding="utf-8")
    try:
        if os.name == "nt":
            import msvcrt

            fh.seek(0)
            fh.write("\0")
            fh.flush()
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fh.seek(0)
        fh.truncate()
        fh.write(str(os.getpid()))
        fh.flush()
        return fh
    except OSError:
        fh.close()
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _SCHEDULER_LOCK_FH
    db.init_db()
    db.seed_admin_if_missing()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    video_temp_util.cleanup_stale(UPLOAD_DIR)

    async def scheduled_worker() -> None:
        while True:
            try:
                await asyncio.to_thread(
                    publish_schedule.process_due_scheduled_publications,
                    upload_dir=UPLOAD_DIR,
                )
                await asyncio.to_thread(publish_pending.process_saved_jobs)
            except Exception:
                pass
            await asyncio.sleep(60)

    async def extractor_worker() -> None:
        while True:
            try:
                await asyncio.to_thread(
                    extractor.process_due_extractor_jobs,
                    upload_dir=UPLOAD_DIR,
                )
            except Exception:
                pass
            await asyncio.sleep(extractor.WORKER_TICK_SECONDS)

    async def bilibili_tv_worker() -> None:
        """Keep-alive Bilibili.tv y QR de .com: 3–5 días, horas distintas, una cuenta por ciclo."""
        while True:
            try:
                import bilibili_tv
                import bilibili_web

                await asyncio.to_thread(bilibili_tv.run_daily_keep_alive_if_due)
                await asyncio.to_thread(bilibili_web.run_keep_alive_if_due)
            except Exception:
                pass
            await asyncio.sleep(300)

    worker = None
    extractor_task = None
    bilibili_tv_task = None
    _SCHEDULER_LOCK_FH = _try_hold_scheduler_lock()
    if _SCHEDULER_LOCK_FH is not None:
        worker = asyncio.create_task(scheduled_worker())
        extractor_task = asyncio.create_task(extractor_worker())
        bilibili_tv_task = asyncio.create_task(bilibili_tv_worker())
    try:
        yield
    finally:
        for task in (worker, extractor_task, bilibili_tv_task):
            if task is not None:
                task.cancel()
        if worker is not None:
            await asyncio.gather(
                worker,
                extractor_task,
                bilibili_tv_task,
                return_exceptions=True,
            )
        if _SCHEDULER_LOCK_FH is not None:
            try:
                _SCHEDULER_LOCK_FH.close()
            except OSError:
                pass
            _SCHEDULER_LOCK_FH = None


class _AccountCredentialsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        name = (
            request.query_params.get("link_name")
            or request.query_params.get("account")
            or ""
        ).strip()
        if not name:
            try:
                name = str(request.session.get("oauth_link_target_name") or "").strip()
            except Exception:
                name = ""
        token = db.set_credentials_account_name(name)
        try:
            return await call_next(request)
        finally:
            db.reset_credentials_account_name(token)


app = FastAPI(lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(_AccountCredentialsMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="tt_session",
    max_age=60 * 60 * 24 * 7,
    same_site="none" if site_config.SITE_URL.startswith("https://") else "lax",
    https_only=site_config.SITE_URL.startswith("https://"),
)


@app.middleware("http")
async def _security_headers_middleware(request: Request, call_next):
    import time as _time

    t0 = _time.perf_counter()
    db.reset_request_db_caches()
    response = await call_next(request)
    elapsed = _time.perf_counter() - t0
    response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
    if elapsed >= 1.0:
        print(
            f"SLOW {elapsed:.2f}s {request.method} {request.url.path}",
            flush=True,
        )
    security_headers.apply_security_headers(request, response)
    return response
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
_jinja_cache_dir = BASE_DIR / ".data" / "jinja_cache"
_jinja_cache_dir.mkdir(parents=True, exist_ok=True)
templates.env.bytecode_cache = FileSystemBytecodeCache(str(_jinja_cache_dir))
templates.env.globals["user_can_access_publicaciones"] = db.user_can_access_publicaciones
templates.env.globals["user_has_admin_privileges"] = db.user_has_admin_privileges
templates.env.globals["user_is_site_admin"] = db.user_is_site_admin
templates.env.globals["user_is_tiktok_mode"] = db.user_is_tiktok_mode
templates.env.globals["user_is_publisher_mode"] = db.user_is_publisher_mode
templates.env.globals["user_can_access_servers"] = db.user_can_access_servers
templates.env.globals["user_can_manage_panel_accounts"] = db.user_can_manage_panel_accounts
templates.env.globals["support_unread_count"] = db.support_unread_count_for_viewer
templates.env.globals["format_publish_schedule"] = publish_schedule.format_scheduled_local
templates.env.filters["fromjson"] = json.loads


def _json_attr(value: object) -> Markup:
    escaped = (
        json.dumps(value, ensure_ascii=True)
        .replace("&", "&amp;")
        .replace("'", "&#39;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
    )
    return Markup(escaped)


templates.env.filters["json_attr"] = _json_attr
templates.env.globals.update(site_config.legal_context())
templates.env.globals["platform_select_label"] = platforms.platform_select_label


def _render(request: Request, template: str, ctx: dict | None = None, status_code: int = 200):
    base = {**site_config.legal_context(), **i18n.page_context(request)}
    if ctx:
        base.update(ctx)
    if "user" not in base:
        base["user"] = _session_user(request)
    return templates.TemplateResponse(request, template, base, status_code=status_code)


def _msg(request: Request, key: str, **kwargs: object) -> str:
    return i18n.t(key, i18n.resolve_lang(request), **kwargs)


def _render_legal(request: Request, template: str, page_title_key: str):
    lang = i18n.resolve_lang(request)
    page_updated = "5 de septiembre de 2026" if lang == "es" else "September 5, 2026"
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
    user = db.get_user_by_id(str(uid))
    if not user:
        return None
    expected = db.get_user_auth_version(user.id)
    session_ver = request.session.get("auth_version")
    if session_ver is None:
        request.session["auth_version"] = expected
        return user
    try:
        if int(session_ver) != expected:
            request.session.clear()
            return None
    except (TypeError, ValueError):
        request.session.clear()
        return None
    return user


def _establish_session(request: Request, user: db.User) -> None:
    request.session["user_id"] = user.id
    request.session["auth_version"] = db.get_user_auth_version(user.id)


def _keep_oauth_login(request: Request, user: db.User) -> None:
    """Reescribe la cookie de sesión en el callback: Snapchat a menudo no envía la cookie Lax."""
    _establish_session(request, user)


def _oauth_debug_log(platform: str, message: str) -> None:
    """Bitácora de diagnóstico OAuth (sin tokens ni secretos) en .data/oauth_debug.log."""
    try:
        from db_engine import DATA_DIR

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with (DATA_DIR / "oauth_debug.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} [{platform}] {message}\n")
    except Exception:
        pass


async def _oauth_callback_params(request: Request) -> dict[str, str]:
    out = {str(k): str(v) for k, v in request.query_params.items()}
    if request.method == "POST":
        try:
            form = await request.form()
        except Exception:
            form = {}
        for key in ("code", "state", "error", "error_description"):
            val = form.get(key) if form is not None else None
            if val and not out.get(key):
                out[key] = str(val)
    return out


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


def require_server_admin(request: Request) -> db.User:
    """Servidores, extractor, API Documento y OAuth: excluye al Usuario TikTok."""
    user = require_user(request)
    if not db.user_can_access_servers(user):
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
    use_own_x_api: bool | None = None


class VmosAccountBody(BaseModel):
    id: str = ""
    platform_id: str = ""
    name: str = ""
    access_key: str = ""
    secret_key: str = ""
    pad_code: str = ""
    template_id: str = ""
    remark: str = ""
    link_name: str = ""


class FilehostAccountBody(BaseModel):
    id: str = ""
    platform_id: str = ""
    name: str = ""
    api_key: str = ""
    extra: str = ""
    link_name: str = ""


class ChainAccountBody(BaseModel):
    id: str = ""
    platform_id: str = ""
    name: str = ""
    login: str = ""
    secret: str = ""
    extra: str = ""
    link_name: str = ""


class BilibiliQrStartBody(BaseModel):
    account_id: str = ""
    link_name: str = ""


class ServerAccountBody(BaseModel):
    name: str = ""
    platform_id: str = ""


class ServerAccountActiveBody(BaseModel):
    active: bool


class AccountLinkBody(BaseModel):
    name: str = ""


class AccountLinkActiveBody(BaseModel):
    active: bool


class ExtractorJobBody(BaseModel):
    account_link_id: str = ""
    source_platform_id: str = ""
    target_platform_ids: list[str] = []
    batch_size: int = 5
    interval_minutes: int = 30
    rest_seconds: int = 45


class LogPurgeBody(BaseModel):
    date_from: str = ""
    date_to: str = ""


def _require_user_json(
    request: Request, *, allow_publisher: bool = True
) -> JSONResponse | None:
    try:
        user = require_user(request)
    except PermissionError:
        return JSONResponse(
            {"ok": False, "error": "Sign in required."},
            status_code=401,
        )
    if not allow_publisher and db.user_is_publisher_mode(user):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    return None


def _require_server_admin_json(request: Request) -> JSONResponse | None:
    try:
        require_server_admin(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse(
                {"ok": False, "error": "Sign in as an administrator."},
                status_code=401,
            )
        return JSONResponse({"ok": False, "error": "Forbidden."}, status_code=403)
    return None


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


def _admin_privileges_redirect_login(request: Request | None = None):
    if request is not None:
        user = _session_user(request)
        if user:
            return RedirectResponse(url=_default_app_home(user), status_code=303)
    return RedirectResponse(url="/login?next=/admin/panel", status_code=303)


def _panel_redirect_login(request: Request | None = None):
    return _admin_privileges_redirect_login(request)


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
    if db.user_is_publisher_mode(user):
        return [str(user.id)]
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


def _comments_inbox_context(user: db.User, lang: str, platform_choices: list) -> dict:
    usage = db.membership_usage(user)
    can = db.user_can_manage_comments(user) and usage["can_view_comments"]
    if not can:
        return {
            "can_manage_comments": False,
            "comment_user_choices": [],
            "platform_labels": {},
            "show_comment_user_filter": False,
            "show_comment_platform_filter": False,
            "comment_platforms": [],
        }
    return {
        "can_manage_comments": True,
        "comment_user_choices": _publicaciones_comment_user_choices(
            db.publicaciones_tiktoker_choices(user)
        ),
        "platform_labels": {
            p["id"]: i18n.t(f"platform.{p['id']}", lang) for p in platform_choices
        },
        "show_comment_user_filter": db.user_can_access_servers(user),
        "show_comment_platform_filter": not db.user_is_publisher_mode(user)
        and len(platform_choices) > 1,
        "comment_platforms": platform_choices,
    }


def _default_app_home(user: db.User) -> str:
    if db.user_can_access_publicaciones(user):
        return "/admin/publicaciones"
    return "/admin"


def _require_publicaciones_user(request: Request) -> db.User:
    user = require_user(request)
    if not db.user_can_access_publicaciones(user):
        raise PermissionError("forbidden")
    return user


def _require_publicaciones_user_json(request: Request) -> JSONResponse | db.User:
    try:
        user = _require_publicaciones_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse(
                {"ok": False, "error": "Sign in required."},
                status_code=401,
            )
        return JSONResponse({"ok": False, "error": "Forbidden."}, status_code=403)
    if not db.user_can_upload_videos(user):
        return JSONResponse(
            {"ok": False, "error": "Upload not allowed."},
            status_code=403,
        )
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
    user = _session_user(request)
    if user and db.user_is_publisher_mode(user):
        code = "es"
    else:
        code = lang_code if lang_code in i18n.LANGUAGES else i18n.DEFAULT_LANG
    request.session["lang"] = code
    referer = request.headers.get("referer", "/")
    from urllib.parse import urlparse

    parsed = urlparse(referer)
    safe_next = parsed.path if parsed.path.startswith("/") else "/"
    if safe_next in ("/register", "/registro"):
        safe_next = i18n.register_path(code)
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


@app.get("/cancellation-policy", response_class=HTMLResponse, name="cancellation")
def page_cancellation(request: Request):
    return _render_legal(request, "legal_cancellation.html", "legal.cancellation_title")


@app.get("/support", response_class=HTMLResponse, name="support")
def page_support(request: Request):
    user = _session_user(request)
    if user and db.user_is_publisher_mode(user):
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    return _render_legal(request, "legal_support.html", "legal.support_title")


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


@app.get("/politica-de-cancelamiento")
def redirect_cancelacion():
    return RedirectResponse(url="/cancellation-policy", status_code=301)


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
    _establish_session(request, u)
    safe_next = next if next.startswith("/") else _default_app_home(u)
    if safe_next == "/":
        safe_next = _default_app_home(u)
    return RedirectResponse(url=safe_next, status_code=303)


@app.get("/login/olvidar", response_class=HTMLResponse, name="login_forgot")
@app.get("/login/forgot", response_class=HTMLResponse, name="login_forgot_en")
def login_forgot_get(request: Request):
    user = _session_user(request)
    if user:
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    return _render(
        request,
        "login_forgot.html",
        {"error": None, "success": None, "email": ""},
    )


@app.post("/login/olvidar", response_class=HTMLResponse, name="login_forgot_post")
@app.post("/login/forgot", response_class=HTMLResponse, name="login_forgot_post_en")
def login_forgot_post(
    request: Request,
    email: Annotated[str, Form()],
):
    lang = i18n.resolve_lang(request)
    addr = (email or "").strip()
    if not _valid_email(addr):
        return _render(
            request,
            "login_forgot.html",
            {
                "error": i18n.t("login.forgot.invalid_email", lang),
                "success": None,
                "email": addr,
            },
            status_code=400,
        )
    if notify.smtp_configured():
        user = db.get_user_by_notification_email(addr)
        if user and db.is_user_notification_email_verified(user.id):
            to = db.get_user_notification_email(user.id)
            if to:
                token = db.create_password_reset_token(user.id)
                reset_url = _password_reset_url(request, token)
                notify.send_password_reset_email(to=to, reset_url=reset_url, lang=lang)
    request.session["login_ok"] = i18n.t("login.forgot.sent_generic", lang)
    return RedirectResponse(url=request.url_for("login"), status_code=303)


@app.post("/logout", name="logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=request.url_for("home"), status_code=303)


# ---------------------------------------------------------------------------
# Registro público con código de invitación
# ---------------------------------------------------------------------------

_REGISTER_ERROR_KEYS = {
    "invite_required": "register.err.code_required",
    "invite_invalid": "register.err.code_invalid",
    "invite_used": "register.err.code_used",
    "Username must be at least 2 characters": "register.err.username_short",
    "Password must be at least 4 characters": "register.err.password_short",
    "Username already exists": "register.err.username_taken",
}


@app.get("/register", response_class=HTMLResponse, name="register")
@app.get("/registro", response_class=HTMLResponse, name="register_es")
def register_get(request: Request):
    if _session_user(request):
        return RedirectResponse(url="/admin/publicaciones", status_code=303)
    return _render(request, "register.html", {"error": None})


@app.post("/register", response_class=HTMLResponse, name="register_post")
@app.post("/registro", response_class=HTMLResponse, name="register_es_post")
def register_post(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password2: Annotated[str, Form()] = "",
    invite_code: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
):
    lang = i18n.resolve_lang(request)
    addr = (email or "").strip()

    def _err(key: str, status: int = 400):
        return _render(
            request,
            "register.html",
            {
                "error": i18n.t(key, lang),
                "username": username,
                "invite_code": invite_code,
                "email": addr,
            },
            status_code=status,
        )

    if not _valid_email(addr):
        return _err("register.err.invalid_email")
    if db.notification_email_is_taken(addr):
        return _err("register.err.email_taken")
    if password != password2:
        return _err("register.err.password_mismatch")
    try:
        user = db.redeem_invite_code(invite_code, username, password)
    except ValueError as e:
        return _err(_REGISTER_ERROR_KEYS.get(str(e), "register.err.generic"))
    if not _send_email_verification(request, user.id, addr):
        request.session["panel_error"] = _msg(request, "panel.flash.no_smtp")
    _establish_session(request, user)
    request.session["panel_ok"] = i18n.t("register.flash.verify_email", lang)
    return RedirectResponse(url="/admin/panel", status_code=303)


# ---------------------------------------------------------------------------
# Chat de soporte
# ---------------------------------------------------------------------------


def _user_is_support_agent(user: db.User) -> bool:
    """Quién atiende los chats: admin del sitio o modo admin (no Usuario TikTok)."""
    return db.user_has_admin_privileges(user) and not db.user_is_tiktok_mode(user)


class SupportMessageBody(BaseModel):
    body: str = ""


class ProxyBody(BaseModel):
    label: str = ""
    proxy: str = ""
    notes: str = ""
    links: list[str] = []


def _proxy_error_message(code: str, lang: str) -> str:
    key = f"proxys.err.{code}"
    msg = i18n.t(key, lang)
    if msg == key:
        return i18n.t("proxys.err.generic", lang)
    return msg


def _proxy_parsed_from_body(proxy_text: str) -> dict:
    parsed = proxy_util.parse_proxy_line(proxy_text)
    parsed["proxy_url"] = proxy_util.build_proxy_url(parsed)
    return parsed


def _proxy_api_item(row: dict) -> dict:
    out = dict(row)
    out.pop("password", None)
    out["display"] = proxy_util.proxy_display(row, mask_password=True)
    return out


def _publisher_media_error(user, path: Path, content_type: str, lang: str) -> str | None:
    """Publicador: solo video de 60 s o más. Admin y modo TikTok no tienen este tope."""
    if not db.user_is_publisher_mode(user):
        return None
    if content_type == "photo" or path.suffix.lower() in ALLOWED_PHOTO_EXT:
        return i18n.t("pub.flash.publisher_no_photos", lang)
    meta = video_probe.probe_video(path)
    duration = meta.get("duration_seconds")
    if duration is None:
        return i18n.t("pub.flash.publisher_duration_unknown", lang)
    try:
        seconds = float(duration)
    except (TypeError, ValueError):
        return i18n.t("pub.flash.publisher_duration_unknown", lang)
    if seconds + 0.05 < PUBLISHER_MIN_VIDEO_SECONDS:
        return i18n.t("pub.flash.publisher_min_duration", lang, seconds=PUBLISHER_MIN_VIDEO_SECONDS)
    return None


def _video_suffix_from_upload(filename: str, content_type: str | None) -> str | None:
    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_VIDEO_EXT:
        return suffix
    mime = (content_type or "").split(";")[0].strip().lower()
    return VIDEO_MIME_EXT.get(mime)


@app.get("/admin/api/proxys/link-choices")
def api_proxys_link_choices(request: Request, q: str = ""):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    return {"ok": True, "choices": db.list_proxy_link_choices(q, lang=lang)}


@app.get("/admin/api/proxys")
def api_proxys_list(request: Request, q: str = ""):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    rows = db.list_proxies(q)
    return {"ok": True, "proxies": rows}


@app.get("/admin/api/proxys/{proxy_id}")
def api_proxys_get(request: Request, proxy_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    row = db.get_proxy(proxy_id)
    if not row:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    out = dict(row)
    out["proxy_line"] = proxy_util.proxy_display(row, mask_password=False)
    return {"ok": True, "proxy": out}


@app.post("/admin/api/proxys")
def api_proxys_create(request: Request, body: ProxyBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        parsed = _proxy_parsed_from_body(body.proxy)
    except ValueError as e:
        code = str(e) or "invalid_format"
        return {"ok": False, "error": _proxy_error_message(code, lang)}
    row = db.create_proxy(
        label=body.label,
        protocol=str(parsed["protocol"]),
        host=str(parsed["host"]),
        port=int(parsed["port"]),
        username=str(parsed.get("username") or ""),
        password=str(parsed.get("password") or ""),
        proxy_url=str(parsed["proxy_url"]),
        notes=body.notes,
    )
    db.set_proxy_links(row["id"], body.links)
    row = db.get_proxy(row["id"]) or row
    return {"ok": True, "proxy": _proxy_api_item(row)}


@app.put("/admin/api/proxys/{proxy_id}")
def api_proxys_update(request: Request, proxy_id: str, body: ProxyBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    existing = db.get_proxy(proxy_id)
    if not existing:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    try:
        parsed = _proxy_parsed_from_body(body.proxy)
    except ValueError as e:
        code = str(e) or "invalid_format"
        return {"ok": False, "error": _proxy_error_message(code, lang)}
    row = db.update_proxy(
        proxy_id,
        label=body.label,
        protocol=str(parsed["protocol"]),
        host=str(parsed["host"]),
        port=int(parsed["port"]),
        username=str(parsed.get("username") or ""),
        password=str(parsed.get("password") or ""),
        proxy_url=str(parsed["proxy_url"]),
        notes=existing.get("notes") or "",
        country_code=existing.get("country_code") or "",
        country_name=existing.get("country_name") or "",
    )
    db.set_proxy_links(proxy_id, body.links)
    row = db.get_proxy(proxy_id) or row
    return {"ok": True, "proxy": _proxy_api_item(row)}


@app.delete("/admin/api/proxys/{proxy_id}")
def api_proxys_delete(request: Request, proxy_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    db.delete_proxy(proxy_id)
    return {"ok": True}


@app.post("/admin/api/proxys/{proxy_id}/active")
def api_proxys_active(request: Request, proxy_id: str, body: EquipoEstadoBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    db.set_proxy_active(proxy_id, bool(body.active))
    return {"ok": True}


@app.post("/admin/api/proxys/{proxy_id}/test")
async def api_proxys_test(request: Request, proxy_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    row = db.get_proxy(proxy_id)
    if not row:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    result = await asyncio.to_thread(proxy_util.test_proxy, row)
    if result.get("ok"):
        message = i18n.t(
            "proxys.test_ok",
            lang,
            country=result.get("country_name") or result.get("country_code") or "—",
            ip=result.get("ip") or "—",
        )
    elif result.get("error"):
        message = _proxy_error_message(str(result.get("error")), lang)
    updated = db.save_proxy_check_result(
        proxy_id,
        ok=bool(result.get("ok")),
        ip=str(result.get("ip") or ""),
        country_code=str(result.get("country_code") or ""),
        country_name=str(result.get("country_name") or ""),
        message=message,
    )
    return {
        "ok": bool(result.get("ok")),
        "message": message,
        "proxy": _proxy_api_item(updated) if updated else None,
    }


def _membership_error(code: str, lang: str) -> str:
    key = f"membresias.err.{code}"
    msg = i18n.t(key, lang)
    if msg == key:
        return i18n.t("membresias.err.generic", lang)
    return msg


def _plan_api_item(plan: dict, lang: str) -> dict:
    pid = plan["id"]
    return {
        "id": pid,
        "name": i18n.t(f"membresias.plan.{pid}.name", lang),
        "tagline": i18n.t(f"membresias.plan.{pid}.tagline", lang),
        "price_usd": int(plan["price_usd"]),
        "videos": int(plan["videos"]),
        "stats": int(plan["stats"]),
        "invite_only": bool(plan["invite_only"]),
        "featured": bool(plan["featured"]),
        "accent": plan["accent"],
        "sort": int(plan["sort"]),
    }


def _payment_kind_api(kind: dict, lang: str) -> dict:
    return {
        "id": kind["id"],
        "icon": kind["icon"],
        "name": i18n.t(kind["label_key"], lang),
    }


class PaymentMethodBody(BaseModel):
    kind: str = "custom"
    name: str = ""
    pay_to: str = ""
    instructions: str = ""
    notes: str = ""
    active: bool = True


class PurchaseBody(BaseModel):
    plan_id: str = ""
    payment_method_id: str = ""
    note: str = ""
    use_wallet: bool = True
    amount_usd: int = 0


class PurchaseStatusBody(BaseModel):
    status: str = ""


class WalletCreditBody(BaseModel):
    user_id: str = ""
    amount_usd: int = 0
    note: str = ""


class WalletRechargeBody(BaseModel):
    amount_usd: int = 0
    payment_method_id: str = ""
    note: str = ""
    use_wallet: bool = True


@app.get("/admin/api/membresias/planes")
def api_membresias_planes(request: Request):
    deny = _require_user_json(request, allow_publisher=False)
    if deny:
        return deny
    user = require_user(request)
    lang = i18n.resolve_lang(request)
    current = (user.membership_plan or "").strip().lower()
    started = db.membership_started_at_for(user)
    wallet = int(getattr(user, "wallet_balance_usd", 0) or 0)
    quotes = {}
    for p in membership.PLANS:
        if p.get("invite_only"):
            continue
        try:
            quotes[p["id"]] = membership.quote_plan_change(
                current_plan=current,
                started_at=started,
                wallet_usd=wallet,
                new_plan_id=p["id"],
                use_wallet=True,
            )
        except ValueError:
            continue
    return {
        "ok": True,
        "current_plan": current,
        "wallet_balance_usd": wallet,
        "unused_credit_usd": membership.unused_plan_credit_usd(current, started),
        "invited": db.user_was_invited(user.id),
        "plans": [_plan_api_item(p, lang) for p in membership.PLANS],
        "quotes": quotes,
    }


@app.get("/admin/api/pagos/medios")
def api_pagos_medios(request: Request):
    deny = _require_user_json(request, allow_publisher=False)
    if deny:
        return deny
    user = require_user(request)
    lang = i18n.resolve_lang(request)
    admin = db.user_can_access_servers(user)
    rows = db.list_payment_methods(active_only=not admin)
    if not admin:
        for row in rows:
            row.pop("notes", None)
    kinds = [_payment_kind_api(k, lang) for k in membership.PAYMENT_KINDS]
    wallet_usd = int(getattr(user, "wallet_balance_usd", 0) or 0)
    rows = [
        {
            "id": membership.WALLET_METHOD_ID,
            "kind": "wallet",
            "name": i18n.t("pagos.kind.wallet", lang),
            "pay_to": "",
            "instructions": i18n.t("pagos.wallet_hint", lang),
            "active": True,
            "sort_order": -1,
        }
    ] + rows
    return {
        "ok": True,
        "methods": rows,
        "kinds": kinds,
        "admin": admin,
        "wallet_balance_usd": wallet_usd,
    }


@app.post("/admin/api/pagos/medios")
def api_pagos_medios_create(request: Request, body: PaymentMethodBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        row = db.create_payment_method(
            kind=body.kind,
            name=body.name,
            pay_to=body.pay_to,
            instructions=body.instructions,
            notes=body.notes,
            active=bool(body.active),
        )
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _membership_error(str(e) or "generic", lang)},
            status_code=400,
        )
    return {"ok": True, "method": row}


@app.put("/admin/api/pagos/medios/{method_id}")
def api_pagos_medios_update(request: Request, method_id: str, body: PaymentMethodBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        row = db.update_payment_method(
            method_id,
            kind=body.kind,
            name=body.name,
            pay_to=body.pay_to,
            instructions=body.instructions,
            notes=body.notes,
            active=bool(body.active),
        )
    except ValueError as e:
        code = str(e) or "generic"
        status = 404 if code == "not_found" else 400
        return JSONResponse(
            {"ok": False, "error": _membership_error(code, lang)},
            status_code=status,
        )
    return {"ok": True, "method": row}


@app.delete("/admin/api/pagos/medios/{method_id}")
def api_pagos_medios_delete(request: Request, method_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    db.delete_payment_method(method_id)
    return {"ok": True}


@app.post("/admin/api/pagos/medios/{method_id}/active")
def api_pagos_medios_active(request: Request, method_id: str, body: EquipoEstadoBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    db.set_payment_method_active(method_id, bool(body.active))
    return {"ok": True}


@app.get("/admin/api/pagos/compras")
def api_pagos_compras(request: Request, status: str = ""):
    deny = _require_user_json(request, allow_publisher=False)
    if deny:
        return deny
    user = require_user(request)
    admin = db.user_can_access_servers(user)
    rows = db.list_purchases(
        user_id=None if admin else user.id,
        status=status,
    )
    return {
        "ok": True,
        "purchases": rows,
        "admin": admin,
        "wallet_balance_usd": int(getattr(user, "wallet_balance_usd", 0) or 0),
        "ledger": db.list_wallet_ledger(user.id),
    }


@app.post("/admin/api/pagos/compras")
def api_pagos_compras_create(request: Request, body: PurchaseBody):
    deny = _require_user_json(request, allow_publisher=False)
    if deny:
        return deny
    user = require_user(request)
    lang = i18n.resolve_lang(request)
    try:
        row = db.create_purchase(
            user_id=user.id,
            plan_id=body.plan_id,
            payment_method_id=body.payment_method_id,
            note=body.note,
            use_wallet=bool(body.use_wallet),
        )
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _membership_error(str(e) or "generic", lang)},
            status_code=400,
        )
    return {"ok": True, "purchase": row}


@app.post("/admin/api/pagos/compras/{purchase_id}/status")
def api_pagos_compras_status(request: Request, purchase_id: str, body: PurchaseStatusBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    user = require_server_admin(request)
    lang = i18n.resolve_lang(request)
    try:
        row = db.update_purchase_status(
            purchase_id,
            status=body.status,
            reviewed_by=user.username,
        )
    except ValueError as e:
        code = str(e) or "generic"
        status_code = 404 if code == "not_found" else 400
        return JSONResponse(
            {"ok": False, "error": _membership_error(code, lang)},
            status_code=status_code,
        )
    return {"ok": True, "purchase": row}


@app.post("/admin/api/membresias/cancel")
def api_membresias_cancel(request: Request):
    deny = _require_user_json(request, allow_publisher=False)
    if deny:
        return deny
    user = require_user(request)
    lang = i18n.resolve_lang(request)
    try:
        result = db.cancel_membership_to_wallet(user.id)
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _membership_error(str(e) or "generic", lang)},
            status_code=400,
        )
    return {"ok": True, **result}


@app.post("/admin/api/pagos/recarga")
def api_pagos_recarga(request: Request, body: WalletRechargeBody):
    deny = _require_user_json(request, allow_publisher=False)
    if deny:
        return deny
    user = require_user(request)
    lang = i18n.resolve_lang(request)
    try:
        row = db.create_wallet_recharge(
            user_id=user.id,
            amount_usd=int(body.amount_usd or 0),
            payment_method_id=body.payment_method_id,
            note=body.note,
            use_wallet=bool(body.use_wallet),
        )
    except ValueError as e:
        return JSONResponse(
            {"ok": False, "error": _membership_error(str(e) or "generic", lang)},
            status_code=400,
        )
    return {"ok": True, "purchase": row}


@app.post("/admin/api/pagos/saldo")
def api_pagos_saldo_manual(request: Request, body: WalletCreditBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    admin = require_server_admin(request)
    lang = i18n.resolve_lang(request)
    amount = int(body.amount_usd or 0)
    if amount == 0 or amount > 10000 or amount < -10000:
        return JSONResponse(
            {"ok": False, "error": _membership_error("invalid_amount", lang)},
            status_code=400,
        )
    target = db.get_user_by_id((body.user_id or "").strip())
    if not target or not db.user_is_tiktok_mode(target):
        return JSONResponse(
            {"ok": False, "error": _membership_error("credit_tiktok_only", lang)},
            status_code=403,
        )
    try:
        bal = db.add_wallet_balance(
            body.user_id,
            amount,
            reason="admin_credit",
            note=body.note,
            created_by=admin.username,
        )
    except ValueError as e:
        code = str(e) or "generic"
        status_code = 404 if code == "not_found" else 400
        return JSONResponse(
            {"ok": False, "error": _membership_error(code, lang)},
            status_code=status_code,
        )
    return {"ok": True, "wallet_balance_usd": bal}


@app.get("/admin/soporte", response_class=HTMLResponse, name="admin_soporte")
def admin_soporte_page(request: Request):
    try:
        user = require_user(request)
    except PermissionError:
        return RedirectResponse(url="/login?next=/admin/soporte", status_code=303)
    if db.user_is_publisher_mode(user):
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    if _user_is_support_agent(user):
        return RedirectResponse(url="/admin/chats-soporte", status_code=303)
    return _render(request, "soporte.html", {"user": user, "nav_active": "soporte"})


@app.get("/admin/api/soporte/unread")
def api_soporte_unread(request: Request):
    try:
        user = require_user(request)
    except PermissionError:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    if db.user_is_publisher_mode(user):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    return {"ok": True, "count": db.support_unread_count_for_viewer(user)}


@app.get("/admin/api/soporte/mensajes")
def api_soporte_mensajes(request: Request):
    try:
        user = require_user(request)
    except PermissionError:
        return JSONResponse({"ok": False, "error": "login_required"}, status_code=401)
    if db.user_is_publisher_mode(user):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    db.mark_support_read(user.id, "user")
    return {"ok": True, "messages": db.list_support_messages(user.id)}


@app.post("/admin/api/soporte/mensajes")
def api_soporte_enviar(request: Request, body: SupportMessageBody):
    try:
        user = require_user(request)
    except PermissionError:
        return JSONResponse({"ok": False, "error": "login_required"}, status_code=401)
    if db.user_is_publisher_mode(user):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    try:
        msg = db.add_support_message(user.id, "user", body.body)
    except ValueError:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    return {"ok": True, "message": msg}


@app.get("/admin/chats-soporte", response_class=HTMLResponse, name="admin_chats_soporte")
def admin_chats_soporte_page(request: Request):
    try:
        user = require_user(request)
    except PermissionError:
        return RedirectResponse(url="/login?next=/admin/chats-soporte", status_code=303)
    if db.user_is_publisher_mode(user):
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    if not _user_is_support_agent(user):
        return RedirectResponse(url="/admin/soporte", status_code=303)
    return _render(
        request,
        "chats_soporte.html",
        {"user": user, "nav_active": "chats_soporte"},
    )


def _require_support_agent_json(request: Request) -> JSONResponse | None:
    try:
        user = require_user(request)
    except PermissionError:
        return JSONResponse({"ok": False, "error": "login_required"}, status_code=401)
    if not _user_is_support_agent(user):
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    return None


@app.get("/admin/api/soporte/hilos")
def api_soporte_hilos(request: Request, q: str = ""):
    deny = _require_support_agent_json(request)
    if deny:
        return deny
    return {"ok": True, "threads": db.list_all_support_threads(q)}


@app.get("/admin/api/soporte/hilos/{user_id}/mensajes")
def api_soporte_hilo_mensajes(request: Request, user_id: str):
    deny = _require_support_agent_json(request)
    if deny:
        return deny
    guest_id = db.parse_guest_thread_id(user_id)
    if guest_id:
        db.mark_guest_support_read(guest_id, "admin")
        lang = i18n.resolve_lang(request)
        return {
            "ok": True,
            "username": i18n.t("support.anonymous_label", lang),
            "is_guest": True,
            "messages": db.list_guest_support_messages(guest_id),
        }
    target = db.get_user_by_id(user_id)
    if not target:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    db.mark_support_read(user_id, "admin")
    return {
        "ok": True,
        "username": target.username,
        "is_guest": False,
        "messages": db.list_support_messages(user_id),
    }


@app.post("/admin/api/soporte/hilos/{user_id}/mensajes")
def api_soporte_hilo_responder(request: Request, user_id: str, body: SupportMessageBody):
    deny = _require_support_agent_json(request)
    if deny:
        return deny
    guest_id = db.parse_guest_thread_id(user_id)
    if guest_id:
        try:
            msg = db.add_guest_support_message(guest_id, "admin", body.body)
        except ValueError:
            return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
        return {"ok": True, "message": msg}
    target = db.get_user_by_id(user_id)
    if not target:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    try:
        msg = db.add_support_message(user_id, "admin", body.body)
    except ValueError:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    return {"ok": True, "message": msg}


@app.get("/admin/api/soporte/logs/count")
def api_soporte_logs_count(request: Request, date_from: str = "", date_to: str = ""):
    deny = _require_support_agent_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(date_from, date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    return {"ok": True, "count": db.count_support_messages_in_range(start, end)}


@app.delete("/admin/api/soporte/logs")
def api_soporte_logs_purge(request: Request, body: LogPurgeBody):
    deny = _require_support_agent_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(body.date_from, body.date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    deleted = db.delete_support_messages_in_range(start, end)
    return {"ok": True, "deleted": deleted}


def _guest_chat_id(request: Request) -> str:
    gid = (request.session.get("guest_chat_id") or "").strip()
    if not gid:
        gid = str(uuid.uuid4())
        request.session["guest_chat_id"] = gid
    return gid


@app.get("/api/soporte-publico/mensajes")
def api_soporte_publico_mensajes(request: Request):
    gid = _guest_chat_id(request)
    db.mark_guest_support_read(gid, "user")
    return {"ok": True, "messages": db.list_guest_support_messages(gid)}


@app.post("/api/soporte-publico/mensajes")
def api_soporte_publico_enviar(request: Request, body: SupportMessageBody):
    gid = _guest_chat_id(request)
    try:
        msg = db.add_guest_support_message(gid, "user", body.body)
    except ValueError:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    return {"ok": True, "message": msg}


# ---------------------------------------------------------------------------
# Códigos de invitación (panel)
# ---------------------------------------------------------------------------


@app.get("/admin/api/invitaciones")
def api_invitaciones_list(request: Request):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    return {"ok": True, "codes": db.list_invite_codes()}


@app.post("/admin/api/invitaciones")
def api_invitaciones_create(request: Request):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    user = require_server_admin(request)
    code = db.create_invite_code(user.id)
    return {"ok": True, "code": code}


@app.get("/admin/api/invitaciones/logs/count")
def api_invitaciones_logs_count(request: Request, date_from: str = "", date_to: str = ""):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(date_from, date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    return {"ok": True, "count": db.count_invite_codes_in_range(start, end)}


@app.delete("/admin/api/invitaciones/logs")
def api_invitaciones_logs_purge(request: Request, body: LogPurgeBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(body.date_from, body.date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    deleted = db.delete_invite_codes_in_range(start, end)
    return {"ok": True, "deleted": deleted}


@app.delete("/admin/api/invitaciones/{code}")
def api_invitaciones_delete(request: Request, code: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    db.delete_invite_code(code)
    return {"ok": True}


def _password_reset_url(request: Request, token: str) -> str:
    """Enlace absoluto al formulario de restablecimiento."""
    return f"{request.url_for('admin_panel_reset_get')}?{urlencode({'token': token})}"


def _viewer_visible_platform_ids(user: db.User) -> set[str] | None:
    """Plataformas visibles en historial/programaciones. None = admin, sin filtro."""
    if db.user_can_access_servers(user):
        return None
    if db.user_is_tiktok_mode(user):
        return _tiktok_user_ready_platform_ids(user)
    return {"tiktok"}


def _filter_log_groups_for_viewer(groups: list[dict], user: db.User) -> list[dict]:
    allowed = _viewer_visible_platform_ids(user)
    if allowed is None:
        return groups
    out: list[dict] = []
    for group in groups:
        entries = [
            e
            for e in (group.get("entries") or [])
            if str(e.get("platform_id") or "") in allowed
        ]
        if not entries:
            continue
        ok_n = sum(1 for e in entries if e.get("status") == "ok")
        fail_n = sum(1 for e in entries if e.get("status") == "fail")
        skipped_n = sum(1 for e in entries if e.get("status") == "skipped")
        pending_n = sum(1 for e in entries if e.get("status") == "pending")
        if fail_n and (ok_n or pending_n):
            status = "mixed"
        elif fail_n:
            status = "fail"
        elif pending_n:
            status = "pending"
        elif ok_n:
            status = "ok"
        else:
            status = "skipped"
        item = dict(group)
        item["entries"] = entries
        item["ok_n"] = ok_n
        item["fail_n"] = fail_n
        item["skipped_n"] = skipped_n
        item["pending_n"] = pending_n
        item["status"] = status
        out.append(item)
    return out


def _filter_scheduled_for_viewer(rows: list[dict], user: db.User) -> list[dict]:
    allowed = _viewer_visible_platform_ids(user)
    if allowed is None:
        return rows

    out: list[dict] = []
    for row in rows:
        try:
            pids = json.loads(row.get("platforms_json") or "[]")
        except (TypeError, ValueError):
            pids = []
        if not isinstance(pids, list):
            pids = []
        kept = [p for p in pids if str(p) in allowed]
        if not kept:
            continue
        item = dict(row)
        item["platforms_json"] = json.dumps(kept)
        out.append(item)
    return out


def _publication_log_groups(lang: str, user: db.User, *, limit: int = 200) -> list[dict]:
    groups = db.list_publication_log_groups(limit=limit, viewer=user)
    for group in groups:
        for entry in group.get("entries") or []:
            pid = str(entry.get("platform_id") or "")
            entry["platform_name"] = i18n.t(f"platform.{pid}", lang) if pid else pid
    return _filter_log_groups_for_viewer(groups, user)


def _email_verify_url(request: Request, token: str) -> str:
    return f"{request.url_for('verify_email')}?{urlencode({'token': token})}"


def _send_email_verification(request: Request, user_id: str, email: str) -> bool:
    lang = i18n.resolve_lang(request)
    addr = (email or "").strip()
    try:
        token = db.queue_notification_email_verification(user_id, addr)
    except ValueError:
        return False
    if not token:
        return True
    if not notify.smtp_configured():
        return False
    verify_url = _email_verify_url(request, token)
    return notify.send_email_verification_email(
        to=addr, verify_url=verify_url, lang=lang
    )


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


def _build_empty_platform_breakdown(
    lang: str,
    *,
    platform_ids: list[str] | None = None,
) -> list[dict]:
    breakdown: list[dict] = []
    allowed = set(platform_ids or [])
    for p in platforms.PLATFORMS:
        pid = str(p["id"])
        if allowed and pid not in allowed:
            continue
        breakdown.append(
            {
                "platform_id": pid,
                "icon": str(p["icon"]),
                "name": i18n.t(f"platform.{pid}", lang),
                "stats": _stats_empty(),
                "visible_stats": platforms.visible_stats_metrics(pid),
                "publications": [],
            }
        )
    return breakdown


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
    is_tiktok_user = db.user_is_tiktok_mode(u)
    is_publisher = db.user_is_publisher_mode(u)
    can_access_servers = db.user_can_access_servers(u)
    lang = i18n.resolve_lang(request)
    all_filter_choices = db.list_stats_filter_choices(u, lang=lang)
    stats_consulted = (request.query_params.get("consult") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    spend_stats = (request.query_params.get("spend") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    usage = db.membership_usage(u)
    user_platform_ids = sorted(
        {pid for acc in all_filter_choices for pid in (acc.get("platform_ids") or [])}
    )

    platform_choices = platforms.platform_list(lang)
    if is_tiktok_user:
        platform_choices = [
            p for p in _tiktok_user_panel_platforms(lang, u) if p.get("configured")
        ]
    elif not can_access_servers:
        platform_choices = [p for p in platform_choices if p["id"] == "tiktok"]
    if is_publisher:
        all_filter_choices = [
            {
                **acc,
                "platform_ids": [
                    pid
                    for pid in (acc.get("platform_ids") or [])
                    if str(pid) == "tiktok"
                ],
            }
            for acc in all_filter_choices
            if "tiktok" in [str(p) for p in (acc.get("platform_ids") or [])]
        ]
    if is_tiktok_user:
        show_stats_filters = bool(platform_choices)
    else:
        show_stats_filters = can_access_servers or bool(all_filter_choices)
    allowed_platform_ids = {p["id"] for p in platform_choices}
    show_stats_all_option = len(platform_choices) > 1 and not is_publisher
    show_stats_platform_filter = not is_publisher and bool(platform_choices)

    platform_sel = (request.query_params.get("platform") or "").strip()
    if platform_sel not in platforms.PLATFORM_IDS and platform_sel != "all":
        platform_sel = ""
    if platform_sel == "all" and not show_stats_all_option:
        platform_sel = ""
    if platform_sel and platform_sel != "all" and platform_sel not in allowed_platform_ids:
        platform_sel = ""
    if not platform_sel:
        if is_publisher:
            platform_sel = "tiktok" if "tiktok" in allowed_platform_ids else (platform_choices[0]["id"] if platform_choices else "tiktok")
        elif show_stats_all_option:
            platform_sel = "all"
        elif platform_choices:
            platform_sel = platform_choices[0]["id"]
        else:
            platform_sel = "all"
    if is_publisher:
        platform_sel = "tiktok"

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
    show_account_filter = bool(account_choices) and not is_tiktok_user
    if is_publisher:
        show_account_filter = len(account_choices) > 1

    if is_tiktok_user and account_choices:
        seen_links: list[str] = []
        seen_set: set[str] = set()
        union_pids: list[str] = []
        pid_set: set[str] = set()
        for acc in account_choices:
            for lid in acc.get("link_ids") or [acc.get("id")]:
                lid_s = str(lid or "").strip()
                if not lid_s or lid_s in seen_set:
                    continue
                seen_set.add(lid_s)
                seen_links.append(lid_s)
            for pid in acc.get("platform_ids") or []:
                pid_s = str(pid or "").strip()
                if pid_s and pid_s not in pid_set:
                    pid_set.add(pid_s)
                    union_pids.append(pid_s)
        selected_account = {
            "id": seen_links[0] if len(seen_links) == 1 else "tiktok-user-all",
            "name": account_choices[0].get("name") or "",
            "kind": "link",
            "platform_ids": [p["id"] for p in platform_choices],
            "link_ids": seen_links,
        }
        sel = selected_account["id"]
    else:
        if sel not in choice_ids:
            sel = ""
        if not sel and account_choices:
            sel = account_choices[0]["id"]
        elif not sel and not is_admin and len(account_choices) == 1:
            sel = account_choices[0]["id"]
        selected_account = next((c for c in account_choices if c["id"] == sel), None)
    selected_account_name = (selected_account or {}).get("name") or ""
    link_kwargs = _stats_link_kwargs(selected_account)

    consult_token = f"{platform_sel}|{sel}|{video_sel}"
    session_token = str(request.session.get("stats_consult_token") or "")
    quota_error = ""
    if stats_consulted and spend_stats:
        quota_code = db.consume_stats_query(u)
        if quota_code:
            stats_consulted = False
            quota_error = i18n.t(quota_code, lang)
            request.session.pop("stats_consult_token", None)
        else:
            request.session["stats_consult_token"] = consult_token
            usage = db.membership_usage(u)
    elif stats_consulted:
        if usage["unlimited"] or session_token == consult_token:
            pass
        else:
            stats_consulted = False

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
        if stats_consulted:
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
        elif platform_sel == "all":
            show_global_breakdown = True
            global_summary = _stats_empty()
            platform_breakdown = _build_empty_platform_breakdown(
                lang, platform_ids=acc_platforms
            )
    else:
        stats = _stats_empty()
        sel = ""
        if is_tiktok_user and platform_sel == "all":
            show_global_breakdown = True
            global_summary = _stats_empty()
            platform_breakdown = _build_empty_platform_breakdown(
                lang, platform_ids=[p["id"] for p in platform_choices]
            )

    err = request.session.pop("admin_error", None) or quota_error
    ok = request.session.pop("admin_ok", None)
    ctx = {
        "user": u,
        "stats": stats,
        "error": err,
        "success": ok,
        "membership_usage": usage,
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
        "show_stats_platform_filter": show_stats_platform_filter,
        "show_stats_filters": show_stats_filters,
        "show_stats_all_option": show_stats_all_option,
        "stats_consulted": stats_consulted,
        "account_filter_label": account_filter_label,
        "selected_account_name": selected_account_name,
    }
    ctx.update(_comments_inbox_context(u, lang, platform_choices))
    return _render(request, "admin.html", ctx)


@app.get("/admin/api/stats-filter-choices")
def api_stats_filter_choices(request: Request, platform: str = "all"):
    try:
        u = require_user(request)
    except PermissionError:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)

    lang = i18n.resolve_lang(request)
    if db.user_is_publisher_mode(u):
        platform_sel = "tiktok"
    else:
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
        u = require_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    if not db.user_can_manage_comments(u):
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    if not db.membership_usage(u)["can_view_comments"]:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    scope = _publicaciones_comment_scope(u)
    threads = db.list_comment_threads_for_owners(scope)
    if db.user_is_publisher_mode(u):
        platform = "tiktok"
        user = str(u.id)
    filtered = _filter_comment_threads(
        threads,
        platform=(platform or "__all__").strip(),
        owner_user_id=(user or "__all__").strip(),
    )
    if db.user_is_publisher_mode(u):
        own_videos = db.video_ids_published_by(u.id, platform_id="tiktok")
        filtered = [t for t in filtered if str(t.get("video_id") or "") in own_videos]
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
    guard = _require_server_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    bounds = _log_purge_bounds(date_from, date_to, lang)
    if isinstance(bounds, JSONResponse):
        return bounds
    start, end = bounds
    return {"ok": True, "count": db.count_publication_logs_in_range(start, end)}


@app.get("/admin/api/publicaciones/logs")
def api_publication_logs(request: Request):
    auth = _require_publicaciones_user_json(request)
    if isinstance(auth, JSONResponse):
        return auth
    u = auth
    lang = i18n.resolve_lang(request)
    return {"ok": True, "logs": _publication_log_groups(lang, u)}


@app.delete("/admin/api/publicaciones/logs")
def api_publication_logs_purge(request: Request, body: LogPurgeBody):
    guard = _require_server_admin_json(request)
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
    guard = _require_server_admin_json(request)
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
    guard = _require_server_admin_json(request)
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
    usage = db.membership_usage(u)
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

    err = request.session.pop("admin_error", None)
    ok = request.session.pop("admin_ok", None)
    is_admin = db.user_has_admin_privileges(u)
    is_publish_admin = db.user_can_access_servers(u)
    is_tiktok_user = db.user_is_tiktok_mode(u)
    is_publisher = db.user_is_publisher_mode(u)
    publish_account_choices = db.list_stats_filter_choices(u, lang=lang)
    show_publish_account_picker = (
        not is_tiktok_user
        and (is_publish_admin or len(publish_account_choices) > 1)
    )
    if is_publisher:
        show_publish_account_picker = len(publish_account_choices) > 1
    publish_unlocked = (
        is_admin or is_tiktok_user or len(publish_account_choices) > 0
    )
    if is_tiktok_user:
        platform_choices = _tiktok_user_panel_platforms(lang, u)
        show_publish_platform_picker = True
        auto_publish_platform_id = ""
    elif not is_publish_admin:
        platform_choices = [p for p in platform_choices if p["id"] == "tiktok"]
        show_publish_platform_picker = False
        auto_publish_platform_id = "tiktok" if platform_choices else ""
    else:
        show_publish_platform_picker = False
        auto_publish_platform_id = ""
    pub_account_i18n = {
        "select": i18n.t("pub.select_account", lang),
        "search_ph": i18n.t("pub.publish_account_search_ph", lang),
        "empty": i18n.t(
            "pub.no_tiktok_linked" if is_publisher else "pub.publish_account_empty",
            lang,
        ),
        "select_required": i18n.t("pub.flash.select_account_publish", lang),
    }
    return _render(
        request,
        "admin_publicaciones.html",
        {
            "user": u,
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
            "membership_usage": usage,
            "publish_platforms": platform_choices,
            "publication_logs": _publication_log_groups(lang, u),
            "scheduled_publications": _filter_scheduled_for_viewer(
                db.list_scheduled_publications(limit=30, viewer=u), u
            ),
            "pending_retry_publications": (
                db.list_awaiting_retry_publications(limit=50, viewer=u)
                if is_publish_admin
                else []
            ),
            "can_manage_publish_retry": is_publish_admin,
            "show_pub_log_user": is_publish_admin,
            "show_pub_log_platform": not db.user_is_publisher_mode(u),
            "show_pub_log_message": not db.user_is_publisher_mode(u),
            "account_filter_label": account_filter_label,
            "publish_account_choices": publish_account_choices,
            "show_publish_account_picker": show_publish_account_picker,
            "show_publish_platform_picker": show_publish_platform_picker,
            "auto_publish_platform_id": auto_publish_platform_id,
            "is_publish_admin": is_publish_admin,
            "publish_unlocked": publish_unlocked,
            "pub_account_i18n": pub_account_i18n,
            "max_upload_mb": MAX_UPLOAD_MB,
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "schedule_datetime_default": publish_schedule.min_datetime_local_input(),
        },
    )


@app.post("/admin/api/videos/temp", name="api_video_temp_upload")
async def api_video_temp_upload(request: Request, file: UploadFile = File(...)):
    auth = _require_publicaciones_user_json(request)
    if isinstance(auth, JSONResponse):
        return auth
    u = auth
    lang = i18n.resolve_lang(request)

    if not file.filename and not file.content_type:
        return JSONResponse({"ok": False, "error": "Missing file."}, status_code=400)

    raw_name = file.filename or ""
    suffix = _video_suffix_from_upload(raw_name, file.content_type)
    if not suffix:
        return JSONResponse({"ok": False, "error": "Invalid video type.", "code": "invalid_type"}, status_code=400)

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            {
                "ok": False,
                "code": "file_too_large",
                "error": i18n.t("pub.flash.file_too_large", lang, max_mb=MAX_UPLOAD_MB),
            },
            status_code=400,
        )

    token, stored = video_temp_util.save_temp(UPLOAD_DIR, u.id, contents, suffix)
    temp_file = UPLOAD_DIR / "temp" / stored
    restrict = _publisher_media_error(u, temp_file, "video", lang)
    if restrict:
        video_temp_util.discard_temp(UPLOAD_DIR, u.id, token)
        return JSONResponse({"ok": False, "error": restrict, "code": "publisher_media"}, status_code=400)
    return {
        "ok": True,
        "token": token,
        "url": f"/uploads/temp/{stored}",
        "name": raw_name,
    }


@app.post("/admin/api/videos/temp/{token}/discard", name="api_video_temp_discard")
def api_video_temp_discard(request: Request, token: str):
    auth = _require_publicaciones_user_json(request)
    if isinstance(auth, JSONResponse):
        return auth
    u = auth
    video_temp_util.discard_temp(UPLOAD_DIR, u.id, token)
    return {"ok": True}


def _publicaciones_result(
    request: Request, *, ok: bool, message: str, status: int = 400
):
    if "application/json" in (request.headers.get("accept") or "").lower():
        return JSONResponse(
            {"ok": ok, "message": message},
            status_code=200 if ok else status,
        )
    if ok:
        request.session["admin_ok"] = message
    else:
        request.session["admin_error"] = message
    return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)


@app.post("/admin/videos", name="admin_upload_video")
async def admin_upload_video(request: Request):
    try:
        u = _require_publicaciones_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            if "application/json" in (request.headers.get("accept") or "").lower():
                return JSONResponse({"ok": False, "message": "login"}, status_code=401)
            return _publicaciones_redirect_login()
        return HTMLResponse("Permission denied.", status_code=403)

    lang = i18n.resolve_lang(request)
    form = await request.form()
    title = (form.get("title") or "").strip()
    description = (form.get("description") or "").strip()
    tiktoker_config_id = (form.get("tiktoker_config_id") or "").strip()
    account_link_id = (form.get("account_link_id") or "").strip()
    selected_platforms = [
        p
        for p in form.getlist("platforms")
        if p in platforms.PLATFORM_IDS and platforms.is_publish_enabled(p)
    ]
    upload = form.get("file")
    video_temp_token = (form.get("video_temp_token") or "").strip().lower()

    if not db.user_can_upload_videos(u):
        return _publicaciones_result(request, ok=False, message=_msg(request, "pub.flash.no_upload"))
    quota_code = db.consume_publish_quota(u)
    if quota_code:
        return _publicaciones_result(request, ok=False, message=_msg(request, quota_code))

    publish_choices = db.list_stats_filter_choices(u, lang=lang)
    choices_by_id = {c["id"]: c for c in publish_choices}
    if not choices_by_id:
        return _publicaciones_result(
            request, ok=False, message=_msg(request, "pub.flash.no_accounts_registered")
        )
    if db.user_is_tiktok_mode(u):
        allowed_platforms = set(PANEL_API_PLATFORM_IDS)
        ready = _tiktok_user_ready_platform_ids(u)
        selected_platforms = [
            p for p in selected_platforms if p in allowed_platforms and p in ready
        ]
        if len(choices_by_id) == 1:
            account_link_id = publish_choices[0]["id"]
        elif account_link_id not in choices_by_id:
            match_id = ""
            wanted = set(selected_platforms)
            for c in publish_choices:
                pids = {str(p).strip() for p in (c.get("platform_ids") or []) if str(p).strip()}
                if wanted and wanted.issubset(pids):
                    match_id = c["id"]
                    break
            if not match_id:
                for c in publish_choices:
                    pids = {
                        str(p).strip() for p in (c.get("platform_ids") or []) if str(p).strip()
                    }
                    if any(p in pids for p in wanted):
                        match_id = c["id"]
                        break
            if not match_id:
                return _publicaciones_result(
                    request,
                    ok=False,
                    message=_msg(request, "pub.flash.select_account_publish"),
                )
            account_link_id = match_id
    elif db.user_can_access_servers(u):
        if not account_link_id or account_link_id not in choices_by_id:
            return _publicaciones_result(
                request,
                ok=False,
                message=_msg(request, "pub.flash.select_account_publish"),
            )
        acc = choices_by_id[account_link_id]
        allowed_platforms = set(acc.get("platform_ids") or [])
        selected_platforms = [p for p in selected_platforms if p in allowed_platforms]
    elif len(choices_by_id) == 1:
        account_link_id = publish_choices[0]["id"]
        acc = choices_by_id[account_link_id]
        allowed_platforms = set(acc.get("platform_ids") or [])
        selected_platforms = [p for p in selected_platforms if p in allowed_platforms]
    elif account_link_id not in choices_by_id:
        return _publicaciones_result(
            request,
            ok=False,
            message=_msg(request, "pub.flash.select_account_publish"),
        )
    else:
        acc = choices_by_id.get(account_link_id)
        if acc:
            allowed_platforms = set(acc.get("platform_ids") or [])
            selected_platforms = [p for p in selected_platforms if p in allowed_platforms]

    if db.user_is_publisher_mode(u):
        acc = choices_by_id.get(account_link_id) or {}
        selected_platforms = [
            str(p)
            for p in (acc.get("platform_ids") or [])
            if platforms.is_publish_enabled(str(p)) and platforms.is_ui_visible(str(p))
        ]
        if "tiktok" not in selected_platforms:
            selected_platforms.append("tiktok")
        if not tiktoker_config_id:
            tiktoker_config_id = (
                db.resolve_tiktok_config_id(account_link_id=account_link_id) or ""
            )
    elif not db.user_can_access_servers(u) and not db.user_is_tiktok_mode(u):
        selected_platforms = [p for p in selected_platforms if p == "tiktok"]
        if not selected_platforms:
            selected_platforms = ["tiktok"]

    if not selected_platforms:
        return _publicaciones_result(
            request, ok=False, message=_msg(request, "pub.flash.no_platforms")
        )

    if not title:
        return _publicaciones_result(
            request, ok=False, message=_msg(request, "pub.flash.missing_title")
        )

    if db.user_is_publisher_mode(u):
        owner_user_id = u.id
    elif "tiktok" in selected_platforms:
        choices = db.publicaciones_tiktoker_choices(u)
        if not choices:
            return _publicaciones_result(
                request, ok=False, message=_msg(request, "pub.flash.no_accounts_registered")
            )
        owner_user_id = db.resolve_publish_owner_user_id(u, tiktoker_config_id)
        if not owner_user_id:
            cid = tiktoker_config_id
            if cid and db.get_config_internal_user_id(cid) is None:
                msg = _msg(request, "pub.flash.no_user_assigned")
            else:
                msg = _msg(request, "pub.flash.select_account_publish")
            return _publicaciones_result(request, ok=False, message=msg)
    else:
        if u.role == "user":
            owner_user_id = u.id
        else:
            ready = [
                c for c in db.publicaciones_tiktoker_choices(u) if c.get("internal_user_id")
            ]
            owner_user_id = ready[0]["internal_user_id"] if ready else u.id

    if not isinstance(upload, UploadFile) or not (upload.filename or "").strip():
        upload = None

    temp_path = None
    if video_temp_token:
        temp_path = video_temp_util.claim_temp(UPLOAD_DIR, u.id, video_temp_token)

    if temp_path:
        suffix = temp_path.suffix.lower()
        if suffix not in ALLOWED_MEDIA_EXT:
            temp_path.unlink(missing_ok=True)
            return _publicaciones_result(
                request,
                ok=False,
                message=_msg(
                    request,
                    "pub.flash.file_type",
                    types=", ".join(sorted(ALLOWED_MEDIA_EXT)),
                ),
            )
        content_type = "photo" if suffix in ALLOWED_PHOTO_EXT else "video"
        stored = f"{uuid.uuid4().hex}{suffix}"
        path = UPLOAD_DIR / stored
        temp_path.replace(path)
    elif upload and upload.filename:
        raw_name = upload.filename or ""
        suffix = Path(raw_name).suffix.lower()
        if suffix not in ALLOWED_MEDIA_EXT:
            return _publicaciones_result(
                request,
                ok=False,
                message=_msg(
                    request,
                    "pub.flash.file_type",
                    types=", ".join(sorted(ALLOWED_MEDIA_EXT)),
                ),
            )

        content_type = "photo" if suffix in ALLOWED_PHOTO_EXT else "video"

        contents = await upload.read()
        if len(contents) > MAX_UPLOAD_BYTES:
            return _publicaciones_result(
                request,
                ok=False,
                message=_msg(request, "pub.flash.file_too_large", max_mb=MAX_UPLOAD_MB),
            )

        stored = f"{uuid.uuid4().hex}{suffix}"
        path = UPLOAD_DIR / stored
        path.write_bytes(contents)
    else:
        missing_key = (
            "pub.flash.missing_file_publisher"
            if db.user_is_publisher_mode(u)
            else "pub.flash.missing_file"
        )
        return _publicaciones_result(
            request, ok=False, message=_msg(request, missing_key)
        )

    restrict = _publisher_media_error(u, path, content_type, lang)
    if restrict:
        path.unlink(missing_ok=True)
        return _publicaciones_result(request, ok=False, message=restrict)

    file_hash = db.file_sha256(path)
    if db.should_block_consecutive_same_file(u.id, file_hash):
        path.unlink(missing_ok=True)
        return _publicaciones_result(
            request, ok=False, message=_msg(request, "pub.flash.video_just_published")
        )

    schedule_enabled = (form.get("schedule_enabled") or "").strip() in ("1", "on", "true")
    scheduled_raw = (form.get("scheduled_at") or "").strip()
    scheduled_utc = None
    schedule_for_later = False
    pace_reason = "now"
    if schedule_enabled:
        scheduled_utc = publish_schedule.parse_scheduled_at_local(scheduled_raw)
        if not scheduled_utc:
            path.unlink(missing_ok=True)
            return _publicaciones_result(
                request, ok=False, message=_msg(request, "pub.flash.schedule_invalid")
            )
        now_utc = publish_schedule.now_publish_tz().astimezone(timezone.utc)
        if scheduled_utc <= now_utc:
            scheduled_utc = now_utc
        slot_utc, pace_reason = db.next_account_publish_slot(
            account_link_id, requested_at=scheduled_utc
        )
        if slot_utc > scheduled_utc:
            scheduled_utc = slot_utc
        schedule_for_later = scheduled_utc > now_utc
    else:
        now_utc = datetime.now(timezone.utc)
        slot_utc, pace_reason = db.next_account_publish_slot(
            account_link_id, requested_at=now_utc
        )
        if slot_utc > now_utc:
            scheduled_utc = slot_utc
            schedule_for_later = True
            schedule_enabled = True
        else:
            pace_reason = "now"

    if not db.try_lock_publish_file(u.id, file_hash):
        path.unlink(missing_ok=True)
        return _publicaciones_result(
            request, ok=False, message=_msg(request, "pub.flash.video_in_queue")
        )

    try:
        video = db.create_video(owner_user_id, title, description, stored, file_hash=file_hash)
    except Exception:
        db.release_publish_file_lock(u.id, file_hash)
        path.unlink(missing_ok=True)
        return _publicaciones_result(
            request, ok=False, message=_msg(request, "pub.flash.save_fail")
        )

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
        if pace_reason == "daily_cap":
            flash_key = "pub.flash.queued_daily_cap"
        elif pace_reason == "spacing":
            flash_key = "pub.flash.queued_spacing"
        else:
            flash_key = "pub.flash.scheduled"
        return _publicaciones_result(
            request, ok=True, message=_msg(request, flash_key, when=when_local)
        )

    ok_n, fail_n, pending_n, failures = await asyncio.to_thread(
        publish_schedule.execute_video_publish,
        upload_dir=UPLOAD_DIR,
        user_id=u.id,
        video=video,
        selected_platforms=selected_platforms,
        tiktoker_config_id=tiktoker_config_id,
        content_type=content_type,
        lang=lang,
        account_link_id=account_link_id,
    )
    db.release_publish_file_lock_if_idle(u.id, file_hash)

    past_schedule_immediate = schedule_enabled and scheduled_utc and not schedule_for_later

    if db.user_is_publisher_mode(u):
        tiktok_fail_entry = next(
            (f for f in (failures or []) if str(f.get("platform_id") or "") == "tiktok"),
            None,
        )
        if tiktok_fail_entry:
            msg = (tiktok_fail_entry.get("message") or "").strip() or _msg(
                request, "pub.flash.partial", ok=0, fail=1
            )
            return _publicaciones_result(request, ok=False, message=msg)
        ok_n = 1 if "tiktok" in selected_platforms else ok_n
        fail_n = 0

    if fail_n:
        return _publicaciones_result(
            request,
            ok=bool(ok_n or pending_n),
            message=_msg(
                request, "pub.flash.partial", ok=ok_n + pending_n, fail=fail_n
            ),
        )
    if pending_n:
        return _publicaciones_result(
            request,
            ok=True,
            message=_msg(request, "pub.flash.pending_review", n=pending_n),
        )
    if past_schedule_immediate:
        return _publicaciones_result(
            request, ok=True, message=_msg(request, "pub.flash.schedule_past_immediate")
        )
    return _publicaciones_result(
        request, ok=True, message=_msg(request, "pub.flash.all_ok", n=ok_n)
    )


def _require_publish_retry_admin(request: Request) -> db.User:
    u = _require_publicaciones_user(request)
    if not db.user_can_access_servers(u):
        raise PermissionError("forbidden")
    return u


def _redirect_after_pending_retry(request: Request, next_path: str = "") -> RedirectResponse:
    nxt = (next_path or "").strip()
    if nxt.startswith("/admin/extractor"):
        return RedirectResponse(url="/admin/extractor", status_code=303)
    return RedirectResponse(url=request.url_for("admin_publicaciones"), status_code=303)


@app.post("/admin/publicaciones/pending/{sched_id}/retry", name="admin_retry_pending_publish")
def admin_retry_pending_publish(
    request: Request,
    sched_id: str,
    next: Annotated[str, Form()] = "",
):
    try:
        u = _require_publish_retry_admin(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return _publicaciones_redirect_login()
        return HTMLResponse("Permission denied.", status_code=403)
    lang = i18n.resolve_lang(request)

    def done() -> RedirectResponse:
        return _redirect_after_pending_retry(request, next)

    row = db.get_scheduled_publication(sched_id)
    if not row or str(row.get("status") or "") != "awaiting_retry":
        request.session["admin_error"] = _msg(request, "pub.flash.pending_gone")
        return done()
    if not db.mark_scheduled_retry_processing(sched_id):
        request.session["admin_error"] = _msg(request, "pub.flash.pending_gone")
        return done()
    video = db.get_video_by_id(row["video_id"])
    if not video:
        db.complete_scheduled_publication(sched_id, "failed", "Video not found")
        request.session["admin_error"] = _msg(request, "pub.flash.pending_no_video")
        return done()
    path = UPLOAD_DIR / video.file_name
    if not path.is_file():
        try:
            leftover = json.loads(row.get("platforms_json") or "[]")
        except (TypeError, ValueError):
            leftover = []
        db.set_scheduled_awaiting_retry(sched_id, leftover, "Video file missing")
        request.session["admin_error"] = _msg(request, "pub.flash.pending_no_file")
        return done()
    try:
        platforms_list = json.loads(row.get("platforms_json") or "[]")
    except (TypeError, ValueError):
        platforms_list = []
    if not isinstance(platforms_list, list) or not platforms_list:
        db.complete_scheduled_publication(sched_id, "failed", "No platforms selected")
        db.release_publish_file_lock_if_idle(
            row["user_id"], getattr(video, "file_hash", "") or ""
        )
        request.session["admin_error"] = _msg(request, "pub.flash.no_platforms")
        return done()
    ok_n, fail_n, pending_n, _ = publish_schedule.execute_video_publish(
        upload_dir=UPLOAD_DIR,
        user_id=row["user_id"],
        video=video,
        selected_platforms=[str(p) for p in platforms_list if str(p).strip()],
        tiktoker_config_id=(row.get("tiktok_config_id") or "").strip(),
        content_type=row.get("content_type") or "video",
        lang=row.get("lang") or lang,
        account_link_id=(row.get("account_link_id") or "").strip(),
        retry_sched_id=sched_id,
    )
    db.release_publish_file_lock_if_idle(
        row["user_id"], getattr(video, "file_hash", "") or ""
    )
    if fail_n and (ok_n or pending_n):
        request.session["admin_ok"] = _msg(
            request, "pub.flash.partial", ok=ok_n + pending_n, fail=fail_n
        )
    elif fail_n:
        request.session["admin_error"] = _msg(
            request, "pub.flash.partial", ok=ok_n, fail=fail_n
        )
    elif pending_n:
        request.session["admin_ok"] = _msg(
            request, "pub.flash.pending_review", n=pending_n
        )
    else:
        request.session["admin_ok"] = _msg(request, "pub.flash.retry_all_ok", n=ok_n)
    return done()


@app.post("/admin/publicaciones/pending/{sched_id}/cancel", name="admin_cancel_pending_publish")
def admin_cancel_pending_publish(
    request: Request,
    sched_id: str,
    next: Annotated[str, Form()] = "",
):
    try:
        u = _require_publish_retry_admin(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return _publicaciones_redirect_login()
        return HTMLResponse("Permission denied.", status_code=403)
    lang = i18n.resolve_lang(request)
    if publish_schedule.cancel_awaiting_retry(
        sched_id=sched_id, actor_user_id=u.id, lang=lang
    ):
        request.session["admin_ok"] = _msg(request, "pub.flash.pending_cancelled")
    else:
        request.session["admin_error"] = _msg(request, "pub.flash.pending_gone")
    return _redirect_after_pending_retry(request, next)


@app.post("/admin/comments/reply", name="admin_reply_comment")
def admin_reply_comment(
    request: Request,
    video_id: Annotated[str, Form()],
    parent_id: Annotated[str, Form()],
    body: Annotated[str, Form()],
):
    try:
        u = require_user(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return RedirectResponse(url="/login?next=/admin", status_code=303)
        return HTMLResponse("Permission denied.", status_code=403)
    if not db.user_can_manage_comments(u) or not db.membership_usage(u)["can_view_comments"]:
        request.session["admin_error"] = _msg(request, "pub.flash.no_comments")
        return RedirectResponse(url=request.url_for("admin"), status_code=303)

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
    return RedirectResponse(url=request.url_for("admin"), status_code=303)


@app.get("/admin/equipo")
def admin_equipo_redirect(request: Request):
    return RedirectResponse(url=request.url_for("admin_panel"), status_code=301)


@app.get("/admin/panel", response_class=HTMLResponse, name="admin_panel")
def admin_panel(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _panel_redirect_login(request)
    lang = i18n.resolve_lang(request)
    err = (
        request.session.pop("panel_error", None)
        or request.session.pop("equipo_error", None)
        or request.session.pop("tiktok_error", None)
    )
    ok = (
        request.session.pop("panel_ok", None)
        or request.session.pop("equipo_ok", None)
        or request.session.pop("tiktok_ok", None)
    )
    admin_email = db.get_user_panel_email(admin.id)
    email_verified = db.is_user_notification_email_verified(admin.id)
    return _render(
        request,
        "admin_panel.html",
        {
            "user": admin,
            "nav_active": "panel",
            "user_email": admin_email,
            "email_verified": email_verified,
            "smtp_configured": notify.smtp_configured(),
            "error": err,
            "success": ok,
            "tiktok_oauth_configured": tiktok_oauth.oauth_configured(),
            "tiktok_linked_accounts": db.list_tiktok_accounts_for_user(admin),
            "panel_account_platforms": _build_panel_account_platforms(admin, lang, request),
            "user_mode_choices": [
                c
                for c in db.regular_user_mode_choices(lang)
                if not (db.user_is_tiktok_mode(admin) and c["id"] == "admin")
            ],
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
        admin = require_server_admin(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
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
    vmos_grouped = db.list_vmos_accounts_grouped()
    filehost_grouped = db.list_filehost_accounts_grouped()
    chain_grouped = db.list_chain_accounts_grouped()

    return _render(
        request,
        "admin_servidores.html",
        {
            "user": admin,
            "nav_active": "servidores",
            "ffmpeg_ok": video_compress.ffmpeg_available(),
            "api_docs": platforms.api_document_rows(lang),
            "platforms": platforms.platform_list(lang),
            "platforms_all": platforms.platform_list(lang, include_hidden=True),
            "linked_accounts": tiktok_linked,
            "youtube_linked": youtube_linked,
            "instagram_linked": instagram_linked,
            "facebook_linked": facebook_linked,
            "x_linked": x_linked,
            "dailymotion_linked": dailymotion_linked,
            "bilibili_linked": bilibili_linked,
            "snapchat_linked": snapchat_linked,
            "vmos_by_platform": vmos_grouped,
            "vmos_platform_ids": list(vmos.PLATFORM_IDS),
            "vmos_short_labels": vmos.SHORT_LABEL,
            "filehost_by_platform": filehost_grouped,
            "filehost_platform_ids": list(filehost.PLATFORM_IDS),
            "filehost_extra_fields": {
                pid: filehost.extra_field(pid) for pid in filehost.PLATFORM_IDS
            },
            "filehost_settings_urls": {
                pid: filehost.settings_url(pid) for pid in filehost.PLATFORM_IDS
            },
            "chain_by_platform": chain_grouped,
            "chain_platform_ids": [
                pid for pid in chain.PLATFORM_IDS if pid not in chain.QR_PLATFORM_IDS
            ],
            "chain_extra_fields": {
                pid: chain.extra_field(pid) for pid in chain.PLATFORM_IDS
            },
            "platform_creds": {},
            "server_accounts": [],
            "oauth_configured": tiktok_oauth.oauth_configured(),
            "oauth_scopes": tiktok_oauth.oauth_scopes(),
            "tiktok_redirect_uri": tiktok_oauth.redirect_uri(request),
            "youtube_oauth_configured": youtube_oauth.oauth_configured(),
            "youtube_oauth_scopes": youtube_oauth.oauth_scopes(),
            "youtube_redirect_uri": youtube_oauth.redirect_uri(request),
            "instagram_oauth_configured": instagram_oauth.oauth_configured(),
            "instagram_redirect_uri": instagram_oauth.redirect_uri(request),
            "facebook_oauth_configured": facebook_oauth.oauth_configured(),
            "facebook_redirect_uri": facebook_oauth.redirect_uri(request),
            "x_oauth_configured": x_oauth.oauth_configured(),
            "x_redirect_uri": x_oauth.redirect_uri(request),
            "dailymotion_oauth_configured": dailymotion_oauth.oauth_configured(),
            "dailymotion_redirect_uri": dailymotion_oauth.redirect_uri(request),
            "bilibili_oauth_configured": bilibili_oauth.oauth_configured(),
            "bilibili_redirect_uri": bilibili_oauth.redirect_uri(request),
            "snapchat_oauth_configured": snapchat_oauth.oauth_configured(),
            "snapchat_redirect_uri": snapchat_oauth.redirect_uri(request),
            "error": err,
            "success": ok,
        },
    )


@app.get("/admin/api-documento", response_class=HTMLResponse, name="admin_api_documento")
def admin_api_documento(request: Request):
    try:
        require_server_admin(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    return RedirectResponse(url="/admin/servidores#api-webs", status_code=303)


@app.get("/admin/condiciones-servidores", response_class=HTMLResponse, name="admin_server_conditions")
def admin_server_conditions(request: Request):
    try:
        require_server_admin(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    return RedirectResponse(url="/admin/servidores#api-webs", status_code=303)


@app.get("/admin/extractor", response_class=HTMLResponse, name="admin_extractor")
def admin_extractor_page(request: Request):
    try:
        admin = require_server_admin(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    return _render(
        request,
        "admin_extractor.html",
        {
            "user": admin,
            "nav_active": "extractor",
            "platform_choices": extractor.extractor_source_platforms(lang),
            "extractor_limits": {
                "batch_min": extractor.MIN_BATCH,
                "batch_max": extractor.MAX_BATCH,
                "batch_default": extractor.DEFAULT_BATCH,
                "interval_min": extractor.MIN_INTERVAL_MINUTES,
                "interval_max": extractor.MAX_INTERVAL_MINUTES,
                "interval_default": extractor.DEFAULT_INTERVAL_MIN,
                "interval_jitter_max": extractor.DEFAULT_INTERVAL_MAX,
                "rest_min": extractor.MIN_REST_SECONDS,
                "rest_max": extractor.MAX_REST_SECONDS,
                "rest_default": extractor.DEFAULT_REST_SECONDS,
            },
        },
    )


@app.get("/admin/proxys", response_class=HTMLResponse, name="admin_proxys")
def admin_proxys_page(request: Request):
    try:
        admin = require_server_admin(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    return _render(
        request,
        "admin_proxys.html",
        {
            "user": admin,
            "nav_active": "proxys",
        },
    )


@app.get("/admin/membresias", response_class=HTMLResponse, name="admin_membresias")
def admin_membresias_page(request: Request):
    try:
        user = require_user(request)
    except PermissionError:
        return RedirectResponse(url="/login?next=/admin/membresias", status_code=303)
    if db.user_is_publisher_mode(user):
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    lang = i18n.resolve_lang(request)
    current = (user.membership_plan or "").strip().lower()
    plans = [_plan_api_item(p, lang) for p in membership.PLANS]
    return _render(
        request,
        "admin_membresias.html",
        {
            "user": user,
            "nav_active": "membresias",
            "plans": plans,
            "current_plan": current,
            "wallet_balance_usd": int(getattr(user, "wallet_balance_usd", 0) or 0),
            "unused_credit_usd": membership.unused_plan_credit_usd(
                current, db.membership_started_at_for(user)
            ),
            "invited": db.user_was_invited(user.id),
            "can_manage_payments": db.user_can_access_servers(user),
        },
    )


@app.get("/admin/pagos", response_class=HTMLResponse, name="admin_pagos")
def admin_pagos_page(request: Request):
    try:
        user = require_user(request)
    except PermissionError:
        return RedirectResponse(url="/login?next=/admin/pagos", status_code=303)
    if db.user_is_publisher_mode(user):
        return RedirectResponse(url=_default_app_home(user), status_code=303)
    return _render(
        request,
        "admin_pagos.html",
        {
            "user": user,
            "nav_active": "pagos",
            "can_manage_payments": db.user_can_access_servers(user),
            "wallet_balance_usd": int(getattr(user, "wallet_balance_usd", 0) or 0),
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
    guard = _require_server_admin_json(request)
    if guard:
        return guard
    user = _session_user(request)
    lang = i18n.resolve_lang(request)
    pid = (platform or "").strip()
    if not extractor.is_extractor_source(pid):
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
    target_ids = [
        t
        for t in (choice.get("platform_ids") or [])
        if t != pid and platforms.is_publish_enabled(t)
    ]
    summary = extractor.scan_summary(
        choice["id"], pid, target_ids, upload_dir=UPLOAD_DIR
    )
    names = _extractor_platform_meta(lang)
    sources = choice.get("platform_sources") or {}
    targets = []
    for item in summary["targets"]:
        tid = item["platform_id"]
        meta = names.get(tid, {})
        via = str(sources.get(tid) or "")
        targets.append(
            {
                "platform_id": tid,
                "name": meta.get("name", tid),
                "icon": meta.get("icon", ""),
                "pending": item["pending"],
                "cycle_cap": extractor.platform_cycle_cap(tid),
                "via": via,
                "via_vmos": via == "vmos",
                "via_filehost": via == "filehost",
                "via_chain": via == "chain",
            }
        )
    source_via = str(sources.get(pid) or "")
    return {
        "ok": True,
        "total": summary["total"],
        "targets": targets,
        "account_name": choice.get("name") or "",
        "source_via": source_via,
        "source_via_vmos": source_via == "vmos",
        "source_via_filehost": source_via == "filehost",
        "source_via_chain": source_via == "chain",
        "conflict": db.extractor_job_conflict_exists(choice["id"], pid),
    }


@app.get("/admin/api/extractor/jobs")
def api_extractor_jobs(request: Request):
    guard = _require_server_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    jobs = [_extractor_job_public(j, lang) for j in db.list_extractor_jobs()]
    return {"ok": True, "jobs": jobs}


@app.post("/admin/api/extractor/jobs")
def api_extractor_create_job(request: Request, body: ExtractorJobBody):
    guard = _require_server_admin_json(request)
    if guard:
        return guard
    user = _session_user(request)
    lang = i18n.resolve_lang(request)

    pid = (body.source_platform_id or "").strip()
    if not extractor.is_extractor_source(pid):
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

    allowed_targets = [
        t
        for t in (choice.get("platform_ids") or [])
        if t != pid and platforms.is_publish_enabled(t)
    ]
    requested = [
        str(t).strip() for t in (body.target_platform_ids or []) if str(t).strip()
    ]
    targets = [t for t in requested if t in allowed_targets] or list(allowed_targets)
    if not targets:
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_no_targets", lang)},
            status_code=400,
        )

    if db.extractor_job_conflict_exists(choice["id"], pid):
        return JSONResponse(
            {"ok": False, "error": i18n.t("extractor.err_duplicate", lang)},
            status_code=409,
        )

    total = extractor.scan_summary(
        choice["id"], pid, targets, upload_dir=UPLOAD_DIR
    )["total"]
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
        batch_size=extractor.DEFAULT_BATCH,
        interval_minutes=extractor.DEFAULT_INTERVAL_MIN,
        rest_seconds=extractor.DEFAULT_REST_SECONDS,
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
    guard = _require_server_admin_json(request)
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
    guard = _require_server_admin_json(request)
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
    guard = _require_server_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    job = extractor.set_target_paused(job_id, platform_id, paused=True, lang=lang)
    if not job:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True, "job": _extractor_job_public(job, lang)}


@app.post("/admin/api/extractor/jobs/{job_id}/targets/{platform_id}/resume")
def api_extractor_resume_target(request: Request, job_id: str, platform_id: str):
    guard = _require_server_admin_json(request)
    if guard:
        return guard
    lang = i18n.resolve_lang(request)
    job = extractor.set_target_paused(job_id, platform_id, paused=False, lang=lang)
    if not job:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True, "job": _extractor_job_public(job, lang)}


@app.delete("/admin/api/extractor/jobs/{job_id}")
def api_extractor_delete_job(request: Request, job_id: str):
    guard = _require_server_admin_json(request)
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
        user = require_admin_privileges(request)
    except PermissionError:
        return _panel_redirect_login(request)
    addr = (email or "").strip()
    if not _valid_email(addr):
        request.session["panel_error"] = _msg(request, "panel.flash.invalid_email")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    try:
        token = db.set_user_notification_email(user.id, addr)
    except ValueError as e:
        msg = str(e)
        if "already in use" in msg.lower():
            request.session["panel_error"] = _msg(request, "panel.flash.email_taken")
        else:
            request.session["panel_error"] = _msg(request, "panel.flash.invalid_email")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    if not token:
        request.session["panel_ok"] = _msg(request, "panel.flash.email_already_verified")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    if not notify.smtp_configured():
        request.session["panel_error"] = _msg(request, "panel.flash.no_smtp")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    verify_url = _email_verify_url(request, token)
    lang = i18n.resolve_lang(request)
    if not notify.send_email_verification_email(
        to=addr, verify_url=verify_url, lang=lang
    ):
        request.session["panel_error"] = _msg(request, "panel.flash.mail_fail")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    request.session["panel_ok"] = _msg(request, "panel.flash.email_saved", email=addr)
    return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)


@app.post("/admin/panel/email-resend", name="admin_panel_resend_email")
def admin_panel_resend_email(request: Request):
    try:
        user = require_admin_privileges(request)
    except PermissionError:
        return _panel_redirect_login(request)
    lang = i18n.resolve_lang(request)
    if db.is_user_notification_email_verified(user.id):
        request.session["panel_ok"] = _msg(request, "panel.flash.email_already_verified")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    token = db.resend_notification_email_verification(user.id)
    if not token:
        request.session["panel_error"] = _msg(request, "panel.flash.no_pending_email")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    if not notify.smtp_configured():
        request.session["panel_error"] = _msg(request, "panel.flash.no_smtp")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    addr = db.get_user_panel_email(user.id)
    verify_url = _email_verify_url(request, token)
    if not notify.send_email_verification_email(
        to=addr, verify_url=verify_url, lang=lang
    ):
        request.session["panel_error"] = _msg(request, "panel.flash.mail_fail")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    request.session["panel_ok"] = _msg(request, "panel.flash.email_saved", email=addr)
    return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)


@app.get("/verificar-correo", response_class=HTMLResponse, name="verify_email")
@app.get("/email/verify", response_class=HTMLResponse, name="verify_email_en")
def verify_email_get(request: Request):
    token = (request.query_params.get("token") or "").strip()
    lang = i18n.resolve_lang(request)
    uid = db.confirm_notification_email(token)
    if not uid:
        request.session["panel_error"] = i18n.t("panel.flash.verification_invalid", lang)
        session_user = _session_user(request)
        if session_user:
            return RedirectResponse(url="/admin/panel", status_code=303)
        request.session["login_ok"] = i18n.t("panel.flash.verification_invalid", lang)
        return RedirectResponse(url="/login", status_code=303)
    msg = i18n.t("panel.flash.email_verified", lang)
    session_user = _session_user(request)
    if session_user and session_user.id == uid:
        request.session["panel_ok"] = msg
        return RedirectResponse(url="/admin/panel", status_code=303)
    request.session["login_ok"] = msg
    return RedirectResponse(url="/login", status_code=303)


@app.post("/admin/panel/password-reset", name="admin_panel_password_reset")
def admin_panel_password_reset(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _panel_redirect_login(request)
    lang = i18n.resolve_lang(request)
    if not db.is_user_notification_email_verified(admin.id):
        request.session["panel_error"] = _msg(request, "panel.flash.email_must_confirm")
        return RedirectResponse(url=request.url_for("admin_panel"), status_code=303)
    to = db.get_user_notification_email(admin.id)
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
        db.set_user_password(uid, pw)
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


def _tiktok_oauth_return_path(user: db.User, request: Request | None = None) -> str:
    return _oauth_return_path(user, request)


def _oauth_return_path(user: db.User, request: Request | None = None) -> str:
    if not db.user_can_access_servers(user):
        if request is not None:
            request.session.pop("oauth_restore_picker_name", None)
        return "/admin/panel"
    name = ""
    if request is not None:
        name = str(request.session.pop("oauth_restore_picker_name", "") or "").strip()
        name = name.replace("\x00", "")[:200]
    if name:
        return "/admin/servidores?open_account=" + quote(name, safe="")
    return "/admin/servidores"


def _store_oauth_redirect(request: Request, session_key: str, oauth_mod) -> str:
    ru = oauth_mod.redirect_uri(request)
    request.session[session_key] = ru
    return ru


def _pop_oauth_redirect(request: Request, session_key: str, oauth_mod) -> str:
    stored = str(request.session.pop(session_key, None) or "").strip()
    return stored or oauth_mod.redirect_uri(request)


def _store_oauth_link_target(request: Request) -> None:
    """Si el connect viene desde una cuenta lógica (?link_name=), recuérdala para el callback."""
    name = (request.query_params.get("link_name") or "").strip()
    if name:
        request.session["oauth_link_target_name"] = name
        request.session["oauth_restore_picker_name"] = name
    else:
        request.session.pop("oauth_link_target_name", None)
        request.session.pop("oauth_restore_picker_name", None)


def _pop_oauth_link_target(request: Request) -> str:
    return str(request.session.pop("oauth_link_target_name", "") or "").strip()


def _bind_oauth_link_target(request: Request, oauth_account_id: str) -> None:
    """Une la cuenta OAuth recién conectada a la cuenta lógica elegida en Servidores."""
    name = _pop_oauth_link_target(request)
    if not name or not oauth_account_id:
        return
    try:
        db.bind_oauth_account_name(oauth_account_id, name)
    except Exception as e:
        print(f"bind_oauth_account_name failed: {e}", flush=True)


def _revoke_oauth_remote(row: dict) -> None:
    """Revoca el token en el proveedor antes de borrar en local (mejor esfuerzo)."""
    pid = str(row.get("platform_id") or "").strip()
    access = str(row.get("access_token") or "").strip()
    refresh = str(row.get("refresh_token") or "").strip()
    name = str(row.get("account_name") or "").strip()
    with db.using_credentials_account(name):
        _revoke_oauth_remote_inner(pid, access, refresh, row)


def _revoke_oauth_remote_inner(pid: str, access: str, refresh: str, row: dict) -> None:
    try:
        if pid == "youtube":
            youtube_oauth.revoke_tokens(access, refresh)
        elif pid == "x":
            x_oauth.revoke_tokens(access, refresh)
        elif pid == "dailymotion":
            dailymotion_oauth.revoke_tokens(access, refresh)
        elif pid == "snapchat":
            snapchat_oauth.revoke_tokens(access, refresh)
        elif pid == "instagram":
            instagram_oauth.revoke_tokens(access, refresh)
        elif pid == "facebook":
            # El refresh_token guarda el user token; revoca la app solo si esta
            # es la última página conectada de ese usuario.
            if refresh and not db.count_other_oauth_accounts_with_refresh(
                "facebook", refresh, exclude_id=str(row.get("id") or "")
            ):
                facebook_oauth.revoke_user_permissions(refresh)
    except Exception:
        pass


def _oauth_redirect(request: Request, user: db.User) -> RedirectResponse:
    return RedirectResponse(url=_oauth_return_path(user, request), status_code=303)


PANEL_API_PLATFORM_IDS = frozenset(
    {"dailymotion", "facebook", "x", "youtube", "instagram", "bilibili"}
)
TIKTOK_USER_PANEL_PLATFORM_ORDER = (
    "youtube",
    "dailymotion",
    "facebook",
    "x",
    "instagram",
    "bilibili",
)

_PANEL_OAUTH_REDIRECT_MODS = {
    "facebook": facebook_oauth,
    "x": x_oauth,
    "dailymotion": dailymotion_oauth,
    "youtube": youtube_oauth,
    "instagram": instagram_oauth,
    "bilibili": bilibili_oauth,
}

_PANEL_OAUTH_REDIRECT_HINT_KEYS: dict[str, str] = {
    "facebook": "servers.facebook_redirect_hint",
    "x": "servers.x_redirect_hint",
    "dailymotion": "servers.dailymotion_redirect_hint",
    "youtube": "servers.youtube_redirect_hint",
    "instagram": "servers.instagram_redirect_hint",
    "bilibili": "servers.bilibili_redirect_hint",
}


def _tiktok_user_panel_platforms(
    lang: str, user: db.User | None = None
) -> list[dict[str, Any]]:
    """Las plataformas de Panel → Cuenta para usuarios modo TikTok."""
    by_id = {p["id"]: dict(p) for p in platforms.platform_list(lang)}
    linked_ids: set[str] = set()
    vmos_ids: set[str] = set()
    if user is not None:
        for acc in db.list_user_publish_accounts(user, lang=lang):
            for pid in acc.get("platform_ids") or []:
                pid_s = str(pid or "").strip()
                if pid_s:
                    linked_ids.add(pid_s)
            for pid, kind in (acc.get("platform_sources") or {}).items():
                if str(kind or "") == "vmos":
                    vmos_ids.add(str(pid).strip())
    out: list[dict[str, Any]] = []
    for pid in TIKTOK_USER_PANEL_PLATFORM_ORDER:
        item = by_id.get(pid)
        if not item:
            continue
        mod = _PANEL_OAUTH_REDIRECT_MODS.get(pid)
        item["configured"] = bool((mod and mod.oauth_configured()) or pid in linked_ids)
        item["via_vmos"] = pid in vmos_ids
        out.append(item)
    return out


def _tiktok_user_ready_platform_ids(user: db.User | None = None) -> set[str]:
    return {
        p["id"]
        for p in _tiktok_user_panel_platforms("es", user)
        if p.get("configured")
    }


def _require_platform_credentials_json(
    request: Request, platform_id: str
) -> JSONResponse | None:
    if platform_id in PANEL_API_PLATFORM_IDS:
        return _require_admin_json(request)
    return _require_server_admin_json(request)


def _build_panel_account_platforms(
    user: db.User, lang: str, request: Request | None = None
) -> list[dict[str, Any]]:
    if not db.user_can_manage_panel_accounts(user):
        return []
    names = {p["id"]: p["name"] for p in platforms.platform_list(lang)}
    meta_by_id = {p["id"]: p for p in platforms.platform_list(lang)}
    defs: tuple[tuple[str, Any, str, str, str, str, str], ...] = (
        (
            "youtube",
            youtube_oauth,
            "servers.connect_with_youtube",
            "servers.youtube_oauth_missing",
            "btn-youtube",
            "▶",
            "oauth",
        ),
        (
            "dailymotion",
            dailymotion_oauth,
            "servers.connect_with_dailymotion",
            "servers.dailymotion_oauth_missing",
            "btn-dailymotion",
            "▶",
            "oauth",
        ),
        (
            "facebook",
            facebook_oauth,
            "servers.connect_with_facebook",
            "servers.facebook_oauth_missing",
            "btn-facebook",
            "f",
            "oauth",
        ),
        (
            "x",
            x_oauth,
            "servers.connect_with_x",
            "servers.x_oauth_missing",
            "btn-x",
            "𝕏",
            "oauth",
        ),
        (
            "instagram",
            instagram_oauth,
            "servers.connect_with_instagram",
            "servers.instagram_oauth_missing",
            "btn-instagram",
            "◎",
            "oauth",
        ),
        (
            "bilibili",
            bilibili_oauth,
            "servers.connect_with_bilibili",
            "servers.bilibili_oauth_missing",
            "btn-bilibili",
            "▶",
            "oauth",
        ),
    )
    out: list[dict[str, Any]] = []
    for pid, oauth_mod, connect_key, missing_key, btn_class, icon, kind in defs:
        configured = oauth_mod.oauth_configured()
        accounts = db.list_oauth_accounts_for_user(user, pid)
        display_name = i18n.t(f"panel.platform.{pid}", lang)
        if display_name == f"panel.platform.{pid}":
            display_name = names.get(pid, pid)
        platform_meta = meta_by_id.get(pid, {})
        creds = db.get_platform_credentials_public(pid)
        item: dict[str, Any] = {
            "id": pid,
            "name": display_name,
            "connect_url": f"/oauth/{pid}/connect",
            "connect_label": i18n.t(connect_key, lang),
            "missing_label": i18n.t(missing_key, lang),
            "configured": configured,
            "btn_class": btn_class,
            "icon": icon,
            "kind": kind,
            "accounts": accounts,
            "api_modal": pid in PANEL_API_PLATFORM_IDS,
            "limits_info": platforms.platform_limits_info(pid, lang),
        }
        if pid in PANEL_API_PLATFORM_IDS:
            item["creds"] = creds
            item["label_client_id"] = platform_meta.get("label_client_id") or ""
            item["label_client_secret"] = platform_meta.get("label_client_secret") or ""
            redirect_mod = _PANEL_OAUTH_REDIRECT_MODS.get(pid)
            item["redirect_uri"] = (
                redirect_mod.redirect_uri(request) if redirect_mod else ""
            )
            hint_key = _PANEL_OAUTH_REDIRECT_HINT_KEYS.get(pid, "")
            item["redirect_hint"] = i18n.t(hint_key, lang) if hint_key else ""
        out.append(item)
    return out


def _tiktok_oauth_redirect(request: Request, user: db.User) -> RedirectResponse:
    return _oauth_redirect(request, user)


@app.get("/oauth/tiktok/connect", name="tiktok_oauth_connect")
def tiktok_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    if not tiktok_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t(
            "panel.tiktok_oauth_missing", i18n.resolve_lang(request)
        )
        return _tiktok_oauth_redirect(request, admin)
    state = tiktok_oauth.new_csrf_state()
    request.session["tiktok_oauth_state"] = state
    request.session["tiktok_oauth_user_id"] = admin.id
    _store_oauth_link_target(request)
    ru = _store_oauth_redirect(request, "tiktok_oauth_redirect_uri", tiktok_oauth)
    url = tiktok_oauth.build_authorize_url(state=state, redirect_uri_value=ru)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/tiktok/callback", name="tiktok_oauth_callback")
def tiktok_oauth_callback(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    saved_state = request.session.pop("tiktok_oauth_state", None)
    linked_by = request.session.pop("tiktok_oauth_user_id", None) or admin.id
    nxt = _tiktok_oauth_return_path(admin, request)
    err_param = request.query_params.get("error")
    if err_param:
        request.session["tiktok_error"] = f"TikTok authorization denied: {err_param}"
        return RedirectResponse(url=nxt, status_code=303)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = "Invalid OAuth state. Please try again."
        return RedirectResponse(url=nxt, status_code=303)
    if not code:
        request.session["tiktok_error"] = "TikTok did not return an authorization code."
        return RedirectResponse(url=nxt, status_code=303)
    try:
        ru = _pop_oauth_redirect(request, "tiktok_oauth_redirect_uri", tiktok_oauth)
        token_data = tiktok_oauth.exchange_code_for_tokens(
            code, redirect_uri_value=ru
        )
        access = token_data.get("access_token") or ""
        refresh = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in TikTok response.")
        profile = tiktok_oauth.fetch_user_profile(access)
        open_id = profile.get("open_id") or token_data.get("open_id") or ""
        cid = db.save_tiktok_oauth_connection(
            open_id=str(open_id),
            tiktok_username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=int(expires_in) if expires_in is not None else None,
            scopes=tiktok_oauth.oauth_scopes(),
            client_key=tiktok_oauth.client_key(),
            client_secret=tiktok_oauth.client_secret(),
            redirect_uri=ru,
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        db.attach_tiktok_config_to_user(cid, str(linked_by))
        link_name = _pop_oauth_link_target(request)
        if link_name:
            db.bind_tiktok_config_name(cid, link_name)
        uname = profile.get("username") or "account"
        request.session["tiktok_ok"] = f"Connected @{uname} successfully."
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return RedirectResponse(url=nxt, status_code=303)


@app.delete("/admin/api/tiktokers/{config_id}")
def api_tiktok_delete(request: Request, config_id: str):
    try:
        me = require_admin_privileges(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse(
                {"ok": False, "error": "Sign in as an administrator."},
                status_code=401,
            )
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    if not db.user_can_manage_tiktok_config(me, config_id):
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    row = db.get_tiktok_oauth_row(config_id)
    if row:
        tok = (row.get("access_token") or "").strip()
        if tok:
            tiktok_oauth.revoke_access_token(tok)
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
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    if not youtube_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.youtube_oauth_missing", lang)
        return _oauth_redirect(request, admin)
    state = youtube_oauth.new_csrf_state()
    request.session["youtube_oauth_state"] = state
    request.session["youtube_oauth_user_id"] = admin.id
    _store_oauth_link_target(request)
    ru = _store_oauth_redirect(request, "youtube_oauth_redirect_uri", youtube_oauth)
    url = youtube_oauth.build_authorize_url(state=state, redirect_uri_value=ru)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/youtube/callback", name="youtube_oauth_callback")
def youtube_oauth_callback(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("youtube_oauth_state", None)
    linked_by = request.session.pop("youtube_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"YouTube: {desc}"
        return _oauth_redirect(request, admin)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return _oauth_redirect(request, admin)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.youtube_no_code", lang)
        return _oauth_redirect(request, admin)
    try:
        ru = _pop_oauth_redirect(request, "youtube_oauth_redirect_uri", youtube_oauth)
        token_data = youtube_oauth.exchange_code_for_tokens(code, redirect_uri_value=ru)
        access = token_data.get("access_token") or ""
        refresh = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in Google response.")
        profile = youtube_oauth.fetch_channel_profile(access)
        open_id = profile.get("open_id") or ""
        if not open_id:
            raise ValueError("YouTube did not return a channel id.")
        cid = db.save_oauth_connection(
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
            redirect_uri=ru,
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        _bind_oauth_link_target(request, cid)
        label = profile.get("display_name") or profile.get("username") or "YouTube"
        request.session["tiktok_ok"] = i18n.t("servers.youtube_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return _oauth_redirect(request, admin)


@app.get("/oauth/instagram/connect", name="instagram_oauth_connect")
def instagram_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    if not instagram_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.instagram_oauth_missing", lang)
        return _oauth_redirect(request, admin)
    state = instagram_oauth.new_csrf_state()
    request.session["instagram_oauth_state"] = state
    request.session["instagram_oauth_user_id"] = admin.id
    _store_oauth_link_target(request)
    ru = _store_oauth_redirect(request, "instagram_oauth_redirect_uri", instagram_oauth)
    url = instagram_oauth.build_authorize_url(state=state, redirect_uri_value=ru)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/instagram/callback", name="instagram_oauth_callback")
def instagram_oauth_callback(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("instagram_oauth_state", None)
    linked_by = request.session.pop("instagram_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Instagram: {desc}"
        return _oauth_redirect(request, admin)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return _oauth_redirect(request, admin)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.instagram_no_code", lang)
        return _oauth_redirect(request, admin)
    try:
        ru = _pop_oauth_redirect(request, "instagram_oauth_redirect_uri", instagram_oauth)
        token_data = instagram_oauth.exchange_code_for_tokens(code, redirect_uri_value=ru)
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
        cid = db.save_oauth_connection(
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
            redirect_uri=ru,
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        _bind_oauth_link_target(request, cid)
        label = profile.get("username") or profile.get("display_name") or "Instagram"
        request.session["tiktok_ok"] = i18n.t("servers.instagram_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return _oauth_redirect(request, admin)


@app.get("/oauth/facebook/connect", name="facebook_oauth_connect")
def facebook_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    if not facebook_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.facebook_oauth_missing", lang)
        return _oauth_redirect(request, admin)
    state = facebook_oauth.new_csrf_state()
    request.session["facebook_oauth_state"] = state
    request.session["facebook_oauth_user_id"] = admin.id
    _store_oauth_link_target(request)
    ru = _store_oauth_redirect(request, "facebook_oauth_redirect_uri", facebook_oauth)
    url = facebook_oauth.build_authorize_url(state=state, redirect_uri_value=ru)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/facebook/callback", name="facebook_oauth_callback")
def facebook_oauth_callback(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("facebook_oauth_state", None)
    linked_by = request.session.pop("facebook_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Facebook: {desc}"
        return _oauth_redirect(request, admin)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return _oauth_redirect(request, admin)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.facebook_no_code", lang)
        return _oauth_redirect(request, admin)
    try:
        ru = _pop_oauth_redirect(request, "facebook_oauth_redirect_uri", facebook_oauth)
        token_data = facebook_oauth.exchange_code_for_tokens(code, redirect_uri_value=ru)
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
        saved_ids: list[str] = []
        for page in pages:
            cid = db.save_oauth_connection(
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
                redirect_uri=ru,
                linked_by_user_id=str(linked_by) if linked_by else None,
            )
            saved_ids.append(cid)
        if len(saved_ids) == 1:
            _bind_oauth_link_target(request, saved_ids[0])
        else:
            _pop_oauth_link_target(request)
        request.session["tiktok_ok"] = i18n.t(
            "servers.facebook_connected", lang, n=len(pages)
        )
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return _oauth_redirect(request, admin)


@app.get("/oauth/x/connect", name="x_oauth_connect")
def x_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    _store_oauth_link_target(request)
    link_name = (request.query_params.get("link_name") or "").strip() or str(
        request.session.get("oauth_link_target_name") or ""
    ).strip()
    x_mode = "own" if db.account_name_wants_own_x_api(link_name) else "funding"
    request.session["x_oauth_app_mode"] = x_mode
    with db.using_credentials_account(link_name):
        with db.using_x_app_mode(x_mode):
            if not x_oauth.oauth_configured():
                request.session["tiktok_error"] = i18n.t("servers.x_oauth_missing", lang)
                return _oauth_redirect(request, admin)
            state = x_oauth.new_csrf_state()
            verifier, challenge = x_oauth.pkce_pair()
            request.session["x_oauth_state"] = state
            request.session["x_oauth_verifier"] = verifier
            request.session["x_oauth_user_id"] = admin.id
            ru = _store_oauth_redirect(request, "x_oauth_redirect_uri", x_oauth)
            url = x_oauth.build_authorize_url(
                state=state, code_challenge=challenge, redirect_uri_value=ru
            )
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/x/callback", name="x_oauth_callback")
def x_oauth_callback(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("x_oauth_state", None)
    verifier = request.session.pop("x_oauth_verifier", None)
    linked_by = request.session.pop("x_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"X: {desc}"
        return _oauth_redirect(request, admin)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state or not verifier:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return _oauth_redirect(request, admin)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.x_no_code", lang)
        return _oauth_redirect(request, admin)
    try:
        link_name = str(request.session.get("oauth_link_target_name") or "").strip()
        x_mode = str(request.session.pop("x_oauth_app_mode", "") or "").strip()
        if x_mode not in ("own", "funding"):
            x_mode = "own" if db.account_name_wants_own_x_api(link_name) else "funding"
        with db.using_credentials_account(link_name):
            with db.using_x_app_mode(x_mode):
                ru = _pop_oauth_redirect(request, "x_oauth_redirect_uri", x_oauth)
                token_data = x_oauth.exchange_code_for_tokens(
                    code, code_verifier=str(verifier), redirect_uri_value=ru
                )
                access = str(token_data.get("access_token") or "").strip()
                refresh = str(token_data.get("refresh_token") or "").strip() or None
                expires_in = token_data.get("expires_in")
                if not access:
                    raise ValueError("No access token in X response.")
                profile = x_oauth.fetch_profile(access)
                open_id = profile.get("open_id") or ""
                if not open_id:
                    raise ValueError("X did not return a user id.")
                cid = db.save_oauth_connection(
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
                    redirect_uri=ru,
                    linked_by_user_id=str(linked_by) if linked_by else None,
                )
        _bind_oauth_link_target(request, cid)
        label = profile.get("username") or profile.get("display_name") or "X"
        request.session["tiktok_ok"] = i18n.t("servers.x_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return _oauth_redirect(request, admin)


@app.get("/oauth/dailymotion/connect", name="dailymotion_oauth_connect")
def dailymotion_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    if not dailymotion_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.dailymotion_oauth_missing", lang)
        return _oauth_redirect(request, admin)
    state = dailymotion_oauth.new_csrf_state()
    request.session["dailymotion_oauth_state"] = state
    request.session["dailymotion_oauth_user_id"] = admin.id
    _store_oauth_link_target(request)
    ru = _store_oauth_redirect(request, "dailymotion_oauth_redirect_uri", dailymotion_oauth)
    url = dailymotion_oauth.build_authorize_url(state=state, redirect_uri_value=ru)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/dailymotion/callback", name="dailymotion_oauth_callback")
def dailymotion_oauth_callback(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("dailymotion_oauth_state", None)
    linked_by = request.session.pop("dailymotion_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Dailymotion: {desc}"
        return _oauth_redirect(request, admin)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return _oauth_redirect(request, admin)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.dailymotion_no_code", lang)
        return _oauth_redirect(request, admin)
    try:
        ru = _pop_oauth_redirect(
            request, "dailymotion_oauth_redirect_uri", dailymotion_oauth
        )
        token_data = dailymotion_oauth.exchange_code_for_tokens(
            code, redirect_uri_value=ru
        )
        access = str(token_data.get("access_token") or "").strip()
        refresh = str(token_data.get("refresh_token") or "").strip() or None
        expires_in = token_data.get("expires_in")
        if not access:
            raise ValueError("No access token in Dailymotion response.")
        profile = dailymotion_oauth.fetch_profile(access)
        open_id = profile.get("open_id") or ""
        if not open_id:
            raise ValueError("Dailymotion did not return a user id.")
        cid = db.save_oauth_connection(
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
            redirect_uri=ru,
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        _bind_oauth_link_target(request, cid)
        label = profile.get("username") or profile.get("display_name") or "Dailymotion"
        request.session["tiktok_ok"] = i18n.t("servers.dailymotion_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return _oauth_redirect(request, admin)


@app.get("/oauth/bilibili/connect", name="bilibili_oauth_connect")
def bilibili_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    if not bilibili_oauth.oauth_configured():
        request.session["tiktok_error"] = i18n.t("servers.bilibili_oauth_missing", lang)
        return _oauth_redirect(request, admin)
    state = bilibili_oauth.new_csrf_state()
    request.session["bilibili_oauth_state"] = state
    request.session["bilibili_oauth_user_id"] = admin.id
    _store_oauth_link_target(request)
    ru = _store_oauth_redirect(request, "bilibili_oauth_redirect_uri", bilibili_oauth)
    url = bilibili_oauth.build_authorize_url(state=state, redirect_uri_value=ru)
    return RedirectResponse(url=url, status_code=303)


@app.get("/oauth/bilibili/callback", name="bilibili_oauth_callback")
def bilibili_oauth_callback(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    saved_state = request.session.pop("bilibili_oauth_state", None)
    linked_by = request.session.pop("bilibili_oauth_user_id", None)
    err_param = request.query_params.get("error")
    if err_param:
        desc = request.query_params.get("error_description") or err_param
        request.session["tiktok_error"] = f"Bilibili: {desc}"
        return _oauth_redirect(request, admin)
    state = (request.query_params.get("state") or "").strip()
    code = (request.query_params.get("code") or "").strip()
    if not saved_state or state != saved_state:
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return _oauth_redirect(request, admin)
    if not code:
        request.session["tiktok_error"] = i18n.t("servers.bilibili_no_code", lang)
        return _oauth_redirect(request, admin)
    try:
        ru = _pop_oauth_redirect(request, "bilibili_oauth_redirect_uri", bilibili_oauth)
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
        cid = db.save_oauth_connection(
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
            redirect_uri=ru,
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        _bind_oauth_link_target(request, cid)
        label = profile.get("username") or profile.get("display_name") or "Bilibili"
        request.session["tiktok_ok"] = i18n.t("servers.bilibili_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        request.session["tiktok_error"] = str(e)
    return _oauth_redirect(request, admin)


@app.get("/oauth/snapchat/connect", name="snapchat_oauth_connect")
def snapchat_oauth_connect(request: Request):
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    link_name = (request.query_params.get("link_name") or "").strip()
    with db.using_credentials_account(link_name):
        ready = snapchat_oauth.oauth_configured()
        ru = snapchat_oauth.redirect_uri(request)
        _oauth_debug_log(
            "snapchat",
            "connect client=%s… scope=%s"
            % ((snapchat_oauth.client_id() or "")[:8], snapchat_oauth.oauth_scopes()),
        )
        _store_oauth_link_target(request)
        if not ready:
            request.session["tiktok_error"] = i18n.t("servers.snapchat_oauth_missing", lang)
            return _oauth_redirect(request, admin)
        request.session["snapchat_oauth_redirect_uri"] = ru
        state = snapchat_oauth.sign_connect_state(
            user_id=admin.id,
            link_name=link_name,
            redirect_uri_value=ru,
        )
        request.session["snapchat_oauth_state"] = state
        request.session["snapchat_oauth_user_id"] = admin.id
        url = snapchat_oauth.build_authorize_url(state=state, redirect_uri_value=ru)
    return RedirectResponse(url=url, status_code=303)


@app.api_route(
    "/oauth/snapchat/callback",
    methods=["GET", "POST"],
    name="snapchat_oauth_callback",
)
async def snapchat_oauth_callback(request: Request):
    lang = i18n.resolve_lang(request)
    params = await _oauth_callback_params(request)
    state = (params.get("state") or "").strip()
    packed = snapchat_oauth.read_connect_state(state)
    _oauth_debug_log(
        "snapchat",
        "callback recibido: method=%s code=%s state=%s packed=%s error=%s"
        % (
            request.method,
            "si" if params.get("code") else "no",
            "si" if state else "no",
            "ok" if packed else "invalido",
            params.get("error") or "-",
        ),
    )
    try:
        admin = require_admin_privileges(request)
    except PermissionError:
        admin = None
        if packed and packed.get("user_id"):
            admin = db.get_user_by_id(packed["user_id"])
            if admin and not db.user_has_admin_privileges(admin):
                admin = None
        if not admin:
            _oauth_debug_log(
                "snapchat", "callback sin sesion y sin usuario del estado -> login"
            )
            return _admin_privileges_redirect_login(request)
        _oauth_debug_log(
            "snapchat", f"sesion perdida; usuario recuperado del estado: {admin.username}"
        )
    _keep_oauth_login(request, admin)
    saved_state = request.session.get("snapchat_oauth_state")
    linked_by = request.session.get("snapchat_oauth_user_id") or (
        packed.get("user_id") if packed else None
    )
    err_param = (params.get("error") or "").strip()
    if err_param:
        desc = params.get("error_description") or err_param
        _oauth_debug_log("snapchat", f"snapchat devolvio error: {desc[:200]}")
        request.session["tiktok_error"] = f"Snapchat: {desc}"
        return _oauth_redirect(request, admin)
    if packed:
        ok_state = True
    else:
        ok_state = bool(saved_state and state == saved_state)
    if not ok_state:
        _oauth_debug_log("snapchat", "estado invalido (firma/sesion no coinciden)")
        request.session["tiktok_error"] = i18n.t("servers.oauth_state_invalid", lang)
        return _oauth_redirect(request, admin)
    code = (params.get("code") or "").strip()
    if not code:
        _oauth_debug_log("snapchat", "callback sin authorization code")
        request.session["tiktok_error"] = i18n.t("servers.snapchat_no_code", lang)
        return _oauth_redirect(request, admin)
    link_name = (packed or {}).get("link_name") or str(
        request.session.get("oauth_link_target_name") or ""
    ).strip()
    ru = (packed or {}).get("redirect_uri") or _pop_oauth_redirect(
        request, "snapchat_oauth_redirect_uri", snapchat_oauth
    )
    try:
        with db.using_credentials_account(link_name):
            token_data = snapchat_oauth.exchange_code_for_tokens(
                code, redirect_uri_value=ru
            )
            access = str(token_data.get("access_token") or "").strip()
            refresh = str(token_data.get("refresh_token") or "").strip() or None
            expires_in = token_data.get("expires_in")
            if not access:
                raise ValueError("No access token in Snapchat response.")
            _oauth_debug_log(
                "snapchat",
                "tokens OK (refresh=%s); consultando perfil publico..."
                % ("si" if refresh else "no"),
            )
            profile = snapchat_oauth.fetch_profile(access)
            client_id_val = snapchat_oauth.client_id()
            client_secret_val = snapchat_oauth.client_secret()
        open_id = profile.get("open_id") or ""
        if not open_id:
            raise ValueError("snapchat_no_profile")
        _oauth_debug_log(
            "snapchat",
            f"perfil OK: {profile.get('username') or profile.get('display_name') or open_id}",
        )
        cid = db.save_oauth_connection(
            platform_id="snapchat",
            open_id=str(open_id),
            username=profile.get("username"),
            display_name=profile.get("display_name"),
            access_token=access,
            refresh_token=refresh,
            expires_in=int(expires_in) if expires_in is not None else 3600,
            scopes=snapchat_oauth.oauth_scopes(),
            client_id=client_id_val,
            client_secret=client_secret_val,
            redirect_uri=ru,
            linked_by_user_id=str(linked_by) if linked_by else None,
        )
        if link_name:
            db.bind_oauth_account_name(cid, link_name)
        else:
            _bind_oauth_link_target(request, cid)
        request.session.pop("snapchat_oauth_state", None)
        request.session.pop("snapchat_oauth_user_id", None)
        request.session.pop("oauth_link_target_name", None)
        label = profile.get("username") or profile.get("display_name") or "Snapchat"
        _oauth_debug_log(
            "snapchat", f"conexion guardada: cuenta='{link_name or '-'}' perfil='{label}'"
        )
        request.session["tiktok_ok"] = i18n.t("servers.snapchat_connected", lang, name=label)
    except (ValueError, urllib.error.URLError, OSError) as e:
        code_err = str(e)
        _oauth_debug_log("snapchat", f"FALLO: {code_err[:300]}")
        if code_err in ("snapchat_no_profile", "snapchat_need_allowlist"):
            request.session["tiktok_error"] = i18n.t(f"servers.{code_err}", lang)
        else:
            request.session["tiktok_error"] = i18n.t(
                "api.snapchat.fail", lang, error=code_err[:180]
            )
    return _oauth_redirect(request, admin)


@app.delete("/admin/api/oauth/{account_id}")
def api_oauth_delete(request: Request, account_id: str):
    try:
        me = require_admin_privileges(request)
    except PermissionError as e:
        if str(e) == "login_required":
            return JSONResponse(
                {"ok": False, "error": "Sign in required."},
                status_code=401,
            )
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    if not db.user_can_manage_oauth_account(me, account_id):
        return JSONResponse({"ok": False, "error": "Permission denied."}, status_code=403)
    row = db.get_oauth_account_row(account_id)
    if row:
        _revoke_oauth_remote(row)
    try:
        db.delete_oauth_account(account_id)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=404)
    return {"ok": True, "message": "Account disconnected."}


@app.post("/admin/api/vmos")
def api_vmos_save(request: Request, body: VmosAccountBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        row = db.upsert_vmos_account(
            account_id=body.id,
            platform_id=body.platform_id,
            name=body.name,
            access_key=body.access_key,
            secret_key=body.secret_key,
            pad_code=body.pad_code,
            template_id=body.template_id,
            remark=body.remark,
            link_name=body.link_name,
        )
    except ValueError as e:
        code = str(e)
        if code == "missing_fields":
            return JSONResponse(
                {"ok": False, "error": i18n.t("servers.vmos_missing", lang)},
                status_code=400,
            )
        if code == "unknown_platform":
            return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=404)
    return {"ok": True, "account": row, "message": i18n.t("servers.vmos_saved", lang)}


@app.post("/admin/api/vmos/test")
def api_vmos_test(request: Request, body: VmosAccountBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    ak = (body.access_key or "").strip()
    sk = (body.secret_key or "").strip()
    pad = (body.pad_code or "").strip()
    if sk in ("unchanged", "x" * 19):
        sk = ""
    if body.id and (not sk or not ak):
        raw = db.get_vmos_account_raw(body.id)
        if raw:
            ak = ak or str(raw.get("access_key") or "")
            sk = sk or str(raw.get("secret_key") or "")
            pad = pad or str(raw.get("pad_code") or "")
    if not ak or not sk or not pad:
        return JSONResponse(
            {"ok": False, "error": i18n.t("servers.vmos_missing", lang)},
            status_code=400,
        )
    try:
        data = vmos.pad_info(ak, sk, pad, lang=lang)
    except vmos.VmosError as e:
        return JSONResponse({"ok": False, "error": str(e)[:300]}, status_code=400)
    info = data.get("data") if isinstance(data.get("data"), dict) else {}
    shown = str((info or {}).get("padCode") or pad).strip()
    return {"ok": True, "message": i18n.t("servers.vmos_test_ok", lang, pad=shown)}


@app.delete("/admin/api/vmos/{account_id}")
def api_vmos_delete(request: Request, account_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    try:
        db.delete_vmos_account(account_id)
    except ValueError:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True}


@app.post("/admin/api/filehost")
def api_filehost_save(request: Request, body: FilehostAccountBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    pid = (body.platform_id or "").strip()
    key = (body.api_key or "").strip()
    extra = (body.extra or "").strip()
    if key in ("unchanged", "x" * 19):
        key = ""
    if body.id and not key:
        raw = db.get_filehost_account_raw(body.id)
        if raw:
            key = key or str(raw.get("api_key") or "")
            extra = extra or str(raw.get("extra") or "")
    ok, detail = filehost.probe_account(pid, key, extra)
    if not ok:
        return JSONResponse(
            {
                "ok": False,
                "error": i18n.t("api.filehost.fail", lang, error=detail),
            },
            status_code=400,
        )
    try:
        row = db.upsert_filehost_account(
            account_id=body.id,
            platform_id=pid,
            name=body.name or detail,
            api_key=body.api_key,
            extra=extra,
            link_name=body.link_name,
        )
    except ValueError as e:
        code = str(e)
        if code == "missing_fields":
            return JSONResponse(
                {"ok": False, "error": i18n.t("servers.filehost_missing", lang)},
                status_code=400,
            )
        if code == "unknown_platform":
            return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=404)
    return {
        "ok": True,
        "account": row,
        "message": i18n.t("servers.filehost_saved", lang, name=detail),
    }


@app.post("/admin/api/filehost/test")
def api_filehost_test(request: Request, body: FilehostAccountBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    key = (body.api_key or "").strip()
    extra = (body.extra or "").strip()
    if key in ("unchanged", "x" * 19):
        key = ""
    if body.id and not key:
        raw = db.get_filehost_account_raw(body.id)
        if raw:
            key = key or str(raw.get("api_key") or "")
            extra = extra or str(raw.get("extra") or "")
    ok, detail = filehost.probe_account(body.platform_id, key, extra)
    if not ok:
        return JSONResponse(
            {"ok": False, "error": i18n.t("api.filehost.fail", lang, error=detail)},
            status_code=400,
        )
    return {"ok": True, "message": i18n.t("api.filehost.ok", lang, name=detail)}


@app.delete("/admin/api/filehost/{account_id}")
def api_filehost_delete(request: Request, account_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    try:
        db.delete_filehost_account(account_id)
    except ValueError:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True}


def _chain_fail_error(lang: str, platform_id: str, detail: str) -> str:
    pid = (platform_id or "").strip()
    msg = (detail or "").strip()
    low = msg.lower()
    if pid == "bilibili_tv":
        key = {
            "email_password_required": "servers.chain_missing",
            "missing_fields": "servers.chain_missing",
            "playwright_missing": "bilibili_tv.err_playwright",
            "website_changed": "bilibili_tv.err_website",
            "captcha": "bilibili_tv.err_captcha",
            "session_dead": "bilibili_tv.err_session",
            "login_failed": "bilibili_tv.err_login",
            "browser_busy": "bilibili_tv.err_busy",
            "browser_error": "bilibili_tv.err_browser",
            "need_saved_account": "servers.chain_missing",
        }.get(msg)
        if key:
            return i18n.t(key, lang)
        return i18n.t("api.chain.fail", lang, error=msg or "error")
    if pid != "odysee":
        return i18n.t("api.chain.fail", lang, error=msg or "error")
    if msg in {"email_password_required", "missing_fields"}:
        return i18n.t("servers.chain_missing", lang)
    if "authentication required" in low or "signin_not_logged_in" in low:
        return i18n.t("odysee.err_auth", lang)
    if "invalid application" in low or "app_id" in low:
        return i18n.t("odysee.err_app_id", lang)
    if "2fa" in low:
        return i18n.t("odysee.err_2fa", lang)
    if "email_unverified" in low or "unverified" in low:
        return i18n.t("odysee.err_unverified", lang)
    if "recaptcha" in low:
        return i18n.t("odysee.err_recaptcha", lang)
    if "user not found" in low or "does not exist" in low:
        return i18n.t("odysee.err_user", lang)
    if "password" in low and "email_password_required" not in low:
        return i18n.t("odysee.err_password", lang)
    return i18n.t("odysee.err_generic", lang, error=msg[:140] or "error")


@app.post("/admin/api/chain")
def api_chain_save(request: Request, body: ChainAccountBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    pid = (body.platform_id or "").strip()
    if not platforms.is_ui_visible(pid):
        return JSONResponse(
            {"ok": False, "error": i18n.t("servers.platform_unavailable", lang)},
            status_code=403,
        )
    login = (body.login or "").strip()
    secret = (body.secret or "").strip()
    extra = (body.extra or "").strip()
    if body.id:
        raw = db.get_chain_account_raw(body.id)
        if raw:
            login = login or str(raw.get("login") or "")
            secret = secret or str(raw.get("secret") or "")
            extra = extra or str(raw.get("extra") or "")
    if pid == "odysee" and extra:
        extra = odysee.normalize_channel_id(extra) or extra
    if pid == "bilibili_tv":
        import bilibili_tv

        ready, err = bilibili_tv.playwright_ready()
        if not ready:
            return JSONResponse(
                {"ok": False, "error": _chain_fail_error(lang, pid, err)},
                status_code=400,
            )
        try:
            row = db.upsert_chain_account(
                account_id=body.id,
                platform_id=pid,
                name=body.name or login,
                login=login,
                secret=body.secret,
                extra="",
                link_name=body.link_name,
            )
        except ValueError as e:
            code = str(e)
            if code == "missing_fields":
                return JSONResponse(
                    {"ok": False, "error": i18n.t("servers.chain_missing", lang)},
                    status_code=400,
                )
            if code == "unknown_platform":
                return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
            return JSONResponse({"ok": False, "error": str(e)}, status_code=404)
        stored = db.get_chain_account_raw(str(row.get("id") or "")) or {}
        probe_secret = secret
        if probe_secret in ("unchanged", "x" * 19) or not probe_secret:
            probe_secret = str(stored.get("secret") or "")
        ok, detail = chain.probe_account(
            pid, login, probe_secret, "", account_id=str(row.get("id") or "")
        )
        now = datetime.now(timezone.utc).isoformat()
        prev_ok = str(stored.get("last_ok_at") or "")
        next_at = ""
        if ok or str(detail or "") == "captcha":
            next_at = bilibili_tv.pick_next_keepalive(
                except_id=str(row.get("id") or "")
            )
        db.update_chain_browser_session(
            str(row.get("id") or ""),
            session_ok=ok,
            last_ok_at=now if ok else prev_ok,
            last_error="" if ok else str(detail or ""),
            next_keepalive_at=next_at or None,
        )
        if ok:
            return {
                "ok": True,
                "account": row,
                "message": i18n.t("servers.chain_saved", lang, name=detail or login),
            }
        if str(detail or "") == "captcha":
            return {
                "ok": True,
                "account": row,
                "message": i18n.t("bilibili_tv.saved_captcha", lang),
            }
        return JSONResponse(
            {"ok": False, "error": _chain_fail_error(lang, pid, detail)},
            status_code=400,
        )
    ok, detail = chain.probe_account(pid, login, secret, extra)
    unverified = pid == "odysee" and (
        "email_unverified" in str(detail or "").lower()
        or "unverified" in str(detail or "").lower()
    )
    if not ok and not unverified:
        return JSONResponse(
            {
                "ok": False,
                "error": _chain_fail_error(lang, pid, detail),
            },
            status_code=400,
        )
    try:
        row = db.upsert_chain_account(
            account_id=body.id,
            platform_id=pid,
            name=body.name or (detail if ok else login),
            login=login,
            secret=body.secret,
            extra=extra,
            link_name=body.link_name,
        )
    except ValueError as e:
        code = str(e)
        if code == "missing_fields":
            return JSONResponse(
                {"ok": False, "error": i18n.t("servers.chain_missing", lang)},
                status_code=400,
            )
        if code == "unknown_platform":
            return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=404)
    return {
        "ok": True,
        "account": row,
        "message": i18n.t("servers.chain_saved", lang, name=detail if ok else login),
    }


@app.post("/admin/api/chain/test")
def api_chain_test(request: Request, body: ChainAccountBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    pid = (body.platform_id or "").strip()
    if not platforms.is_ui_visible(pid):
        return JSONResponse(
            {"ok": False, "error": i18n.t("servers.platform_unavailable", lang)},
            status_code=403,
        )
    login = (body.login or "").strip()
    secret = (body.secret or "").strip()
    extra = (body.extra or "").strip()
    if secret in ("unchanged", "x" * 19):
        secret = ""
    if body.id and (not login or not secret):
        raw = db.get_chain_account_raw(body.id)
        if raw:
            login = login or str(raw.get("login") or "")
            secret = secret or str(raw.get("secret") or "")
            extra = extra or str(raw.get("extra") or "")
    ok, detail = chain.probe_account(
        body.platform_id,
        login,
        secret,
        extra,
        account_id=body.id or "",
    )
    if not ok:
        return JSONResponse(
            {"ok": False, "error": _chain_fail_error(lang, body.platform_id, detail)},
            status_code=400,
        )
    return {"ok": True, "message": i18n.t("api.chain.ok", lang, name=detail)}


def _bilibili_qr_error(lang: str, detail: str) -> str:
    key = {
        "need_account_name": "servers.bilibili_qr_need_name",
        "missing_fields": "servers.bilibili_qr_need_name",
        "not_found": "servers.disconnect_error",
        "playwright_missing": "bilibili_tv.err_playwright",
        "website_changed": "bilibili_qr.err_website",
        "captcha": "bilibili_qr.err_captcha",
        "session_dead": "bilibili_qr.err_session",
        "browser_busy": "bilibili_qr.err_busy",
        "browser_error": "bilibili_qr.err_browser",
        "expired": "bilibili_qr.err_expired",
        "cancelled": "bilibili_qr.err_cancelled",
    }.get((detail or "").strip())
    if key:
        return i18n.t(key, lang)
    return i18n.t("bilibili_qr.err_browser", lang)


@app.post("/admin/api/bilibili/qr/start")
def api_bilibili_qr_start(request: Request, body: BilibiliQrStartBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    import bilibili_web

    result = bilibili_web.start_qr_login(
        link_name=(body.link_name or "").strip(),
        account_id=(body.account_id or "").strip(),
    )
    if not result.get("ok"):
        return JSONResponse(
            {"ok": False, "error": _bilibili_qr_error(lang, str(result.get("error") or ""))},
            status_code=400,
        )
    return {
        "ok": True,
        "job_id": result.get("job_id"),
        "account_id": result.get("account_id"),
        "qr_png": result.get("qr_png") or "",
    }


@app.get("/admin/api/bilibili/qr/{job_id}")
def api_bilibili_qr_status(request: Request, job_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    import bilibili_web

    job = bilibili_web.get_qr_job(job_id)
    if not job:
        return JSONResponse(
            {"ok": False, "error": i18n.t("bilibili_qr.err_expired", lang)},
            status_code=404,
        )
    status = str(job.get("status") or "")
    err = str(job.get("error") or "")
    out = {
        "ok": True,
        "status": status,
        "qr_png": job.get("qr_png") or "",
        "nickname": job.get("nickname") or "",
        "account_id": job.get("account_id") or "",
    }
    if status in {"ok"}:
        nick = str(job.get("nickname") or "").strip()
        out["message"] = i18n.t(
            "bilibili_qr.connected",
            lang,
            name=f" ({nick})" if nick else "",
        )
    elif status in {"expired", "captcha", "website_changed", "browser_error", "browser_busy", "cancelled"} or (
        err and status not in {"starting", "waiting", "scanned"}
    ):
        out["ok"] = False
        out["error"] = _bilibili_qr_error(lang, err or status)
    return out


@app.post("/admin/api/bilibili/qr/{job_id}/cancel")
def api_bilibili_qr_cancel(request: Request, job_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    import bilibili_web

    bilibili_web.cancel_qr_job(job_id)
    return {"ok": True}


@app.delete("/admin/api/chain/{account_id}")
def api_chain_delete(request: Request, account_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    try:
        db.delete_chain_account(account_id)
    except ValueError:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True}


@app.get("/admin/config-x", name="admin_config_x")
def admin_config_x(request: Request):
    try:
        admin = require_server_admin(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
    lang = i18n.resolve_lang(request)
    sources = db.list_x_funding_sources()
    source_oauth_ids = {s["oauth_account_id"] for s in sources}
    x_accounts = db.list_oauth_accounts_public("x")
    checks = db.list_x_monetize_checks()
    rows = []
    for acc in x_accounts:
        oid = str(acc.get("id") or "")
        chk = checks.get(oid) or {}
        rows.append(
            {
                "id": oid,
                "name": acc.get("name")
                or (f"@{acc.get('username')}" if acc.get("username") else oid[:8]),
                "username": acc.get("username") or "",
                "is_source": oid in source_oauth_ids,
                "followers": chk.get("followers"),
                "posts_count": chk.get("posts_count"),
                "meets": chk.get("meets"),
                "detail": chk.get("detail") or "",
                "checked_at": chk.get("checked_at") or "",
            }
        )
    return _render(
        request,
        "admin_config_x.html",
        {
            "user": admin,
            "nav_active": "config_x",
            "sources": sources,
            "x_accounts": rows,
            "min_followers": x_funding.min_followers(),
            "last_check": (db.get_app_setting(x_funding.LAST_CHECK_KEY) or ""),
        },
    )


class XFundingSourceBody(BaseModel):
    oauth_account_id: str = ""
    active: bool = True


class XFundingSettingsBody(BaseModel):
    min_followers: int = 0


@app.post("/admin/api/xconfig/source")
def api_xconfig_source_save(request: Request, body: XFundingSourceBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        src = db.upsert_x_funding_source(
            oauth_account_id=body.oauth_account_id,
            active=bool(body.active),
        )
    except ValueError:
        return JSONResponse(
            {"ok": False, "error": i18n.t("configx.err.account_not_found", lang)},
            status_code=400,
        )
    return {"ok": True, "source": src, "message": i18n.t("configx.saved", lang)}


@app.delete("/admin/api/xconfig/source/{source_id}")
def api_xconfig_source_delete(request: Request, source_id: str):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    try:
        db.delete_x_funding_source(source_id)
    except ValueError:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return {"ok": True}


@app.post("/admin/api/xconfig/settings")
def api_xconfig_settings(request: Request, body: XFundingSettingsBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    if body.min_followers <= 0:
        return JSONResponse(
            {"ok": False, "error": i18n.t("configx.err.bad_amount", lang)}, status_code=400
        )
    x_funding.set_min_followers(body.min_followers)
    return {"ok": True, "message": i18n.t("configx.saved", lang)}


@app.post("/admin/api/xconfig/check")
def api_xconfig_check(request: Request):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    results = x_funding.run_check_now()
    meets = sum(1 for r in results if r.get("meets"))
    return {
        "ok": True,
        "results": results,
        "message": i18n.t("configx.check_done", lang, n=len(results), meets=meets),
    }


@app.get("/admin/api/platforms/{platform_id}/credentials")
def api_get_platform_credentials(request: Request, platform_id: str, account: str = ""):
    deny = _require_platform_credentials_json(request, platform_id)
    if deny:
        return deny
    if platform_id not in platforms.PLATFORM_IDS:
        return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
    label = (account or "").strip()
    if label:
        db.set_credentials_account_name(label)
    return {"ok": True, **db.get_platform_credentials_editor(platform_id)}


@app.post("/admin/api/platforms/{platform_id}/credentials")
def api_save_platform_credentials(request: Request, platform_id: str, body: PlatformApiBody):
    deny = _require_platform_credentials_json(request, platform_id)
    if deny:
        return deny
    if platform_id not in platforms.PLATFORM_IDS:
        return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
    lang = i18n.resolve_lang(request)
    user = require_admin_privileges(request)
    db.set_credentials_account_name((body.name or "").strip())
    try:
        public = db.upsert_platform_credentials(
            platform_id,
            name=body.name,
            client_id=body.client_id,
            client_secret=body.client_secret,
            access_token=body.access_token,
            extra=body.extra,
            owner_user_id=user.id if db.user_can_manage_panel_accounts(user) else None,
            use_own_x_api=body.use_own_x_api if platform_id == "x" else None,
        )
    except ValueError as e:
        code = str(e)
        if code == "x_own_api_needs_keys":
            return JSONResponse(
                {"ok": False, "error": i18n.t("servers.x_own_api_needs_keys", lang)},
                status_code=400,
            )
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(code, lang)},
            status_code=400,
        )
    editor = db.get_platform_credentials_editor(platform_id)
    msg_key = "api.cleared" if not editor.get("configured") else "api.saved"
    return {"ok": True, "message": i18n.t(msg_key, lang), **editor}


@app.delete("/admin/api/platforms/{platform_id}/credentials")
def api_clear_platform_credentials(request: Request, platform_id: str, account: str = ""):
    deny = _require_platform_credentials_json(request, platform_id)
    if deny:
        return deny
    if platform_id not in platforms.PLATFORM_IDS:
        return JSONResponse({"ok": False, "error": "Unknown platform."}, status_code=404)
    lang = i18n.resolve_lang(request)
    label = (account or "").strip()
    if label:
        db.set_credentials_account_name(label)
    public = db.clear_platform_credentials(platform_id)
    return {"ok": True, "message": i18n.t("api.cleared", lang), **public}


@app.post("/admin/api/platforms/{platform_id}/test")
def api_test_platform(request: Request, platform_id: str, body: PlatformApiBody):
    deny = _require_platform_credentials_json(request, platform_id)
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
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    results = platform_api.test_all_platforms(lang)
    return {"ok": True, "results": results}


def _server_account_error_message(code: str, lang: str) -> str:
    keys = {
        "name_required": "servers.accounts_name_required",
        "platform_required": "servers.accounts_platform_required",
        "not_found": "servers.accounts_not_found",
        "save_fail": "servers.accounts_save_fail",
        "name_taken": "servers.accounts_name_taken",
        "link_name_taken": "servers.accounts_link_name_taken",
    }
    return i18n.t(keys.get(code, "servers.network_error"), lang)


@app.post("/admin/api/server-account-links")
def api_create_account_link(request: Request, body: AccountLinkBody):
    deny = _require_server_admin_json(request)
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
    }


@app.put("/admin/api/server-account-links/{link_id}")
def api_rename_account_link(request: Request, link_id: str, body: AccountLinkBody):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    try:
        group = db.rename_account_link(link_id, body.name, lang=lang)
    except ValueError as e:
        code = str(e)
        status = 404 if code == "not_found" else 400
        return JSONResponse(
            {"ok": False, "error": _server_account_error_message(code, lang)},
            status_code=status,
        )
    return {
        "ok": True,
        "group": group,
        "message": i18n.t("servers.accounts_saved", lang),
    }


@app.delete("/admin/api/server-account-links/{link_id}")
def api_delete_account_link(request: Request, link_id: str):
    deny = _require_server_admin_json(request)
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
    }


@app.post("/admin/api/server-account-links/{link_id}/active")
def api_set_account_link_active(
    request: Request, link_id: str, body: AccountLinkActiveBody
):
    deny = _require_server_admin_json(request)
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
    }


@app.get("/admin/api/server-accounts")
def api_list_server_accounts(request: Request):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    lang = i18n.resolve_lang(request)
    accounts = db.list_server_accounts(lang)
    return {
        "ok": True,
        "accounts": accounts,
    }


@app.get("/admin/api/server-account-groups")
def api_list_server_account_groups(
    request: Request, q: str = "", page: int = 1, per_page: str = "10"
):
    deny = _require_server_admin_json(request)
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
    deny = _require_server_admin_json(request)
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
    }


@app.put("/admin/api/server-accounts/{account_id}")
def api_update_server_account(request: Request, account_id: str, body: ServerAccountBody):
    deny = _require_server_admin_json(request)
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
    }


@app.post("/admin/api/server-accounts/{account_id}/active")
def api_set_server_account_active(
    request: Request, account_id: str, body: ServerAccountActiveBody
):
    deny = _require_server_admin_json(request)
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
    }


@app.delete("/admin/api/server-accounts/{account_id}")
def api_delete_server_account(request: Request, account_id: str):
    deny = _require_server_admin_json(request)
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
    }


@app.get("/admin/api/equipo/cuentas")
def api_equipo_cuentas(request: Request, q: str = "", selected: str = ""):
    deny = _require_server_admin_json(request)
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
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    me = require_server_admin(request)
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
    invites = db.invite_info_map([u.id for u in users])
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
                "created_at": u.created_at,
                "invite_code": (invites.get(u.id) or {}).get("code") or "",
                "linked_tiktok_config_id": u.linked_tiktok_config_id or "",
                "linked_account_link_ids": db.list_user_account_link_ids(u.id),
                "can_manage": db.user_can_manage_member(me, u),
                "wallet_balance_usd": int(getattr(u, "wallet_balance_usd", 0) or 0),
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
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    me = require_server_admin(request)
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
    user_mode: Annotated[str, Form()] = "publisher",
):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    me = require_server_admin(request)
    lang = i18n.resolve_lang(request)
    if db.user_is_tiktok_mode(me) and user_mode.strip().lower() == "admin":
        return JSONResponse(
            {"ok": False, "error": _equipo_user_form_error("Invalid user mode", lang)},
            status_code=403,
        )
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
    user_mode: Annotated[str, Form()] = "publisher",
):
    deny = _require_server_admin_json(request)
    if deny:
        return deny
    me = require_server_admin(request)
    target = db.get_user_by_id(user_id)
    if not target or target.role == "admin":
        return JSONResponse(
            {"ok": False, "error": "You cannot edit that user."},
            status_code=400,
        )
    pw = password.strip()
    u = username.strip()
    lang = i18n.resolve_lang(request)
    if db.user_is_tiktok_mode(me) and user_mode.strip().lower() == "admin":
        return JSONResponse(
            {"ok": False, "error": _equipo_user_form_error("Invalid user mode", lang)},
            status_code=403,
        )
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
        me = require_server_admin(request)
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
    user_mode: Annotated[str, Form()] = "publisher",
    linked_tiktok_config_id: Annotated[str, Form()] = "",
    can_view_comments: Annotated[str, Form()] = "1",
):
    try:
        require_server_admin(request)
    except PermissionError:
        return _admin_privileges_redirect_login(request)
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


# ---------------------------------------------------------------------------
# Archivos de verificación de dominio (TikTok, Google, Meta…)
# Coloca en la carpeta `verification/` el archivo de firma que te dé la
# plataforma (p. ej. tiktokXXXX.txt) y quedará servido en la raíz del sitio.
# Debe registrarse al final: solo captura rutas de un segmento no usadas.
# ---------------------------------------------------------------------------
VERIFICATION_DIR = BASE_DIR / "verification"
_VERIFICATION_EXT = {".txt", ".html", ".json", ".xml"}


@app.get("/{verification_file}", include_in_schema=False)
def serve_verification_file(verification_file: str):
    name = os.path.basename((verification_file or "").strip())
    if (
        not name
        or name.startswith(".")
        or Path(name).suffix.lower() not in _VERIFICATION_EXT
    ):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    path = VERIFICATION_DIR / name
    if not path.is_file():
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    media = {
        ".txt": "text/plain",
        ".html": "text/html",
        ".json": "application/json",
        ".xml": "application/xml",
    }[Path(name).suffix.lower()]
    return FileResponse(path, media_type=media)
