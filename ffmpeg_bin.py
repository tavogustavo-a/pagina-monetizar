"""Ruta al binario de ffmpeg: paquete imageio-ffmpeg, o el del sistema."""
from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        path = (imageio_ffmpeg.get_ffmpeg_exe() or "").strip()
        if path and Path(path).is_file():
            return path
    except Exception:
        pass
    found = shutil.which("ffmpeg")
    return found or "ffmpeg"


@lru_cache(maxsize=1)
def ffprobe_exe() -> str:
    ff = ffmpeg_exe()
    parent = Path(ff).parent
    for name in ("ffprobe.exe", "ffprobe"):
        cand = parent / name
        if cand.is_file():
            return str(cand)
    found = shutil.which("ffprobe")
    return found or "ffprobe"
