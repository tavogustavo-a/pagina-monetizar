"""Publicaciones aceptadas por la plataforma pero aún en procesamiento/revisión.

YouTube e Instagram aceptan el video y lo procesan/revisan por su cuenta durante
minutos. En vez de bloquear la petición o marcar un fallo falso, la publicación
queda en el registro con estado "pending" y un hilo en segundo plano consulta a
la plataforma hasta que acepte (→ ok) o rechace (→ fail) el video.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

import db

# Devuelve ("ok"|"fail"|"pending", mensaje final para el registro).
CheckFn = Callable[[], tuple[str, str]]

CHECK_INTERVAL_SECONDS = 30.0
MAX_WAIT_SECONDS = 30 * 60.0

_local = threading.local()


def clear() -> None:
    _local.check = None


def mark(check: CheckFn) -> None:
    """Lo llama el módulo de la plataforma cuando el envío quedó aceptado pero en revisión."""
    _local.check = check


def has_pending() -> bool:
    return getattr(_local, "check", None) is not None


def pop() -> CheckFn | None:
    check = getattr(_local, "check", None)
    _local.check = None
    return check


def attach(log_id: str) -> None:
    """Tras insertar la fila 'pending' del registro, vigila y actualiza el estado solo."""
    check = pop()
    if not check or not (log_id or "").strip():
        return

    def _run() -> None:
        deadline = time.monotonic() + MAX_WAIT_SECONDS
        while time.monotonic() < deadline:
            time.sleep(CHECK_INTERVAL_SECONDS)
            try:
                status, message = check()
            except Exception:
                continue
            if status in ("ok", "fail"):
                try:
                    db.update_publication_log_entry(
                        log_id, status=status, message=message
                    )
                except Exception:
                    pass
                return

    threading.Thread(
        target=_run, daemon=True, name=f"pending-pub-{log_id[:8]}"
    ).start()
