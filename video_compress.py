"""Baja peso/resolución para no pasarnos del tope de cada red."""
from __future__ import annotations

import subprocess
import tempfile
import uuid
from pathlib import Path

import ffmpeg_bin
import video_probe

MB = 1024 * 1024
DEFAULT_MAX_BYTES = 450 * MB
INSTAGRAM_MAX_BYTES = 290 * MB
PHOTO_MAX_BYTES = int(7.80 * MB)
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

_LADDER: tuple[tuple[int, int, str], ...] = (
    (1280, 26, "128k"),
    (960, 30, "96k"),
    (720, 32, "80k"),
    (540, 35, "64k"),
)
_PHOTO_LADDER: tuple[tuple[int, int], ...] = (
    (4096, 4),
    (2560, 8),
    (1920, 12),
    (1440, 16),
    (1080, 22),
    (720, 28),
)


def ffmpeg_available() -> bool:
    exe = ffmpeg_bin.ffmpeg_exe()
    try:
        proc = subprocess.run(
            [exe, "-version"],
            capture_output=True,
            timeout=8,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def max_bytes_for(platform_id: str, content_type: str = "video") -> int:
    if (content_type or "").strip().lower() == "photo":
        return PHOTO_MAX_BYTES
    pid = (platform_id or "").strip().lower()
    if pid == "instagram":
        return INSTAGRAM_MAX_BYTES
    return DEFAULT_MAX_BYTES


def ensure_under_bytes(
    path: Path, max_bytes: int, *, kind: str = "video"
) -> tuple[Path, Path | None]:
    """Si el archivo pasa de max_bytes, recodifica. El original no se toca."""
    src = Path(path)
    if kind == "photo" or src.suffix.lower() in PHOTO_EXT:
        return _ensure_photo(src, max_bytes)
    return _ensure_video(src, max_bytes)


def _out_path(src: Path, suffix: str) -> Path:
    parent = src.parent if src.parent.is_dir() else Path(tempfile.gettempdir())
    return parent / f"pub_fit_{uuid.uuid4().hex}{suffix}"


def _ensure_video(src: Path, max_bytes: int) -> tuple[Path, Path | None]:
    limit = max(1, int(max_bytes))
    if not src.is_file() or src.stat().st_size <= limit:
        return src, None
    last: Path | None = None
    for width, crf, audio in _LADDER:
        dest = _run_ffmpeg_video(src, width=width, crf=crf, audio=audio, max_bytes=limit)
        if dest is None:
            continue
        if last and last != dest:
            last.unlink(missing_ok=True)
        last = dest
        if dest.stat().st_size <= limit:
            return dest, dest
    if last:
        last.unlink(missing_ok=True)
    raise ValueError("compress_failed")


def _ensure_photo(src: Path, max_bytes: int) -> tuple[Path, Path | None]:
    limit = max(1, int(max_bytes))
    if not src.is_file() or src.stat().st_size <= limit:
        return src, None
    last: Path | None = None
    for width, qv in _PHOTO_LADDER:
        dest = _run_ffmpeg_photo(src, width=width, qv=qv)
        if dest is None:
            continue
        if last and last != dest:
            last.unlink(missing_ok=True)
        last = dest
        if dest.stat().st_size <= limit:
            return dest, dest
    if last:
        last.unlink(missing_ok=True)
    raise ValueError("compress_failed")


def _run_ffmpeg_photo(src: Path, *, width: int, qv: int) -> Path | None:
    dest = _out_path(src, ".jpg")
    scale = (
        f"scale={width}:{width}:force_original_aspect_ratio=decrease,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    )
    cmd = [
        ffmpeg_bin.ffmpeg_exe(),
        "-y",
        "-i",
        str(src),
        "-vf",
        scale,
        "-frames:v",
        "1",
        "-q:v",
        str(qv),
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        dest.unlink(missing_ok=True)
        return None
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    dest.unlink(missing_ok=True)
    return None


def _run_ffmpeg_video(
    src: Path, *, width: int, crf: int, audio: str, max_bytes: int
) -> Path | None:
    dest = _out_path(src, ".mp4")
    scale = (
        f"scale={width}:{width}:force_original_aspect_ratio=decrease,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    )
    cmd = [
        ffmpeg_bin.ffmpeg_exe(),
        "-y",
        "-i",
        str(src),
        "-vf",
        scale,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        audio,
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    duration = video_probe.probe_video(src).get("duration_seconds")
    try:
        seconds = float(duration) if duration is not None else 0.0
    except (TypeError, ValueError):
        seconds = 0.0
    if seconds > 1:
        budget_bits = max_bytes * 8 * 0.72
        audio_bps = 128_000 if audio == "128k" else 96_000 if audio == "96k" else 64_000
        video_bps = int(max(250_000, (budget_bits / seconds) - audio_bps))
        cmd = [
            ffmpeg_bin.ffmpeg_exe(),
            "-y",
            "-i",
            str(src),
            "-vf",
            scale,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            str(video_bps),
            "-maxrate",
            str(video_bps),
            "-bufsize",
            str(video_bps * 2),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            audio,
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        dest.unlink(missing_ok=True)
        return None
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    dest.unlink(missing_ok=True)
    return None
