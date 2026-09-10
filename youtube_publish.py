"""Subida real a YouTube (Data API v3). Videos cortos → Shorts; largos → video normal."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import db
import video_probe

UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SHORTS_MAX_SECONDS = 180.0
TITLE_MAX = 100
MIME = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".m4v": "video/mp4",
}


def _privacy() -> str:
    raw = (os.environ.get("YOUTUBE_PRIVACY_STATUS") or "public").strip().lower()
    return raw if raw in ("public", "unlisted", "private") else "public"


def _parse_extra(extra: str) -> dict[str, str]:
    s = (extra or "").strip()
    out = {"api_key": "", "refresh_token": ""}
    if not s:
        return out
    if s.startswith("{"):
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            return out
        if isinstance(data, dict):
            out["api_key"] = str(data.get("api_key") or data.get("key") or "").strip()
            out["refresh_token"] = str(data.get("refresh_token") or "").strip()
        return out
    if s.startswith("1/") or s.startswith("1//"):
        out["refresh_token"] = s
    else:
        out["api_key"] = s
    return out


def _google_error(raw: str, fallback: str) -> str:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}
    err = data.get("error") if isinstance(data, dict) else None
    if isinstance(err, dict):
        msg = err.get("message") or ""
        errors = err.get("errors") or []
        if errors and isinstance(errors[0], dict):
            msg = errors[0].get("message") or msg
        if msg:
            return str(msg)[:220]
    if isinstance(err, str) and err:
        desc = data.get("error_description") if isinstance(data, dict) else ""
        return f"{err}: {desc}".strip(": ")[:220]
    return (fallback or raw or "YouTube API error")[:220]


def _refresh_oauth_row(row: dict[str, Any]) -> str:
    import youtube_oauth

    refresh = str(row.get("refresh_token") or "").strip()
    if not refresh:
        raise ValueError("missing_token")
    data = youtube_oauth.refresh_access_token(
        refresh,
        client_id_value=str(row.get("client_id") or ""),
        client_secret_value=str(row.get("client_secret") or ""),
    )
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("YouTube did not return an access token.")
    new_refresh = str(data.get("refresh_token") or "").strip() or None
    expires_in = data.get("expires_in")
    db.update_oauth_tokens(
        str(row["id"]),
        access_token=token,
        refresh_token=new_refresh,
        expires_in=int(expires_in) if expires_in is not None else None,
    )
    return token


def _refresh_legacy_token(raw: dict[str, Any]) -> str | None:
    extra = _parse_extra(str(raw.get("extra") or ""))
    refresh = extra.get("refresh_token") or ""
    client_id = str(raw.get("client_id") or "").strip()
    secret = str(raw.get("client_secret") or "").strip()
    if not (refresh and client_id and secret):
        return None
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": secret,
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        raise ValueError(_google_error(e.read().decode("utf-8", errors="replace"), str(e))) from e
    token = str(data.get("access_token") or "").strip()
    if not token:
        raise ValueError("YouTube did not return an access token.")
    db.upsert_platform_credentials("youtube", access_token=token)
    return token


def _access_from_oauth(row: dict[str, Any], *, force_refresh: bool = False) -> str:
    token = str(row.get("access_token") or "").strip()
    if token and not force_refresh:
        return token
    return _refresh_oauth_row(row)


def _access_from_legacy(raw: dict[str, Any], *, force_refresh: bool = False) -> str:
    token = str(raw.get("access_token") or "").strip()
    if token and not force_refresh:
        return token
    refreshed = _refresh_legacy_token(raw)
    if refreshed:
        return refreshed
    if token:
        return token
    raise ValueError("missing_token")


def _resolve_auth(account_link_id: str | None) -> tuple[str, dict[str, Any]]:
    oid = db.resolve_oauth_account_id("youtube", account_link_id=account_link_id)
    if oid:
        row = db.get_oauth_account_row(oid)
        if row:
            return "oauth", row
    raw = db.get_platform_credentials_raw("youtube") or {}
    return "legacy", raw


def _shorts_title(title: str) -> str:
    base = str(title or "Video").strip() or "Video"
    if "shorts" in base.casefold():
        return base[:TITLE_MAX]
    tag = " #Shorts"
    room = TITLE_MAX - len(tag)
    return (base[:room].rstrip() + tag)[:TITLE_MAX]


def _regular_title(title: str) -> str:
    return (str(title or "Video").strip() or "Video")[:TITLE_MAX]


def _description(description: str, *, is_short: bool) -> str:
    text = str(description or "").strip()
    if is_short and "#shorts" not in text.casefold():
        text = f"{text}\n\n#Shorts".strip()
    return text[:4900]


def _init_resumable(token: str, *, mime: str, size: int, snippet: dict, status: dict) -> str:
    qs = urllib.parse.urlencode(
        {"uploadType": "resumable", "part": "snippet,status"}
    )
    payload = json.dumps({"snippet": snippet, "status": status}).encode("utf-8")
    req = urllib.request.Request(
        f"{UPLOAD_URL}?{qs}",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": mime,
            "X-Upload-Content-Length": str(size),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            loc = resp.headers.get("Location") or ""
            if not loc:
                raise ValueError("YouTube did not return an upload URL.")
            return loc
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        if e.code in (401, 403):
            raise ValueError(f"401 { _google_error(body, str(e)) }") from e
        raise ValueError(_google_error(body, str(e))) from e


def _put_file(upload_url: str, path: Path, mime: str, size: int) -> dict[str, Any]:
    with path.open("rb") as fh:
        data = fh.read()
    req = urllib.request.Request(
        upload_url,
        data=data,
        method="PUT",
        headers={
            "Content-Type": mime,
            "Content-Length": str(size),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        if e.code in (401, 403):
            raise ValueError(f"401 {_google_error(body, str(e))}") from e
        raise ValueError(_google_error(body, str(e))) from e
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}


def _video_status(token: str, video_id: str) -> dict[str, Any]:
    qs = urllib.parse.urlencode({"part": "status,processingDetails", "id": video_id})
    req = urllib.request.Request(
        f"{VIDEOS_URL}?{qs}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise ValueError(_google_error(body, str(e))) from e
    return data if isinstance(data, dict) else {}


def _watch_processing(
    *,
    token: str,
    video_id: str,
    lang: str,
    is_short: bool,
    requested_privacy: str,
) -> None:
    """YouTube aceptó la subida pero aún procesa/revisa. Vigila y cierra el estado."""
    import publish_pending

    payload = {
        "token": token,
        "video_id": video_id,
        "lang": lang,
        "is_short": bool(is_short),
        "requested_privacy": requested_privacy,
    }

    def _check() -> tuple[str, str]:
        return resume_pending(payload)

    publish_pending.mark(_check, platform="youtube", payload=payload)


def resume_pending(payload: dict[str, Any]) -> tuple[str, str]:
    from i18n import t

    token = str(payload.get("token") or "").strip()
    video_id = str(payload.get("video_id") or "").strip()
    lang = str(payload.get("lang") or "es")
    is_short = bool(payload.get("is_short"))
    requested_privacy = str(payload.get("requested_privacy") or "public")
    ok_key = "pub.youtube.shorts_ok" if is_short else "pub.youtube.video_ok"
    if not (token and video_id):
        return "fail", t("pub.youtube.no_token", lang)
    data = _video_status(token, video_id)
    items = data.get("items") or []
    if not items:
        return "fail", t(
            "pub.youtube.upload_fail", lang, error="video not found on channel"
        )
    st = items[0].get("status") or {}
    proc = items[0].get("processingDetails") or {}
    upload_status = str(st.get("uploadStatus") or "").lower()
    proc_status = str(proc.get("processingStatus") or "").lower()
    if upload_status in {"rejected", "failed"} or proc_status == "failed":
        reason = str(
            st.get("rejectionReason")
            or st.get("failureReason")
            or upload_status
            or proc_status
        )
        return "fail", t("pub.youtube.upload_fail", lang, error=reason[:180])
    if upload_status != "processed" and proc_status != "succeeded":
        return "pending", ""
    privacy = str(st.get("privacyStatus") or "").lower()
    if requested_privacy == "public" and privacy == "private":
        return "fail", t("pub.youtube.locked_private", lang, id=video_id)
    return "ok", t(ok_key, lang, id=video_id)


def publish_video(
    *,
    file_path: Path,
    title: str,
    description: str,
    lang: str,
    account_link_id: str | None = None,
) -> tuple[bool, str]:
    from i18n import explain_provider_error, t

    if Path(file_path).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return False, t("pub.youtube.no_photo", lang)

    kind, auth = _resolve_auth(account_link_id)
    path = Path(file_path)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.youtube.file_missing", lang)

    try:
        token = (
            _access_from_oauth(auth)
            if kind == "oauth"
            else _access_from_legacy(auth)
        )
    except ValueError:
        return False, t("pub.youtube.no_token", lang)

    meta = video_probe.probe_video(path)
    is_short = video_probe.is_youtube_short(meta, max_seconds=SHORTS_MAX_SECONDS)
    snippet = {
        "title": _shorts_title(title) if is_short else _regular_title(title),
        "description": _description(description, is_short=is_short),
        "categoryId": "22",
    }
    status = {
        "privacyStatus": _privacy(),
        "selfDeclaredMadeForKids": False,
    }
    mime = MIME.get(path.suffix.lower(), "video/mp4")
    size = path.stat().st_size

    def _send(access: str) -> dict[str, Any]:
        loc = _init_resumable(
            access, mime=mime, size=size, snippet=snippet, status=status
        )
        return _put_file(loc, path, mime, size)

    try:
        try:
            result = _send(token)
        except ValueError as e:
            msg = str(e).lower()
            if "auth" in msg or "token" in msg or "401" in msg or "invalid" in msg:
                kind, auth = _resolve_auth(account_link_id)
                token = (
                    _access_from_oauth(auth, force_refresh=True)
                    if kind == "oauth"
                    else _access_from_legacy(auth, force_refresh=True)
                )
                result = _send(token)
            else:
                raise
        video_id = str(result.get("id") or "").strip()
        upload_status = str(
            (result.get("status") or {}).get("uploadStatus") or ""
        ).lower()
        if video_id and upload_status != "processed":
            # YouTube aceptó el archivo pero sigue procesando/revisando.
            _watch_processing(
                token=token,
                video_id=video_id,
                lang=lang,
                is_short=is_short,
                requested_privacy=str(status.get("privacyStatus") or "public"),
            )
            return True, t("pub.youtube.pending", lang, id=video_id)
        if is_short:
            return True, t("pub.youtube.shorts_ok", lang, id=video_id or "ok")
        return True, t("pub.youtube.video_ok", lang, id=video_id or "ok")
    except ValueError as e:
        key = str(e)
        if key == "missing_token":
            return False, t("pub.youtube.no_token", lang)
        return False, t(
            "pub.youtube.upload_fail",
            lang,
            error=explain_provider_error("youtube", str(e), lang),
        )
    except Exception as e:
        return False, t(
            "pub.youtube.upload_fail",
            lang,
            error=explain_provider_error("youtube", str(e), lang),
        )
