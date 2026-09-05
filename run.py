import os
import sys
from pathlib import Path

import uvicorn

BASE_DIR = Path(__file__).resolve().parent


def _reload_kwargs() -> dict:
    """Opciones de recarga más estables en Windows (evita KeyboardInterrupt por recargas encadenadas)."""
    delay = float(os.environ.get("RELOAD_DELAY", "1.5" if sys.platform == "win32" else "0.5"))
    return {
        "reload_dirs": [str(BASE_DIR)],
        "reload_delay": delay,
        "reload_excludes": [
            "**/__pycache__/**",
            "**/*.pyc",
            "**/.git/**",
            "**/.data/**",
            "**/uploads/**",
            "**/backups/**",
            "**/.venv/**",
            "**/venv/**",
            "**/.pytest_cache/**",
            "**/.mypy_cache/**",
            "**/.ruff_cache/**",
            "**/*.db",
            "**/*.db-wal",
            "**/*.db-shm",
        ],
    }


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "1").lower() in ("1", "true", "yes")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        **(_reload_kwargs() if reload else {}),
    )
