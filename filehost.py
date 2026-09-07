"""Hosters PPV: subida real por API (8 sólidas + 4 de prueba de pago)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

UA = "Tuyaho/1.0 (file host upload)"
VIDEO_EXT = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".m4v"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

PLATFORM_IDS = frozenset(
    {
        "doodstream",
        "streamwish",
        "filemoon",
        "mixdrop",
        "streamtape",
        "voe",
        "vidoza",
        "lulustream",
        "loadvid",
        "vidsonic",
        "flyfile",
        "venvo",
    }
)

# Hosts más nuevos: en el panel salen como «(pago)» para probar si realmente pagan.
TRIAL_PAYOUT_IDS = frozenset({"loadvid", "vidsonic", "flyfile", "venvo"})

# extra_field: mixdrop=email, streamtape=login
HOSTS: dict[str, dict[str, Any]] = {
    "doodstream": {
        "kind": "dood",
        "info": "https://doodapi.co/api/account/info",
        "upload_server": "https://doodapi.co/api/upload/server",
        "form_key": "api_key",
        "watch": "https://dood.watch/d/{code}",
        "settings": "https://doodstream.com/settings",
    },
    "streamwish": {
        "kind": "dood",
        "info": "https://api.streamwish.com/api/account/info",
        "upload_server": "https://api.streamwish.com/api/upload/server",
        "form_key": "key",
        "title_field": "file_title",
        "descr_field": "file_descr",
        "watch": "https://streamwish.to/{code}",
    },
    "filemoon": {
        "kind": "dood",
        "info": "https://filemoonapi.com/api/account/info",
        "upload_server": "https://filemoonapi.com/api/upload/server",
        "form_key": "key",
        "watch": "https://filemoon.sx/e/{code}",
    },
    "voe": {
        "kind": "dood",
        "info": "https://voe.sx/api/account/info",
        "upload_server": "https://voe.sx/api/upload/server",
        "form_key": "key",
        "watch": "https://voe.sx/{code}",
    },
    "vidoza": {
        "kind": "dood",
        "info": "https://api.vidoza.net/api/account/info",
        "upload_server": "https://api.vidoza.net/api/upload/server",
        "form_key": "key",
        "title_field": "file_title",
        "watch": "https://vidoza.net/{code}",
    },
    "lulustream": {
        "kind": "dood",
        "info": "https://api.lulustream.com/api/account/info",
        "upload_server": "https://api.lulustream.com/api/upload/server",
        "form_key": "key",
        "title_field": "file_title",
        "descr_field": "file_descr",
        "watch": "https://lulustream.com/e/{code}",
    },
    "mixdrop": {
        "kind": "mixdrop",
        "info": "https://api.mixdrop.ag/accountinfo",
        "upload": "https://ul.mixdrop.ag/api",
        "extra_field": "email",
        "watch": "https://mixdrop.ag/e/{code}",
    },
    "streamtape": {
        "kind": "streamtape",
        "info": "https://api.streamtape.com/account/info",
        "upload_url": "https://api.streamtape.com/file/ul",
        "extra_field": "login",
        "watch": "https://streamtape.com/v/{code}",
    },
    "loadvid": {
        "kind": "loadvid",
        "info": "https://api.loadvid.com/v1/user/info",
        "upload_server": "https://api.loadvid.com/v1/upload/server",
        "form_key": "key",
        "watch": "https://www.loadvid.com/{code}",
    },
    "vidsonic": {
        "kind": "vidsonic",
        "info": "https://vidsonic.net/api/v1/account",
        "upload_server": "https://vidsonic.net/api/v1/getUploadSrv",
        "form_key": "apiKey",
        "file_field": "video",
        "watch": "https://vidsonic.net/{code}",
    },
    "flyfile": {
        "kind": "flyfile",
        "info": "https://api.flyfile.app/api/v1/account",
        "assign": "https://api.flyfile.app/api/v1/upload/assign",
        "init": "https://api.flyfile.app/api/v1/upload/init",
        "complete": "https://api.flyfile.app/api/v1/upload/complete",
        "watch": "https://flyfile.app/v/{code}",
    },
    "venvo": {
        "kind": "dood",
        "info": "https://venvo.net/api/account/info",
        "upload_server": "https://venvo.net/api/upload/server",
        "form_key": "key",
        "title_field": "file_title",
        "descr_field": "file_descr",
        "watch": "https://venvo.net/{code}",
    },
}


class FileHostError(ValueError):
    pass


def extra_field(platform_id: str) -> str:
    spec = HOSTS.get((platform_id or "").strip()) or {}
    return str(spec.get("extra_field") or "")


def settings_url(platform_id: str) -> str:
    spec = HOSTS.get((platform_id or "").strip()) or {}
    return str(spec.get("settings") or "").strip()


def _parse(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _ok_status(data: dict[str, Any]) -> bool:
    status = data.get("status")
    if status in (200, "200", True):
        return True
    if data.get("success") is True:
        return True
    result = data.get("result")
    if isinstance(data.get("result"), dict) and data.get("email"):
        return True
    if isinstance(result, dict) and (result.get("email") or result.get("balance") is not None):
        return True
    inner = data.get("data")
    if isinstance(inner, dict) and (inner.get("email") or inner.get("profit") is not None):
        return True
    if data.get("email") or data.get("uploadId") or data.get("server"):
        return True
    return False


def _err(data: dict[str, Any], raw: str = "") -> str:
    msg = str(
        data.get("msg")
        or data.get("message")
        or data.get("error")
        or (data.get("result") if isinstance(data.get("result"), str) else "")
        or raw
        or "API error"
    ).strip()
    return msg[:280]


def _get(
    url: str,
    params: dict[str, str] | None = None,
    *,
    timeout: int = 45,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    qs = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v})
    full = f"{url}?{qs}" if qs else url
    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(full, method="GET", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        data = _parse(raw)
        raise FileHostError(_err(data, raw or f"HTTP {e.code}")) from e
    except urllib.error.URLError as e:
        raise FileHostError(str(e.reason or e)[:280]) from e
    data = _parse(raw)
    if not data:
        raise FileHostError((raw or "empty")[:220])
    if not _ok_status(data) and status_fail(data):
        raise FileHostError(_err(data, raw))
    return data


def status_fail(data: dict[str, Any]) -> bool:
    status = data.get("status")
    if status in (400, 401, 403, 404, 422, 429, "400", "401", "403"):
        return True
    if data.get("success") is False:
        return True
    return False


def _multipart(fields: dict[str, str], files: list[tuple[str, str, str, bytes]]) -> tuple[bytes, str]:
    boundary = "----FileHost" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    for field, filename, ctype, raw in files:
        safe = filename.replace('"', "")
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field}"; filename="{safe}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(raw)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _post_multipart(
    url: str,
    fields: dict[str, str],
    files: list[tuple[str, str, str, bytes]],
    *,
    timeout: int = 300,
) -> dict[str, Any]:
    body, content_type = _multipart(fields, files)
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": content_type,
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        data = _parse(raw)
        raise FileHostError(_err(data, raw or f"HTTP {e.code}")) from e
    except urllib.error.URLError as e:
        raise FileHostError(str(e.reason or e)[:280]) from e
    data = _parse(raw)
    if not data:
        raise FileHostError((raw or "empty")[:220])
    if status_fail(data):
        raise FileHostError(_err(data, raw))
    return data


def _account_label(data: dict[str, Any]) -> str:
    result = data.get("result")
    if isinstance(result, dict):
        email = str(result.get("email") or result.get("login") or "").strip()
        if email:
            return email
        bal = result.get("balance")
        if bal is not None:
            return str(bal)
    inner = data.get("data")
    if isinstance(inner, dict):
        email = str(inner.get("email") or inner.get("login") or "").strip()
        if email:
            return email
    email = str(data.get("email") or "").strip()
    return email or "ok"


def _file_code(data: dict[str, Any]) -> str:
    result = data.get("result")
    if isinstance(result, list) and result:
        result = result[0]
    if isinstance(result, dict):
        for key in ("filecode", "file_code", "code", "fileref", "id", "uploadId"):
            val = str(result.get(key) or "").strip()
            if val:
                return val
        url = str(result.get("url") or result.get("download_url") or result.get("shareUrl") or "").strip()
        if url:
            return url
    url = ""
    files = data.get("files")
    if isinstance(files, list) and files and isinstance(files[0], dict):
        for key in ("filecode", "file_code", "fileref"):
            val = str(files[0].get(key) or "").strip()
            if val:
                return val
    inner = data.get("result")
    if isinstance(inner, str) and inner.startswith("http"):
        return inner
    nested = data.get("data")
    if isinstance(nested, dict):
        for key in ("id", "filecode", "file_code", "fileCode", "shareUrl", "shareToken"):
            val = str(nested.get(key) or "").strip()
            if val:
                return val
    for key in ("id", "fileCode", "shareUrl", "shareToken", "url"):
        val = str(data.get(key) or "").strip()
        if val:
            return val
    return "ok"


def probe_account(
    platform_id: str, api_key: str, extra: str = ""
) -> tuple[bool, str]:
    pid = (platform_id or "").strip()
    spec = HOSTS.get(pid)
    key = (api_key or "").strip()
    extra = (extra or "").strip()
    if not spec or not key:
        return False, "missing_key"
    kind = str(spec.get("kind") or "")
    try:
        if kind == "mixdrop":
            if not extra:
                return False, "missing_email"
            data = _get(str(spec["info"]), {"email": extra, "key": key})
        elif kind == "streamtape":
            if not extra:
                return False, "missing_login"
            data = _get(str(spec["info"]), {"login": extra, "key": key})
        elif kind == "flyfile":
            data = _get(str(spec["info"]), headers={"x-api-key": key})
        else:
            data = _get(str(spec["info"]), {"key": key})
        return True, _account_label(data)
    except FileHostError as e:
        return False, str(e)


def _upload_dood(
    spec: dict[str, Any],
    *,
    api_key: str,
    file_path: Path,
    title: str,
    description: str,
) -> str:
    server = _get(str(spec["upload_server"]), {"key": api_key})
    url = _upload_server_url(server)
    if not url:
        raise FileHostError("no upload server")
    form_key = str(spec.get("form_key") or "key")
    fields = {form_key: api_key}
    title_field = str(spec.get("title_field") or "")
    descr_field = str(spec.get("descr_field") or "")
    if title_field:
        fields[title_field] = (title or file_path.stem)[:200]
    if descr_field:
        fields[descr_field] = (description or "")[:2000]
    file_field = str(spec.get("file_field") or "file")
    sep = "&" if "?" in url else "?"
    post_url = f"{url}{sep}{urllib.parse.urlencode({form_key: api_key})}"
    data = _post_multipart(
        post_url,
        fields,
        [(file_field, file_path.name, "video/mp4", file_path.read_bytes())],
    )
    code = _file_code(data)
    watch = str(spec.get("watch") or "{code}")
    if code.startswith("http"):
        return code
    return watch.replace("{code}", code)


def _upload_server_url(data: dict[str, Any]) -> str:
    result = data.get("result")
    if isinstance(result, str) and result.strip():
        return result.strip()
    if isinstance(result, dict):
        url = str(result.get("url") or result.get("server") or "").strip()
        if url:
            return url
    return str(data.get("server") or data.get("url") or "").strip()


def _upload_mixdrop(spec: dict[str, Any], *, api_key: str, email: str, file_path: Path) -> str:
    data = _post_multipart(
        str(spec["upload"]),
        {"email": email, "key": api_key},
        [("file", file_path.name, "video/mp4", file_path.read_bytes())],
    )
    result = data.get("result")
    if isinstance(result, dict):
        fileref = str(result.get("fileref") or result.get("filecode") or "").strip()
        url = str(result.get("url") or "").strip()
        if url:
            return url
        if fileref:
            return str(spec.get("watch") or "").replace("{code}", fileref)
    code = _file_code(data)
    if code.startswith("http"):
        return code
    return str(spec.get("watch") or "").replace("{code}", code)


def _upload_streamtape(
    spec: dict[str, Any], *, api_key: str, login: str, file_path: Path
) -> str:
    data = _get(str(spec["upload_url"]), {"login": login, "key": api_key})
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    url = str((result or {}).get("url") or "").strip()
    if not url:
        raise FileHostError("no upload url")
    posted = _post_multipart(
        url,
        {},
        [("file", file_path.name, "video/mp4", file_path.read_bytes())],
    )
    code = _file_code(posted)
    inner = posted.get("result")
    if isinstance(inner, dict):
        link = str(inner.get("url") or inner.get("linkid") or "").strip()
        if link.startswith("http"):
            return link
        if link:
            return str(spec.get("watch") or "").replace("{code}", link)
    if code.startswith("http"):
        return code
    return str(spec.get("watch") or "").replace("{code}", code)


def _flyfile_headers(api_key: str) -> dict[str, str]:
    return {"x-api-key": api_key, "Accept": "application/json"}


def _post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    hdrs = {"User-Agent": UA, "Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=body, method="POST", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        data = _parse(raw)
        raise FileHostError(_err(data, raw or f"HTTP {e.code}")) from e
    except urllib.error.URLError as e:
        raise FileHostError(str(e.reason or e)[:280]) from e
    data = _parse(raw)
    if status_fail(data):
        raise FileHostError(_err(data, raw))
    return data or {}


def _put_raw(url: str, raw_body: bytes, *, headers: dict[str, str], timeout: int = 300) -> dict[str, Any]:
    hdrs = {"User-Agent": UA, "Content-Type": "application/octet-stream", **headers}
    req = urllib.request.Request(url, data=raw_body, method="PUT", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        data = _parse(raw)
        raise FileHostError(_err(data, raw or f"HTTP {e.code}")) from e
    except urllib.error.URLError as e:
        raise FileHostError(str(e.reason or e)[:280]) from e
    return _parse(raw)


def _upload_flyfile(spec: dict[str, Any], *, api_key: str, file_path: Path) -> str:
    hdrs = _flyfile_headers(api_key)
    assigned = _get(str(spec["assign"]), headers=hdrs)
    node = str(assigned.get("url") or "").rstrip("/")
    if not node:
        raise FileHostError("no upload node")
    init = _post_json(
        str(spec["init"]),
        {"fileName": file_path.name, "fileSize": file_path.stat().st_size},
        headers=hdrs,
    )
    upload_id = str(init.get("uploadId") or init.get("id") or "").strip()
    if not upload_id:
        raise FileHostError("no uploadId")
    raw = file_path.read_bytes()
    put_url = f"{node}/upload/{upload_id}"
    try:
        _put_raw(put_url, raw, headers=hdrs)
    except FileHostError:
        _post_multipart(
            put_url,
            {"uploadId": upload_id},
            [("file", file_path.name, "video/mp4", raw)],
        )
    done = _post_json(str(spec["complete"]), {"uploadId": upload_id}, headers=hdrs)
    code = _file_code(done)
    if code.startswith("http"):
        return code
    if code and code != "ok":
        return str(spec.get("watch") or "").replace("{code}", code)
    raise FileHostError("upload complete without file URL")


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
    from i18n import t

    pid = (platform_id or "").strip()
    spec = HOSTS.get(pid)
    path = Path(file_path)
    if not spec:
        return False, t("api.unknown_platform", lang)
    if content_type == "photo" or path.suffix.lower() in PHOTO_EXT:
        return False, t("pub.filehost.no_photo", lang)
    if not path.is_file() or path.stat().st_size <= 0:
        return False, t("pub.filehost.file_missing", lang)
    if path.suffix.lower() not in VIDEO_EXT:
        return False, t("pub.filehost.bad_video", lang)
    key = str(account.get("api_key") or "").strip()
    extra = str(account.get("extra") or "").strip()
    if not key:
        return False, t("pub.filehost.no_key", lang)
    kind = str(spec.get("kind") or "")
    need = extra_field(pid)
    if need and not extra:
        return False, t("pub.filehost.no_extra", lang, field=need)
    try:
        if kind == "mixdrop":
            url = _upload_mixdrop(spec, api_key=key, email=extra, file_path=path)
        elif kind == "streamtape":
            url = _upload_streamtape(spec, api_key=key, login=extra, file_path=path)
        elif kind == "flyfile":
            url = _upload_flyfile(spec, api_key=key, file_path=path)
        else:
            url = _upload_dood(
                spec,
                api_key=key,
                file_path=path,
                title=title,
                description=description,
            )
        return True, t("pub.filehost.ok", lang, url=url)
    except FileHostError as e:
        return False, t("pub.filehost.upload_fail", lang, error=str(e)[:180])
    except Exception as e:
        return False, t("pub.filehost.upload_fail", lang, error=str(e)[:180])
