#!/usr/bin/env python3
"""Copia de seguridad diaria enviada a Gmail. SQLite en local; pg_dump en producción."""
from __future__ import annotations

import gzip
import os
import smtplib
import subprocess
import tempfile
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

import db_engine  # noqa: E402

HOST = (os.environ.get("SMTP_HOST") or "smtp.gmail.com").strip()
PORT = int(os.environ.get("SMTP_PORT") or "465")
USER = (os.environ.get("SMTP_USER") or "").strip()
PASSWORD = (os.environ.get("SMTP_PASSWORD") or "").replace(" ", "")
FROM = (os.environ.get("SMTP_FROM") or USER).strip()
TO = (os.environ.get("BACKUP_EMAIL") or os.environ.get("CONTACT_EMAIL") or USER).strip()
SITE = (os.environ.get("SITE_NAME") or "Creator Hub").strip()


def _dump_bytes() -> tuple[bytes, str]:
    stamp = datetime.now().strftime("%Y%m%d")
    if db_engine.uses_postgres():
        info = db_engine.parse_database_url()
        env = os.environ.copy()
        if info.get("password"):
            env["PGPASSWORD"] = info["password"]
        proc = subprocess.run(
            [
                "pg_dump",
                "-h",
                info.get("host") or "127.0.0.1",
                "-p",
                info.get("port") or "5432",
                "-U",
                info.get("user") or "monetizar",
                "-d",
                info.get("dbname") or "pagina_monetizar",
                "--no-owner",
                "--no-acl",
            ],
            check=True,
            capture_output=True,
            env=env,
        )
        return gzip.compress(proc.stdout), f"pagina_monetizar_{stamp}.sql.gz"
    db_path = db_engine.DB_PATH
    if not db_path.is_file():
        raise SystemExit(f"No existe {db_path}")
    return gzip.compress(db_path.read_bytes()), f"app_{stamp}.db.gz"


def main() -> None:
    if not USER or not PASSWORD or not TO:
        raise SystemExit("Falta SMTP_USER / SMTP_PASSWORD / destinatario en .env")
    blob, name = _dump_bytes()
    tmp = Path(tempfile.gettempdir()) / f"pagina-monetizar-{name}"
    try:
        tmp.write_bytes(blob)
        msg = EmailMessage()
        engine = "PostgreSQL" if db_engine.uses_postgres() else "SQLite"
        msg["Subject"] = f"[{SITE}] Backup {engine} {datetime.now().strftime('%Y%m%d')}"
        msg["From"] = FROM
        msg["To"] = TO
        msg.set_content(f"Backup {engine} ({len(blob)} bytes gzip).")
        msg.add_attachment(blob, maintype="application", subtype="gzip", filename=name)
        with smtplib.SMTP_SSL(HOST, PORT, timeout=120) as smtp:
            smtp.login(USER, PASSWORD)
            smtp.send_message(msg)
        print(f"OK backup enviado a {TO} ({name})")
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
