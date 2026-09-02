"""Email: publication alerts, admin password reset, generic SMTP."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

import site_config


def smtp_configured() -> bool:
    return bool(site_config.SMTP_HOST)


def _recipient_email() -> str:
    return site_config.notification_email()


def send_plain_email(*, to: str, subject: str, body: str) -> bool:
    if not smtp_configured() or not (to or "").strip():
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = site_config.SMTP_FROM
    msg["To"] = to.strip()
    msg.set_content(body)
    try:
        host = site_config.SMTP_HOST
        port = site_config.SMTP_PORT
        if port == 465:
            smtp_cls = smtplib.SMTP_SSL
            ctx_mgr = smtp_cls(host, port, timeout=20)
        else:
            ctx_mgr = smtplib.SMTP(host, port, timeout=20)
        with ctx_mgr as smtp:
            if port != 465 and site_config.SMTP_USE_TLS:
                smtp.starttls()
            if site_config.SMTP_USER:
                smtp.login(site_config.SMTP_USER, site_config.SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except OSError:
        return False


def send_password_reset_email(*, to: str, reset_url: str, lang: str = "es") -> bool:
    if lang == "es":
        subject = f"[{site_config.SITE_NAME}] Cambiar contraseña de administrador"
        body = (
            f"Recibimos una solicitud para cambiar la contraseña del administrador en {site_config.SITE_NAME}.\n\n"
            f"Abre este enlace (válido 2 horas):\n{reset_url}\n\n"
            "Si no fuiste tú, ignora este mensaje."
        )
    else:
        subject = f"[{site_config.SITE_NAME}] Administrator password reset"
        body = (
            f"We received a request to change the administrator password on {site_config.SITE_NAME}.\n\n"
            f"Open this link (valid for 2 hours):\n{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
    return send_plain_email(to=to, subject=subject, body=body)


def send_publish_failure_alert(
    *,
    video_title: str,
    failures: list[dict[str, Any]],
    lang: str = "es",
) -> bool:
    """Send one email summarizing failed platform uploads. Returns True if sent."""
    to = _recipient_email()
    if not failures or not smtp_configured() or not to:
        return False

    subject_es = f"[{site_config.SITE_NAME}] Falló publicación: {video_title}"
    subject_en = f"[{site_config.SITE_NAME}] Publish failed: {video_title}"
    subject = subject_es if lang == "es" else subject_en

    lines = []
    for f in failures:
        platform = f.get("platform_name") or f.get("platform_id", "?")
        msg = f.get("message") or ""
        lines.append(f"• {platform}: {msg}")

    body_es = (
        f"Al publicar «{video_title}» fallaron las siguientes plataformas marcadas:\n\n"
        + "\n".join(lines)
        + f"\n\nRevisa el registro en Publicaciones → {site_config.SITE_URL}/admin/publicaciones"
    )
    body_en = (
        f"While publishing «{video_title}», these checked platforms failed:\n\n"
        + "\n".join(lines)
        + f"\n\nSee the log at Publications → {site_config.SITE_URL}/admin/publicaciones"
    )
    body = body_es if lang == "es" else body_en
    return send_plain_email(to=to, subject=subject, body=body)
