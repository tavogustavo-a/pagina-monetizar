"""Publicación real vía VMOS Cloud: sube el archivo al móvil y dispara la plantilla RPA."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

import vmos

_CAPTION_KEYS = {
    "caption",
    "title",
    "description",
    "text",
    "content",
    "desc",
    "keyword",
    "copy",
    "texto",
    "descripcion",
}
_FILE_KEYS = {
    "video",
    "videopath",
    "filepath",
    "file",
    "path",
    "media",
    "mediapath",
    "video_path",
    "file_path",
    "filename",
    "file_name",
    "mediafile",
}
_URL_KEYS = {"url", "videourl", "mediaurl", "fileurl", "media_url", "video_url"}


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _script_id(raw: str) -> int:
    text = (raw or "").strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _caption(title: str, description: str) -> str:
    title = (title or "").strip()
    description = (description or "").strip()
    if title and description and title != description:
        return f"{title}\n{description}".strip()
    return title or description


def _params(
    keys: list[str],
    *,
    caption: str,
    device_path: str,
    file_url: str,
    file_name: str,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in keys:
        low = key.replace("-", "").replace(" ", "").lower()
        if low in _CAPTION_KEYS:
            out[key] = caption
        elif low in _URL_KEYS:
            out[key] = file_url
        elif low in _FILE_KEYS:
            if "name" in low:
                out[key] = file_name
            else:
                out[key] = device_path
    if not out:
        out = {
            "caption": caption,
            "title": caption,
            "videoPath": device_path,
            "filePath": device_path,
            "url": file_url,
        }
    return out


def _poll_file(ak: str, sk: str, task_id: int, *, lang: str) -> None:
    last = None
    for _ in range(20):
        last = vmos.file_task_status(access_key=ak, secret_key=sk, task_id=task_id, lang=lang)
        if last == 3:
            return
        if last is not None and last < 0:
            raise vmos.VmosError(f"file task {task_id} status {last}")
        time.sleep(1.5)
    raise vmos.VmosError(f"file task {task_id} timeout ({last})")


def publish(
    *,
    file_path: Path,
    title: str,
    description: str,
    lang: str,
    account: dict[str, Any],
) -> tuple[bool, str]:
    from i18n import t

    ak = str(account.get("access_key") or "").strip()
    sk = str(account.get("secret_key") or "").strip()
    pad = str(account.get("pad_code") or "").strip()
    script_id = _script_id(str(account.get("template_id") or ""))
    if not ak or not sk or not pad:
        return False, t("pub.vmos_no_account", lang)
    if not script_id:
        return False, t("pub.vmos_no_template", lang)
    if not file_path.is_file():
        return False, t("pub.vmos_no_file", lang)

    try:
        vmos.pad_info(ak, sk, pad, lang=lang)
        cloud_url = vmos.upload_to_cloud(ak, sk, file_path, lang=lang)
        digest = _md5(file_path)
        task_id = vmos.push_file_to_pad(
            ak,
            sk,
            pad,
            url=cloud_url,
            file_name=file_path.name,
            md5=digest,
            lang=lang,
        )
        _poll_file(ak, sk, task_id, lang=lang)
        device_path = f"/sdcard/DCIM/{file_path.name}"
        caption = _caption(title, description)
        try:
            keys = vmos.script_param_keys(ak, sk, script_id, lang=lang)
        except vmos.VmosError:
            keys = []
        params = _params(
            keys,
            caption=caption,
            device_path=device_path,
            file_url=cloud_url,
            file_name=file_path.name,
        )
        flow = vmos.dispatch_flow(
            ak,
            sk,
            script_id=script_id,
            pad_code=pad,
            params=params,
            lang=lang,
        )
        flow_id = int(flow.get("id") or 0)
        status = str(flow.get("status") or "pending")
        for _ in range(12):
            if status in {"success", "failed", "cancelled"}:
                break
            time.sleep(2)
            try:
                info = vmos.flow_task(ak, sk, flow_id, lang=lang)
                status = str(info.get("status") or status)
            except vmos.VmosError:
                break
        if status in {"failed", "cancelled"}:
            return False, t("pub.vmos_task_failed", lang, task=str(flow_id))
        return True, t("pub.vmos_ok", lang, task=str(flow_id), status=status)
    except vmos.VmosError as e:
        return False, str(e)[:300]
