"""Duración y tamaño de un video, sin dependencias extra."""
from __future__ import annotations

import struct
import subprocess
from pathlib import Path
from typing import Any


def probe_video(path: Path) -> dict[str, Any]:
    """Devuelve duration_seconds, width, height (None si no se puede leer)."""
    meta = {"duration_seconds": None, "width": None, "height": None}
    p = Path(path)
    if not p.is_file():
        return meta
    suffix = p.suffix.lower()
    if suffix in {".mp4", ".mov", ".m4v", ".m4a"}:
        meta.update(_probe_mp4(p))
    if meta["duration_seconds"] is None:
        ff = _probe_ffprobe(p)
        for key, val in ff.items():
            if val is not None:
                meta[key] = val
    return meta


def is_youtube_short(meta: dict[str, Any], *, max_seconds: float = 180.0) -> bool:
    """Corto (Shorts) si dura 3 minutos o menos. Si no hay duración, se trata como largo."""
    duration = meta.get("duration_seconds")
    if duration is None:
        return False
    try:
        return float(duration) <= float(max_seconds) + 0.05
    except (TypeError, ValueError):
        return False


def _probe_ffprobe(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "duration_seconds": None,
        "width": None,
        "height": None,
    }
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,duration:format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return out
    if proc.returncode != 0 or not proc.stdout:
        return out
    try:
        import json

        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return out
    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    if streams and isinstance(streams[0], dict):
        st = streams[0]
        try:
            out["width"] = int(st["width"]) if st.get("width") else None
        except (TypeError, ValueError):
            pass
        try:
            out["height"] = int(st["height"]) if st.get("height") else None
        except (TypeError, ValueError):
            pass
        if st.get("duration"):
            try:
                out["duration_seconds"] = float(st["duration"])
            except (TypeError, ValueError):
                pass
    if out["duration_seconds"] is None and fmt.get("duration"):
        try:
            out["duration_seconds"] = float(fmt["duration"])
        except (TypeError, ValueError):
            pass
    return out


def _read_box_header(fh) -> tuple[int, bytes, int] | None:
    header = fh.read(8)
    if len(header) < 8:
        return None
    size, typ = struct.unpack(">I4s", header)
    header_len = 8
    if size == 1:
        ext = fh.read(8)
        if len(ext) < 8:
            return None
        size = struct.unpack(">Q", ext)[0]
        header_len = 16
    elif size == 0:
        pos = fh.tell()
        fh.seek(0, 2)
        end = fh.tell()
        fh.seek(pos)
        size = end - pos + 8
    if size < header_len:
        return None
    return size, typ, header_len


def _probe_mp4(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "duration_seconds": None,
        "width": None,
        "height": None,
    }
    try:
        with path.open("rb") as fh:
            _walk_mp4(fh, path.stat().st_size, meta, depth=0)
    except OSError:
        return meta
    return meta


def _walk_mp4(fh, end: int, meta: dict[str, Any], depth: int) -> None:
    if depth > 12:
        return
    start = fh.tell()
    while fh.tell() + 8 <= end:
        header = _read_box_header(fh)
        if not header:
            break
        size, typ, header_len = header
        payload_start = fh.tell()
        payload_end = payload_start + size - header_len
        if payload_end > end + 8:
            break
        if typ in (b"moov", b"trak", b"mdia", b"minf", b"stbl"):
            _walk_mp4(fh, payload_end, meta, depth + 1)
        elif typ == b"mvhd" and meta["duration_seconds"] is None:
            _parse_mvhd(fh, payload_end - payload_start, meta)
        elif typ == b"tkhd" and (meta["width"] is None or meta["height"] is None):
            _parse_tkhd(fh, payload_end - payload_start, meta)
        fh.seek(payload_end)
        if fh.tell() <= start:
            break


def _parse_mvhd(fh, length: int, meta: dict[str, Any]) -> None:
    data = fh.read(min(length, 128))
    if len(data) < 20:
        return
    version = data[0]
    try:
        if version == 1:
            if len(data) < 32:
                return
            timescale = struct.unpack(">I", data[20:24])[0]
            duration = struct.unpack(">Q", data[24:32])[0]
        else:
            timescale = struct.unpack(">I", data[12:16])[0]
            duration = struct.unpack(">I", data[16:20])[0]
        if timescale:
            meta["duration_seconds"] = duration / float(timescale)
    except struct.error:
        return


def _parse_tkhd(fh, length: int, meta: dict[str, Any]) -> None:
    data = fh.read(min(length, 128))
    if len(data) < 84:
        return
    version = data[0]
    try:
        if version == 1:
            if len(data) < 96:
                return
            w = struct.unpack(">I", data[88:92])[0] / 65536.0
            h = struct.unpack(">I", data[92:96])[0] / 65536.0
        else:
            w = struct.unpack(">I", data[76:80])[0] / 65536.0
            h = struct.unpack(">I", data[80:84])[0] / 65536.0
        if w >= 16 and h >= 16:
            meta["width"] = int(w)
            meta["height"] = int(h)
    except struct.error:
        return
