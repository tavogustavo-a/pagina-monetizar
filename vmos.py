"""Cliente OpenAPI VMOS Cloud (firma V2: X-Access-Key, X-Timestamp, X-Sign)."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

PLATFORM_IDS = frozenset(
    {"tiktok", "instagram", "facebook", "youtube", "x", "snapchat"}
)

SHORT_LABEL = {
    "tiktok": "Tik",
    "instagram": "IG",
    "facebook": "FB",
    "youtube": "YT",
    "x": "X",
    "snapchat": "Snap",
}

BASE_URL = (os.environ.get("VMOS_API_URL") or "https://api.vmoscloud.com").strip().rstrip("/")
_UNSIGNED = ("/uploadFile", "/uploadFileV3", "/asyncCmd", "/syncCmd")


def _dumps(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _parse(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _sign(secret: str, timestamp: str, path: str, body_or_query: str) -> str:
    raw = f"{secret}{timestamp}{path}{body_or_query}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _unsigned_body(path: str) -> bool:
    return any(path.endswith(suffix) for suffix in _UNSIGNED)


class VmosError(ValueError):
    pass


def request(
    access_key: str,
    secret_key: str,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    query: str = "",
    data: bytes | None = None,
    content_type: str = "application/json",
    timeout: int = 90,
    lang: str = "es",
) -> dict[str, Any]:
    ak = (access_key or "").strip()
    sk = (secret_key or "").strip()
    if not ak or not sk:
        raise VmosError("missing_keys")
    if not path.startswith("/"):
        path = "/" + path
    ts = str(int(time.time()))
    body_bytes = data
    if payload is not None and body_bytes is None:
        body_bytes = _dumps(payload)
    if _unsigned_body(path):
        body_or_query = ""
    elif (method or "POST").upper() == "GET":
        body_or_query = query or ""
    else:
        body_or_query = (body_bytes or b"").decode("utf-8")
    headers = {
        "X-Access-Key": ak,
        "X-Timestamp": ts,
        "X-Sign": _sign(sk, ts, path, body_or_query),
        "Content-Type": content_type,
        "Accept": "application/json",
        "Accept-Language": "es-ES" if (lang or "").startswith("es") else "en-US",
    }
    url = f"{BASE_URL}{path}"
    if query:
        url = f"{url}?{query}"
    req = urllib.request.Request(url, data=body_bytes, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        parsed = _parse(raw)
        msg = str(parsed.get("msg") or parsed.get("message") or raw or e).strip()
        raise VmosError(msg or f"HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise VmosError(str(e.reason or e)) from e
    parsed = _parse(raw)
    code = parsed.get("code")
    if parsed and "code" in parsed and code not in (200, "200", 0):
        raise VmosError(str(parsed.get("msg") or parsed.get("message") or raw)[:300])
    return parsed


def pad_info(access_key: str, secret_key: str, pad_code: str, *, lang: str = "es") -> dict[str, Any]:
    return request(
        access_key,
        secret_key,
        "POST",
        "/vcpcloud/api/padApi/padInfo",
        payload={"padCode": (pad_code or "").strip()},
        lang=lang,
    )


def upload_to_cloud(
    access_key: str,
    secret_key: str,
    file_path: Path,
    *,
    lang: str = "es",
) -> str:
    blob = file_path.read_bytes()
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    boundary = "----VmosUpload" + uuid.uuid4().hex
    safe = file_path.name.replace('"', "")
    chunks = [
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{safe}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode("utf-8"),
        blob,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    parsed = request(
        access_key,
        secret_key,
        "POST",
        "/vcpcloud/api/padApi/uploadFile",
        data=b"".join(chunks),
        content_type=f"multipart/form-data; boundary={boundary}",
        timeout=180,
        lang=lang,
    )
    data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
    url = str((data or {}).get("downloadUrl") or "").strip()
    if not url:
        raise VmosError(str(parsed.get("msg") or "uploadFile"))
    return url


def push_file_to_pad(
    access_key: str,
    secret_key: str,
    pad_code: str,
    *,
    url: str,
    file_name: str,
    md5: str,
    dest_dir: str = "/DCIM/",
    lang: str = "es",
) -> int:
    parsed = request(
        access_key,
        secret_key,
        "POST",
        "/vcpcloud/api/padApi/uploadFileV3",
        payload={
            "padCodes": [(pad_code or "").strip()],
            "customizeFilePath": dest_dir,
            "fileName": file_name,
            "url": url,
            "md5": md5,
            "autoInstall": 0,
        },
        lang=lang,
    )
    data = parsed.get("data")
    row = data[0] if isinstance(data, list) and data else {}
    task_id = int(row.get("taskId") or 0) if isinstance(row, dict) else 0
    if not task_id:
        raise VmosError(str(parsed.get("msg") or "uploadFileV3"))
    return task_id


def file_task_status(
    access_key: str,
    secret_key: str,
    task_id: int,
    *,
    lang: str = "es",
) -> int | None:
    parsed = request(
        access_key,
        secret_key,
        "POST",
        "/vcpcloud/api/padApi/fileTaskDetail",
        payload={"taskIds": [task_id]},
        lang=lang,
    )
    data = parsed.get("data")
    row = data[0] if isinstance(data, list) and data else {}
    if not isinstance(row, dict):
        return None
    try:
        return int(row.get("taskStatus"))
    except (TypeError, ValueError):
        return None


def script_param_keys(
    access_key: str,
    secret_key: str,
    script_id: int,
    *,
    lang: str = "es",
) -> list[str]:
    parsed = request(
        access_key,
        secret_key,
        "POST",
        "/vcpcloud/api/padApi/automation/scripts/get",
        payload={"scriptId": script_id},
        lang=lang,
    )
    data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
    raw = str((data or {}).get("content") or "")
    if not raw:
        return []
    try:
        content = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(content, dict):
        return []
    keys: list[str] = []
    for item in content.get("startParamMap") or []:
        if isinstance(item, dict) and item.get("key"):
            keys.append(str(item["key"]))
    return keys


def dispatch_flow(
    access_key: str,
    secret_key: str,
    *,
    script_id: int,
    pad_code: str,
    params: dict[str, Any],
    lang: str = "es",
) -> dict[str, Any]:
    parsed = request(
        access_key,
        secret_key,
        "POST",
        "/vcpcloud/api/padApi/automation/tasks/batch-dispatch",
        payload={
            "scriptId": script_id,
            "padCodes": [(pad_code or "").strip()],
            "params": json.dumps(params, ensure_ascii=False, separators=(",", ":")),
        },
        lang=lang,
    )
    data = parsed.get("data")
    row = data[0] if isinstance(data, list) and data else {}
    if not isinstance(row, dict) or not row.get("id"):
        raise VmosError(str(parsed.get("msg") or "batch-dispatch"))
    return row


def flow_task(
    access_key: str,
    secret_key: str,
    task_id: int,
    *,
    lang: str = "es",
) -> dict[str, Any]:
    parsed = request(
        access_key,
        secret_key,
        "POST",
        "/vcpcloud/api/padApi/automation/tasks/get",
        payload={"taskId": task_id},
        lang=lang,
    )
    data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
    if not isinstance(data, dict):
        raise VmosError(str(parsed.get("msg") or "tasks/get"))
    return data
