"""Videos temporales para el editor de subtítulos en publicaciones."""
from __future__ import annotations

import re
import time
import uuid
from pathlib import Path

TEMP_MAX_AGE_SECONDS = 6 * 60 * 60


def temp_dir(upload_dir: Path) -> Path:
    path = upload_dir / "temp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_user_id(user_id: str) -> str:
    uid = re.sub(r"[^a-zA-Z0-9_-]", "", str(user_id or "user")).strip()
    return uid or "user"


def _prefix(user_id: str, token: str) -> str:
    return f"{_safe_user_id(user_id)}_{token}"


def _find_temp(upload_dir: Path, user_id: str, token: str) -> Path | None:
    token = (token or "").strip().lower()
    if not token or not token.isalnum():
        return None
    base = temp_dir(upload_dir)
    prefix = _prefix(user_id, token)
    matches = sorted(base.glob(f"{prefix}.*"))
    return matches[0] if matches else None


def save_temp(
    upload_dir: Path, user_id: str, contents: bytes, suffix: str
) -> tuple[str, str]:
    token = uuid.uuid4().hex
    safe_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    stored = f"{_prefix(user_id, token)}{safe_suffix}"
    path = temp_dir(upload_dir) / stored
    path.write_bytes(contents)
    return token, stored


def claim_temp(upload_dir: Path, user_id: str, token: str) -> Path | None:
    return _find_temp(upload_dir, user_id, token)


def discard_temp(upload_dir: Path, user_id: str, token: str) -> bool:
    path = _find_temp(upload_dir, user_id, token)
    if not path:
        return False
    path.unlink(missing_ok=True)
    return True


def cleanup_stale(upload_dir: Path, max_age_seconds: int = TEMP_MAX_AGE_SECONDS) -> int:
    base = temp_dir(upload_dir)
    cutoff = time.time() - max(60, int(max_age_seconds))
    removed = 0
    for path in base.iterdir():
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
                removed += 1
        except OSError:
            pass
    return removed
