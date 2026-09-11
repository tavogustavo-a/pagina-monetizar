"""Email: publication alerts, admin password reset, generic SMTP."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

import site_config


def smtp_configured() -> bool:
    return bool(site_config.SMTP_HOST)


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


def send_email_verification_email(*, to: str, verify_url: str, lang: str = "es") -> bool:
    if lang == "es":
        subject = f"[{site_config.SITE_NAME}] Confirma tu correo"
        body = (
            f"Confirma el correo de tu cuenta en {site_config.SITE_NAME}.\n\n"
            f"Abre este enlace (válido 24 horas):\n{verify_url}\n\n"
            "Si no creaste esta cuenta, ignora este mensaje."
        )
    else:
        subject = f"[{site_config.SITE_NAME}] Confirm your email"
        body = (
            f"Confirm the email for your account on {site_config.SITE_NAME}.\n\n"
            f"Open this link (valid for 24 hours):\n{verify_url}\n\n"
            "If you did not create this account, you can ignore this email."
        )
    return send_plain_email(to=to, subject=subject, body=body)


def send_password_reset_email(*, to: str, reset_url: str, lang: str = "es") -> bool:
    if lang == "es":
        subject = f"[{site_config.SITE_NAME}] Restablecer contraseña"
        body = (
            f"Recibimos una solicitud para restablecer la contraseña de tu cuenta en {site_config.SITE_NAME}.\n\n"
            f"Abre este enlace (válido 2 horas):\n{reset_url}\n\n"
            "Si no fuiste tú, ignora este mensaje."
        )
    else:
        subject = f"[{site_config.SITE_NAME}] Password reset"
        body = (
            f"We received a request to reset your account password on {site_config.SITE_NAME}.\n\n"
            f"Open this link (valid for 2 hours):\n{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
    return send_plain_email(to=to, subject=subject, body=body)


def _failure_lines(failures: list[dict[str, Any]]) -> str:
    lines = []
    for f in failures:
        platform = f.get("platform_name") or f.get("platform_id", "?")
        msg = f.get("message") or ""
        lines.append(f"• {platform}: {msg}")
    return "\n".join(lines)


def _publish_failure_body(video_title: str, failures: list[dict[str, Any]], lang: str) -> tuple[str, str]:
    subject_es = f"[{site_config.SITE_NAME}] Falló publicación: {video_title}"
    subject_en = f"[{site_config.SITE_NAME}] Publish failed: {video_title}"
    subject = subject_es if lang == "es" else subject_en
    block = _failure_lines(failures)
    body_es = (
        f"Al publicar «{video_title}» fallaron las siguientes plataformas marcadas:\n\n"
        + block
        + f"\n\nRevisa el registro en Publicaciones → {site_config.SITE_URL}/admin/publicaciones"
    )
    body_en = (
        f"While publishing «{video_title}», these checked platforms failed:\n\n"
        + block
        + f"\n\nSee the log at Publications → {site_config.SITE_URL}/admin/publicaciones"
    )
    body = body_es if lang == "es" else body_en
    return subject, body


def publish_failure_alert_jobs(
    *,
    failures: list[dict[str, Any]],
    user_id: str | None = None,
    tiktok_config_id: str | None = None,
) -> list[tuple[str, list[dict[str, Any]]]]:
    """Quién recibe qué: admins todo; TikTok solo lo vinculado; el resto sin fallos solo-TikTok."""
    if not failures:
        return []
    import db

    tiktok_fails = [f for f in failures if str(f.get("platform_id") or "") == "tiktok"]
    other_fails = [f for f in failures if str(f.get("platform_id") or "") != "tiktok"]
    jobs: list[tuple[str, list[dict[str, Any]]]] = []
    seen_full: set[str] = set()
    seen_any: set[str] = set()

    def _add(emails: list[str], subset: list[dict[str, Any]], *, full: bool) -> None:
        if not subset:
            return
        for email in emails:
            key = email.strip().lower()
            if not key or key in seen_any:
                continue
            if not full and key in seen_full:
                continue
            seen_any.add(key)
            if full:
                seen_full.add(key)
            jobs.append((email.strip(), subset))

    admin_emails = db.list_admin_notification_emails()
    if not admin_emails:
        fallback = site_config.notification_email()
        if fallback:
            admin_emails = [fallback]
    _add(admin_emails, failures, full=True)

    if tiktok_fails:
        _add(
            db.list_tiktok_mode_notification_emails_for_config(tiktok_config_id or ""),
            tiktok_fails,
            full=False,
        )

    if other_fails and user_id:
        publisher = db.get_user_by_id(user_id)
        if (
            publisher
            and publisher.role == "user"
            and not db.user_is_admin_mode_user(publisher)
            and not db.user_is_tiktok_mode(publisher)
        ):
            pub_email = (publisher.notification_email or "").strip()
            if pub_email:
                _add([pub_email], other_fails, full=False)

    return jobs


def send_bilibili_tv_session_alert(*, login: str, code: str, lang: str = "es") -> bool:
    """Avisa a admins si la sesión de Bilibili.tv caducó o cambió la web."""
    if not smtp_configured():
        return False
    import db
    from i18n import t

    emails = db.list_admin_notification_emails()
    if not emails:
        return False
    err_key = {
        "website_changed": "bilibili_tv.err_website",
        "captcha": "bilibili_tv.err_captcha",
        "session_dead": "bilibili_tv.err_session",
        "login_failed": "bilibili_tv.err_login",
        "browser_error": "bilibili_tv.err_browser",
    }.get(code, "bilibili_tv.err_session")
    detail = t(err_key, lang)
    subject = t("bilibili_tv.alert_subject", lang, site=site_config.SITE_NAME, login=login)
    body = t("bilibili_tv.alert_body", lang, login=login, detail=detail)
    sent_any = False
    for to in emails:
        if send_plain_email(to=to, subject=subject, body=body):
            sent_any = True
    return sent_any


def send_bilibili_qr_session_alert(*, login: str, code: str, lang: str = "es") -> bool:
    """Avisa si la sesión QR de Bilibili.com caducó o pide captcha."""
    if not smtp_configured():
        return False
    import db
    from i18n import t

    emails = db.list_admin_notification_emails()
    if not emails:
        return False
    err_key = {
        "website_changed": "bilibili_qr.err_website",
        "captcha": "bilibili_qr.err_captcha",
        "session_dead": "bilibili_qr.err_session",
        "browser_error": "bilibili_qr.err_browser",
    }.get(code, "bilibili_qr.err_session")
    detail = t(err_key, lang)
    subject = t("bilibili_qr.alert_subject", lang, site=site_config.SITE_NAME, login=login)
    body = t("bilibili_qr.alert_body", lang, login=login, detail=detail)
    sent_any = False
    for to in emails:
        if send_plain_email(to=to, subject=subject, body=body):
            sent_any = True
    return sent_any


def send_bilibili_followers_alert(
    *,
    login: str,
    followers: int,
    goal: int = 1000,
    lang: str = "es",
) -> bool:
    """Avisa cuando la cuenta llega al umbral de fans para pedir 创作激励."""
    if not smtp_configured():
        return False
    import db
    from i18n import t

    emails = db.list_admin_notification_emails()
    if not emails:
        return False
    subject = t(
        "bilibili_qr.followers_alert_subject",
        lang,
        site=site_config.SITE_NAME,
        login=login,
        followers=followers,
    )
    body = t(
        "bilibili_qr.followers_alert_body",
        lang,
        login=login,
        followers=followers,
        goal=goal,
    )
    sent_any = False
    for to in emails:
        if send_plain_email(to=to, subject=subject, body=body):
            sent_any = True
    return sent_any


def send_publish_failure_alert(
    *,
    video_title: str,
    failures: list[dict[str, Any]],
    lang: str = "es",
    user_id: str | None = None,
    tiktok_config_id: str | None = None,
) -> bool:
    """Envía alertas de fallo según rol. Devuelve True si al menos un correo salió."""
    if not failures or not smtp_configured():
        return False
    jobs = publish_failure_alert_jobs(
        failures=failures,
        user_id=user_id,
        tiktok_config_id=tiktok_config_id,
    )
    sent_any = False
    for to, subset in jobs:
        subject, body = _publish_failure_body(video_title, subset, lang)
        if send_plain_email(to=to, subject=subject, body=body):
            sent_any = True
    return sent_any
