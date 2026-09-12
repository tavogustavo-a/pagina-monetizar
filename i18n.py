"""Lightweight UI translations (English / Spanish)."""
from __future__ import annotations

from fastapi import Request

DEFAULT_LANG = "en"

LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Español",
}

MESSAGES: dict[str, dict[str, str]] = {
    "lang.label": {"en": "Language", "es": "Idioma"},
    "nav.about": {"en": "About", "es": "Nosotros"},
    "nav.sign_in": {"en": "Sign In", "es": "Iniciar sesión"},
    "nav.home": {"en": "Home", "es": "Inicio"},
    "nav.feed": {"en": "Feed", "es": "Feed"},
    "nav.sign_out": {"en": "Sign out", "es": "Cerrar sesión"},
    "nav.toggle_expand": {"en": "Expand menu", "es": "Expandir menú"},
    "nav.toggle_collapse": {"en": "Collapse menu", "es": "Contraer menú"},
    "nav.statistics": {"en": "Statistics", "es": "Estadísticas"},
    "nav.api_docs": {"en": "API webs", "es": "API webs"},
    "nav.publications": {"en": "Publications", "es": "Publicaciones"},
    "nav.team": {"en": "Team", "es": "Equipo"},
    "nav.tiktok_accounts": {"en": "TikTok Accounts", "es": "Cuentas TikTok"},
    "nav.servers": {"en": "Servers", "es": "Servidores"},
    "nav.panel": {"en": "Panel", "es": "Panel"},
    "nav.support": {"en": "Support", "es": "Soporte"},
    "nav.support_chats": {"en": "Chats", "es": "Chats"},
    "panel.title": {"en": "Admin panel", "es": "Panel de administración"},
    "panel.title_prefix": {"en": "Panel of", "es": "Panel de"},
    "panel.page_hint": {
        "en": "Notification email: used for password reset and publication failure alerts. Admins receive every failed platform. TikTok users only receive failures of their linked TikTok account. Other users are not emailed when the only failure is TikTok. Password: we send the reset link to that email.",
        "es": "Correo de notificaciones: se usa para cambiar contraseña y alertas si falla una publicación. Los administradores reciben todos los fallos. El usuario TikTok solo recibe fallos de su cuenta vinculada. Al resto no les llega un correo si el único problema es TikTok. Contraseña: enviamos el enlace de restablecimiento a ese correo.",
    },
    "panel.tiktok_title": {"en": "TikTok account", "es": "Cuenta TikTok"},
    "panel.accounts_title": {"en": "Accounts", "es": "Cuenta"},
    "panel.accounts_intro": {
        "en": "Connect your social accounts with official OAuth to publish from the panel. You can renew login or revoke access at any time.",
        "es": "Conecta tus cuentas con OAuth oficial para publicar desde el panel. Puedes renovar el inicio de sesión o revocar el acceso cuando quieras.",
    },
    "panel.accounts_info_btn": {
        "en": "About connected accounts",
        "es": "Información sobre cuentas conectadas",
    },
    "panel.account_none": {
        "en": "No {platform} account connected.",
        "es": "No hay cuenta de {platform} conectada.",
    },
    "panel.renew_login": {"en": "Renew login", "es": "Renovar inicio de sesión"},
    "panel.revoke": {"en": "Revoke connection", "es": "Revocar conexión"},
    "panel.revoke_confirm": {
        "en": "Revoke this connection?",
        "es": "¿Revocar esta conexión?",
    },
    "panel.configure_api": {
        "en": "Configure API",
        "es": "Configurar API",
    },
    "panel.edit_api": {
        "en": "Edit API keys",
        "es": "Editar API",
    },
    "panel.in_production": {
        "en": "In production",
        "es": "En producción",
    },
    "panel.implementing_note": {
        "en": "This integration is still being implemented.",
        "es": "Esta integración se está implementando.",
    },
    "panel.api_modal_title": {
        "en": "API credentials — {platform}",
        "es": "Credenciales API — {platform}",
    },
    "panel.save": {"en": "Save", "es": "Guardar"},
    "panel.test_connection": {
        "en": "Test connection",
        "es": "Probar conexión",
    },
    "panel.platform.facebook": {"en": "Facebook Page", "es": "Facebook Página"},
    "panel.tiktok_intro": {
        "en": "Connect your TikTok with the official OAuth flow so you can publish from the panel. You can revoke the connection at any time.",
        "es": "Conecta tu TikTok con el flujo oficial OAuth para publicar desde el panel. Puedes revocar la conexión cuando quieras.",
    },
    "panel.tiktok_oauth_missing": {
        "en": "TikTok is not configured on the server yet. Ask the site administrator to save the Client Key and Secret in Servers.",
        "es": "TikTok aún no está configurado en el servidor. Pide al administrador que guarde el Client Key y el Secret en Servidores.",
    },
    "panel.tiktok_none": {
        "en": "No TikTok account connected yet.",
        "es": "No hay cuenta TikTok conectada.",
    },
    "panel.tiktok_revoke": {"en": "Revoke connection", "es": "Revocar conexión"},
    "panel.tiktok_info_btn": {
        "en": "About TikTok connection",
        "es": "Información sobre la conexión TikTok",
    },
    "panel.tiktok_revoke_confirm": {
        "en": "Revoke this TikTok connection? The app will lose access until you connect again.",
        "es": "¿Revocar esta conexión de TikTok? La app perderá el acceso hasta que vuelvas a conectar.",
    },
    "panel.current_user": {"en": "User", "es": "Usuario"},
    "panel.email_section": {"en": "Notification email", "es": "Correo de notificaciones"},
    "panel.email_info_btn": {
        "en": "What is this email for?",
        "es": "¿Para qué sirve este correo?",
    },
    "panel.email_hint": {
        "en": "This is the email where the panel sends important messages. You must confirm it from the link we email you (valid 24 hours).",
        "es": "Es el correo donde el panel te envía avisos importantes. Debes confirmarlo con el enlace que te enviamos (válido 24 horas).",
    },
    "panel.email_ph": {"en": "admin@example.com", "es": "admin@ejemplo.com"},
    "panel.email_save": {"en": "Save", "es": "Guardar"},
    "panel.email_resend": {"en": "Resend email", "es": "Reenviar correo"},
    "panel.email_verified": {"en": "Confirmed", "es": "Confirmado"},
    "panel.email_pending": {"en": "Pending confirmation", "es": "Pendiente de confirmación"},
    "panel.email_pending_resend": {
        "en": "Pending confirmation Resend email",
        "es": "Pendiente de confirmación Reenviar correo",
    },
    "panel.email_current_none": {
        "en": "No email configured yet.",
        "es": "Aún no hay correo configurado.",
    },
    "panel.email_current": {"en": "Current: {email}", "es": "Actual: {email}"},
    "panel.smtp_section": {"en": "SMTP", "es": "SMTP"},
    "panel.smtp_ok": {
        "en": "SMTP host configured in .env",
        "es": "Servidor SMTP configurado en .env",
    },
    "panel.smtp_missing": {
        "en": "Configure SMTP_HOST, SMTP_USER and SMTP_PASSWORD in .env",
        "es": "Configura SMTP_HOST, SMTP_USER y SMTP_PASSWORD en .env",
    },
    "panel.password_section": {"en": "Change password", "es": "Cambiar contraseña"},
    "panel.password_hint": {
        "en": "We will send a reset link to your confirmed notification email.",
        "es": "Enviaremos un enlace de restablecimiento a tu correo confirmado.",
    },
    "panel.password_requires_email": {
        "en": "Confirm your email before changing your password.",
        "es": "Confirma tu correo antes de cambiar la contraseña.",
    },
    "panel.password_info_btn": {
        "en": "About password reset",
        "es": "Información sobre cambiar contraseña",
    },
    "panel.password_send": {
        "en": "Send link to change password",
        "es": "Enviar enlace para cambiar contraseña",
    },
    "panel.flash.invalid_email": {
        "en": "Enter a valid email address.",
        "es": "Introduce un correo válido.",
    },
    "panel.flash.email_saved": {
        "en": "Confirmation link sent to {email}.",
        "es": "Enlace de confirmación enviado a {email}.",
    },
    "panel.flash.email_verified": {
        "en": "Email confirmed successfully.",
        "es": "Correo confirmado correctamente.",
    },
    "panel.flash.verification_invalid": {
        "en": "This confirmation link is invalid or has expired. Resend the email from your panel.",
        "es": "Este enlace no es válido o ha expirado. Reenvía el correo desde tu panel.",
    },
    "panel.flash.no_pending_email": {
        "en": "There is no email pending confirmation.",
        "es": "No hay un correo pendiente de confirmación.",
    },
    "panel.flash.email_must_confirm": {
        "en": "Confirm your email before resetting your password.",
        "es": "Confirma tu correo antes de restablecer la contraseña.",
    },
    "panel.flash.email_already_verified": {
        "en": "This email is already confirmed.",
        "es": "Este correo ya está confirmado.",
    },
    "panel.flash.email_taken": {
        "en": "That email is already used by another account.",
        "es": "Ese correo ya está en uso por otra cuenta.",
    },
    "panel.flash.no_email": {
        "en": "Set a notification email first.",
        "es": "Configura primero un correo de notificaciones.",
    },
    "panel.flash.no_smtp": {
        "en": "SMTP is not configured in .env yet.",
        "es": "SMTP aún no está configurado en .env.",
    },
    "panel.flash.mail_fail": {
        "en": "Could not send email. Check SMTP settings.",
        "es": "No se pudo enviar el correo. Revisa la configuración SMTP.",
    },
    "panel.flash.reset_sent": {
        "en": "Reset link sent to {email}.",
        "es": "Enlace enviado a {email}.",
    },
    "panel.reset.title": {"en": "New password", "es": "Nueva contraseña"},
    "panel.reset.subtitle": {
        "en": "Choose a new password for your account.",
        "es": "Elige una nueva contraseña para tu cuenta.",
    },
    "panel.reset.password": {"en": "New password", "es": "Nueva contraseña"},
    "panel.reset.password_confirm": {
        "en": "Confirm password",
        "es": "Confirmar contraseña",
    },
    "panel.reset.submit": {"en": "Save password", "es": "Guardar contraseña"},
    "panel.reset.invalid": {
        "en": "This link is invalid or has expired.",
        "es": "Este enlace no es válido o ha expirado.",
    },
    "panel.reset.too_short": {
        "en": "Password must be at least 4 characters.",
        "es": "La contraseña debe tener al menos 4 caracteres.",
    },
    "panel.reset.mismatch": {
        "en": "Passwords do not match.",
        "es": "Las contraseñas no coinciden.",
    },
    "panel.reset.fail": {
        "en": "Could not update password.",
        "es": "No se pudo actualizar la contraseña.",
    },
    "panel.reset.ok": {
        "en": "Password changed successfully.",
        "es": "Cambio de contraseña exitoso.",
    },
    "platform.tiktok": {"en": "TikTok", "es": "TikTok"},
    "platform.youtube": {"en": "YouTube", "es": "YouTube"},
    "platform.instagram": {"en": "Instagram", "es": "Instagram"},
    "platform.x": {"en": "X", "es": "X"},
    "platform.dailymotion": {"en": "Dailymotion", "es": "Dailymotion"},
    "platform.bilibili": {"en": "Bilibili.com", "es": "Bilibili.com"},
    "platform.bilibili_tv": {"en": "Bilibili.tv", "es": "Bilibili.tv"},
    "platform.rumble": {"en": "Rumble", "es": "Rumble"},
    "platform.snapchat": {"en": "Snapchat", "es": "Snapchat"},
    "platform.odysee": {"en": "Odysee", "es": "Odysee"},
    "platform.dtube": {"en": "DTube", "es": "DTube"},
    "platform.facebook": {"en": "Facebook", "es": "Facebook"},
    "platform.threads": {"en": "Threads", "es": "Threads"},
    "platform.doodstream": {"en": "DoodStream", "es": "DoodStream"},
    "platform.streamwish": {"en": "StreamWish", "es": "StreamWish"},
    "platform.filemoon": {"en": "FileMoon", "es": "FileMoon"},
    "platform.mixdrop": {"en": "MixDrop", "es": "MixDrop"},
    "platform.streamtape": {"en": "Streamtape", "es": "Streamtape"},
    "platform.voe": {"en": "VOE", "es": "VOE"},
    "platform.vidoza": {"en": "Vidoza", "es": "Vidoza"},
    "platform.lulustream": {"en": "LuluStream", "es": "LuluStream"},
    "platform.loadvid": {"en": "Loadvid (pago)", "es": "Loadvid (pago)"},
    "platform.vidsonic": {"en": "VidSonic (pago)", "es": "VidSonic (pago)"},
    "platform.flyfile": {"en": "FlyFile (pago)", "es": "FlyFile (pago)"},
    "platform.venvo": {"en": "VenVo (pago)", "es": "VenVo (pago)"},
    "limits.note.odysee": {
        "en": "Video only. Sign in from Servers with the Odysee email and password (no public OAuth). The panel publishes with TUS + LBRY stream_create.",
        "es": "Solo video. En Servidores entra con el email y la contraseña de Odysee (no hay OAuth público). El panel publica con TUS + stream_create de LBRY.",
    },
    "limits.note.dtube": {
        "en": "Video only. Sign in from Servers with the d.tube email and password. The panel keeps the browser session and re-logs in if cookies expire.",
        "es": "Solo vídeo. En Servidores entra con el email y la contraseña de d.tube. El panel guarda la sesión del navegador y vuelve a entrar si caducan las cookies.",
    },
    "servers.intro": {
        "en": "Connect creator accounts on each platform. TikTok is available now; more platforms are coming soon.",
        "es": "Conecta cuentas de creador en cada plataforma. TikTok ya está disponible; más plataformas llegarán pronto.",
    },
    "servers.coming_soon": {"en": "Coming soon", "es": "Próximamente"},
    "servers.publish_paused": {"en": "Paused", "es": "Pausado"},
    "servers.platform_unavailable": {
        "en": "This server is temporarily unavailable.",
        "es": "Este servidor no está disponible por ahora.",
    },
    "servers.dtube_uploader_paused": {
        "en": "Publishing is paused: DTube’s upload servers (cluster.d.tube) are not available. Your Hive username and posting key stay saved. We will use them again if the uploader returns.",
        "es": "La publicación está pausada: los servidores de subida de DTube (cluster.d.tube) no están disponibles. El usuario Hive y la clave posting se quedan guardados. Se usarán otra vez si el uploader vuelve.",
    },
    "servers.accounts_btn": {"en": "Accounts", "es": "Cuentas"},
    "servers.platform_configure": {
        "en": "Configure server",
        "es": "Configurar servidor",
    },
    "servers.modal_accounts_title": {
        "en": "{platform} accounts · API credentials",
        "es": "Cuentas de {platform} · Credenciales de API",
    },
    "servers.modal_api_credentials": {
        "en": "API credentials",
        "es": "Credenciales de API",
    },
    "servers.modal_accounts_prefix": {
        "en": "{platform} accounts ·",
        "es": "Cuentas de {platform} ·",
    },
    "servers.modal_account_name": {
        "en": "Account",
        "es": "Cuenta",
    },
    "servers.modal_close": {"en": "Close", "es": "Cerrar"},
    "servers.platform_soon": {
        "en": "Integration with {platform} is not available yet. It will appear here when ready.",
        "es": "La integración con {platform} aún no está disponible. Aparecerá aquí cuando esté lista.",
    },
    "servers.connect_tiktok": {"en": "Connect a TikTok account", "es": "Conectar cuenta TikTok"},
    "servers.tiktok_oauth_desc": {
        "en": "Use the official TikTok OAuth 2.0 flow. You will be redirected to TikTok to sign in and grant permissions ({scopes}). App credentials are stored securely on the server only.",
        "es": "Usa el flujo oficial OAuth 2.0 de TikTok. Serás redirigido a TikTok para iniciar sesión y otorgar permisos ({scopes}). Las credenciales de la app se guardan solo en el servidor.",
    },
    "servers.tiktok_oauth_info_title": {
        "en": "Linked accounts",
        "es": "Cuentas vinculadas",
    },
    "servers.tiktok_redirect_hint": {
        "en": "Paste this exact Redirect URI in the TikTok developer portal (SITE_URL/oauth/tiktok/callback).",
        "es": "Pega esta Redirect URI exacta en el portal de desarrolladores de TikTok (SITE_URL/oauth/tiktok/callback).",
    },
    "servers.connect_with_tiktok": {"en": "Connect with TikTok", "es": "Conectar con TikTok"},
    "servers.connect_with_vmos": {
        "en": "Connect with VMOS {short}",
        "es": "Conectar con VMOS {short}",
    },
    "servers.vmos_hint": {
        "en": "VMOS Cloud alternative: Access Key, Secret, cloud phone ID (padCode) and optional template. Developer → API in vmoscloud.com.",
        "es": "Alternativa VMOS Cloud: Access Key, Secret, ID del móvil (padCode) y plantilla opcional. Developer → API en vmoscloud.com.",
    },
    "servers.vmos_title": {
        "en": "VMOS Cloud · {platform}",
        "es": "VMOS Cloud · {platform}",
    },
    "servers.vmos_section_title": {
        "en": "VMOS {platform}",
        "es": "VMOS {platform}",
    },
    "servers.vmos_save": {"en": "Save VMOS", "es": "Guardar VMOS"},
    "servers.vmos_saved": {"en": "VMOS account saved.", "es": "Cuenta VMOS guardada."},
    "servers.vmos_missing": {
        "en": "Access Key, Secret Access Key and padCode are required.",
        "es": "Hacen falta Access Key, Secret Access Key y padCode.",
    },
    "servers.vmos_badge": {"en": "VMOS", "es": "VMOS"},
    "servers.vmos_field_access_key": {"en": "Access Key ID", "es": "Access Key ID"},
    "servers.vmos_field_secret": {"en": "Secret Access Key", "es": "Secret Access Key"},
    "servers.vmos_field_pad": {"en": "Cloud phone ID (padCode)", "es": "ID del móvil (padCode)"},
    "servers.vmos_field_template": {
        "en": "Flow template ID (scriptId, required to publish)",
        "es": "ID de plantilla RPA (scriptId, obligatorio para publicar)",
    },
    "servers.vmos_test": {"en": "Test VMOS", "es": "Probar VMOS"},
    "servers.vmos_test_ok": {
        "en": "VMOS Cloud phone reachable: {pad}.",
        "es": "Móvil VMOS Cloud accesible: {pad}.",
    },
    "servers.connect_with_filehost": {
        "en": "Connect {name}",
        "es": "Conectar {name}",
    },
    "servers.filehost_title": {
        "en": "Connect {platform}",
        "es": "Conectar {platform}",
    },
    "servers.filehost_hint": {
        "en": "",
        "es": "",
    },
    "servers.filehost_field_key": {"en": "API key", "es": "API key"},
    "servers.filehost_field_email": {"en": "API email", "es": "Email de la API"},
    "servers.filehost_field_login": {"en": "API login", "es": "API login"},
    "servers.filehost_save": {"en": "Save host", "es": "Guardar host"},
    "servers.filehost_saved": {
        "en": "Host account saved ({name}).",
        "es": "Cuenta del host guardada ({name}).",
    },
    "servers.filehost_missing": {
        "en": "API key is required. MixDrop needs email; Streamtape needs API login.",
        "es": "La API key es obligatoria. MixDrop pide email; Streamtape pide API login.",
    },
    "servers.filehost_test": {"en": "Test API", "es": "Probar API"},
    "servers.filehost_badge": {"en": "PPV", "es": "PPV"},
    "servers.connect_with_chain": {
        "en": "Connect {name}",
        "es": "Conectar {name}",
    },
    "servers.chain_title": {
        "en": "Connect {platform}",
        "es": "Conectar {platform}",
    },
    "servers.chain_hint_odysee": {
        "en": "Sign in with the email and password of odysee.com (not Google-only login). The panel stores them and renews the auth token when it expires. Channel is optional: paste the 40-character claim ID, or @channel / the Odysee URL; @name is not the claim ID.",
        "es": "Entra con el email y la contraseña de odysee.com (no vale si solo usas Google). El panel los guarda y renueva el auth token cuando caduca. El canal es opcional: pega el claim ID de 40 caracteres, o @canal / la URL de Odysee; @nombre no es el claim ID.",
    },
    "servers.chain_hint_bilibili_tv": {
        "en": "Sign in with the email and password of bilibili.tv.",
        "es": "Entra con el email y la contraseña de bilibili.tv.",
    },
    "servers.chain_hint_dtube": {
        "en": "Sign in with your d.tube email and password. Legacy accounts: Hive username and posting key (WIF).",
        "es": "Entra con el email y la contraseña de d.tube. Cuentas antiguas: usuario de Hive y posting key (WIF).",
    },
    "servers.chain_field_email": {"en": "Odysee email", "es": "Email de Odysee"},
    "servers.chain_field_password": {
        "en": "Odysee password",
        "es": "Contraseña de Odysee",
    },
    "servers.chain_field_email_tv": {"en": "Bilibili.tv email", "es": "Email de Bilibili.tv"},
    "servers.chain_field_password_tv": {
        "en": "Bilibili.tv password",
        "es": "Contraseña de Bilibili.tv",
    },
    "servers.chain_field_email_dtube": {"en": "DTube email", "es": "Email de DTube"},
    "servers.chain_field_password_dtube": {
        "en": "DTube password",
        "es": "Contraseña de DTube",
    },
    "servers.chain_field_hive": {"en": "DTube username", "es": "Usuario de DTube"},
    "servers.chain_field_wif": {"en": "Posting key", "es": "Clave posting"},
    "servers.chain_field_channel": {
        "en": "Channel claim ID or @channel (optional)",
        "es": "Claim ID del canal o @canal (opcional)",
    },
    "servers.chain_save": {"en": "Save account", "es": "Guardar cuenta"},
    "servers.chain_connecting": {
        "en": "Connecting… this can take a minute. Do not close this window.",
        "es": "Conectando… puede tardar un minuto. No cierres esta ventana.",
    },
    "servers.chain_connecting_btn": {"en": "Connecting…", "es": "Conectando…"},
    "servers.chain_saved": {
        "en": "Account saved ({name}).",
        "es": "Cuenta guardada ({name}).",
    },
    "servers.chain_missing": {
        "en": "Odysee, DTube and Bilibili.tv need email and password.",
        "es": "Odysee, DTube y Bilibili.tv piden email y contraseña.",
    },
    "servers.chain_test": {"en": "Test API", "es": "Probar API"},
    "servers.chain_badge_odysee": {"en": "LBRY", "es": "LBRY"},
    "servers.chain_badge_dtube": {"en": "Browser", "es": "Navegador"},
    "servers.chain_badge_bilibili_tv": {"en": "Browser", "es": "Navegador"},
    "servers.chain_badge": {"en": "Chain", "es": "Cadena"},
    "servers.chain_session_ok": {"en": "Session active", "es": "Sesión activa"},
    "servers.chain_session_bad": {"en": "Session expired", "es": "Sesión caducada"},
    "servers.vmos_field_remark": {"en": "Remark", "es": "Nota"},
    "servers.oauth_missing": {
        "en": "Save the TikTok Client Key and Client Secret first, then connect an account.",
        "es": "Guarda primero el Client Key y el Client Secret de TikTok, luego conecta una cuenta.",
    },
    "servers.linked_accounts": {"en": "Linked accounts", "es": "Cuentas vinculadas"},
    "servers.no_accounts": {
        "en": "No accounts connected yet. Use the connect button above.",
        "es": "Aún no hay cuentas conectadas. Usa el botón de conectar arriba.",
    },
    "servers.connected": {"en": "Connected", "es": "Conectado"},
    "servers.disconnected": {"en": "Disconnected", "es": "Desconectado"},
    "servers.team_user": {"en": "team:", "es": "equipo:"},
    "servers.assign_team": {
        "en": "Assign this account to a team member in {team}.",
        "es": "Asigna esta cuenta a un miembro del equipo en {team}.",
    },
    "servers.disconnect": {"en": "Disconnect", "es": "Desconectar"},
    "servers.team_assignment": {"en": "Team assignment", "es": "Asignación de equipo"},
    "servers.team_assignment_desc": {
        "en": "After connecting accounts here, assign them to team members from the {team} screen so they can publish.",
        "es": "Tras conectar cuentas aquí, asígnalas a miembros del equipo desde la pantalla {team} para que puedan publicar.",
    },
    "servers.disconnect_confirm": {
        "en": "Disconnect this account? Tokens will be removed from this app.",
        "es": "¿Desconectar esta cuenta? Se eliminarán los tokens de esta app.",
    },
    "servers.connect_with_youtube": {
        "en": "Connect with YouTube",
        "es": "Conectar con YouTube",
    },
    "servers.youtube_oauth_missing": {
        "en": "Save the YouTube Client ID and Client secret first (Google Cloud OAuth client of type Web application).",
        "es": "Guarda primero el Client ID y el Client secret de YouTube (cliente OAuth de tipo aplicación web en Google Cloud).",
    },
    "servers.youtube_redirect_hint": {
        "en": "Paste this exact URI in Google Cloud → Authorized redirect URIs (SITE_URL/oauth/youtube/callback).",
        "es": "Pega esta URI exacta en Google Cloud → URIs de redirección autorizadas (SITE_URL/oauth/youtube/callback).",
    },
    "servers.youtube_connected": {
        "en": "Connected {name} successfully.",
        "es": "Se conectó {name} correctamente.",
    },
    "servers.youtube_no_code": {
        "en": "YouTube did not return an authorization code.",
        "es": "YouTube no devolvió un código de autorización.",
    },
    "servers.oauth_state_invalid": {
        "en": "Invalid OAuth state. Please try again.",
        "es": "Estado OAuth inválido. Inténtalo de nuevo.",
    },
    "servers.connect_with_instagram": {
        "en": "Connect with Instagram",
        "es": "Conectar con Instagram",
    },
    "servers.instagram_oauth_missing": {
        "en": "Save the Instagram App ID and App Secret first (Meta App Dashboard → Instagram → API setup with Instagram Login).",
        "es": "Guarda primero el App ID y el App Secret de Instagram (Meta App Dashboard → Instagram → API con Instagram Login).",
    },
    "servers.instagram_redirect_hint": {
        "en": "Paste this exact URI in Meta App Dashboard (SITE_URL/oauth/instagram/callback).",
        "es": "Pega esta URI exacta en Meta App Dashboard (SITE_URL/oauth/instagram/callback).",
    },
    "servers.instagram_connected": {
        "en": "Connected @{name} successfully.",
        "es": "Se conectó @{name} correctamente.",
    },
    "servers.instagram_no_code": {
        "en": "Instagram did not return an authorization code.",
        "es": "Instagram no devolvió un código de autorización.",
    },
    "servers.connect_with_facebook": {
        "en": "Connect with Facebook",
        "es": "Conectar con Facebook",
    },
    "servers.facebook_oauth_missing": {
        "en": "Save the Facebook App ID and App Secret first (Meta App Dashboard → Facebook Login).",
        "es": "Guarda primero el App ID y el App Secret de Facebook (Meta App Dashboard → Facebook Login).",
    },
    "servers.facebook_redirect_hint": {
        "en": "Paste this exact URI in Meta App Dashboard (SITE_URL/oauth/facebook/callback).",
        "es": "Pega esta URI exacta en Meta App Dashboard (SITE_URL/oauth/facebook/callback).",
    },
    "servers.facebook_dev_hint": {
        "en": "If publish fails after a successful connect: the app is still in Development. Tap the info icon for how to switch it to Live and reconnect.",
        "es": "Si al publicar falla aunque la cuenta esté Conectada: la app sigue en Desarrollo. Pulsa el icono i para ver cómo pasarla a En vivo y reconectar.",
    },
    "servers.facebook_connected": {
        "en": "Connected {n} Facebook Page(s).",
        "es": "Se conectaron {n} página(s) de Facebook.",
    },
    "servers.facebook_no_code": {
        "en": "Facebook did not return an authorization code.",
        "es": "Facebook no devolvió un código de autorización.",
    },
    "servers.facebook_no_pages": {
        "en": "This Facebook user has no Pages with permission to publish. Create a Page and grant pages_manage_posts.",
        "es": "Este usuario de Facebook no tiene Páginas con permiso para publicar. Crea una Página y concede pages_manage_posts.",
    },
    "servers.connect_with_x": {
        "en": "Connect with X",
        "es": "Conectar con X",
    },
    "servers.x_oauth_missing": {
        "en": "Save this account’s X Client ID and Secret (with “Use own X API” checked), or add an app in Config X and leave that box unchecked.",
        "es": "Guarda el Client ID y el Secret de esta cuenta (con «Usar API propia de X» marcado), o añade una app en Config X y deja esa casilla sin marcar.",
    },
    "servers.x_api_inherit_hint": {
        "en": "By default this name publishes through Config X (one app, or split across several). Check “Use own X API” only if this name has its own developer app.",
        "es": "Por defecto este nombre publica por Config X (una app, o varias si hay más). Marca «Usar API propia de X» solo si este nombre tiene su propia app de desarrollador.",
    },
    "servers.x_use_own_api": {
        "en": "Use own X API",
        "es": "Usar API propia de X",
    },
    "servers.x_use_own_api_hint": {
        "en": "Checked: this account’s Client ID and Secret are used. Unchecked: Config X is used (one app if there is only one; if there are several, posts are split).",
        "es": "Marcado: se usan el Client ID y el Secret de esta cuenta. Sin marcar: se usa Config X (si hay una app, esa; si hay varias, se reparte).",
    },
    "servers.x_own_api_needs_keys": {
        "en": "To use this account’s own X API, save Client ID and Secret first.",
        "es": "Para usar la API propia de esta cuenta, guarda primero el Client ID y el Secret.",
    },
    "servers.x_redirect_hint": {
        "en": "Paste this exact Callback URI in the X developer portal (SITE_URL/oauth/x/callback).",
        "es": "Pega esta Callback URI exacta en el portal de X (SITE_URL/oauth/x/callback).",
    },
    "servers.x_connected": {
        "en": "Connected @{name} successfully.",
        "es": "Se conectó @{name} correctamente.",
    },
    "servers.x_no_code": {
        "en": "X did not return an authorization code.",
        "es": "X no devolvió un código de autorización.",
    },
    "servers.connect_with_dailymotion": {
        "en": "Connect with Dailymotion",
        "es": "Conectar con Dailymotion",
    },
    "servers.dailymotion_oauth_missing": {
        "en": "Save the Dailymotion API Key and API Secret first, then connect an account.",
        "es": "Guarda primero la API Key y el API Secret de Dailymotion, luego conecta una cuenta.",
    },
    "servers.dailymotion_redirect_hint": {
        "en": "Paste this exact Callback URL in Dailymotion Studio → API keys, then Connect with Dailymotion.",
        "es": "Pega esta Callback URL exacta en Dailymotion Studio → API keys y luego pulsa Conectar con Dailymotion.",
    },
    "servers.oauth_save_then_connect": {
        "en": "Each account name has its own API Key and Secret (they are not shared). Saving the keys only stores the app for this name. The server stays “Not linked” until you click Connect and sign in. Disconnect or Remove API unlinks it. Connecting another account on the same card replaces the previous one.",
        "es": "Cada nombre de cuenta tiene su propia API Key y Secret (no se comparten). Guardar las claves solo guarda la app de este nombre. El servidor sigue «Sin vincular» hasta que pulses Conectar e inicies sesión. Desconectar o Quitar API lo desvincula. Si conectas otra cuenta en la misma ficha, reemplaza la anterior.",
    },
    "servers.oauth_saved_click_connect": {
        "en": "API saved. Now click Connect so this account is linked.",
        "es": "API guardada. Ahora pulsa Conectar para vincular esta cuenta.",
    },
    "servers.dailymotion_connected": {
        "en": "Connected {name} successfully.",
        "es": "Se conectó {name} correctamente.",
    },
    "servers.dailymotion_no_code": {
        "en": "Dailymotion did not return an authorization code.",
        "es": "Dailymotion no devolvió un código de autorización.",
    },
    "servers.connect_with_bilibili": {
        "en": "Connect with Bilibili",
        "es": "Conectar con Bilibili",
    },
    "servers.bilibili_oauth_missing": {
        "en": "Save the Bilibili Client ID and Client Secret first. Docs: https://open.bilibili.com/doc?utm_source",
        "es": "Guarda primero el Client ID y el Client Secret de Bilibili. Documentación: https://open.bilibili.com/doc?utm_source",
    },
    "servers.bilibili_redirect_hint": {
        "en": "Paste this exact Callback URL in Bilibili Open Platform (SITE_URL/oauth/bilibili/callback).",
        "es": "Pega esta Callback URL exacta en Bilibili Open Platform (SITE_URL/oauth/bilibili/callback).",
    },
    "servers.bilibili_connected": {
        "en": "Connected {name} successfully.",
        "es": "Se conectó {name} correctamente.",
    },
    "servers.bilibili_no_code": {
        "en": "Bilibili did not return an authorization code.",
        "es": "Bilibili no devolvió un código de autorización.",
    },
    "servers.bilibili_qr_title": {
        "en": "Web session (QR code)",
        "es": "Sesión web (código QR)",
    },
    "servers.bilibili_qr_hint": {
        "en": "No company Open Platform app. Scan the QR with the Bilibili app on your phone. The panel keeps that browser session and publishes 稿件 with it. Keep-alive every 3–5 days at 3 am (panel time), not every day; fan count is checked then and when you connect. If cookies die, scan again — there is no password to sign in alone. Link a proxy to this account in Proxies and keep the same one, or the session often dies when the IP changes.",
        "es": "Sin app de empresa en Open Platform. Escanea el QR con la app de Bilibili en el móvil. El panel guarda esa sesión del navegador y con ella publica 稿件. Keep-alive cada 3–5 días a las 3 am (hora del panel), no cada día; los fans se consultan al conectar y en esa visita. Si las cookies mueren, vuelves a escanear: no hay contraseña para entrar solo. Vincula un proxy a esta cuenta en Proxys y no lo cambies, o la sesión suele caer al cambiar la IP.",
    },
    "servers.connect_with_bilibili_qr": {
        "en": "Connect with QR code",
        "es": "Conectar con código QR",
    },
    "servers.bilibili_qr_rescan": {
        "en": "Scan QR again",
        "es": "Volver a escanear QR",
    },
    "servers.bilibili_qr_need_name": {
        "en": "Open this server from an account in Servers first, then scan the QR.",
        "es": "Abre este servidor desde una cuenta en Servidores y luego escanea el QR.",
    },
    "servers.bilibili_qr_waiting": {
        "en": "Scan with the Bilibili app. The code updates by itself when Bilibili refreshes it.",
        "es": "Escanea con la app de Bilibili. El código se actualiza solo cuando Bilibili lo renueva.",
    },
    "servers.bilibili_qr_generating": {
        "en": "Preparing the QR code…",
        "es": "Preparando el código QR…",
    },
    "servers.bilibili_qr_scanned": {
        "en": "Scanned. Confirm the login in the Bilibili app.",
        "es": "Escaneado. Confirma el inicio de sesión en la app de Bilibili.",
    },
    "servers.bilibili_qr_cancel": {"en": "Cancel scan", "es": "Cancelar escaneo"},
    "bilibili_qr.connected": {
        "en": "Bilibili web session connected{name}.",
        "es": "Sesión web de Bilibili conectada{name}.",
    },
    "bilibili_qr.err_website": {
        "en": "Bilibili.com login page does not match what this panel expects. The site may have changed; nothing was marked as sent.",
        "es": "La página de login de Bilibili.com no coincide con lo que espera este panel. Puede que hayan cambiado la web; no se marcó nada como enviado.",
    },
    "bilibili_qr.err_captcha": {
        "en": "Bilibili.com asked for captcha or SMS. Complete that check yourself and scan again. The panel will not guess codes.",
        "es": "Bilibili.com pidió captcha o SMS. Completa esa comprobación tú y vuelve a escanear; el panel no adivina códigos.",
    },
    "bilibili_qr.err_session": {
        "en": "The Bilibili.com web session expired. Open Servers and scan the QR again.",
        "es": "La sesión web de Bilibili.com caducó. Abre Servidores y vuelve a escanear el QR.",
    },
    "bilibili_qr.err_busy": {
        "en": "The internal browser is already in use. Wait a minute and try again.",
        "es": "El navegador interno ya está ocupado. Espera un minuto y reintenta.",
    },
    "bilibili_qr.err_browser": {
        "en": "The internal browser could not open Bilibili.com.",
        "es": "El navegador interno no pudo abrir Bilibili.com.",
    },
    "bilibili_qr.err_expired": {
        "en": "The QR code expired. Click Connect with QR code again.",
        "es": "El código QR caducó. Pulsa otra vez Conectar con código QR.",
    },
    "bilibili_qr.err_cancelled": {
        "en": "QR login was cancelled.",
        "es": "Se canceló el inicio con QR.",
    },
    "bilibili_qr.alert_subject": {
        "en": "[{site}] Bilibili.com QR session: {login}",
        "es": "[{site}] Sesión QR Bilibili.com: {login}",
    },
    "bilibili_qr.alert_body": {
        "en": "Bilibili.com account {login}:\n\n{detail}\n\nOpen Servers and scan the QR again if needed. Nothing was marked as published.",
        "es": "Cuenta de Bilibili.com {login}:\n\n{detail}\n\nAbre Servidores y vuelve a escanear el QR si hace falta. No se marcó nada como publicado.",
    },
    "bilibili_qr.followers_alert_subject": {
        "en": "[{site}] Bilibili.com {login} reached {followers} fans — apply for monetization",
        "es": "[{site}] Bilibili.com {login} llegó a {followers} fans — pide la monetización",
    },
    "bilibili_qr.followers_alert_body": {
        "en": "Bilibili.com account {login} has {followers} fans (goal {goal}).\n\nThat is the usual threshold for 创作激励 (creator incentive). Open the Bilibili app → Creator Center → Creator incentive and apply yourself. The panel cannot complete real-name verification or the application.\n\nOther typical requirements: original videos, credit score, and sometimes 电磁力. The panel does not mark anything as published.",
        "es": "La cuenta de Bilibili.com {login} tiene {followers} fans (objetivo {goal}).\n\nEse es el umbral habitual para pedir 创作激励 (incentivo de creadores). Ábrelo tú: app de Bilibili → Centro de creación → Incentivo de creación. El panel no puede hacer la verificación de identidad ni enviar la solicitud.\n\nSuelen pedir también videos originales, puntuación de crédito y a veces 电磁力. El panel no marca nada como publicado.",
    },
    "servers.bilibili_followers": {
        "en": "{count} / {goal} fans",
        "es": "{count} / {goal} fans",
    },
    "servers.bilibili_monetize_ready": {
        "en": "Ready to apply for monetization",
        "es": "Ya puedes pedir la monetización",
    },
    "servers.rumble_partner_hint": {
        "en": "Rumble has no public OAuth. Save the partner Upload API token and Channel ID that Rumble issued (not a livestream chat URL).",
        "es": "Rumble no tiene OAuth público. Guarda el token de la Upload API de partners y el Channel ID que te dio Rumble (no la URL de chat en vivo).",
    },
    "servers.rumble_ready": {
        "en": "Upload API token saved. Channel {channel}.",
        "es": "Token de Upload API guardado. Canal {channel}.",
    },
    "servers.rumble_token_only": {
        "en": "Token saved. Add the Channel ID to publish.",
        "es": "Token guardado. Añade el Channel ID para publicar.",
    },
    "servers.connect_with_snapchat": {
        "en": "Connect with Snapchat",
        "es": "Conectar con Snapchat",
    },
    "servers.snapchat_oauth_missing": {
        "en": "Save the Snapchat Client ID and Client Secret first (Snap Business Manager → Business Details → OAuth app).",
        "es": "Guarda primero el Client ID y el Client Secret de Snapchat (Snap Business Manager → Business Details → app OAuth).",
    },
    "servers.snapchat_redirect_hint": {
        "en": "Paste this exact Redirect URI in Snap Business Manager (SITE_URL/oauth/snapchat/callback). Connect asks for Public Profile and the Business org (needed to find the Page).",
        "es": "Pega esta Redirect URI exacta en Snap Business Manager (SITE_URL/oauth/snapchat/callback). Conectar pide Perfil público y la organización Business (hace falta para encontrar la Página).",
    },
    "servers.snapchat_connected": {
        "en": "Connected {name} successfully.",
        "es": "Se conectó {name} correctamente.",
    },
    "servers.snapchat_no_code": {
        "en": "Snapchat did not return an authorization code.",
        "es": "Snapchat no devolvió un código de autorización.",
    },
    "servers.snapchat_no_profile": {
        "en": "Snapchat signed in, but did not return a Public Profile. Use the Business Manager OAuth Client ID (not Snap Kit), save it in Servers, then connect while logged in as the owner of that Public Profile (e.g. juancarl1294 / Kirth Melo). Create the Public Profile in Snapchat if it does not exist.",
        "es": "Snapchat inició sesión, pero no devolvió un perfil público. Usa el Client ID OAuth de Business Manager (no Snap Kit), gúardalo en Servidores y conecta con la cuenta dueña de ese perfil (p. ej. juancarl1294 / Kirth Melo). Si no existe, créalo en Snapchat.",
    },
    "servers.snapchat_client_hint": {
        "en": "Paste the Confidential OAuth Client ID from Snap Business Manager (Business Details), not a Snap Kit Staging ID. The panel already calls the Business Content Management API (businessapi.snapchat.com).",
        "es": "Pega el Client ID OAuth Confidential de Snap Business Manager (Business Details), no el de Snap Kit Staging. Este panel ya llama a la Content Management API de Business (businessapi.snapchat.com).",
    },
    "servers.snapchat_need_allowlist": {
        "en": "The app is not allowed to read Public Profiles. In Snap Business Manager the OAuth app needs Public Profile API access (allowlist). Send the Client ID to Snap if that toggle is missing, then connect again.",
        "es": "La app no tiene permiso para leer perfiles públicos. En Snap Business Manager la app OAuth necesita acceso a Public Profile API (allowlist). Si no aparece esa opción, envía el Client ID a Snap y vuelve a conectar.",
    },
    "servers.disconnect_error": {
        "en": "Could not disconnect.",
        "es": "No se pudo desconectar.",
    },
    "servers.network_error": {"en": "Network error.", "es": "Error de red."},
    "servers.groups_save": {"en": "Save", "es": "Guardar"},
    "servers.accounts_section_title": {"en": "Accounts", "es": "Cuentas"},
    "servers.accounts_search": {
        "en": "Search by account name or server...",
        "es": "Buscar por nombre de cuenta o servidor...",
    },
    "servers.accounts_pagination": {
        "en": "Accounts pagination",
        "es": "Paginación de cuentas",
    },
    "servers.accounts_info_title": {"en": "About accounts", "es": "Sobre las cuentas"},
    "servers.accounts_empty": {
        "en": "No accounts yet. Create one with the button above, then link servers with Edit.",
        "es": "Aún no hay cuentas. Crea una con el botón de arriba y luego vincula servidores con Editar.",
    },
    "servers.accounts_hint": {
        "en": "Create an account with a name in Accounts, or add one from a server row (name + credentials link it at once). Accounts with the same name are linked automatically. Each name must be unique per server.",
        "es": "Crea una cuenta con nombre en Cuentas, o agrégala desde la fila de un servidor (nombre + credenciales la vinculan de una vez). Las cuentas con el mismo nombre se vinculan solas. El nombre debe ser único en cada servidor.",
    },
    "servers.accounts_create": {"en": "Create", "es": "Crear"},
    "servers.accounts_name_taken": {
        "en": "That name is already used on this server.",
        "es": "Ese nombre ya existe en este servidor.",
    },
    "servers.accounts_link_name_taken": {
        "en": "That account name already exists.",
        "es": "Ese nombre de cuenta ya existe.",
    },
    "servers.accounts_col_linked": {"en": "Linked servers", "es": "Servidores vinculados"},
    "servers.accounts_link_solo": {"en": "Only this server", "es": "Solo este servidor"},
    "servers.accounts_col_name": {"en": "Name", "es": "Nombre"},
    "servers.accounts_col_server": {"en": "Server", "es": "Servidor"},
    "servers.accounts_col_actions": {"en": "Actions", "es": "Acciones"},
    "servers.accounts_modal_create": {"en": "New account", "es": "Nueva cuenta"},
    "servers.accounts_modal_edit": {"en": "Edit account", "es": "Editar cuenta"},
    "servers.accounts_edit_servers_title": {
        "en": "Edit servers for",
        "es": "Editar servidores de",
    },
    "servers.accounts_rename": {
        "en": "Change account name",
        "es": "Cambiar nombre de la cuenta",
    },
    "servers.accounts_edit_servers_info_title": {
        "en": "Edit servers",
        "es": "Editar servidores",
    },
    "servers.accounts_edit_servers_hint": {
        "en": "Pick a server to review credentials, test the API, and fix issues before publishing. For Dailymotion, YouTube, X and similar, “Linked” appears only after you click Connect and authorize the account — saving the API Key is not enough.",
        "es": "Elige un servidor para revisar credenciales, probar la API y corregir errores antes de publicar. En Dailymotion, YouTube, X y similares, «Vinculado» aparece solo después de pulsar Conectar y autorizar la cuenta: guardar la API Key no basta.",
    },
    "servers.accounts_server_linked": {"en": "Connected", "es": "Conectado"},
    "servers.accounts_server_api_ready": {
        "en": "API saved · connect",
        "es": "API lista · conectar",
    },
    "servers.accounts_server_not_linked": {"en": "Disconnected", "es": "Desconectado"},
    "servers.accounts_platform": {"en": "Server", "es": "Servidor"},
    "servers.accounts_edit": {"en": "Edit", "es": "Editar"},
    "servers.accounts_delete": {"en": "Delete account", "es": "Eliminar cuenta"},
    "servers.accounts_toggle": {
        "en": "Enable or disable account",
        "es": "Activar o desactivar cuenta",
    },
    "servers.accounts_confirm_delete": {
        "en": "Delete this account?",
        "es": "¿Eliminar esta cuenta?",
    },
    "servers.accounts_confirm_delete_group": {
        "en": "Delete this account and all linked servers?",
        "es": "¿Eliminar esta cuenta y todos los servidores vinculados?",
    },
    "servers.accounts_saved": {"en": "Account saved.", "es": "Cuenta guardada."},
    "servers.accounts_deleted": {"en": "Account deleted.", "es": "Cuenta eliminada."},
    "servers.accounts_name_required": {"en": "Enter a name.", "es": "Escribe un nombre."},
    "servers.accounts_platform_required": {
        "en": "Select a server.",
        "es": "Selecciona un servidor.",
    },
    "servers.accounts_not_found": {"en": "Account not found.", "es": "Cuenta no encontrada."},
    "servers.accounts_save_fail": {
        "en": "Could not save the account.",
        "es": "No se pudo guardar la cuenta.",
    },
    "servers.limits_title": {
        "en": "File compression",
        "es": "Compresión de archivos",
    },
    "servers.limits_hint": {
        "en": "What this panel can publish with the official APIs. Comments from each network are not synced yet.",
        "es": "Lo que este panel puede publicar con las APIs oficiales. Los comentarios de cada red aún no se sincronizan.",
    },
    "servers.col_platform": {"en": "Platform", "es": "Plataforma"},
    "servers.col_video": {"en": "Videos", "es": "Videos"},
    "servers.col_photo": {"en": "Photos", "es": "Fotos"},
    "servers.col_comment": {"en": "Comments", "es": "Comentarios"},
    "servers.col_note": {"en": "Notes", "es": "Notas"},
    "cap.yes": {"en": "Yes", "es": "Sí"},
    "cap.no": {"en": "No", "es": "No"},
    "cap.limited": {"en": "Limited", "es": "Limitado"},
    "limits.note.tiktok": {
        "en": "Video only. Connect a TikTok account. Photos are not supported.",
        "es": "Solo video. Conecta una cuenta de TikTok. Las fotos no se publican.",
    },
    "limits.note.youtube": {
        "en": "Videos only. Clips of 3 minutes or less upload as Shorts. No photo posts.",
        "es": "Solo videos. Los de 3 minutos o menos se suben como Shorts. Sin publicaciones de foto.",
    },
    "limits.note.instagram": {
        "en": "Professional account. Feed photos and Reels. Photos need a public https SITE_URL (not localhost).",
        "es": "Cuenta profesional. Fotos del feed y Reels. Las fotos necesitan un SITE_URL público https (no localhost).",
    },
    "limits.note.facebook": {
        "en": "Pages only (not personal profiles). Photos and videos.",
        "es": "Páginas (no perfiles personales): fotos y videos.",
    },
    "limits.note.threads": {
        "en": "No official API in this panel yet. Connect with VMOS Threads (cloud phone).",
        "es": "Aún no hay API oficial en este panel. Conecta con VMOS Threads (móvil en la nube).",
    },
    "limits.note.x": {
        "en": "Photos, GIF and short video. Paid X API access is required to publish.",
        "es": "Fotos, GIF y video corto. Hace falta acceso de pago a la API de X para publicar.",
    },
    "limits.note.dailymotion": {
        "en": "Video only. Connect a Dailymotion account; uploads go to that channel.",
        "es": "Solo video. Conecta una cuenta de Dailymotion; las subidas van a ese canal.",
    },
    "limits.note.bilibili": {
        "en": "Videos only (稿件) on Bilibili.com. Connect with QR in Servers, or with a company Open Platform app. Needs ffmpeg for the cover.",
        "es": "Solo video (稿件) en Bilibili.com. Conecta con QR en Servidores, o con una app de empresa en Open Platform. Hace falta ffmpeg para la portada.",
    },
    "limits.note.bilibili_tv": {
        "en": "Bilibili.tv (international). Sign in from Servers with email and password. Isolated browser profile per account; keep-alive every 3–5 days at staggered hours; re-login if the session expired. Videos go to studio.bilibili.tv; the post is only marked sent if Bilibili.tv returns a video id.",
        "es": "Bilibili.tv (internacional). En Servidores entra con email y contraseña. Perfil de navegador por cuenta; keep-alive cada 3–5 días a horas distintas; si la sesión caduca, vuelve a entrar. Los videos salen por studio.bilibili.tv; el post solo se marca enviado si Bilibili.tv devuelve un id.",
    },
    "limits.note.rumble": {
        "en": "No public OAuth. Partner Upload API: access token + Channel ID. Videos only.",
        "es": "Sin OAuth público. Upload API de partners: access token y Channel ID. Solo video.",
    },
    "limits.note.snapchat": {
        "en": "Public Profile: photos as 24h Stories; MP4 min. 5 s (Spotlight 6–55 s, min. 540×960). Videos over 55 s are trimmed to the first 55 s. Needs OpenSSL.",
        "es": "Perfil público: fotos como Stories de 24 h; MP4 mín. 5 s (Spotlight 6–55 s, mín. 540×960). Si pasa de 55 s se recorta a los primeros 55 s. Hace falta OpenSSL.",
    },
    "limits.note.doodstream": {
        "en": "Video only. API key from DoodStream dashboard. Payout is on the host (PPV ads), not in this panel.",
        "es": "Solo video. API key del panel de DoodStream. El cobro es en el host (anuncios PPV), no en este panel.",
    },
    "limits.note.streamwish": {
        "en": "Video only. API key from StreamWish dashboard. Payout is on the host (PPV ads), not in this panel.",
        "es": "Solo video. API key del panel de StreamWish. El cobro es en el host (anuncios PPV), no en este panel.",
    },
    "limits.note.filemoon": {
        "en": "Video only. API key from FileMoon dashboard. Payout is on the host (PPV ads), not in this panel.",
        "es": "Solo video. API key del panel de FileMoon. El cobro es en el host (anuncios PPV), no en este panel.",
    },
    "limits.note.mixdrop": {
        "en": "Video only. MixDrop API email + key. Payout is on MixDrop, not in this panel.",
        "es": "Solo video. Email + API key de MixDrop. El cobro es en MixDrop, no en este panel.",
    },
    "limits.note.streamtape": {
        "en": "Video only. Streamtape API login + key. Payout is on Streamtape, not in this panel.",
        "es": "Solo video. API login + key de Streamtape. El cobro es en Streamtape, no en este panel.",
    },
    "limits.note.voe": {
        "en": "Video only. API key from VOE dashboard. Payout is on the host (PPV ads), not in this panel.",
        "es": "Solo video. API key del panel de VOE. El cobro es en el host (anuncios PPV), no en este panel.",
    },
    "limits.note.vidoza": {
        "en": "Video only. API key from Vidoza dashboard. Payout is on the host (PPV ads), not in this panel.",
        "es": "Solo video. API key del panel de Vidoza. El cobro es en el host (anuncios PPV), no en este panel.",
    },
    "limits.note.lulustream": {
        "en": "Video only. API key from LuluStream dashboard. Payout is on the host (PPV ads), not in this panel.",
        "es": "Solo video. API key del panel de LuluStream. El cobro es en el host (anuncios PPV), no en este panel.",
    },
    "limits.note.loadvid": {
        "en": "Trial payout host. Video only. API key from Loadvid. Marked (pago) until payouts are proven.",
        "es": "Host de prueba de cobro. Solo video. API key de Loadvid. Marcado (pago) hasta comprobar que pagan.",
    },
    "limits.note.vidsonic": {
        "en": "Trial payout host. Video only. API key from VidSonic. Marked (pago) until payouts are proven.",
        "es": "Host de prueba de cobro. Solo video. API key de VidSonic. Marcado (pago) hasta comprobar que pagan.",
    },
    "limits.note.flyfile": {
        "en": "Trial payout host. Video only. API key header from FlyFile. Marked (pago) until payouts are proven.",
        "es": "Host de prueba de cobro. Solo video. API key de FlyFile. Marcado (pago) hasta comprobar que pagan.",
    },
    "limits.note.venvo": {
        "en": "Trial payout host. Video only. API key from VenVo. Marked (pago) until payouts are proven.",
        "es": "Host de prueba de cobro. Solo video. API key de VenVo. Marcado (pago) hasta comprobar que pagan.",
    },
    "api.save": {"en": "Save API", "es": "Guardar API"},
    "api.test": {"en": "Test API", "es": "Probar API"},
    "api.test_all": {"en": "Test all APIs", "es": "Probar todas las APIs"},
    "api.section": {"en": "API credentials", "es": "Credenciales de API"},
    "api.saved": {"en": "API credentials saved.", "es": "Credenciales de API guardadas."},
    "api.clear": {"en": "Remove API", "es": "Quitar API"},
    "api.cleared": {
        "en": "API credentials removed. The server is unlinked.",
        "es": "Credenciales de API eliminadas. El servidor quedó desvinculado.",
    },
    "api.clear_confirm": {
        "en": "Remove the saved API keys? The server will show as not linked until you connect again.",
        "es": "¿Quitar las claves de API guardadas? El servidor quedará sin vincular hasta que conectes de nuevo.",
    },
    "api.keep_secret": {
        "en": "Leave blank to keep the current secret.",
        "es": "Déjalo vacío para mantener el secreto actual.",
    },
    "api.field.name": {"en": "Name", "es": "Nombre"},
    "api.field.client_id": {"en": "Client ID", "es": "Client ID"},
    "api.field.client_id.tiktok": {"en": "Client Key", "es": "Client Key"},
    "api.field.client_id.instagram": {"en": "App ID", "es": "App ID"},
    "api.field.client_id.facebook": {"en": "App ID", "es": "App ID"},
    "api.field.client_id.dailymotion": {"en": "API Key", "es": "API Key"},
    "api.field.client_secret": {"en": "Client secret", "es": "Client secret"},
    "api.field.client_secret.dailymotion": {"en": "API Secret", "es": "API Secret"},
    "api.field.access_token": {"en": "Access token", "es": "Token de acceso"},
    "api.field.extra.tiktok": {"en": "Redirect URI", "es": "URI de redirección"},
    "api.field.extra.youtube": {
        "en": "API key (optional, for tests only)",
        "es": "API key (opcional, solo para pruebas)",
    },
    "api.field.extra.instagram": {
        "en": "Redirect URI registered in Meta (must match exactly)",
        "es": "Redirect URI registrada en Meta (tiene que coincidir exacta)",
    },
    "api.field.extra.facebook": {
        "en": "Redirect URI registered in Meta (must match exactly)",
        "es": "Redirect URI registrada en Meta (tiene que coincidir exacta)",
    },
    "api.field.extra.x": {
        "en": "Callback URI registered in the X portal (must match exactly)",
        "es": "Callback URI registrada en el portal de X (tiene que coincidir exacta)",
    },
    "api.field.extra.dailymotion": {
        "en": "Callback URL registered in Dailymotion Studio (must match exactly)",
        "es": "Callback URL registrada en Dailymotion Studio (tiene que coincidir exacta)",
    },
    "api.field.extra.bilibili": {
        "en": "Callback URL registered in Bilibili Open Platform (must match exactly)",
        "es": "Callback URL registrada en Bilibili Open Platform (tiene que coincidir exacta)",
    },
    "api.field.extra.snapchat": {
        "en": "Redirect URI registered in Snap (must match exactly)",
        "es": "Redirect URI registrada en Snap (tiene que coincidir exacta)",
    },
    "api.never_tested": {"en": "Not tested yet", "es": "Aún no se ha probado"},
    "api.ok": {"en": "Working", "es": "Funciona"},
    "api.fail": {"en": "Failed", "es": "Falló"},
    "api.unknown_platform": {"en": "Unknown platform.", "es": "Plataforma desconocida."},
    "api.need_credentials": {
        "en": "Save Client ID, secret, or access token first.",
        "es": "Guarda primero Client ID, secreto o token de acceso.",
    },
    "api.saved_no_live_token": {
        "en": "Keys saved. Add an access token to run a live publish/comment check.",
        "es": "Claves guardadas. Añade un token de acceso para una prueba real de publicar/comentar.",
    },
    "api.http_fail": {"en": "Server error (HTTP {status}).", "es": "Error del servidor (HTTP {status})."},
    "api.graph_fail": {"en": "API error: {error}", "es": "Error de API: {error}"},
    "api.err.generic": {
        "en": "Could not verify the connection. Check your credentials and try again.",
        "es": "No se pudo verificar la conexión. Revisa las credenciales e inténtalo de nuevo.",
    },
    "api.err.token_expired": {
        "en": "The {platform} session is invalid or expired. Reconnect the account from the panel.",
        "es": "La sesión de {platform} no es válida o expiró. Vuelve a conectar la cuenta desde el panel.",
    },
    "api.err.bad_client": {
        "en": "The {platform} Client ID or secret is incorrect. Copy them from the developer console.",
        "es": "El Client ID o el secreto de {platform} no son correctos. Cópialos desde la consola del desarrollador.",
    },
    "api.err.invalid_credentials": {
        "en": "These credentials do not look valid. Check the Client ID and secret.",
        "es": "Las credenciales no parecen válidas. Revisa el Client ID y el secreto.",
    },
    "api.err.need_secret": {
        "en": "Client secret is missing. Fill it in and try again.",
        "es": "Falta el Client secret. Complétalo y vuelve a probar.",
    },
    "api.err.permission_denied": {
        "en": "{platform} denied access. Check the app permissions in the developer console.",
        "es": "{platform} rechazó el acceso. Revisa los permisos de la app en la consola.",
    },
    "api.err.redirect_mismatch": {
        "en": "The redirect URI does not match the one registered in the developer console.",
        "es": "La URI de redirección no coincide con la registrada en la consola.",
    },
    "api.err.rate_limit": {
        "en": "Request limit reached. Wait a few minutes and try again.",
        "es": "Se alcanzó el límite de peticiones. Espera unos minutos y vuelve a intentar.",
    },
    "api.err.network": {
        "en": "Could not reach the server. Check your connection and try again.",
        "es": "No se pudo contactar con el servidor. Revisa tu conexión e inténtalo de nuevo.",
    },
    "api.err.detail": {
        "en": "{detail}",
        "es": "{detail}",
    },
    "api.tiktok.token_ok": {
        "en": "Linked TikTok account works (@{name}).",
        "es": "La cuenta TikTok vinculada funciona (@{name}).",
    },
    "api.tiktok.token_fail": {
        "en": "TikTok token failed: {error}",
        "es": "Falló el token de TikTok: {error}",
    },
    "api.tiktok.client_ok": {
        "en": "TikTok app credentials were accepted. Connect an account to publish.",
        "es": "Las credenciales de la app TikTok fueron aceptadas. Conecta una cuenta para publicar.",
    },
    "api.tiktok.bad_client": {
        "en": "TikTok rejected the Client Key or Client Secret.",
        "es": "TikTok rechazó el Client Key o el Client Secret.",
    },
    "api.tiktok.dummy": {
        "en": "Those values look like placeholders. Use the real Client Key and Client Secret from TikTok Developer.",
        "es": "Esos valores parecen de prueba. Usa el Client Key y Client Secret reales de TikTok Developer.",
    },
    "api.tiktok.probe_fail": {
        "en": "TikTok did not accept the app credentials: {error}",
        "es": "TikTok no aceptó las credenciales de la app: {error}",
    },
    "api.youtube.token_ok": {"en": "YouTube OAuth token works.", "es": "El token OAuth de YouTube funciona."},
    "api.youtube.client_ok": {
        "en": "YouTube app credentials were accepted. Connect an account to publish.",
        "es": "Las credenciales de la app de YouTube se aceptaron. Conecta una cuenta para publicar.",
    },
    "api.youtube.key_ok": {"en": "YouTube API key works.", "es": "La API key de YouTube funciona."},
    "api.youtube.fail": {"en": "YouTube error: {error}", "es": "Error de YouTube: {error}"},
    "api.instagram.ok": {"en": "Instagram works (@{name}).", "es": "Instagram funciona (@{name})."},
    "api.instagram.client_ok": {
        "en": "Instagram app credentials were saved. Connect an account to publish.",
        "es": "Las credenciales de la app de Instagram se guardaron. Conecta una cuenta para publicar.",
    },
    "api.instagram.fail": {"en": "Instagram error: {error}", "es": "Error de Instagram: {error}"},
    "api.facebook.ok": {"en": "Facebook Page works ({name}).", "es": "La Página de Facebook funciona ({name})."},
    "api.facebook.client_ok": {
        "en": "Facebook app credentials were saved. Connect a Page to publish.",
        "es": "Las credenciales de la app de Facebook se guardaron. Conecta una Página para publicar.",
    },
    "api.facebook.fail": {"en": "Facebook error: {error}", "es": "Error de Facebook: {error}"},
    "api.x.ok": {"en": "X works (@{name}).", "es": "X funciona (@{name})."},
    "api.x.client_ok": {
        "en": "X app credentials were saved. Connect an account to publish.",
        "es": "Las credenciales de la app de X se guardaron. Conecta una cuenta para publicar.",
    },
    "api.x.fail": {"en": "X API error: {error}", "es": "Error de API de X: {error}"},
    "api.dailymotion.ok": {"en": "Dailymotion works ({name}).", "es": "Dailymotion funciona ({name})."},
    "api.dailymotion.client_ok": {
        "en": "Dailymotion app credentials were saved. Connect an account to publish.",
        "es": "Las credenciales de la app de Dailymotion se guardaron. Conecta una cuenta para publicar.",
    },
    "api.dailymotion.fail": {"en": "Dailymotion error: {error}", "es": "Error de Dailymotion: {error}"},
    "api.bilibili.ok": {
        "en": "Bilibili works ({name}).",
        "es": "Bilibili funciona ({name}).",
    },
    "api.bilibili.client_ok": {
        "en": "Bilibili app credentials were saved. Connect an account to publish.",
        "es": "Las credenciales de la app de Bilibili se guardaron. Conecta una cuenta para publicar.",
    },
    "api.bilibili.fail": {"en": "Bilibili error: {error}", "es": "Error de Bilibili: {error}"},
    "api.rumble.ok": {
        "en": "Rumble Upload API accepted the token (channel {channel}).",
        "es": "La Upload API de Rumble aceptó el token (canal {channel}).",
    },
    "api.rumble.token_ok": {
        "en": "Rumble Upload API accepted the token. Add a Channel ID to publish.",
        "es": "La Upload API de Rumble aceptó el token. Añade un Channel ID para publicar.",
    },
    "api.rumble.fail": {"en": "Rumble error: {error}", "es": "Error de Rumble: {error}"},
    "api.filehost.ok": {
        "en": "Host API works ({name}).",
        "es": "La API del host funciona ({name}).",
    },
    "api.filehost.fail": {
        "en": "Host API error: {error}",
        "es": "Error de la API del host: {error}",
    },
    "api.filehost.need_account": {
        "en": "Connect this host in Servers with an API key first.",
        "es": "Primero conecta este host en Servidores con una API key.",
    },
    "api.chain.ok": {
        "en": "Account works ({name}).",
        "es": "La cuenta funciona ({name}).",
    },
    "api.chain.fail": {
        "en": "Connection error: {error}",
        "es": "Error de conexión: {error}",
    },
    "odysee.err_auth": {
        "en": "Odysee rejected the login from this server (same message as a wrong password). If you can sign in at odysee.com, the VPS IP is blocked: assign a residential proxy to this account in Proxies, Save account again, then republish.",
        "es": "Odysee rechazó el login desde este servidor (el mismo aviso que si la contraseña fallara). Si en odysee.com sí entra, la IP del VPS está bloqueada: en Proxys vincula un proxy residencial a esta cuenta, vuelve a Guardar cuenta y luego republica.",
    },
    "odysee.err_app_id": {
        "en": "Odysee blocked the test before checking your password (invalid install ID). Reload Servers and try again.",
        "es": "Odysee cortó la prueba antes de revisar tu contraseña (identificador de instalación no válido). Recarga Servidores y vuelve a Probar API.",
    },
    "odysee.err_user": {
        "en": "Odysee does not have an account with that email.",
        "es": "Odysee no tiene una cuenta con ese email.",
    },
    "odysee.err_password": {
        "en": "The Odysee password is not correct.",
        "es": "La contraseña de Odysee no es correcta.",
    },
    "odysee.err_generic": {
        "en": "Odysee could not verify the account ({error}). Confirm you can sign in at odysee.com with that email and password.",
        "es": "Odysee no pudo verificar la cuenta ({error}). Confirma que puedes entrar en odysee.com con ese email y contraseña.",
    },
    "odysee.err_2fa": {
        "en": "This Odysee account has extra verification (2FA / email code). The panel cannot complete that step yet.",
        "es": "Esta cuenta de Odysee pide verificación extra (2FA / código al email). El panel aún no puede completar ese paso.",
    },
    "odysee.err_unverified": {
        "en": "Odysee asked to verify the email before signing in. Open odysee.com, confirm the email, then try again.",
        "es": "Odysee pide verificar el email antes de entrar. Entra en odysee.com, confirma el correo y vuelve a probar.",
    },
    "odysee.err_recaptcha": {
        "en": "Odysee required a captcha. Sign in once at odysee.com in the browser, then try again here.",
        "es": "Odysee pidió un captcha. Entra una vez en odysee.com en el navegador y luego vuelve a probar aquí.",
    },
    "api.chain.need_account": {
        "en": "Connect this network in Servers first.",
        "es": "Primero conecta esta red en Servidores.",
    },
    "bilibili_tv.err_playwright": {
        "en": "Playwright/Chromium is not installed on this server. Run: pip install -r requirements.txt && playwright install chromium",
        "es": "Playwright/Chromium no está instalado en este servidor. Ejecuta: pip install -r requirements.txt && playwright install chromium",
    },
    "bilibili_tv.err_website": {
        "en": "Could not open the Bilibili.tv login modal (Sign In → age checkbox → Log in with Phone/Email → Account). Nothing was marked as sent. Try again in Servers; complete captcha there if it appears.",
        "es": "No se pudo abrir el login de Bilibili.tv (Sign In → casilla de 13 años → Log in with Phone/Email → Account). No se marcó como enviado. Reintenta en Servidores; si sale captcha, lo completas ahí.",
    },
    "bilibili_tv.err_captcha": {
        "en": "Bilibili.tv asked for captcha or SMS. Complete that check yourself; the panel will not guess codes. Then save the account again.",
        "es": "Bilibili.tv pidió captcha o SMS. Completa esa comprobación tú; el panel no adivina códigos. Luego vuelve a guardar la cuenta.",
    },
    "bilibili_tv.err_session": {
        "en": "The Bilibili.tv session expired. Open Servers, save the account again, and complete login if the site asks.",
        "es": "La sesión de Bilibili.tv caducó. Abre Servidores, vuelve a guardar la cuenta y completa el login si la web lo pide.",
    },
    "bilibili_tv.err_login": {
        "en": "Bilibili.tv did not accept this email and password.",
        "es": "Bilibili.tv no aceptó este email y contraseña.",
    },
    "bilibili_tv.err_busy": {
        "en": "The internal browser is already in use (another Bilibili.tv account). Wait a minute and try again.",
        "es": "El navegador interno ya está ocupado (otra cuenta de Bilibili.tv). Espera un minuto y reintenta.",
    },
    "bilibili_tv.err_browser": {
        "en": "The internal browser could not open Bilibili.tv. The post was not sent.",
        "es": "El navegador interno no pudo abrir Bilibili.tv. El post no se envió.",
    },
    "bilibili_tv.saved_captcha": {
        "en": "Account saved. Bilibili.tv asked for captcha or SMS — the session is not active until you complete that check.",
        "es": "Cuenta guardada. Bilibili.tv pidió captcha o SMS: la sesión no está activa hasta que completes esa comprobación.",
    },
    "dtube.err_website": {
        "en": "Could not use the d.tube website (login or upload form changed). Nothing was marked as sent.",
        "es": "No se pudo usar la web de d.tube (cambió el login o el formulario de subida). No se marcó nada como enviado.",
    },
    "dtube.err_captcha": {
        "en": "Cloudflare on d.tube asked for human verification (Turnstile) and blocked the automated upload. The video was not sent.",
        "es": "Cloudflare en d.tube pidió verificación humana (Turnstile) y bloqueó la subida automática. El vídeo no se envió.",
    },
    "dtube.err_session": {
        "en": "The d.tube session expired and re-login failed. Open Servers and save the account again.",
        "es": "La sesión de d.tube caducó y el re-login falló. Abre Servidores y vuelve a guardar la cuenta.",
    },
    "dtube.err_login": {
        "en": "d.tube did not accept this email and password.",
        "es": "d.tube no aceptó este email y contraseña.",
    },
    "dtube.err_busy": {
        "en": "The internal browser is already in use. Wait a minute and try again.",
        "es": "El navegador interno ya está ocupado. Espera un minuto y reintenta.",
    },
    "dtube.err_browser": {
        "en": "The internal browser could not open d.tube. The post was not sent.",
        "es": "El navegador interno no pudo abrir d.tube. El post no se envió.",
    },
    "dtube.err_upload": {
        "en": "d.tube did not confirm the upload (error or timeout). Check the account on d.tube before retrying.",
        "es": "d.tube no confirmó la subida (error o tiempo agotado). Revisa la cuenta en d.tube antes de reintentar.",
    },
    "dtube.saved_captcha": {
        "en": "Account saved. d.tube asked for extra verification — the session is not active until you complete that check.",
        "es": "Cuenta guardada. d.tube pidió una verificación extra: la sesión no está activa hasta que completes esa comprobación.",
    },
    "bilibili_tv.alert_subject": {
        "en": "[{site}] Bilibili.tv session: {login}",
        "es": "[{site}] Sesión Bilibili.tv: {login}",
    },
    "bilibili_tv.alert_body": {
        "en": "Bilibili.tv account {login}:\n\n{detail}\n\nOpen Servers, reconnect if needed. Nothing was marked as published.",
        "es": "Cuenta de Bilibili.tv {login}:\n\n{detail}\n\nAbre Servidores y vuelve a conectar si hace falta. No se marcó nada como publicado.",
    },
    "api.snapchat.ok": {
        "en": "Snapchat public profile works ({name}).",
        "es": "El perfil público de Snapchat funciona ({name}).",
    },
    "api.snapchat.client_ok": {
        "en": "Snapchat app credentials were saved. Connect an account to publish.",
        "es": "Las credenciales de la app de Snapchat se guardaron. Conecta una cuenta para publicar.",
    },
    "api.snapchat.fail": {"en": "Snapchat error: {error}", "es": "Error de Snapchat: {error}"},
    "servers.ref_team": {"en": "Team", "es": "Equipo"},
    "servers.ref_servers": {"en": "Servers", "es": "Servidores"},
    "pub.no_accounts_hint": {
        "en": "Create accounts in {servers}, then link them to this user in {team}.",
        "es": "Crea cuentas en {servers} y vincúlalas a este usuario en {team}.",
    },
    "pub.no_accounts_tiktok_hint": {
        "en": "Connect your platforms to publish.",
        "es": "Conecta tus plataformas para publicar.",
    },
    "pub.no_accounts_title": {
        "en": "No accounts registered",
        "es": "No hay cuentas registradas",
    },
    "pub.no_tiktok_linked": {
        "en": "This account has no TikTok linked.",
        "es": "Esta cuenta no tiene TikTok vinculado.",
    },
    "pub.publish_video": {"en": "Publish video", "es": "Publicar video"},
    "pub.platforms_toggle": {
        "en": "Show or hide platforms",
        "es": "Mostrar u ocultar plataformas",
    },
    "pub.formats_hint": {
        "en": "MP4, WebM, MOV, MKV (max. 100 MB).",
        "es": "MP4, WebM, MOV, MKV (máx. 100 MB).",
    },
    "pub.select_account": {
        "en": "Select account to publish",
        "es": "Seleccionar cuenta a publicar",
    },
    "pub.publish_account_search": {
        "en": "Search account to publish to",
        "es": "Buscar cuenta a publicar",
    },
    "pub.publish_account_empty": {
        "en": "This account has no linked servers.",
        "es": "Esta cuenta no tiene servidores vinculados.",
    },
    "pub.publish_account_search_ph": {
        "en": "Search account…",
        "es": "Buscar cuenta…",
    },
    "pub.assign_in_team": {"en": "(assign in Team)", "es": "(asignar en Equipo)"},
    "pub.account_selected": {"en": "Account selected: {name}", "es": "Cuenta seleccionada: {name}"},
    "pub.unlock_team": {
        "en": "Assign this TikTok account to a team user in {team} to unlock publishing.",
        "es": "Asigna esta cuenta TikTok a un usuario del equipo en {team} para desbloquear la publicación.",
    },
    "pub.publishing_as": {"en": "Publishing as", "es": "Publicando como"},
    "pub.dropzone_text": {
        "en": "Drag your video here",
        "es": "Arrastra tu video aquí",
    },
    "pub.dropzone_publisher_hint": {
        "en": "Videos of 60 seconds or more only. Photos are not allowed.",
        "es": "Solo videos de 60 segundos o más. No se admiten fotos.",
    },
    "pub.browse_files": {"en": "Browse files", "es": "Explorar archivos"},
    "pub.remove_file": {"en": "Remove file", "es": "Quitar archivo"},
    "pub.cancel_job": {"en": "Cancel this video", "es": "Cancelar este video"},
    "pub.captions_uploading": {
        "en": "Wait, the video is still uploading…",
        "es": "Espera, el video se está subiendo…",
    },
    "pub.flash.wait_upload": {
        "en": "Wait, the video is still uploading. It will publish when the upload finishes.",
        "es": "Espera, el video se está subiendo. Se publicará cuando termine la subida.",
    },
    "pub.publishing_job": {
        "en": "Publishing “{title}”…",
        "es": "Publicando «{title}»…",
    },
    "pub.captions_upload_fail": {
        "en": "Could not upload the video. Try again.",
        "es": "No se pudo subir el video. Inténtalo de nuevo.",
    },
    "pub.field_video": {"en": "Video file", "es": "Archivo de video"},
    "pub.caption": {"en": "Optional description", "es": "Descripción opcional"},
    "pub.caption_ph": {
        "en": "Optional description",
        "es": "Descripción opcional",
    },
    "pub.title_internal": {"en": "Title (internal)", "es": "Título (interno)"},
    "pub.field_title": {"en": "Video title", "es": "Título del video"},
    "pub.title_ph": {
        "en": "Required title",
        "es": "Título requerido",
    },
    "pub.publish_btn": {"en": "Publish", "es": "Publicar"},
    "pub.schedule_enable": {
        "en": "Schedule publication",
        "es": "Programar publicación",
    },
    "pub.schedule_submit_btn": {"en": "Schedule", "es": "Programar"},
    "pub.schedule_datetime": {
        "en": "Publication date and time",
        "es": "Fecha y hora de publicación",
    },
    "pub.scheduled_section": {
        "en": "Scheduled publications",
        "es": "Publicaciones programadas",
    },
    "pub.scheduled_col_when": {"en": "Scheduled for", "es": "Programado para"},
    "pub.scheduled_col_title": {"en": "Title", "es": "Título"},
    "pub.scheduled_col_platforms": {"en": "Platforms", "es": "Plataformas"},
    "pub.scheduled_empty": {
        "en": "No scheduled publications.",
        "es": "No hay publicaciones programadas.",
    },
    "pub.flash.scheduled": {
        "en": "Publication scheduled for {when} (Chicago / Colombia time).",
        "es": "Publicación programada para {when} (hora Chicago / Colombia).",
    },
    "pub.flash.queued_spacing": {
        "en": "Queued for this account. It will publish at {when} (at least 20 minutes after the previous video).",
        "es": "En cola para esta cuenta. Se publicará a las {when} (mínimo 20 minutos después del video anterior).",
    },
    "pub.flash.queued_daily_cap": {
        "en": "This account already has 5 videos in 24 hours. Queued until {when}.",
        "es": "Esta cuenta ya tiene 5 videos en 24 horas. En cola hasta las {when}.",
    },
    "pub.flash.schedule_invalid": {
        "en": "Invalid date or time.",
        "es": "Fecha u hora no válida.",
    },
    "pub.flash.schedule_past": {
        "en": "The scheduled time must be in the future.",
        "es": "La fecha y hora deben ser futuras.",
    },
    "pub.flash.schedule_past_immediate": {
        "en": "The scheduled time had already passed; published immediately.",
        "es": "La hora programada ya había pasado; se publicó de inmediato.",
    },
    "pub.select_account_continue": {
        "en": "Select a TikTok account above to continue.",
        "es": "Selecciona una cuenta TikTok arriba para continuar.",
    },
    "pub.comments_section": {"en": "Comments", "es": "Comentarios"},
    "pub.comments_filter_platform": {"en": "Platform", "es": "Plataforma"},
    "pub.comments_filter_user": {"en": "User", "es": "Usuario"},
    "pub.comments_search_btn": {"en": "Search", "es": "Buscar"},
    "pub.comments_search_hint": {
        "en": "Choose filters and press Search to view comments.",
        "es": "Elige los filtros y pulsa Buscar para ver comentarios.",
    },
    "pub.comments_no_results": {
        "en": "No comments match these filters.",
        "es": "No hay comentarios con estos filtros.",
    },
    "pub.comments_count": {
        "en": "{n} comments",
        "es": "{n} comentarios",
    },
    "pub.comments_scopes": {
        "en": "View and reply to comments on your published videos from this panel. The connected account must have permission to read and reply to comments.",
        "es": "Aquí puedes ver y responder comentarios de tus videos publicados. La cuenta conectada debe tener permiso para leer y responder comentarios.",
    },
    "pub.comments_info_btn": {
        "en": "About comments",
        "es": "Información sobre comentarios",
    },
    "pub.filter_account": {"en": "Filter by account", "es": "Filtrar por cuenta"},
    "pub.recent_inbox": {"en": "Recent inbox", "es": "Bandeja reciente"},
    "pub.no_comments": {
        "en": "No comments in this filter yet.",
        "es": "Aún no hay comentarios con este filtro.",
    },
    "pub.page_of": {
        "en": "Page {page} of {pages} ({total} total).",
        "es": "Página {page} de {pages} ({total} en total).",
    },
    "pub.badge_you": {"en": "You", "es": "Tú"},
    "pub.reply_ph": {"en": "Your reply…", "es": "Tu respuesta…"},
    "pub.reply_btn": {"en": "Reply", "es": "Responder"},
    "pub.pagination": {"en": "Comment pagination", "es": "Paginación de comentarios"},
    "pub.previous": {"en": "← Previous", "es": "← Anterior"},
    "pub.next": {"en": "Next →", "es": "Siguiente →"},
    "pub.flash.published": {
        "en": "Video published. It now appears in the feed and your statistics.",
        "es": "Video publicado. Ya aparece en el feed y en tus estadísticas.",
    },
    "pub.flash.save_fail": {
        "en": "Could not save the video.",
        "es": "No se pudo guardar el video.",
    },
    "pub.flash.no_upload": {
        "en": "Your account cannot upload videos.",
        "es": "Tu cuenta no puede subir videos.",
    },
    "pub.flash.compress_fail": {
        "en": "Could not compress the file under the platform size limit. Install ffmpeg.",
        "es": "No se pudo comprimir el archivo por debajo del tope de la red. Instala ffmpeg.",
    },
    "pub.flash.file_too_large": {
        "en": "File exceeds the maximum size ({max_mb} MB).",
        "es": "El archivo supera el tamaño máximo ({max_mb} MB).",
    },
    "pub.flash.no_comments": {
        "en": "Your account cannot manage comments.",
        "es": "Tu cuenta no puede gestionar comentarios.",
    },
    "pub.flash.reply_published": {"en": "Reply published.", "es": "Respuesta publicada."},
    "pub.flash.sample_comment": {
        "en": "Sample fan comment added.",
        "es": "Comentario de ejemplo añadido.",
    },
    "pub.flash.no_accounts_registered": {
        "en": "No accounts registered. Connect one in the panel.",
        "es": "No hay cuentas registradas. Conecta una en el panel.",
    },
    "pub.flash.no_user_assigned": {
        "en": "That TikTok account has no internal user assigned. Link a team member under Team.",
        "es": "Esa cuenta TikTok no tiene usuario interno asignado. Vincula un miembro del equipo en Equipo.",
    },
    "pub.flash.select_account_publish": {
        "en": "Select which TikTok account to publish to (must have an assigned team user).",
        "es": "Selecciona a qué cuenta TikTok publicar (debe tener un usuario del equipo asignado).",
    },
    "pub.flash.file_type": {
        "en": "File type not allowed. Use: {types}",
        "es": "Tipo de archivo no permitido. Usa: {types}",
    },
    "pub.flash.missing_file": {
        "en": "Upload a photo or video before publishing.",
        "es": "Sube una foto o un video antes de publicar.",
    },
    "pub.flash.missing_file_publisher": {
        "en": "Upload a video of 60 seconds or more before publishing.",
        "es": "Sube un video de 60 segundos o más antes de publicar.",
    },
    "pub.flash.publisher_no_photos": {
        "en": "Publisher accounts can only upload videos, not photos.",
        "es": "Las cuentas de publicador solo pueden subir videos, no fotos.",
    },
    "pub.flash.publisher_min_duration": {
        "en": "Publisher videos must last {seconds} seconds or more.",
        "es": "Los videos de publicador deben durar {seconds} segundos o más.",
    },
    "pub.flash.publisher_duration_unknown": {
        "en": "Could not read the video duration. Use an MP4 of 60 seconds or more.",
        "es": "No se pudo leer la duración del video. Usa un MP4 de 60 segundos o más.",
    },
    "pub.flash.video_in_queue": {
        "en": "That video is already in the queue. Wait until it is published.",
        "es": "Ese video ya está en cola. Espera a que se publique.",
    },
    "pub.flash.video_just_published": {
        "en": "That video was just published. Upload a different one before sending it again.",
        "es": "Ese video acaba de publicarse. Sube uno distinto antes de volver a enviarlo.",
    },
    "pub.flash.missing_description": {
        "en": "Description is required.",
        "es": "La descripción es obligatoria.",
    },
    "pub.flash.missing_title": {
        "en": "Title is required.",
        "es": "El título es obligatorio.",
    },
    "pub.flash.cannot_reply": {
        "en": "You cannot reply on this video.",
        "es": "No puedes responder en este video.",
    },
    "pub.flash.cannot_comment": {
        "en": "You cannot comment on this video.",
        "es": "No puedes comentar en este video.",
    },
    "admin.totals": {"en": "Summary", "es": "Resumen"},
    "admin.single_video_metrics": {
        "en": "Metrics for a single video: <strong>{title}</strong>. Use the dropdown below to switch videos, or pick another account above.",
        "es": "Métricas de un solo video: <strong>{title}</strong>. Usa el menú de abajo para cambiar de video o elige otra cuenta arriba.",
    },
    "admin.tiktoker_totals": {
        "en": "Videos published with this server account.",
        "es": "Videos publicados con esta cuenta de servidores.",
    },
    "admin.your_totals": {
        "en": "Videos you publish here.",
        "es": "Videos que publicas aquí.",
    },
    "admin.no_user_linked": {
        "en": "No internal user linked; there is no content to measure.",
        "es": "No hay usuario interno vinculado; no hay contenido que medir.",
    },
    "admin.tiktoker_metrics_sub": {
        "en": "Metrics for the creator linked to this TikTok account.",
        "es": "Métricas del creador vinculado a esta cuenta TikTok.",
    },
    "admin.account_metrics_sub": {
        "en": "Metrics for videos published with this server account.",
        "es": "Métricas de los videos publicados con esta cuenta de servidores.",
    },
    "admin.per_video_metrics": {"en": "Per-video metrics", "es": "Métricas por video"},
    "admin.all_videos_creator": {
        "en": "All videos from this creator",
        "es": "Todos los videos de este creador",
    },
    "pub.platform_video_soon": {
        "en": "Video publishing for {platform} is not connected yet. Configure API credentials in Servers.",
        "es": "La publicación de video en {platform} aún no está conectada. Configura las credenciales API en Servidores.",
    },
    "pub.platform_no_comments": {
        "en": "This platform does not support comment management via API.",
        "es": "Esta plataforma no admite gestión de comentarios por API.",
    },
    "pub.platforms_title": {"en": "Platforms", "es": "Plataformas"},
    "pub.platforms_hint": {
        "en": "Uncheck a platform to skip it. All are selected by default.",
        "es": "Desmarca una plataforma para no publicar ahí. Todas vienen marcadas por defecto.",
    },
    "pub.col_publish": {"en": "Publish", "es": "Publicar"},
    "pub.col_supports": {"en": "Supports", "es": "Admite"},
    "pub.platforms_support_info_title": {
        "en": "What each platform supports",
        "es": "Qué admite cada plataforma",
    },
    "pub.platforms_support_info_hint": {
        "en": "What this panel can publish on each platform (official APIs).",
        "es": "Lo que este panel puede publicar en cada plataforma (APIs oficiales).",
    },
    "pub.platform_limits_btn": {
        "en": "Limits for {platform}",
        "es": "Límites de {platform}",
    },
    "pub.platform_limits_body": {
        "en": "{safe} Do not exceed that volume: extra uploads can be rejected or throttled. {detail}",
        "es": "{safe} No superes ese volumen: las subidas extra pueden rechazarse o frenarse. {detail}",
    },
    "pub.failure_log": {"en": "Publication log", "es": "Registro de publicaciones"},
    "pub.log_col_platform": {"en": "Platform", "es": "Plataforma"},
    "pub.log_col_status": {"en": "Status", "es": "Estado"},
    "pub.log_col_message": {"en": "Message", "es": "Mensaje"},
    "pub.log_col_date": {"en": "Date", "es": "Fecha"},
    "pub.log_col_user": {"en": "User", "es": "Usuario"},
    "pub.log_status_ok": {"en": "OK", "es": "OK"},
    "pub.log_status_fail": {"en": "Failed", "es": "Falló"},
    "pub.log_status_mixed": {"en": "Mixed", "es": "Mixto"},
    "pub.log_status_skipped": {"en": "Skipped", "es": "Omitido"},
    "pub.log_status_pending": {"en": "Pending", "es": "Pendiente"},
    "pub.log_view": {"en": "View", "es": "Ver"},
    "pub.log_modal_platforms": {"en": "Platforms", "es": "Plataformas"},
    "pub.log_modal_status": {"en": "Status", "es": "Estado"},
    "pub.log_modal_errors": {"en": "Errors", "es": "Errores"},
    "pub.log_platforms_n": {
        "en": "{n} platforms",
        "es": "{n} plataformas",
    },
    "pub.log_search": {
        "en": "Search by status, platform or account…",
        "es": "Buscar por estado, plataforma o cuenta…",
    },
    "pub.log_no_results": {
        "en": "No publications match that search.",
        "es": "Ninguna publicación coincide con esa búsqueda.",
    },
    "pub.log_pagination": {
        "en": "Publication log pagination",
        "es": "Paginación del registro de publicaciones",
    },
    "log.purge_from": {"en": "From", "es": "Desde"},
    "log.purge_to": {"en": "To", "es": "Hasta"},
    "log.purge_delete": {"en": "Delete", "es": "Eliminar"},
    "log.purge_need_dates": {
        "en": "Choose from and to dates.",
        "es": "Elige fecha desde y hasta.",
    },
    "log.purge_invalid": {
        "en": "Invalid dates. Use a range where From is not after To.",
        "es": "Fechas no válidas. Desde no puede ser posterior a Hasta.",
    },
    "log.purge_none": {
        "en": "No records in that date range.",
        "es": "No hay registros en ese rango de fechas.",
    },
    "log.purge_confirm_title": {
        "en": "Delete records",
        "es": "Eliminar registros",
    },
    "log.purge_confirm_pub": {
        "en": "Delete {n} publication records from {from} to {to}? Videos stay; only the log is removed. Stats for those deliveries will no longer count them.",
        "es": "¿Eliminar {n} registros del {from} al {to}? Los videos se conservan; solo se borra el historial. Las estadísticas de esos envíos dejarán de contarlos.",
    },
    "log.purge_confirm_events": {
        "en": "Delete {n} extractor log entries from {from} to {to}?",
        "es": "¿Eliminar {n} entradas del registro del extractor del {from} al {to}?",
    },
    "log.purge_confirm_chat": {
        "en": "Delete {n} support chat messages from {from} to {to}? Threads with no remaining messages disappear.",
        "es": "¿Eliminar {n} mensajes del chat de soporte del {from} al {to}? Los hilos sin mensajes restantes desaparecen.",
    },
    "log.purge_confirm_invites": {
        "en": "Delete {n} invitation codes from {from} to {to}? Users who already registered keep their accounts.",
        "es": "¿Eliminar {n} códigos de invitación del {from} al {to}? Quienes ya se registraron conservan su cuenta.",
    },
    "log.purge_ok": {
        "en": "{n} records deleted.",
        "es": "{n} registros eliminados.",
    },
    "log.purge_cancel": {"en": "Cancel", "es": "Cancelar"},
    "log.purge_confirm_btn": {"en": "Delete", "es": "Eliminar"},
    "log.purge_network": {
        "en": "Network error. Please try again.",
        "es": "Error de red. Inténtalo de nuevo.",
    },
    "pub.fail_no_creds": {
        "en": "API credentials not configured.",
        "es": "Credenciales API no configuradas.",
    },
    "pub.fail_api_test": {
        "en": "API test failed — fix credentials in Servers.",
        "es": "La prueba de API falló — corrige credenciales en Servidores.",
    },
    "pub.fail_no_api": {
        "en": "This platform has no publish API wired. The post was not sent.",
        "es": "Esta plataforma no tiene API de publicación cableada. El post no se envió.",
    },
    "pub.fail_vmos_pending": {
        "en": "VMOS Cloud is saved in Servers, but publishing through the cloud phone is not wired yet. The post was not sent.",
        "es": "VMOS Cloud está guardado en Servidores, pero la publicación por el móvil en la nube aún no está cableada. El post no se envió.",
    },
    "pub.vmos_no_account": {
        "en": "No VMOS Cloud account with Access Key, Secret and padCode for this server.",
        "es": "No hay cuenta VMOS Cloud con Access Key, Secret y padCode para este servidor.",
    },
    "pub.vmos_no_template": {
        "en": "Save the VMOS flow template ID (scriptId) in Servers. The post was not sent.",
        "es": "Guarda el ID de plantilla RPA (scriptId) de VMOS en Servidores. El post no se envió.",
    },
    "pub.vmos_no_file": {
        "en": "The media file was not found. The post was not sent.",
        "es": "No se encontró el archivo. El post no se envió.",
    },
    "pub.vmos_task_failed": {
        "en": "VMOS Cloud task {task} failed. The post was not sent.",
        "es": "La tarea VMOS Cloud {task} falló. El post no se envió.",
    },
    "pub.vmos_ok": {
        "en": "Sent to the VMOS Cloud phone (task {task}, {status}).",
        "es": "Enviado al móvil VMOS Cloud (tarea {task}, {status}).",
    },
    "pub.fail_tiktok_token": {
        "en": "No TikTok account connected with a valid token.",
        "es": "No hay cuenta TikTok conectada con token válido.",
    },
    "pub.skipped_unsupported": {
        "en": "Omitted: {platform} does not accept {kind}.",
        "es": "Omitido: {platform} no admite {kind}.",
    },
    "pub.kind.photo": {"en": "photos", "es": "fotos"},
    "pub.kind.video": {"en": "video", "es": "video"},
    "pub.fail_no_photo": {
        "en": "TikTok does not support still photos via this API.",
        "es": "TikTok no admite fotos fijas con esta API.",
    },
    "pub.ok_sent": {"en": "Sent to {platform}.", "es": "Enviado a {platform}."},
    "pub.tiktok.inbox_ok": {
        "en": "Video sent to the TikTok inbox. Open the TikTok app to finish publishing.",
        "es": "Video enviado a la bandeja de TikTok. Ábrelo en la app para terminar de publicar.",
    },
    "pub.tiktok.direct_ok": {
        "en": "Video uploaded to TikTok.",
        "es": "Video subido a TikTok.",
    },
    "pub.tiktok.upload_fail": {
        "en": "TikTok upload failed: {error}",
        "es": "Falló la subida a TikTok: {error}",
    },
    "pub.tiktok.refresh_fail": {
        "en": "The TikTok token expired. Reconnect the account in Servers.",
        "es": "El token de TikTok caducó. Vuelve a conectar la cuenta en Servidores.",
    },
    "pub.youtube.shorts_ok": {
        "en": "Uploaded to YouTube as a Short ({id}).",
        "es": "Subido a YouTube como Short ({id}).",
    },
    "pub.youtube.pending": {
        "en": "YouTube accepted the video ({id}) and is processing/reviewing it. This entry will update automatically when YouTube accepts it.",
        "es": "YouTube aceptó el video ({id}) y lo está procesando/revisando. Este registro se actualizará solo cuando YouTube lo acepte.",
    },
    "pub.youtube.locked_private": {
        "en": "YouTube left the video ({id}) locked as private. This happens when the app's Google API project is not verified/audited yet. Check YouTube Studio and the app verification in Google Cloud Console.",
        "es": "YouTube dejó el video ({id}) bloqueado en privado. Pasa cuando el proyecto de API de Google de la app aún no está verificado/auditado. Revisa YouTube Studio y la verificación de la app en Google Cloud Console.",
    },
    "pub.youtube.video_ok": {
        "en": "Uploaded to YouTube as a regular video ({id}).",
        "es": "Subido a YouTube como video normal ({id}).",
    },
    "pub.youtube.upload_fail": {
        "en": "YouTube upload failed: {error}",
        "es": "Falló la subida a YouTube: {error}",
    },
    "pub.youtube.err_creds": {
        "en": "YouTube rejected the credentials. Click Connect with YouTube again in Servers.",
        "es": "YouTube rechazó las credenciales. Vuelve a pulsar Conectar con YouTube en Servidores.",
    },
    "pub.youtube.no_token": {
        "en": "Connect a YouTube account from Servers (Connect with YouTube). An API key cannot upload videos.",
        "es": "Conecta una cuenta de YouTube en Servidores (Conectar con YouTube). La API key no sirve para subir.",
    },
    "pub.youtube.no_photo": {
        "en": "YouTube does not accept photo posts. Upload a video or a Short.",
        "es": "YouTube no acepta publicaciones de foto. Sube un video o un Short.",
    },
    "pub.youtube.file_missing": {
        "en": "The video file was not found on the server.",
        "es": "No se encontró el archivo de video en el servidor.",
    },
    "pub.instagram.photo_ok": {
        "en": "Published photo to Instagram ({id}).",
        "es": "Foto publicada en Instagram ({id}).",
    },
    "pub.instagram.pending": {
        "en": "Instagram accepted the video and is still processing it. It will be published automatically when Instagram accepts it; this entry will update on its own.",
        "es": "Instagram aceptó el video y sigue procesándolo. Se publicará automáticamente cuando Instagram lo acepte; este registro se actualizará solo.",
    },
    "pub.instagram.reel_ok": {
        "en": "Published Reel to Instagram ({id}).",
        "es": "Reel publicado en Instagram ({id}).",
    },
    "pub.instagram.upload_fail": {
        "en": "Instagram publish failed: {error}",
        "es": "Falló la publicación en Instagram: {error}",
    },
    "pub.instagram.no_token": {
        "en": "Connect an Instagram account from Servers (Connect with Instagram).",
        "es": "Conecta una cuenta de Instagram en Servidores (Conectar con Instagram).",
    },
    "pub.instagram.file_missing": {
        "en": "The media file was not found on the server.",
        "es": "No se encontró el archivo en el servidor.",
    },
    "pub.instagram.need_public_url": {
        "en": "Instagram must download the file from a public SITE_URL (not localhost). Set SITE_URL to your public https domain.",
        "es": "Instagram tiene que descargar el archivo desde un SITE_URL público (no localhost). Pon SITE_URL con tu dominio https público.",
    },
    "pub.instagram.bad_photo": {
        "en": "Instagram feed photos must be JPG or PNG.",
        "es": "Las fotos del feed de Instagram deben ser JPG o PNG.",
    },
    "pub.instagram.bad_video": {
        "en": "Instagram Reels must be MP4 or MOV.",
        "es": "Los Reels de Instagram deben ser MP4 o MOV.",
    },
    "pub.instagram.bad_file": {
        "en": "Instagram only accepts JPG/PNG photos or MP4/MOV videos.",
        "es": "Instagram solo acepta fotos JPG/PNG o videos MP4/MOV.",
    },
    "pub.facebook.photo_ok": {
        "en": "Published photo to the Facebook Page ({id}).",
        "es": "Foto publicada en la Página de Facebook ({id}).",
    },
    "pub.facebook.video_ok": {
        "en": "Published video to the Facebook Page ({id}).",
        "es": "Video publicado en la Página de Facebook ({id}).",
    },
    "pub.facebook.upload_fail": {
        "en": "Facebook: {error}",
        "es": "Facebook: {error}",
    },
    "pub.facebook.err_dev_mode": {
        "en": "Meta blocked the Page: the app is in Development. Switch it to Live in developers.facebook.com, or add the Page owner as app admin/tester. Then Disconnect and Connect with Facebook again. Tap the Facebook info icon for the steps.",
        "es": "Meta bloqueó la Página: la app está en Desarrollo. Pásala a En vivo en developers.facebook.com, o añade al dueño de la Página como administrador/tester de la app. Luego Desconectar y Conectar con Facebook otra vez. Pulsa el icono i de Facebook para los pasos.",
    },
    "pub.facebook.err_generic": {
        "en": "Facebook rejected the post. Check the Page connection in Servers and the Facebook info icon.",
        "es": "Facebook rechazó la publicación. Revisa la conexión de la Página en Servidores y el icono i de Facebook.",
    },
    "pub.facebook.no_token": {
        "en": "Connect a Facebook Page from Servers (Connect with Facebook).",
        "es": "Conecta una Página de Facebook en Servidores (Conectar con Facebook).",
    },
    "pub.facebook.file_missing": {
        "en": "The media file was not found on the server.",
        "es": "No se encontró el archivo en el servidor.",
    },
    "pub.facebook.bad_photo": {
        "en": "Facebook photos must be JPG, PNG, GIF or WebP.",
        "es": "Las fotos de Facebook deben ser JPG, PNG, GIF o WebP.",
    },
    "pub.facebook.bad_video": {
        "en": "Facebook videos must be MP4 or MOV.",
        "es": "Los videos de Facebook deben ser MP4 o MOV.",
    },
    "pub.facebook.bad_file": {
        "en": "Facebook only accepts photos (JPG/PNG/GIF/WebP) or videos (MP4/MOV).",
        "es": "Facebook solo acepta fotos (JPG/PNG/GIF/WebP) o videos (MP4/MOV).",
    },
    "pub.x.photo_ok": {
        "en": "Published photo to X ({id}).",
        "es": "Foto publicada en X ({id}).",
    },
    "pub.x.video_ok": {
        "en": "Published video to X ({id}).",
        "es": "Video publicado en X ({id}).",
    },
    "pub.x.credits_depleted": {
        "en": "The X developer app used for this post ran out of monthly write credits (X bills the app, not Tuyaho). Wait for the next billing cycle or add another app in Config X.",
        "es": "La app de desarrollador de X que usó este post se quedó sin créditos de escritura del mes (los cobra X a esa app, no es saldo de Tuyaho). Espera al siguiente ciclo de facturación o añade otra app en Config X.",
    },
    "pub.x.no_token": {
        "en": "Connect an X account from Servers (Connect with X).",
        "es": "Conecta una cuenta de X en Servidores (Conectar con X).",
    },
    "pub.x.need_own_api": {
        "en": "This X account is set to use its own API. Save its Client ID and Secret in Servers first.",
        "es": "Esta cuenta de X está marcada para gastar de su propia API. Guarda primero su Client ID y Secret en Servidores.",
    },
    "pub.x.need_funding_api": {
        "en": "No Config X app is available (no keys, or the 9,900 posts / 24 h cap was reached). Add another app or wait.",
        "es": "No hay app de Config X disponible (sin claves o se llegó a 9.900 posts / 24 h). Añade otra app o espera.",
    },
    "pub.x.file_missing": {
        "en": "The media file was not found on the server.",
        "es": "No se encontró el archivo en el servidor.",
    },
    "pub.x.bad_photo": {
        "en": "X photos must be JPG, PNG, WebP or GIF.",
        "es": "Las fotos de X deben ser JPG, PNG, WebP o GIF.",
    },
    "pub.x.bad_video": {
        "en": "X videos must be MP4 or MOV.",
        "es": "Los videos de X deben ser MP4 o MOV.",
    },
    "pub.x.bad_file": {
        "en": "X only accepts photos (JPG/PNG/WebP/GIF) or videos (MP4/MOV).",
        "es": "X solo acepta fotos (JPG/PNG/WebP/GIF) o videos (MP4/MOV).",
    },
    "pub.dailymotion.ok": {
        "en": "Uploaded to Dailymotion ({id}).",
        "es": "Subido a Dailymotion ({id}).",
    },
    "pub.dailymotion.upload_fail": {
        "en": "Dailymotion upload failed: {error}",
        "es": "Falló la subida a Dailymotion: {error}",
    },
    "pub.dailymotion.err_no_user": {
        "en": "The API Key has no user session. The panel will publish to the Studio profile instead of /me.",
        "es": "La API Key no tiene sesión de usuario. El panel publica en el perfil de Studio, no en /me.",
    },
    "pub.dailymotion.err_v2_auth": {
        "en": "The token is not valid for Dailymotion API v2. Connect with Dailymotion again in Servers.",
        "es": "El token no vale para la API v2 de Dailymotion. Vuelve a pulsar Conectar con Dailymotion en Servidores.",
    },
    "pub.dailymotion.err_no_profile": {
        "en": "Dailymotion did not list a channel. Connect with Dailymotion in Servers so the panel can use that channel.",
        "es": "Dailymotion no listó el canal. Pulsa Conectar con Dailymotion en Servidores para usar ese canal.",
    },
    "pub.dailymotion.err_generic": {
        "en": "Check the API Key in Studio and click Connect with Dailymotion again.",
        "es": "Revisa la API Key en Studio y vuelve a pulsar Conectar con Dailymotion.",
    },
    "pub.api_error_generic": {
        "en": "The network rejected the request. Check the connection in Servers.",
        "es": "La red rechazó la petición. Revisa la conexión en Servidores.",
    },
    "pub.dailymotion.no_token": {
        "en": "Connect a Dailymotion account from Servers (Connect with Dailymotion).",
        "es": "Conecta una cuenta de Dailymotion en Servidores (Conectar con Dailymotion).",
    },
    "pub.dailymotion.file_missing": {
        "en": "The video file was not found on the server.",
        "es": "No se encontró el archivo de video en el servidor.",
    },
    "pub.dailymotion.no_photo": {
        "en": "Dailymotion does not accept photo posts. Upload a video.",
        "es": "Dailymotion no acepta publicaciones de foto. Sube un video.",
    },
    "pub.dailymotion.bad_video": {
        "en": "Dailymotion videos must be MP4, MOV, WebM or MKV.",
        "es": "Los videos de Dailymotion deben ser MP4, MOV, WebM o MKV.",
    },
    "pub.bilibili.ok": {
        "en": "Uploaded to Bilibili ({id}).",
        "es": "Subido a Bilibili ({id}).",
    },
    "pub.bilibili.upload_fail": {
        "en": "Bilibili upload failed: {error}",
        "es": "Falló la subida a Bilibili: {error}",
    },
    "pub.bilibili.no_token": {
        "en": "Connect a Bilibili account from Servers (Connect with Bilibili).",
        "es": "Conecta una cuenta de Bilibili en Servidores (Conectar con Bilibili).",
    },
    "pub.bilibili.file_missing": {
        "en": "The video file was not found on the server.",
        "es": "No se encontró el archivo de video en el servidor.",
    },
    "pub.bilibili.no_photo": {
        "en": "Bilibili does not accept photo posts. Upload a video.",
        "es": "Bilibili no acepta publicaciones de foto. Sube un video.",
    },
    "pub.bilibili.bad_video": {
        "en": "Bilibili videos must be MP4, FLV, AVI, WMV, MOV, MKV or WebM.",
        "es": "Los videos de Bilibili deben ser MP4, FLV, AVI, WMV, MOV, MKV o WebM.",
    },
    "pub.rumble.ok": {
        "en": "Uploaded to Rumble ({id}).",
        "es": "Subido a Rumble ({id}).",
    },
    "pub.rumble.upload_fail": {
        "en": "Rumble upload failed: {error}",
        "es": "Falló la subida a Rumble: {error}",
    },
    "pub.rumble.no_token": {
        "en": "Save the Rumble Upload API access token in Servers. Rumble does not offer public OAuth.",
        "es": "Guarda el access token de la Upload API de Rumble en Servidores. Rumble no ofrece OAuth público.",
    },
    "pub.rumble.no_channel": {
        "en": "Save the Rumble Channel ID in Servers (required by the Upload API).",
        "es": "Guarda el Channel ID de Rumble en Servidores (lo exige la Upload API).",
    },
    "pub.rumble.file_missing": {
        "en": "The video file was not found on the server.",
        "es": "No se encontró el archivo de video en el servidor.",
    },
    "pub.rumble.no_photo": {
        "en": "Rumble does not accept photo posts. Upload a video.",
        "es": "Rumble no acepta publicaciones de foto. Sube un video.",
    },
    "pub.rumble.bad_video": {
        "en": "Rumble videos must be MP4, MOV, AVI, WMV, FLV, MKV or WebM.",
        "es": "Los videos de Rumble deben ser MP4, MOV, AVI, WMV, FLV, MKV o WebM.",
    },
    "pub.filehost.ok": {
        "en": "Uploaded to the host: {url}",
        "es": "Subido al host: {url}",
    },
    "pub.filehost.upload_fail": {
        "en": "Host upload failed: {error}",
        "es": "Falló la subida al host: {error}",
    },
    "pub.filehost.no_key": {
        "en": "Connect this host in Servers with an API key first.",
        "es": "Primero conecta este host en Servidores con una API key.",
    },
    "pub.filehost.no_extra": {
        "en": "This host also needs {field} (MixDrop: email, Streamtape: login).",
        "es": "Este host también pide {field} (MixDrop: email, Streamtape: login).",
    },
    "pub.filehost.file_missing": {
        "en": "The video file was not found on the server.",
        "es": "No se encontró el archivo de video en el servidor.",
    },
    "pub.filehost.no_photo": {
        "en": "This host does not accept photo posts. Upload a video.",
        "es": "Este host no acepta publicaciones de foto. Sube un video.",
    },
    "pub.filehost.bad_video": {
        "en": "Host videos must be MP4, MOV, AVI, WMV, FLV, MKV, WebM or M4V.",
        "es": "Los videos del host deben ser MP4, MOV, AVI, WMV, FLV, MKV, WebM o M4V.",
    },
    "pub.chain.no_account": {
        "en": "Connect this network in Servers first.",
        "es": "Primero conecta esta red en Servidores.",
    },
    "pub.bilibili_tv.ok": {
        "en": "Uploaded to Bilibili.tv ({id}).",
        "es": "Subido a Bilibili.tv ({id}).",
    },
    "pub.bilibili_tv.not_wired": {
        "en": "Bilibili.tv is connected (browser session), but studio upload is not wired yet. The post was not sent.",
        "es": "Bilibili.tv está conectado (sesión del navegador), pero la subida al estudio aún no está cableada. El post no se envió.",
    },
    "pub.bilibili_qr.not_wired": {
        "en": "Bilibili.com is connected (QR web session), but studio upload is not wired yet. The post was not sent.",
        "es": "Bilibili.com está conectado (sesión web por QR), pero la subida al estudio aún no está cableada. El post no se envió.",
    },
    "pub.odysee.ok": {
        "en": "Published on Odysee: {url}",
        "es": "Publicado en Odysee: {url}",
    },
    "pub.odysee.upload_fail": {
        "en": "Odysee publish failed: {error}",
        "es": "Falló la publicación en Odysee: {error}",
    },
    "pub.odysee.no_account": {
        "en": "Connect Odysee in Servers with email and password first.",
        "es": "Primero conecta Odysee en Servidores con email y contraseña.",
    },
    "pub.odysee.file_missing": {
        "en": "The video file was not found on the server.",
        "es": "No se encontró el archivo de video en el servidor.",
    },
    "pub.odysee.no_photo": {
        "en": "Odysee from this panel is video only.",
        "es": "Odysee en este panel solo acepta video.",
    },
    "pub.odysee.bad_video": {
        "en": "Odysee videos must be MP4, MOV, AVI, WMV, FLV, MKV, WebM or M4V.",
        "es": "Los videos de Odysee deben ser MP4, MOV, AVI, WMV, FLV, MKV, WebM o M4V.",
    },
    "pub.platform_paused": {
        "en": "{platform} publishing is paused until the platform’s upload API is available again.",
        "es": "La publicación en {platform} está pausada hasta que vuelva a estar disponible la API de subida.",
    },
    "pub.dtube.ok": {
        "en": "Published on DTube: {url}",
        "es": "Publicado en DTube: {url}",
    },
    "pub.dtube.upload_fail": {
        "en": "DTube publish failed: {error}",
        "es": "Falló la publicación en DTube: {error}",
    },
    "pub.dtube.dns_fail": {
        "en": "Could not reach DTube’s upload servers (the address was not found). Try again later; this is not your Hive key.",
        "es": "No se pudo llegar a los servidores de subida de DTube (no se encontró la dirección). Prueba más tarde; no es tu clave Hive.",
    },
    "pub.dtube.timeout": {
        "en": "DTube’s upload servers did not respond in time. Try again later.",
        "es": "Los servidores de subida de DTube no respondieron a tiempo. Prueba más tarde.",
    },
    "pub.dtube.unreachable": {
        "en": "Could not connect to DTube’s upload servers. Try again later.",
        "es": "No se pudo conectar a los servidores de subida de DTube. Prueba más tarde.",
    },
    "pub.dtube.no_account": {
        "en": "Connect DTube in Servers with Hive username and posting WIF first.",
        "es": "Primero conecta DTube en Servidores con usuario Hive y posting WIF.",
    },
    "pub.dtube.bad_wif": {
        "en": "The posting WIF is not valid.",
        "es": "El posting WIF no es válido.",
    },
    "pub.dtube.file_missing": {
        "en": "The video file was not found on the server.",
        "es": "No se encontró el archivo de video en el servidor.",
    },
    "pub.dtube.no_photo": {
        "en": "DTube from this panel is video only.",
        "es": "DTube en este panel solo acepta video.",
    },
    "pub.dtube.bad_video": {
        "en": "DTube videos must be MP4, MOV, AVI, WMV, FLV, MKV, WebM or M4V.",
        "es": "Los videos de DTube deben ser MP4, MOV, AVI, WMV, FLV, MKV, WebM o M4V.",
    },
    "pub.snapchat.ok_spotlight": {
        "en": "Posted to Snapchat Spotlight ({id}).",
        "es": "Publicado en Snapchat Spotlight ({id}).",
    },
    "pub.snapchat.ok_story": {
        "en": "Posted to Snapchat Story ({id}).",
        "es": "Publicado en la Story de Snapchat ({id}).",
    },
    "pub.snapchat.upload_fail": {
        "en": "Snapchat upload failed: {error}",
        "es": "Falló la subida a Snapchat: {error}",
    },
    "pub.snapchat.no_token": {
        "en": "Connect a Snapchat public profile from Servers (Connect with Snapchat).",
        "es": "Conecta un perfil público de Snapchat en Servidores (Conectar con Snapchat).",
    },
    "pub.snapchat.no_profile": {
        "en": "The connected Snapchat account has no public profile id.",
        "es": "La cuenta de Snapchat conectada no tiene id de perfil público.",
    },
    "pub.snapchat.file_missing": {
        "en": "The media file was not found on the server.",
        "es": "No se encontró el archivo en el servidor.",
    },
    "pub.snapchat.bad_photo": {
        "en": "Snapchat Stories photos must be JPG, PNG or WebP.",
        "es": "Las fotos de Stories de Snapchat deben ser JPG, PNG o WebP.",
    },
    "pub.snapchat.bad_video": {
        "en": "Snapchat videos must be MP4.",
        "es": "Los videos de Snapchat deben ser MP4.",
    },
    "pub.snapchat.trim_fail": {
        "en": "Could not trim the video to 55 seconds for Snapchat. Install ffmpeg.",
        "es": "No se pudo recortar el video a 55 segundos para Snapchat. Instala ffmpeg.",
    },
    "pub.snapchat.bad_duration": {
        "en": "Snapchat videos must be at least 5 seconds. Longer than 55 s is trimmed to the first 55 s.",
        "es": "Los videos de Snapchat deben durar al menos 5 segundos. Si pasan de 55 s se recortan a los primeros 55 s.",
    },
    "pub.snapchat.bad_size": {
        "en": "Snapchat video must be at least 540×960 px.",
        "es": "El video de Snapchat debe medir al menos 540×960 px.",
    },
    "pub.snapchat.need_openssl": {
        "en": "Could not encrypt the Snapchat video (AES-256-CBC). Install the Python package cryptography on the server.",
        "es": "No se pudo cifrar el vídeo de Snapchat (AES-256-CBC). Instala el paquete Python cryptography en el servidor.",
    },
    "pub.snapchat.need_allowlist": {
        "en": "Snapchat rejected the upload with 403 (permission denied). The Public Profile API is allowlist-only: email dev-support@snap.com with your OAuth Client ID (from Snap Business Manager, not the Developer Portal) and your use case, and make sure the connected account has the Profile Admin role. Nothing was marked as sent.",
        "es": "Snapchat rechazó la subida con 403 (permiso denegado). La Public Profile API es solo por allowlist: escribe a dev-support@snap.com con tu Client ID de OAuth (de Snap Business Manager, NO del Developer Portal) y tu caso de uso, y asegúrate de que la cuenta conectada tenga el rol Profile Admin. No se marcó nada como enviado.",
    },
    "pub.flash.no_platforms": {
        "en": "Select at least one platform.",
        "es": "Selecciona al menos una plataforma.",
    },
    "pub.flash.pending_review": {
        "en": "Sent. {n} platform(s) accepted the video and are still processing/reviewing it. The log will update automatically when they accept it.",
        "es": "Enviado. {n} plataforma(s) aceptaron el video y siguen procesándolo/revisándolo. El registro se actualizará solo cuando lo acepten.",
    },
    "pub.pending_timeout": {
        "en": "The platform accepted the video but did not finish reviewing it in time. Check the app (YouTube Studio / Instagram) and the info icon.",
        "es": "La plataforma aceptó el video pero no terminó de revisarlo a tiempo. Revisa la app (YouTube Studio / Instagram) y el icono i.",
    },
    "pub.flash.partial": {
        "en": "Saved locally. {ok} OK, {fail} still pending — an admin can republish or cancel below.",
        "es": "Guardado localmente. {ok} OK, {fail} pendientes — un admin puede republicar o cancelar abajo.",
    },
    "pub.flash.all_ok": {
        "en": "Published to {n} platform(s).",
        "es": "Publicado en {n} plataforma(s).",
    },
    "pub.pending_section": {
        "en": "Pending republication",
        "es": "Pendientes de republicar",
    },
    "pub.pending_hint": {
        "en": "These videos stay available until an admin republishes the remaining platforms or cancels. Republish runs in the background; you can leave the page.",
        "es": "Estos videos siguen disponibles hasta que un admin republica en las plataformas restantes o cancela. Republicar trabaja en segundo plano; puedes salir de la página.",
    },
    "pub.pending_col_user": {"en": "User", "es": "Usuario"},
    "pub.pending_col_actions": {"en": "Actions", "es": "Acciones"},
    "pub.retry_in_progress": {
        "en": "Republishing…",
        "es": "Republicando…",
    },
    "pub.retry_modal_title": {
        "en": "Platforms to republish",
        "es": "Plataformas a republicar",
    },
    "pub.retry_remove": {
        "en": "Do not republish {name}",
        "es": "Quitar {name} de esta republicación",
    },
    "pub.retry_remove_title": {
        "en": "Remove {name}?",
        "es": "¿Quitar {name}?",
    },
    "pub.retry_remove_body": {
        "en": "This platform will not be republished. You can add it again below if you change your mind.",
        "es": "Esta plataforma no se republicará. Si te arrepientes, puedes volver a agregarla abajo.",
    },
    "pub.retry_remove_ok": {"en": "Remove", "es": "Quitar"},
    "pub.retry_add_btn": {"en": "Add platforms", "es": "Agregar plataformas"},
    "pub.retry_add_title": {"en": "Add platforms", "es": "Agregar plataformas"},
    "pub.retry_add_none": {
        "en": "No more platforms to add.",
        "es": "No hay más plataformas para agregar.",
    },
    "pub.retry_add_apply": {"en": "Add", "es": "Agregar"},
    "pub.retry_need_one": {
        "en": "Leave at least one platform, or cancel the whole job.",
        "es": "Deja al menos una plataforma, o cancela el envío.",
    },
    "pub.retry_save_fail": {
        "en": "Could not save the platform list. Try again.",
        "es": "No se pudo guardar la lista de plataformas. Inténtalo otra vez.",
    },
    "pub.cancel_pending_btn": {"en": "Cancel", "es": "Cancelar"},
    "pub.cancel_pending_confirm": {
        "en": "Cancel the remaining platforms for this video?",
        "es": "¿Cancelar las plataformas restantes de este video?",
    },
    "pub.pending_cancelled_log": {
        "en": "Remaining publish cancelled by an admin.",
        "es": "Publicación restante cancelada por un administrador.",
    },
    "pub.flash.retry_queued": {
        "en": "Republish started in the background. You can leave this page; the log will update when each platform finishes.",
        "es": "Republicación en segundo plano. Puedes salir de esta página; el registro se actualiza cuando termine cada plataforma.",
    },
    "pub.flash.pending_cancelled": {
        "en": "Remaining publications cancelled. The video is no longer queued.",
        "es": "Publicaciones restantes canceladas. El video ya no está en cola.",
    },
    "pub.flash.pending_gone": {
        "en": "That pending publication is no longer available.",
        "es": "Esa publicación pendiente ya no está disponible.",
    },
    "pub.flash.pending_no_video": {
        "en": "The video record was not found.",
        "es": "No se encontró el registro del video.",
    },
    "pub.flash.pending_no_file": {
        "en": "The video file is missing from disk. It stays pending until you cancel or restore the file.",
        "es": "Falta el archivo del video en disco. Sigue pendiente hasta que canceles o restaures el archivo.",
    },
    "pub.upload_media_hint": {
        "en": "Video or photo — each platform uses what its API allows.",
        "es": "Video o foto — cada plataforma usa lo que su API permita.",
    },
    "footer.about": {"en": "About", "es": "Nosotros"},
    "footer.privacy": {"en": "Privacy Policy", "es": "Política de privacidad"},
    "footer.terms": {"en": "Terms of Service", "es": "Términos de servicio"},
    "footer.deletion": {"en": "Data Deletion", "es": "Eliminación de datos"},
    "footer.cancellation": {
        "en": "Cancellation Policy",
        "es": "Política de cancelamiento",
    },
    "footer.support": {"en": "Support", "es": "Soporte"},
    "footer.not_affiliated": {
        "en": "Independent service. Not affiliated with any social network.",
        "es": "Servicio independiente. No afiliado a ninguna red social.",
    },
    "site.description": {
        "en": (
            "Grow on social media from one dashboard: schedule posts, track performance, "
            "and engage your audience with official, permission-based connections."
        ),
        "es": (
            "Crece en redes sociales desde un solo panel: programa publicaciones, sigue el rendimiento "
            "y atiende a tu audiencia con conexiones oficiales basadas en tu permiso."
        ),
    },
    "site.hero_title": {
        "en": "Grow your presence on social media",
        "es": "Haz crecer tu presencia en redes sociales",
    },
    "site.hero_subtitle": {
        "en": (
            "Schedule posts, track performance statistics, and grow your audience "
            "from a single, powerful dashboard."
        ),
        "es": (
            "Programa publicaciones, sigue estadísticas de rendimiento y haz crecer "
            "tu audiencia desde un solo panel."
        ),
    },
    "landing.title_suffix": {
        "en": "Grow on social media",
        "es": "Crece en redes sociales",
    },
    "landing.learn_more": {"en": "Learn more", "es": "Saber más"},
    "landing.built_for": {
        "en": "Built for creators and teams",
        "es": "Hecho para creadores y equipos",
    },
    "landing.feature1.title": {
        "en": "Efficient content management",
        "es": "Gestión eficiente de contenido",
    },
    "landing.feature1.body": {
        "en": "Schedule and publish videos and posts to the social accounts you connect, from one dashboard.",
        "es": "Programa y publica videos y publicaciones en las cuentas sociales que conectes, desde un solo panel.",
    },
    "landing.feature1.scope": {
        "en": "Publishing from one workspace",
        "es": "Publicación desde un solo espacio",
    },
    "landing.feature2.title": {
        "en": "Performance metrics & insights",
        "es": "Métricas e insights de rendimiento",
    },
    "landing.feature2.body": {
        "en": "Track views, likes, shares, and audience growth in real time to optimize your content strategy.",
        "es": "Sigue vistas, me gusta, compartidos y crecimiento de audiencia en tiempo real para optimizar tu estrategia de contenido.",
    },
    "landing.feature2.scope": {
        "en": "Analytics from connected accounts",
        "es": "Analíticas de cuentas conectadas",
    },
    "landing.feature3.title": {
        "en": "Comment inbox & replies",
        "es": "Bandeja de comentarios y respuestas",
    },
    "landing.feature3.body": {
        "en": "Read recent comments on your posts and reply directly from the panel without switching apps.",
        "es": "Lee comentarios recientes en tus publicaciones y responde directamente desde el panel sin cambiar de app.",
    },
    "landing.feature3.scope": {
        "en": "Community tools in one place",
        "es": "Herramientas de comunidad en un solo lugar",
    },
    "landing.api.title": {
        "en": "Official connections, your permission",
        "es": "Conexiones oficiales, con tu permiso",
    },
    "landing.api.p1": {
        "en": (
            "{site_name} connects to the social platforms you choose using each network's "
            "<strong>official login (OAuth)</strong>, only after the account owner grants permission. "
            "Access is limited to invited team members. Data from connected platforms is used solely "
            "to provide the features above and is never sold to third parties."
        ),
        "es": (
            "{site_name} se conecta a las plataformas sociales que elijas usando el "
            "<strong>inicio de sesión oficial (OAuth)</strong> de cada red, solo después de que el "
            "titular de la cuenta otorgue permiso. El acceso está limitado a miembros invitados del "
            "equipo. Los datos de las plataformas conectadas se usan únicamente para ofrecer las "
            "funciones anteriores y nunca se venden a terceros."
        ),
    },
    "landing.api.p2": {
        "en": "Read our Privacy Policy and Terms of Service.",
        "es": "Lee nuestra Política de privacidad y Términos de servicio.",
    },
    "login.dashboard": {
        "en": "Grow on social media.",
        "es": "Crece en redes sociales.",
    },
    "login.tagline": {
        "en": "Schedule content, monitor analytics, and engage your community — all in one place.",
        "es": "Programa contenido, sigue analíticas e interactúa con tu comunidad, todo en un solo lugar.",
    },
    "login.title": {"en": "Sign In", "es": "Iniciar sesión"},
    "login.welcome": {
        "en": "Welcome back! Please enter your details.",
        "es": "¡Bienvenido de nuevo! Introduce tus datos.",
    },
    "login.username": {"en": "Username", "es": "Usuario"},
    "login.password": {"en": "Password", "es": "Contraseña"},
    "login.username_ph": {"en": "Enter your username", "es": "Introduce tu usuario"},
    "login.password_ph": {"en": "Enter your password", "es": "Introduce tu contraseña"},
    "login.submit": {"en": "Sign In", "es": "Iniciar sesión"},
    "login.show_password": {"en": "Show password", "es": "Mostrar contraseña"},
    "login.hide_password": {"en": "Hide password", "es": "Ocultar contraseña"},
    "login.register_hint": {
        "en": "Have an invitation code?",
        "es": "¿Tienes un código de invitación?",
    },
    "login.register_link": {"en": "Create your account", "es": "Crea tu cuenta"},
    "login.forgot_link": {"en": "Forgot your password?", "es": "¿Olvidaste tu contraseña?"},
    "login.forgot.title": {"en": "Forgot password", "es": "Olvidé mi contraseña"},
    "login.forgot.headline": {
        "en": "Reset your password",
        "es": "Restablece tu contraseña",
    },
    "login.forgot.tagline": {
        "en": "Enter the email linked to your account. We will send you a link to choose a new password.",
        "es": "Introduce el correo asociado a tu cuenta. Te enviaremos un enlace para elegir una nueva contraseña.",
    },
    "login.forgot.welcome": {
        "en": "Use the notification email saved in your account settings.",
        "es": "Usa el correo de notificaciones guardado en la configuración de tu cuenta.",
    },
    "login.forgot.email": {"en": "Email", "es": "Correo"},
    "login.forgot.email_ph": {
        "en": "you@example.com",
        "es": "tu@ejemplo.com",
    },
    "login.forgot.submit": {"en": "Send reset link", "es": "Enviar enlace"},
    "login.forgot.back": {"en": "Back to sign in", "es": "Volver al inicio de sesión"},
    "login.forgot.invalid_email": {
        "en": "Enter a valid email address.",
        "es": "Introduce un correo válido.",
    },
    "login.forgot.sent_generic": {
        "en": "If an account exists with that email, you will receive a reset link shortly.",
        "es": "Si existe una cuenta con ese correo, recibirás un enlace de restablecimiento en breve.",
    },
    "register.title": {"en": "Create account", "es": "Crear cuenta"},
    "register.headline": {
        "en": "Join with your invitation",
        "es": "Únete con tu invitación",
    },
    "register.tagline": {
        "en": "Registration is by invitation only. Enter the code you received from our support team.",
        "es": "El registro es solo con invitación. Ingresa el código que recibiste de nuestro equipo de soporte.",
    },
    "register.welcome": {
        "en": "Enter your invitation code and choose your credentials.",
        "es": "Ingresa tu código de invitación y elige tus credenciales.",
    },
    "register.code": {"en": "Invitation code", "es": "Código de invitación"},
    "register.code_ph": {"en": "e.g. AB12CD34", "es": "p. ej. AB12CD34"},
    "register.password2": {"en": "Confirm password", "es": "Confirmar contraseña"},
    "register.email": {"en": "Email", "es": "Correo electrónico"},
    "register.email_ph": {"en": "you@example.com", "es": "tu@ejemplo.com"},
    "register.submit": {"en": "Create account", "es": "Crear cuenta"},
    "register.no_code_hint": {
        "en": "Don't have a code? Contact our support team to request an invitation.",
        "es": "¿No tienes código? Contacta a nuestro equipo de soporte para pedir una invitación.",
    },
    "register.have_account": {
        "en": "Already have an account?",
        "es": "¿Ya tienes una cuenta?",
    },
    "register.login_link": {"en": "Sign in", "es": "Inicia sesión"},
    "register.err.code_required": {
        "en": "Enter your invitation code.",
        "es": "Ingresa tu código de invitación.",
    },
    "register.err.code_invalid": {
        "en": "That invitation code is not valid.",
        "es": "Ese código de invitación no es válido.",
    },
    "register.err.code_used": {
        "en": "That invitation code was already used.",
        "es": "Ese código de invitación ya fue usado.",
    },
    "register.err.username_short": {
        "en": "Username must be at least 2 characters.",
        "es": "El usuario debe tener al menos 2 caracteres.",
    },
    "register.err.password_short": {
        "en": "Password must be at least 4 characters.",
        "es": "La contraseña debe tener al menos 4 caracteres.",
    },
    "register.err.username_taken": {
        "en": "That username is already taken.",
        "es": "Ese usuario ya está en uso.",
    },
    "register.err.password_mismatch": {
        "en": "Passwords do not match.",
        "es": "Las contraseñas no coinciden.",
    },
    "register.err.invalid_email": {
        "en": "Enter a valid email address.",
        "es": "Introduce un correo válido.",
    },
    "register.err.email_taken": {
        "en": "That email is already in use.",
        "es": "Ese correo ya está en uso.",
    },
    "register.flash.verify_email": {
        "en": "Account created. Check your email to confirm your address (link valid 24 hours).",
        "es": "Cuenta creada. Revisa tu correo para confirmar tu dirección (enlace válido 24 horas).",
    },
    "register.err.generic": {
        "en": "Could not create the account. Please try again.",
        "es": "No se pudo crear la cuenta. Inténtalo de nuevo.",
    },
    "support.title": {"en": "Support", "es": "Soporte"},
    "support.intro": {
        "en": "Write to our team. We answer here as soon as possible.",
        "es": "Escríbenos a nuestro equipo. Respondemos aquí lo antes posible.",
    },
    "support.empty": {
        "en": "No messages yet. Say hello!",
        "es": "Aún no hay mensajes. ¡Saluda!",
    },
    "support.placeholder": {"en": "Type your message…", "es": "Escribe tu mensaje…"},
    "support.send": {"en": "Send", "es": "Enviar"},
    "support.admin_label": {"en": "Support", "es": "Soporte"},
    "support.anonymous_label": {"en": "Anonymous", "es": "Anónimo"},
    "support.you_label": {"en": "You", "es": "Tú"},
    "support.chats_title": {"en": "Chats", "es": "Chats"},
    "support.chats_intro": {
        "en": "Conversations with registered users and anonymous visitors from the public site. Unread messages show a badge.",
        "es": "Conversaciones con usuarios registrados y visitantes anónimos del sitio público. Los mensajes sin leer muestran una insignia.",
    },
    "support.chats_info_btn": {
        "en": "About support chats",
        "es": "Información sobre chats de soporte",
    },
    "support.search_ph": {
        "en": "Search user or anonymous…",
        "es": "Buscar usuario o anónimo…",
    },
    "support.no_threads": {
        "en": "No conversations yet.",
        "es": "Aún no hay conversaciones.",
    },
    "support.pick_thread": {
        "en": "Select a user on the left.",
        "es": "Selecciona un usuario.",
    },
    "support.threads_collapse": {
        "en": "Hide conversations",
        "es": "Ocultar conversaciones",
    },
    "support.threads_expand": {
        "en": "Show conversations",
        "es": "Mostrar conversaciones",
    },
    "support.threads_rail_label": {
        "en": "Quick switch between chats",
        "es": "Cambio rápido entre chats",
    },
    "support.reply_placeholder": {"en": "Type your reply…", "es": "Escribe tu respuesta…"},
    "support.notify_new": {
        "en": "You have a new support message",
        "es": "Tienes un nuevo mensaje de soporte",
    },
    "support.notify_new_admin": {
        "en": "New user message in support chat",
        "es": "Nuevo mensaje de un usuario en el chat",
    },
    "support.unread_badge": {
        "en": "Unread messages",
        "es": "Mensajes sin leer",
    },
    "invites.title": {"en": "Invitation codes", "es": "Códigos invitación"},
    "invites.generate": {"en": "Generate code", "es": "Generar código"},
    "invites.hint": {
        "en": "Share a code with someone so they can register at {register_path}. Each code works once.",
        "es": "Comparte un código para que alguien se registre en {register_path}. Cada código sirve una vez.",
    },
    "invites.info_btn": {
        "en": "About invitation codes",
        "es": "Información sobre códigos de invitación",
    },
    "invites.empty": {"en": "No codes yet.", "es": "Aún no hay códigos."},
    "invites.used_by": {"en": "Used by", "es": "Usado por"},
    "invites.unused": {"en": "Available", "es": "Disponible"},
    "invites.expired": {"en": "Expired", "es": "Expirado"},
    "invites.expired_by": {
        "en": "Expired by {user}",
        "es": "Expirado por {user}",
    },
    "invites.delete": {"en": "Delete", "es": "Eliminar"},
    "invites.copy": {"en": "Copy", "es": "Copiar"},
    "invites.copied": {"en": "Copied!", "es": "¡Copiado!"},
    "invites.info_title": {"en": "Invitation", "es": "Invitación"},
    "invites.registered": {"en": "Registered", "es": "Se registró"},
    "invites.code_used": {"en": "Invitation code", "es": "Código de invitación"},
    "invites.no_code": {
        "en": "Created from the panel (no invitation code).",
        "es": "Creado desde el panel (sin código de invitación).",
    },
    "support.widget_open": {"en": "Chat with support", "es": "Chatea con soporte"},
    "support.widget_title": {"en": "Support chat", "es": "Chat de soporte"},
    "support.widget_close": {"en": "Close chat", "es": "Cerrar chat"},
    "support.chat_refresh": {"en": "Refresh", "es": "Actualizar"},
    "support.chat_off": {"en": "Turn off chat", "es": "Apagar chat"},
    "support.chat_on": {"en": "Turn on chat", "es": "Encender chat"},
    "login.error": {
        "en": "Invalid username or password",
        "es": "Usuario o contraseña incorrectos",
    },
    "legal.last_updated": {"en": "Last updated:", "es": "Última actualización:"},
    "legal.about_title": {"en": "About Us", "es": "Sobre nosotros"},
    "legal.privacy_title": {"en": "Privacy Policy", "es": "Política de privacidad"},
    "legal.terms_title": {"en": "Terms of Service", "es": "Términos de servicio"},
    "legal.deletion_title": {"en": "Data Deletion", "es": "Eliminación de datos"},
    "legal.cancellation_title": {
        "en": "Cancellation Policy",
        "es": "Política de cancelamiento",
    },
    "legal.support_title": {"en": "Support", "es": "Soporte"},
    "feed.empty_title": {"en": "The feed is empty", "es": "El feed está vacío"},
    "feed.empty_hint": {
        "en": "Published content will appear here.",
        "es": "El contenido publicado aparecerá aquí.",
    },
    "feed.views": {"en": "views", "es": "vistas"},
    "admin.all": {"en": "All", "es": "Todos"},
    "admin.platform": {"en": "Platform", "es": "Plataforma"},
    "admin.tiktok_account": {"en": "TikTok account", "es": "Cuenta TikTok"},
    "admin.accounts": {"en": "Accounts", "es": "Cuentas"},
    "admin.stats_account_pick": {"en": "Choose account", "es": "Elegir cuenta"},
    "admin.stats_platform_pick": {"en": "Choose platform", "es": "Elegir plataforma"},
    "admin.stats_platform_search": {
        "en": "Search platform…",
        "es": "Buscar plataforma…",
    },
    "admin.stats_video_pick": {"en": "Choose video", "es": "Elegir video"},
    "admin.stats_video_search": {
        "en": "Search video…",
        "es": "Buscar video…",
    },
    "admin.stats_account_search": {
        "en": "Search account or group…",
        "es": "Buscar cuenta o grupo…",
    },
    "admin.stats_kind_group": {"en": "Group", "es": "Grupo"},
    "admin.stats_kind_account": {"en": "Account", "es": "Cuenta"},
    "admin.via_api": {"en": "API", "es": "API"},
    "admin.via_mixed": {"en": "Mixed", "es": "Mixto"},
    "offline.title": {"en": "No connection", "es": "Sin conexión"},
    "offline.message": {
        "en": "There is no internet or the server is not responding right now.",
        "es": "No hay internet o el servidor no responde ahora.",
    },
    "offline.hint": {
        "en": "When the connection is back, tap retry. You do not need to copy any link.",
        "es": "Cuando vuelva la conexión, pulsa reintentar. No hace falta copiar ningún enlace.",
    },
    "offline.retry": {"en": "Retry", "es": "Reintentar"},
    "offline.home": {"en": "Go to home", "es": "Ir al inicio"},
    "offline.banner": {"en": "No connection", "es": "Sin conexión"},
    "offline.restored": {"en": "Connection restored", "es": "Conexión restaurada"},
    "admin.platform_account": {"en": "{platform} account", "es": "Cuenta {platform}"},
    "admin.stats_consult": {"en": "Query", "es": "Consultar"},
    "admin.stats_tiktok_hint": {
        "en": "If you query all accounts, each TikTok account counts as one stats query.",
        "es": "Si consultas todas las cuentas, cada cuenta de TikTok cuenta como una consulta de estadísticas.",
    },
    "admin.global_summary": {"en": "Global summary", "es": "Resumen global"},
    "admin.summary_platform": {
        "en": "Summary {platform}",
        "es": "Resumen {platform}",
    },
    "admin.summary_account": {
        "en": "Summary {account}",
        "es": "Resumen {account}",
    },
    "admin.global_summary_sub": {
        "en": "All videos and comments in the app.",
        "es": "Todos los videos y comentarios en la app.",
    },
    "admin.published_videos": {
        "en": "Published videos",
        "es": "Videos publicados",
    },
    "admin.published_videos_sub": {
        "en": "All publications across every connected platform, newest first.",
        "es": "Todas las publicaciones en cada plataforma conectada, más recientes primero.",
    },
    "admin.platform_summary_sub": {
        "en": "Videos published on {platform}.",
        "es": "Videos publicados en {platform}.",
    },
    "admin.local_only": {
        "en": "App only",
        "es": "Solo en app",
    },
    "admin.no_videos_on_platform": {
        "en": "No videos published on this platform yet.",
        "es": "Aún no hay videos publicados en esta plataforma.",
    },
    "admin.no_videos_published": {
        "en": "No videos published yet.",
        "es": "Aún no hay videos publicados.",
    },
    "admin.views": {"en": "Views", "es": "Vistas"},
    "admin.likes": {"en": "Likes", "es": "Me gusta"},
    "admin.comments": {"en": "Comments", "es": "Comentarios"},
    "admin.videos": {"en": "Videos", "es": "Videos"},
    "admin.shares": {"en": "Shares", "es": "Compartidos"},
    "admin.followers_demo": {"en": "Followers (demo)", "es": "Seguidores (demo)"},
    "admin.no_tiktok_linked": {
        "en": "No TikTok account is linked to your profile.",
        "es": "No hay cuenta TikTok vinculada a tu perfil.",
    },
    "admin.no_tiktok_accounts_panel": {
        "en": "No accounts connected yet.",
        "es": "Aún no tienes cuentas conectadas.",
    },
    "admin.no_server_account_linked": {
        "en": "No server account is linked to your profile. Ask an administrator to assign one in Team.",
        "es": "No hay cuenta de servidores vinculada a tu perfil. Pide a un administrador que te asigne una en Equipo.",
    },
    "team.create_user": {"en": "Create user", "es": "Crear usuario"},
    "team.members": {"en": "Members", "es": "Miembros"},
    "team.show": {"en": "Show", "es": "Mostrar"},
    "team.per_page_all": {"en": "All", "es": "Todos"},
    "team.per_page_label": {
        "en": "Rows per page",
        "es": "Filas por página",
    },
    "team.username": {"en": "Username", "es": "Usuario"},
    "team.display_name": {"en": "Display name", "es": "Nombre visible"},
    "team.mode": {"en": "Mode", "es": "Modo"},
    "team.can_view_comments": {
        "en": "View comments",
        "es": "Ver comentarios",
    },
    "team.link_tiktok": {"en": "Link TikTok account", "es": "Vincular cuenta TikTok"},
    "team.link_account": {"en": "Link account", "es": "Vincular cuenta"},
    "team.linked_account": {"en": "Linked account", "es": "Cuenta vinculada"},
    "team.link_account_placeholder": {
        "en": "Link account",
        "es": "Vincular cuenta",
    },
    "team.password": {"en": "Password", "es": "Contraseña"},
    "team.create_btn": {"en": "Create user", "es": "Crear usuario"},
    "team.none": {"en": "None", "es": "Ninguna"},
    "team.no_users": {"en": "No users yet.", "es": "Aún no hay usuarios."},
    "team.active": {"en": "Active", "es": "Activo"},
    "team.disabled": {"en": "Disabled", "es": "Deshabilitado"},
    "team.edit": {"en": "Edit", "es": "Editar"},
    "team.disable": {"en": "Disable", "es": "Deshabilitar"},
    "team.enable": {"en": "Enable", "es": "Habilitar"},
    "team.toggle_active": {
        "en": "Enable or disable user",
        "es": "Activar o desactivar usuario",
    },
    "team.delete_user": {"en": "Delete user", "es": "Eliminar usuario"},
    "team.admin_badge": {"en": "admin", "es": "admin"},
    "team.edit_user": {"en": "Edit user", "es": "Editar usuario"},
    "team.new_password": {"en": "New password", "es": "Nueva contraseña"},
    "team.password_optional": {
        "en": "New password (optional)",
        "es": "Nueva contraseña (opcional)",
    },
    "team.password_keep": {
        "en": "Leave blank to keep current",
        "es": "Dejar vacío para mantener la actual",
    },
    "team.save_changes": {"en": "Save changes", "es": "Guardar cambios"},
    "team.search_members": {
        "en": "Search by username or mode…",
        "es": "Buscar por usuario o modo…",
    },
    "team.search_clear": {"en": "Clear search", "es": "Limpiar búsqueda"},
    "team.search_accounts": {
        "en": "Search account…",
        "es": "Buscar cuenta…",
    },
    "team.search_accounts_to_link": {
        "en": "Search accounts to link…",
        "es": "Buscar cuentas a vincular…",
    },
    "team.view_linked_accounts": {
        "en": "View linked",
        "es": "Ver vinculadas",
    },
    "team.no_linked_accounts": {
        "en": "No linked accounts",
        "es": "Ninguna cuenta vinculada",
    },
    "team.no_results": {
        "en": "No members match your search.",
        "es": "Ningún miembro coincide con la búsqueda.",
    },
    "team.no_account_results": {
        "en": "No accounts match your search.",
        "es": "Ninguna cuenta coincide con la búsqueda.",
    },
    "team.pagination": {"en": "Members pagination", "es": "Paginación de miembros"},
    "team.previous": {"en": "← Previous", "es": "← Anterior"},
    "team.next": {"en": "Next →", "es": "Siguiente →"},
    "team.page_info": {"en": "Page {page} of {total}", "es": "Página {page} de {total}"},
    "team.page_info_compact": {"en": "{page} / {total}", "es": "{page} / {total}"},
    "team.loading": {"en": "Loading members…", "es": "Cargando miembros…"},
    "mode.admin": {"en": "Admin mode", "es": "Modo admin"},
    "mode.tiktok": {"en": "TikTok user", "es": "Usuario TikTok"},
    "mode.publisher": {"en": "Publisher user", "es": "Usuario publicador"},
    "mode.admin.hint": {
        "en": "High permission level in the app (separate from site administrator account).",
        "es": "Nivel alto de permisos en la app (aparte de la cuenta administradora del sitio).",
    },
    "mode.tiktok.hint": {
        "en": "Admin-like workspace: publish, stats and team, without server credentials.",
        "es": "Espacio tipo admin: publicar, estadísticas y equipo, sin credenciales de servidores.",
    },
    "mode.publisher.hint": {
        "en": "Only linked TikTok accounts: own posts, stats and comments. No panel, chats or servers.",
        "es": "Solo las cuentas TikTok vinculadas: publicaciones, estadísticas y comentarios propios. Sin panel, chats ni servidores.",
    },
    "team.js.show_password": {"en": "Show password", "es": "Mostrar contraseña"},
    "team.js.hide_password": {"en": "Hide password", "es": "Ocultar contraseña"},
    "team.js.err_status": {
        "en": "Could not update status.",
        "es": "No se pudo actualizar el estado.",
    },
    "team.js.updated": {"en": "Updated.", "es": "Actualizado."},
    "team.js.network_error": {
        "en": "Network error. Please try again.",
        "es": "Error de red. Inténtalo de nuevo.",
    },
    "team.js.delete_confirm": {
        "en": "Delete @{user}? Their videos, comments, and server files will be removed. This cannot be undone.",
        "es": "¿Eliminar @{user}? Se borrarán sus videos, comentarios y archivos del servidor. No se puede deshacer.",
    },
    "team.js.err_delete": {
        "en": "Could not delete user.",
        "es": "No se pudo eliminar el usuario.",
    },
    "team.js.user_deleted": {"en": "User deleted.", "es": "Usuario eliminado."},
    "team.js.err_save": {
        "en": "Could not save changes.",
        "es": "No se pudieron guardar los cambios.",
    },
    "team.js.user_updated": {"en": "User updated.", "es": "Usuario actualizado."},
    "team.js.user_created": {"en": "User created successfully.", "es": "Usuario creado correctamente."},
    "team.err.username_exists": {
        "en": "Username already exists.",
        "es": "Ese usuario ya existe.",
    },
    "team.err.username_short": {
        "en": "Username must be at least 2 characters.",
        "es": "El usuario debe tener al menos 2 caracteres.",
    },
    "team.err.password_short": {
        "en": "Password must be at least 4 characters.",
        "es": "La contraseña debe tener al menos 4 caracteres.",
    },
    "team.err.invalid_mode": {
        "en": "Invalid user mode.",
        "es": "Modo de usuario no válido.",
    },
    "team.err.site_admin_only": {
        "en": "Only the site administrator can manage this user.",
        "es": "Solo el administrador del sitio puede gestionar este usuario.",
    },
    "team.js.user_enabled": {"en": "User enabled.", "es": "Usuario habilitado."},
    "team.js.user_disabled": {
        "en": "User disabled. They will not be able to sign in.",
        "es": "Usuario deshabilitado. No podrá iniciar sesión.",
    },
    # ------------------------------------------------------------------
    # API Documento
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Condiciones de servidores (cuotas API)
    # ------------------------------------------------------------------
    "cond.intro": {
        "en": "Official API limits for each connected account (YouTube is per Google Cloud project). Going over them can pause publishing or flag the account. The Safe column is a conservative pace so you do not abuse the API. Networks change these numbers; stay under Safe, not at the hard ceiling. VMOS Cloud is an alternative for TikTok, Instagram, Facebook, YouTube, X and Snapchat: those official caps do not apply; the cloud phone and the app’s own limits do. Panel proxies are not used on VMOS accounts. Dailymotion, Bilibili and Rumble stay on their APIs. Odysee uses LBRY (email/password, TUS upload).",
        "es": "Límites oficiales de la API de cada cuenta conectada (YouTube es por proyecto de Google Cloud). Pasarse puede pausar la publicación o marcar la cuenta. La columna Uso seguro es un ritmo conservador para no abusar. Las redes cambian estas cifras; quédate en Uso seguro, no en el tope máximo. VMOS Cloud es una alternativa para TikTok, Instagram, Facebook, YouTube, X y Snapchat: esos topes oficiales no aplican; rigen el móvil en la nube y los límites de la app. Las cuentas VMOS no usan el proxy del panel. Dailymotion, Bilibili y Rumble siguen por su API. Odysee usa LBRY (email/contraseña, subida TUS).",
    },
    "cond.col_server": {"en": "Server", "es": "Servidor"},
    "cond.col_api": {"en": "API", "es": "API"},
    "cond.col_cap": {"en": "Official cap", "es": "Tope oficial"},
    "cond.col_window": {"en": "Time window", "es": "Ventana de tiempo"},
    "cond.col_rate": {"en": "API pace", "es": "Ritmo de la API"},
    "cond.col_safe": {"en": "Safe use", "es": "Uso seguro"},
    "cond.col_detail": {"en": "Conditions", "es": "Condiciones"},
    "cond.vmos.cap": {
        "en": "No official OAuth quota. Limits come from the VMOS Cloud phone and the social app signed in on that pad.",
        "es": "Sin cuota OAuth oficial. Los límites los pone el móvil VMOS Cloud y la app con la que iniciaste sesión en ese pad.",
    },
    "cond.vmos.window": {
        "en": "Depends on the RPA template and the app on the cloud phone (not a midnight API reset).",
        "es": "Depende de la plantilla RPA y de la app en el móvil en la nube (no hay reinicio de cuota a medianoche).",
    },
    "cond.vmos.rate": {
        "en": "One automation task at a time per pad. Space posts; bursts look like a real phone tapping too fast.",
        "es": "Una tarea de automatización a la vez por pad. Separa las publicaciones; las ráfagas parecen un móvil tocando demasiado rápido.",
    },
    "cond.vmos.safe": {
        "en": "Few posts per day per cloud phone until the account is stable. Do not share one pad across many accounts at once.",
        "es": "Pocas publicaciones al día por móvil hasta que la cuenta esté estable. No compartas un pad entre muchas cuentas a la vez.",
    },
    "cond.vmos.detail": {
        "en": "Alternative to official OAuth for TikTok, Instagram, Facebook, YouTube, X and Snapchat. In Servers, Connect with VMOS: Access Key, Secret, padCode and template/scriptId. The panel uploads the file to the pad and runs the template. Dailymotion, Bilibili and Rumble stay on their APIs. Panel proxies are not used.",
        "es": "Alternativa al OAuth oficial para TikTok, Instagram, Facebook, YouTube, X y Snapchat. En Servidores, Conectar con VMOS: Access Key, Secret, padCode y plantilla/scriptId. El panel sube el archivo al pad y lanza la plantilla. Dailymotion, Bilibili y Rumble siguen por su API. No se usa el proxy del panel.",
    },
    "cond.vmos_alt": {
        "en": "If this account is linked with VMOS instead of OAuth, the official API caps in this row do not apply; see the VMOS Cloud row. Panel proxies are not used.",
        "es": "Si esta cuenta está unida por VMOS en lugar de OAuth, los topes oficiales de esta fila no aplican; mira la fila VMOS Cloud. No se usa el proxy del panel.",
    },
    "cond.filehost.cap": {
        "en": "No social-network post quota. Limits come from the host (file size, daily uploads) and PPV rules: unique views, often ~10k/day, country-based rates.",
        "es": "Sin cuota de red social. Los límites los pone el host (tamaño, subidas/día) y las reglas PPV: vistas únicas, a menudo ~10 mil/día, tarifas por país.",
    },
    "cond.filehost.window": {
        "en": "Host dashboard (not a midnight social API reset). Payouts follow that host’s reporting, usually unique views.",
        "es": "El panel del host (no hay reinicio de cuota de red a medianoche). Los pagos siguen su reporte, normalmente vistas únicas.",
    },
    "cond.filehost.rate": {
        "en": "Upload one file per request. Space large uploads; the host may reject bursts or oversized files.",
        "es": "Un archivo por petición. Separa subidas grandes; el host puede rechazar ráfagas o archivos demasiado pesados.",
    },
    "cond.filehost.safe": {
        "en": "You bring the traffic. AdBlock, VPN and fake/duplicate views usually do not pay. Do not mark a post sent unless the host returned a file URL.",
        "es": "Tú llevas el tráfico. AdBlock, VPN y vistas falsas o duplicadas casi nunca pagan. No marques enviado si el host no devolvió una URL.",
    },
    "cond.filehost.detail": {
        "en": "{name}: connect in Servers with the API key from the host dashboard (MixDrop: email+key, Streamtape: login+key). Video only. Money is paid by the host, not this panel. Linked panel proxies are used like OAuth.",
        "es": "{name}: en Servidores conecta con la API key del panel del host (MixDrop: email+key, Streamtape: login+key). Solo video. El dinero lo paga el host, no este panel. El proxy vinculado se usa como en OAuth.",
    },
    "cond.filehost.trial": {
        "en": "(pago) means trial payout: newer host, not proven. Confirm they pay before depending on them.",
        "es": "(pago) significa prueba de cobro: host más nuevo, no contrastado. Confirma que pagan antes de depender de ellos.",
    },
    "cond.odysee.cap": {
        "en": "No social-network post quota. Limited by LBC bid, wallet balance and Odysee/LBRY publish pipeline.",
        "es": "Sin cuota de red social. Limitan el bid en LBC, el saldo del monedero y el pipeline de publicación de Odysee/LBRY.",
    },
    "cond.odysee.window": {
        "en": "On-chain confirmations plus Odysee asynquery processing (minutes, not a midnight reset).",
        "es": "Confirmaciones en cadena más el asynquery de Odysee (minutos, no un reinicio a medianoche).",
    },
    "cond.odysee.rate": {
        "en": "One TUS upload + stream_create at a time. Space large files; do not start several publishes on the same account at once.",
        "es": "Una subida TUS + stream_create a la vez. Separa archivos grandes; no lances varias publicaciones a la vez en la misma cuenta.",
    },
    "cond.odysee.safe": {
        "en": "Few videos per day until the channel is stable. Do not mark sent unless asynquery returned a claim URL.",
        "es": "Pocos videos al día hasta que el canal esté estable. No marques enviado si el asynquery no devolvió una URL de claim.",
    },
    "cond.odysee.detail": {
        "en": "Connect in Servers with Odysee email and password. The panel stores the LBRY auth token. Optional channel claim ID. Video only. Linked proxies are used. Stats/comments in this panel stay local.",
        "es": "En Servidores conecta con email y contraseña de Odysee. El panel guarda el auth token de LBRY. Claim ID de canal opcional. Solo video. Se usa el proxy vinculado. Estadísticas y comentarios de este panel siguen siendo locales.",
    },
    "cond.bilibili_tv.cap": {
        "en": "No public daily quota. Limited by Bilibili.tv anti-bot and creator-studio rules.",
        "es": "Sin cuota diaria pública. Limitan el anti-bot de Bilibili.tv y las reglas del estudio.",
    },
    "cond.bilibili_tv.window": {
        "en": "Keep-alive every 3–5 days at a random hour, one account at a time (not all the same day). If the session expired, it signs in again with the saved password.",
        "es": "Keep-alive cada 3–5 días a una hora distinta, una cuenta a la vez (no todas el mismo día). Si la sesión caducó, vuelve a entrar con la clave guardada.",
    },
    "cond.bilibili_tv.rate": {
        "en": "One Chromium at a time. Do not open several Bilibili.tv logins at once.",
        "es": "Un Chromium a la vez. No abras varios logins de Bilibili.tv a la vez.",
    },
    "cond.bilibili_tv.safe": {
        "en": "Do not mark sent unless studio.bilibili.tv returns a video id. If captcha appears, stop and complete it by hand.",
        "es": "No marques enviado si studio.bilibili.tv no devuelve un id de video. Si sale captcha, para y complétalo a mano.",
    },
    "cond.bilibili_tv.detail": {
        "en": "This is Bilibili.tv, not Bilibili.com. Email/password in Servers. Isolated browser profile per account. VMOS is not used. Upload goes through studio.bilibili.tv.",
        "es": "Esto es Bilibili.tv, no Bilibili.com. Email/contraseña en Servidores. Perfil de navegador aislado por cuenta. VMOS no se usa. La subida va por studio.bilibili.tv.",
    },
    "cond.dtube.cap": {
        "en": "Hive resource credits (RC) plus IPFS cluster capacity. No PPV host quota.",
        "es": "Resource credits (RC) de Hive más la capacidad del cluster IPFS. No hay cuota de host PPV.",
    },
    "cond.dtube.window": {
        "en": "Hive blocks (~3 s) after IPFS upload finishes. RC regenerates over time.",
        "es": "Bloques de Hive (~3 s) cuando termina la subida IPFS. Los RC se regeneran con el tiempo.",
    },
    "cond.dtube.rate": {
        "en": "One Hive comment per video. Do not broadcast bursts; low RC will reject the tx.",
        "es": "Un comentario Hive por video. No emitas en ráfaga; con RC bajos Hive rechaza la transacción.",
    },
    "cond.dtube.safe": {
        "en": "Keep RC headroom. Do not mark sent unless Hive accepted the comment and the cluster returned a video hash.",
        "es": "Deja margen de RC. No marques enviado si Hive no aceptó el comentario y el cluster no devolvió el hash del video.",
    },
    "cond.dtube.detail": {
        "en": "Hive username + posting WIF stay in Servers. Publishing is paused while cluster.d.tube has no DNS. Linked proxies unused until then. Stats/comments stay local.",
        "es": "Usuario Hive + posting WIF se quedan en Servidores. La publicación está pausada mientras cluster.d.tube no tenga DNS. El proxy no se usa hasta entonces. Estadísticas y comentarios siguen locales.",
    },
    "cond.tiktok.cap": {
        "en": "Daily post cap exists, number not published. Integrators usually see 15–25 videos per account/day. Error: spam_risk_too_many_posts.",
        "es": "Hay tope diario de posts, pero TikTok no publica el número. Quien integra suele ver 15–25 videos por cuenta/día. Error: spam_risk_too_many_posts.",
    },
    "cond.tiktok.window": {
        "en": "24 hours rolling per creator + 6 publish-init requests per minute per access token.",
        "es": "24 horas corridas por creador + 6 inicios de publicación por minuto por token.",
    },
    "cond.tiktok.rate": {
        "en": "6 requests/minute per user token on Direct Post / upload init.",
        "es": "6 peticiones/minuto por token de usuario en Direct Post / inicio de subida.",
    },
    "cond.tiktok.safe": {
        "en": "Up to 10 videos/day per TikTok account, 10–15 minutes apart. Never send bursts.",
        "es": "Hasta 10 videos/día por cuenta de TikTok, con 10–15 minutos de separación. Nunca en ráfaga.",
    },
    "cond.tiktok.detail": {
        "en": "Unaudited apps can only post private/self-only. Inbox upload: at most 5 pending shares in 24 hours. The app also has a daily cap of active publishing users (reached_active_user_cap). Limits are per creator account, shared across all apps that post for that user.",
        "es": "Apps sin auditoría solo pueden publicar en privado/solo yo. Subida al inbox: como máximo 5 pendientes en 24 horas. La app también tiene cupo diario de usuarios activos publicando (reached_active_user_cap). El tope es por cuenta de creador, compartido entre todas las apps que publiquen por ese usuario.",
    },
    "cond.youtube.cap": {
        "en": "Default 10,000 quota units/day per Google Cloud project. videos.insert costs ~1,600 units → about 6 uploads/day. Console may also show a separate videos.insert bucket (often 100/day).",
        "es": "Por defecto 10.000 unidades/día por proyecto de Google Cloud. videos.insert gasta ~1.600 → unos 6 videos/día. En la consola puede haber un cupo aparte de videos.insert (a menudo 100/día).",
    },
    "cond.youtube.window": {
        "en": "Quota resets at midnight Pacific Time (not midnight in your country).",
        "es": "La cuota se reinicia a medianoche del Pacífico (no a las 00:00 de tu país).",
    },
    "cond.youtube.rate": {
        "en": "Unit budget, not a posts-per-minute clock. Failed uploads still spend quota.",
        "es": "Presupuesto de unidades, no un reloj de posts por minuto. Las subidas fallidas también gastan cuota.",
    },
    "cond.youtube.safe": {
        "en": "4–5 videos/day per Google project, 20–30 minutes apart. Leave units for token refresh and metadata.",
        "es": "4–5 videos/día por proyecto de Google, con 20–30 minutos de separación. Deja unidades para renovar token y metadatos.",
    },
    "cond.youtube.detail": {
        "en": "Quota is per project, not per channel: several YouTube accounts on the same Client ID share the 10,000 units. YouTube also has a separate anti-spam upload limit per channel (not in the API docs). Clips of 3 minutes or less go up as Shorts in this panel. You can request more quota in Google Cloud; it is not guaranteed.",
        "es": "La cuota es por proyecto, no por canal: varias cuentas de YouTube con el mismo Client ID comparten las 10.000 unidades. YouTube también tiene un tope anti-spam de subidas por canal (no está en la docs de la API). En este panel, los de 3 minutos o menos se suben como Shorts. Se puede pedir más cuota en Google Cloud; no está garantizado.",
    },
    "cond.instagram.cap": {
        "en": "API-published posts: Meta docs say 100 per 24-hour moving window in one place and 50 in another. Live value: GET /{ig-user-id}/content_publishing_limit (quota_total is often 50). Max 50 unpublished containers at once.",
        "es": "Posts vía API: Meta pone 100 por ventana móvil de 24 h en un sitio y 50 en otro. Valor real: GET /{ig-user-id}/content_publishing_limit (quota_total suele ser 50). Máximo 50 contenedores sin publicar a la vez.",
    },
    "cond.instagram.window": {
        "en": "Rolling 24 hours per professional Instagram account (capacity returns 24 h after each post, not at midnight).",
        "es": "24 horas corridas por cuenta profesional de Instagram (la capacidad vuelve 24 h después de cada post, no a medianoche).",
    },
    "cond.instagram.rate": {
        "en": "Also Graph call budget (often ~200 calls/hour per user token) plus app-level Business Use Case limits.",
        "es": "También hay cupo de llamadas Graph (suele ~200/hora por token de usuario) y límites de Business Use Case a nivel app.",
    },
    "cond.instagram.safe": {
        "en": "Up to 15–20 Reels/photos per 24 h per Instagram account, 30+ minutes apart. Stay well under 50.",
        "es": "Hasta 15–20 Reels/fotos por 24 h por cuenta de Instagram, con 30+ minutos de separación. Quédate bastante por debajo de 50.",
    },
    "cond.instagram.detail": {
        "en": "Needs a professional account. Reels, feed photos and Stories share the publishing cap; a carousel counts as one post. Error 9 / 2207042 when the cap is hit. Photos in this panel need a public https SITE_URL (not localhost).",
        "es": "Hace falta cuenta profesional. Reels, fotos del feed e Historias comparten el tope; un carrusel cuenta como un post. Error 9 / 2207042 al llegar al cupo. Las fotos en este panel necesitan un SITE_URL público https (no localhost).",
    },
    "cond.facebook.cap": {
        "en": "Pages only (not personal profiles). Reels API: 30 API-published Reels per 24-hour moving window. Feed videos have no small official “X/day” like Instagram; Graph uses 200 × active users calls/hour.",
        "es": "Solo Páginas (no perfiles personales). API de Reels: 30 Reels por API en ventana móvil de 24 h. Los videos del feed no tienen un “X/día” oficial pequeño como Instagram; Graph usa 200 × usuarios activos llamadas/hora.",
    },
    "cond.facebook.window": {
        "en": "Reels: rolling 24 hours. Graph call budget: rolling 1 hour (and a 24 h Business Use Case window).",
        "es": "Reels: 24 horas corridas. Cupo de llamadas Graph: 1 hora corrida (y ventana de 24 h de Business Use Case).",
    },
    "cond.facebook.rate": {
        "en": "Calls/hour ≈ 200 × number of active app users. Watch X-App-Usage / X-Business-Use-Case-Usage headers.",
        "es": "Llamadas/hora ≈ 200 × usuarios activos de la app. Mira las cabeceras X-App-Usage / X-Business-Use-Case-Usage.",
    },
    "cond.facebook.safe": {
        "en": "Up to 10–12 videos/day per Page, 20+ minutes apart. If you publish Reels via API, stay under ~25/24 h.",
        "es": "Hasta 10–12 videos/día por Página, con 20+ minutos de separación. Si publicas Reels por API, no pases de ~25/24 h.",
    },
    "cond.facebook.detail": {
        "en": "Page quality and spam filters can still block bursts even with quota left. Photos and long videos share the Page; space everything. Tokens are Page tokens, renewed automatically in this panel. If publish fails with “cannot call API for app”: the Meta app is in Development mode. Switch it to Live in developers.facebook.com (privacy policy URL required), request App Review for pages_manage_posts and pages_read_engagement, or add the Page owner as App admin/tester. Then Disconnect and Connect with Facebook again in Servers.",
        "es": "La calidad de la Página y el anti-spam pueden bloquear ráfagas aunque quede cupo. Fotos y videos largos comparten la Página; espacia todo. Los tokens son de Página; este panel los renueva solo. Si falla con “cannot call API for app”: la app de Meta está en modo Desarrollo. En developers.facebook.com pásala a En vivo (pide URL de política de privacidad), pide revisión de pages_manage_posts y pages_read_engagement, o añade al dueño de la Página como administrador/tester de la app. Luego Desconectar y Conectar con Facebook otra vez en Servidores.",
    },
    "cond.x.cap": {
        "en": "POST /2/tweets: 10,000/24 h per app and 100/15 min per user (some docs also cite 300 posts+reposts / 3 h). Unverified X accounts: about 50 original posts/day on the platform (API + manual). Paid API access is required.",
        "es": "POST /2/tweets: 10.000/24 h por app y 100/15 min por usuario (algunas docs también citan 300 posts+reposts / 3 h). Cuentas X sin verificar: unos 50 posts originales/día en la plataforma (API + a mano). Hace falta API de pago.",
    },
    "cond.x.window": {
        "en": "15-minute and 24-hour rolling windows for the API. Account daily caps reset on X’s clock, with extra unofficial sub-limits during the day.",
        "es": "Ventanas corridas de 15 minutos y 24 h en la API. El tope diario de la cuenta sigue el reloj de X, con sublímites extra no oficiales a lo largo del día.",
    },
    "cond.x.rate": {
        "en": "Do not post faster than one every few minutes on one account. HTTP 429 if you burst.",
        "es": "No publiques más rápido que uno cada varios minutos en la misma cuenta. HTTP 429 si vas en ráfaga.",
    },
    "cond.x.safe": {
        "en": "10–15 posts/day per X account, 10+ minutes apart. Unverified: stay under 40/day including posts you make in the X app.",
        "es": "10–15 posts/día por cuenta de X, con 10+ minutos de separación. Sin verificar: no pases de 40/día contando lo que publiques a mano en X.",
    },
    "cond.x.detail": {
        "en": "This panel posts photos, GIF and short video. Premium/verified accounts are often exempt from the low 50/day account cap; the API 15-minute limit still applies. Media upload has its own 15-minute quotas (initialize/append/finalize).",
        "es": "Este panel publica fotos, GIF y video corto. Las cuentas Premium/verificadas suelen estar exentas del tope bajo de 50/día; el límite de 15 minutos de la API sigue. La subida de media tiene cupos propios de 15 minutos (initialize/append/finalize).",
    },
    "cond.dailymotion.cap": {
        "en": "No public “videos per day” quota like YouTube units. Partner/app rate limits apply (commonly around 60 requests/minute). The channel can still be throttled for spam.",
        "es": "No hay un cupo público de “videos por día” como las unidades de YouTube. Sí hay rate limit de partner/app (suele ~60 peticiones/minuto). El canal igual puede frenarse por spam.",
    },
    "cond.dailymotion.window": {
        "en": "Per-minute API window. No official midnight reset for uploads.",
        "es": "Ventana de la API por minuto. No hay reinicio oficial a medianoche para las subidas.",
    },
    "cond.dailymotion.rate": {
        "en": "Keep well under ~60 calls/minute (upload is several calls: create + send + publish).",
        "es": "Quédate bastante por debajo de ~60 llamadas/minuto (una subida son varias: crear + enviar + publicar).",
    },
    "cond.dailymotion.safe": {
        "en": "10–12 videos/day per Dailymotion channel, 15+ minutes apart.",
        "es": "10–12 videos/día por canal de Dailymotion, con 15+ minutos de separación.",
    },
    "cond.dailymotion.detail": {
        "en": "Uploads go to the connected channel. Partner terms can add extra caps. If a day of heavy posting starts failing, wait and drop volume; Dailymotion does not publish a single daily number.",
        "es": "Las subidas van al canal conectado. El contrato de partner puede añadir topes extra. Si un día de mucho volumen empieza a fallar, espera y baja la cadencia; Dailymotion no publica un número diario único.",
    },
    "cond.bilibili.cap": {
        "en": "Member level usually caps daily uploads (often about 5 videos/day on lower levels; higher levels get more). The open platform follows similar account rules.",
        "es": "El nivel de miembro suele limitar las subidas diarias (a menudo unos 5 videos/día en niveles bajos; más en niveles altos). La open platform sigue reglas parecidas de la cuenta.",
    },
    "cond.bilibili.window": {
        "en": "Calendar day on Bilibili (China time), not a rolling 24 h window like Instagram.",
        "es": "Día natural en Bilibili (hora de China), no una ventana corrida de 24 h como Instagram.",
    },
    "cond.bilibili.rate": {
        "en": "Space uploads; the API also rate-limits submit/cover calls. This panel needs ffmpeg for the cover.",
        "es": "Separa las subidas; la API también limita submit/portada. Este panel necesita ffmpeg para la portada.",
    },
    "cond.bilibili.safe": {
        "en": "3–5 videos/day per Bilibili account until you confirm that account’s member-level cap.",
        "es": "3–5 videos/día por cuenta de Bilibili hasta confirmar el tope de nivel de esa cuenta.",
    },
    "cond.bilibili.detail": {
        "en": "稿件 (video submissions) only in this panel. Duplicate or low-quality bursts get held for review. If an upload is rejected for frequency, wait until the next China calendar day.",
        "es": "Solo 稿件 (envíos de video) en este panel. Las ráfagas duplicadas o de baja calidad se quedan en revisión. Si rechazan por frecuencia, espera al siguiente día natural de China.",
    },
    "cond.rumble.cap": {
        "en": "Partner Upload API (token + Channel ID). Rumble does not publish a public daily video quota. Abuse is handled per channel/partner agreement.",
        "es": "Upload API de partners (token + Channel ID). Rumble no publica un cupo diario público de videos. El abuso se gestiona por canal/contrato de partner.",
    },
    "cond.rumble.window": {
        "en": "No official reset clock. Treat activity as a rolling day and space uploads.",
        "es": "Sin reloj oficial de reinicio. Trata la actividad como un día corrido y separa las subidas.",
    },
    "cond.rumble.rate": {
        "en": "One upload at a time per channel is safest; do not parallelize many simple-upload calls.",
        "es": "Lo más seguro es una subida a la vez por canal; no paralelices muchas llamadas a simple-upload.",
    },
    "cond.rumble.safe": {
        "en": "8–10 videos/day per Rumble channel, 15–20 minutes apart.",
        "es": "8–10 videos/día por canal de Rumble, con 15–20 minutos de separación.",
    },
    "cond.rumble.detail": {
        "en": "No public OAuth. Token and Channel ID come from Rumble as a partner. If uploads start returning errors after a burst, stop for several hours. Videos only.",
        "es": "Sin OAuth público. El token y el Channel ID los da Rumble como partner. Si tras una ráfaga empiezan los errores, para varias horas. Solo video.",
    },
    "cond.snapchat.cap": {
        "en": "Public Profile API. No simple public “X videos/day” number. Stories last 24 hours. This panel trims Snapchat video to the first 55 s (min. 540×960).",
        "es": "API de perfil público. No hay un “X videos/día” público simple. Las Stories duran 24 horas. Este panel recorta el video de Snapchat a los primeros 55 s (mín. 540×960).",
    },
    "cond.snapchat.window": {
        "en": "Stories expire after 24 h. API rate limits are per app/profile (429 if you burst).",
        "es": "Las Stories caducan a las 24 h. El rate limit de la API es por app/perfil (429 si vas en ráfaga).",
    },
    "cond.snapchat.rate": {
        "en": "Needs OpenSSL for the request signing this panel uses. Serialize posts; wait between Story and Spotlight.",
        "es": "Hace falta OpenSSL para la firma que usa este panel. Serializa los posts; espera entre Story y Spotlight.",
    },
    "cond.snapchat.safe": {
        "en": "8–10 posts/day per public profile, 20+ minutes apart.",
        "es": "8–10 posts/día por perfil público, con 20+ minutos de separación.",
    },
    "cond.snapchat.detail": {
        "en": "Photos go as 24 h Stories; short vertical MP4 as Spotlight when it meets duration/size. Public profile required. Hitting 429 means wait, do not retry immediately.",
        "es": "Las fotos van como Stories de 24 h; el MP4 vertical corto como Spotlight si cumple duración/tamaño. Hace falta perfil público. Si sale 429, espera; no reintentes al momento.",
    },
    "cond.threads.cap": {
        "en": "VMOS Cloud phone automation (no Meta Threads API in this panel).",
        "es": "Automatización en móvil VMOS Cloud (no hay API de Threads de Meta en este panel).",
    },
    "cond.threads.window": {
        "en": "Depends on the VMOS template and the Threads app on the cloud phone.",
        "es": "Depende de la plantilla VMOS y de la app Threads en el móvil en la nube.",
    },
    "cond.threads.rate": {
        "en": "Space posts; cloud-phone automation can trigger app limits.",
        "es": "Separa las publicaciones; la automatización en el móvil puede chocar con límites de la app.",
    },
    "cond.threads.safe": {
        "en": "Few posts per day per cloud phone until you confirm the account is stable.",
        "es": "Pocas publicaciones al día por móvil hasta confirmar que la cuenta está estable.",
    },
    "cond.threads.detail": {
        "en": "Save Access Key, Secret and padCode in Servers. Publishing via VMOS is the next step.",
        "es": "Guarda Access Key, Secret y padCode en Servidores. Publicar por VMOS es el siguiente paso.",
    },
    "apidoc.limits_title": {
        "en": "Daily video limits",
        "es": "Topes diarios de video",
    },
    "apidoc.limits_intro": {
        "en": "None of these servers allows unlimited video posting. Stay under the safe daily pace so accounts are not flagged.",
        "es": "Ninguno de estos servidores permite publicar videos sin límite. Quédate en el ritmo diario seguro para no marcar las cuentas.",
    },
    "apidoc.limits_col_server": {"en": "Server", "es": "Servidor"},
    "apidoc.limits_col_unlimited": {"en": "Unlimited?", "es": "¿Ilimitado?"},
    "apidoc.limits_col_cap": {"en": "Daily cap / safe pace", "es": "Tope / uso seguro"},
    "apidoc.limits_no": {"en": "No", "es": "No"},
    "apidoc.limits_no_public": {
        "en": "No public daily quota",
        "es": "No hay cupo diario público",
    },
    "apidoc.limits.tiktok": {
        "en": "Daily cap exists (TikTok does not publish the number; integrators usually see 15–25/day). Safe: up to 10/day, 10–15 minutes apart.",
        "es": "Hay tope diario (TikTok no publica el número; suele ser 15–25/día). Uso seguro: hasta 10/día, con 10–15 min de separación.",
    },
    "apidoc.limits.youtube": {
        "en": "Google project quota: 10,000 units/day. videos.insert costs ~1,600 → about 6/day. Safe: 4–5/day. Shared by all channels on the same Client ID.",
        "es": "Cuota del proyecto Google: 10.000 unidades/día. videos.insert gasta ~1.600 → unos 6/día. Uso seguro: 4–5/día. Varias cuentas con el mismo Client ID comparten esa cuota.",
    },
    "apidoc.limits.instagram": {
        "en": "API publishing cap ~50 posts / rolling 24 h (Meta sometimes cites 100). Safe: 15–20 Reels/photos per 24 h.",
        "es": "Tope API ~50 posts / 24 h corridas (Meta a veces cita 100). Uso seguro: 15–20 Reels/fotos cada 24 h.",
    },
    "apidoc.limits.facebook": {
        "en": "API Reels: 30 per rolling 24 h. Safe: 10–12 videos/day per Page; if they are Reels, stay under ~25/24 h.",
        "es": "Reels por API: 30 cada 24 h. Uso seguro: 10–12 videos/día por Página; si son Reels, no pases de ~25/24 h.",
    },
    "apidoc.limits.x": {
        "en": "API: 100 posts / 15 min per user. Unverified accounts: ~50 original posts/day (API + manual). Safe: 10–15/day; unverified under 40/day.",
        "es": "API: 100 posts / 15 min por usuario. Cuentas sin verificar: ~50 posts originales/día (API + a mano). Uso seguro: 10–15/día; sin verificar, menos de 40/día.",
    },
    "apidoc.limits.dailymotion": {
        "en": "No public videos-per-day quota. ~60 API calls/minute and anti-spam still apply. Safe: 10–12/day.",
        "es": "No hay cupo público de videos por día. Sí hay ~60 llamadas/minuto y anti-spam. Uso seguro: 10–12/día.",
    },
    "apidoc.limits.bilibili": {
        "en": "Member level usually caps uploads (often ~5/day on lower levels). China calendar day. Safe: 3–5/day until that account’s level is confirmed.",
        "es": "El nivel de miembro suele limitar (a menudo ~5/día en niveles bajos). Día natural de China. Uso seguro: 3–5/día hasta confirmar el nivel de esa cuenta.",
    },
    "apidoc.limits.bilibili_tv": {
        "en": "No public daily quota. Safe: few videos/day. Keep-alive every 3–5 days. Only mark sent if Bilibili.tv returns a video id.",
        "es": "Sin cuota diaria pública. Uso seguro: pocos videos/día. Keep-alive cada 3–5 días. Solo marca enviado si Bilibili.tv devuelve un id de video.",
    },
    "apidoc.limits.rumble": {
        "en": "No public daily video quota. Safe: 8–10/day, one upload at a time.",
        "es": "No hay cupo diario público. Uso seguro: 8–10/día, una subida a la vez.",
    },
    "apidoc.limits.snapchat": {
        "en": "No simple public X videos/day number. This panel sends max 55 s. Safe: 8–10 posts/day. Wait on HTTP 429.",
        "es": "No hay un X videos/día público simple. Este panel envía como máximo 55 s. Uso seguro: 8–10 posts/día. Si sale 429, espera.",
    },
    "apidoc.limits.odysee": {
        "en": "No social-network quota. Limited by LBC bid, wallet and pipeline. Safe: few videos/day, one upload at a time.",
        "es": "Sin cuota de red social. Limitan el bid LBC, el saldo y el pipeline. Uso seguro: pocos videos al día, una subida a la vez.",
    },
    "apidoc.limits.vmos": {
        "en": "No OAuth quota. Safe: one RPA task at a time per pad; space posts like a real phone.",
        "es": "Sin cuota OAuth. Uso seguro: una tarea RPA a la vez por pad; separa los posts como un móvil real.",
    },
    "apidoc.ffmpeg_ok": {
        "en": "ffmpeg is bundled with the app (imageio-ffmpeg). Heavy files are compressed per network (Instagram 290 MB, others 450 MB, photos 7.8 MB).",
        "es": "ffmpeg viene con la app (imageio-ffmpeg). Los archivos pesados se comprimen por red (Instagram 290 MB, el resto 450 MB, fotos 7,8 MB).",
    },
    "apidoc.ffmpeg_missing": {
        "en": "ffmpeg could not start. Run pip install -r requirements.txt (includes imageio-ffmpeg).",
        "es": "No se pudo arrancar ffmpeg. Ejecuta pip install -r requirements.txt (incluye imageio-ffmpeg).",
    },
    "apidoc.intro": {
        "en": "What each server needs so publishing works. Official OAuth (or Rumble’s partner API) is the default. Saving Client ID/Secret only stores the app: the server stays unlinked until you click Connect and sign in; Disconnect or Remove API unlinks it, and connecting another account on the same card replaces the previous one. Register SITE_URL/oauth/{platform}/callback in each developer console. VMOS Cloud is an alternative for TikTok, Instagram, Facebook, YouTube, X and Snapchat: connect from Servers without pasting social access tokens. Dailymotion, Bilibili.com and Rumble stay on their APIs. Bilibili.tv uses an isolated browser session (email/password). Odysee signs in with email/password (LBRY auth token, TUS). API type, video, photo and token renewal are on Servers.",
        "es": "Qué hay que hacer en cada servidor para que la publicación funcione. El camino por defecto es OAuth oficial (o la API de partners de Rumble). Guardar Client ID/Secret solo guarda la app: el servidor sigue sin vincular hasta que pulses Conectar e inicies sesión; Desconectar o Quitar API lo desvincula, y conectar otra cuenta en la misma ficha reemplaza la anterior. Registra SITE_URL/oauth/{plataforma}/callback en cada consola de desarrollador. VMOS Cloud es una alternativa para TikTok, Instagram, Facebook, YouTube, X y Snapchat: se conecta desde Servidores sin pegar tokens de esas redes. Dailymotion, Bilibili.com y Rumble siguen por su API. Bilibili.tv usa un navegador interno (email/contraseña). Odysee entra con email/contraseña (auth token LBRY, TUS). El tipo de API, video, foto y renovación de token se ven en Servidores.",
    },
    "apidoc.col_server": {"en": "Server", "es": "Servidor"},
    "apidoc.col_api": {"en": "API", "es": "API"},
    "apidoc.col_video": {"en": "Video", "es": "Video"},
    "apidoc.col_photo": {"en": "Photo", "es": "Foto"},
    "apidoc.col_token": {"en": "Token renewal", "es": "Renovación de token"},
    "apidoc.col_setup": {"en": "Setup steps", "es": "Pasos para que funcione"},
    "apidoc.col_extra": {"en": "Extra steps", "es": "Pasos extra"},
    "apidoc.api.oauth": {"en": "Official OAuth", "es": "OAuth oficial"},
    "apidoc.api.partner": {"en": "Partner API", "es": "API de partners"},
    "apidoc.api.none": {"en": "No API", "es": "No es API"},
    "apidoc.api.vmos": {"en": "VMOS Cloud", "es": "VMOS Cloud"},
    "apidoc.api.filehost": {"en": "Host API (PPV)", "es": "API del host (PPV)"},
    "apidoc.api.lbry": {"en": "LBRY / Odysee", "es": "LBRY / Odysee"},
    "apidoc.api.hive": {"en": "Hive + IPFS", "es": "Hive + IPFS"},
    "apidoc.api.browser": {"en": "Internal browser", "es": "Navegador interno"},
    "apidoc.token.auto": {"en": "Automatic", "es": "Automático"},
    "apidoc.token.manual": {"en": "Manual", "es": "Manual"},
    "apidoc.token.none": {"en": "Not used", "es": "No aplica"},
    "apidoc.vmos.name": {"en": "VMOS Cloud", "es": "VMOS Cloud"},
    "apidoc.vmos.step1": {
        "en": "vmoscloud.com → Developer → API: copy Access Key ID and Secret.",
        "es": "vmoscloud.com → Developer → API: copia Access Key ID y Secret.",
    },
    "apidoc.vmos.step2": {
        "en": "Create a cloud phone, install the app, sign in, copy padCode.",
        "es": "Crea un móvil en la nube, instala la app, inicia sesión y copia el padCode.",
    },
    "apidoc.vmos.step3": {
        "en": "Create an RPA template that posts from a file or URL; copy template/scriptId.",
        "es": "Crea una plantilla RPA que publique desde archivo o URL y copia el template/scriptId.",
    },
    "apidoc.vmos.step4": {
        "en": "Servers → Connect with VMOS. Save keys, padCode and template. Test before posting.",
        "es": "Servidores → Conectar con VMOS. Guarda keys, padCode y plantilla. Prueba antes de publicar.",
    },
    "apidoc.vmos.extra": {
        "en": "TikTok, Instagram, Facebook, YouTube, X, Snapchat. No template = not sent. Not for Dailymotion, Bilibili or Rumble.",
        "es": "TikTok, Instagram, Facebook, YouTube, X y Snapchat. Sin plantilla no se envía. No aplica a Dailymotion, Bilibili ni Rumble.",
    },
    "apidoc.vmos_alt": {
        "en": "Optional: Connect with VMOS instead of OAuth (Access Key, Secret, padCode, template).",
        "es": "Opcional: Conectar con VMOS en lugar de OAuth (Access Key, Secret, padCode, plantilla).",
    },
    "apidoc.filehost.step1": {
        "en": "On {name}: Settings / API. Copy the API key (MixDrop: also email; Streamtape: API login).",
        "es": "En {name}: Settings / API. Copia la API key (MixDrop: también el email; Streamtape: API login).",
    },
    "apidoc.filehost.step2": {
        "en": "Servers → Connect. Paste the key (and extra field if asked). Test the API.",
        "es": "Servidores → Conectar. Pega la key (y el extra si lo pide). Prueba la API.",
    },
    "apidoc.filehost.step3": {
        "en": "Publish a video; the host returns the watch URL. Payouts stay on {name}.",
        "es": "Publica un video; el host devuelve la URL. Los pagos siguen en {name}.",
    },
    "apidoc.filehost.extra": {
        "en": "No OAuth. Video only. Linked proxy is used.",
        "es": "Sin OAuth. Solo video. Se usa el proxy vinculado.",
    },
    "apidoc.filehost.trial": {
        "en": "(pago) = trial host. Check if they pay before relying on them.",
        "es": "(pago) = host de prueba. Comprueba si pagan antes de depender de él.",
    },
    "apidoc.odysee.step1": {
        "en": "Create an account on odysee.com (no public OAuth).",
        "es": "Crea una cuenta en odysee.com (no hay OAuth público).",
    },
    "apidoc.odysee.step2": {
        "en": "Servers → Connect with email/password of odysee.com. Optional channel: 40-char claim ID or @handle. The panel stores the auth token.",
        "es": "Servidores → Conectar con email/contraseña de odysee.com. Canal opcional: claim ID de 40 caracteres o @canal. El panel guarda el auth token.",
    },
    "apidoc.odysee.step3": {
        "en": "Publish: TUS upload (50 MB chunks) then stream_create. Needs LBC in the wallet for the bid.",
        "es": "Publica: subida TUS (trozos de 50 MB) y luego stream_create. Hace falta LBC en el monedero para el bid.",
    },
    "apidoc.odysee.extra": {
        "en": "Video only. Linked proxy is used.",
        "es": "Solo video. Se usa el proxy vinculado.",
    },
    "apidoc.dtube.step1": {
        "en": "Create or use a d.tube account with email and password.",
        "es": "Cuenta de d.tube con email y contraseña.",
    },
    "apidoc.dtube.step2": {
        "en": "Servers → Connect. Save email and password. The panel keeps the browser session.",
        "es": "Servidores → Conectar. Guarda email y contraseña. El panel mantiene la sesión del navegador.",
    },
    "apidoc.dtube.step3": {
        "en": "If the session expires, the panel logs in again automatically. Cloudflare Turnstile on upload may still block automated publishing.",
        "es": "Si la sesión caduca, el panel vuelve a entrar solo. El Turnstile de Cloudflare en la subida puede seguir bloqueando la publicación automática.",
    },
    "apidoc.dtube.extra": {
        "en": "Video only. Linked proxy is used.",
        "es": "Solo vídeo. Se usa el proxy vinculado.",
    },
    "apidoc.extra_none": {"en": "None", "es": "Ninguno"},
    "apidoc.tiktok.step1": {
        "en": "Create an app on developers.tiktok.com.",
        "es": "Crea una app en developers.tiktok.com.",
    },
    "apidoc.tiktok.step2": {
        "en": "Enable Login Kit + Content Posting (user.info.basic, video.upload).",
        "es": "Activa Login Kit y Content Posting (user.info.basic, video.upload).",
    },
    "apidoc.tiktok.step3": {
        "en": "Redirect URI: SITE_URL/oauth/tiktok/callback.",
        "es": "URI de redirección: SITE_URL/oauth/tiktok/callback.",
    },
    "apidoc.tiktok.step4": {
        "en": "Servers: save Client Key/Secret → Connect with TikTok.",
        "es": "Servidores: guarda Client Key/Secret → Conectar con TikTok.",
    },
    "apidoc.tiktok.extra": {
        "en": "Wait for TikTok to approve Content Posting before Direct Post.",
        "es": "Espera a que TikTok apruebe Content Posting para el envío directo.",
    },
    "apidoc.youtube.step1": {
        "en": "Google Cloud: web OAuth client + YouTube Data API v3.",
        "es": "Google Cloud: cliente OAuth web + YouTube Data API v3.",
    },
    "apidoc.youtube.step2": {
        "en": "Redirect URI: SITE_URL/oauth/youtube/callback.",
        "es": "URI de redirección: SITE_URL/oauth/youtube/callback.",
    },
    "apidoc.youtube.step3": {
        "en": "Servers: save Client ID/Secret → Connect with YouTube.",
        "es": "Servidores: guarda Client ID/Secret → Conectar con YouTube.",
    },
    "apidoc.youtube.extra": {
        "en": "Google may warn until the OAuth consent screen is verified. Clips ≤ 3 min go up as Shorts.",
        "es": "Google puede avisar hasta verificar la pantalla de consentimiento. Clips ≤ 3 min se suben como Shorts.",
    },
    "apidoc.instagram.step1": {
        "en": "Meta for Developers: Instagram + Business Login.",
        "es": "Meta for Developers: Instagram + Business Login.",
    },
    "apidoc.instagram.step2": {
        "en": "Redirect URI: SITE_URL/oauth/instagram/callback.",
        "es": "URI de redirección: SITE_URL/oauth/instagram/callback.",
    },
    "apidoc.instagram.step3": {
        "en": "Use a professional account (Business or Creator), not personal.",
        "es": "Usa una cuenta profesional (Business o Creador), no personal.",
    },
    "apidoc.instagram.step4": {
        "en": "Servers: save App ID/Secret → Connect with Instagram.",
        "es": "Servidores: guarda App ID/Secret → Conectar con Instagram.",
    },
    "apidoc.instagram.extra": {
        "en": "Photos need a public https SITE_URL (not localhost). Video = Reels.",
        "es": "Fotos: SITE_URL público https (no localhost). Video = Reels.",
    },
    "apidoc.facebook.step1": {
        "en": "Meta: Facebook Login with pages_show_list and pages_manage_posts.",
        "es": "Meta: Facebook Login con pages_show_list y pages_manage_posts.",
    },
    "apidoc.facebook.step2": {
        "en": "Redirect URI: SITE_URL/oauth/facebook/callback.",
        "es": "URI de redirección: SITE_URL/oauth/facebook/callback.",
    },
    "apidoc.facebook.step3": {
        "en": "Servers: save App ID/Secret → Connect with Facebook → pick Pages.",
        "es": "Servidores: guarda App ID/Secret → Conectar con Facebook → elige Páginas.",
    },
    "apidoc.facebook.extra": {
        "en": "Pages only, not personal profiles. App must be Live (or the Page owner must be an app admin/tester) or Meta returns “cannot call API for app”.",
        "es": "Solo Páginas, no perfiles personales. La app debe estar En vivo (o el dueño de la Página ser admin/tester de la app); si no, Meta responde “cannot call API for app”.",
    },
    "apidoc.threads.step1": {
        "en": "VMOS: cloud phone, install Threads, copy Access Key, Secret and padCode.",
        "es": "VMOS: móvil en la nube, instala Threads y copia Access Key, Secret y padCode.",
    },
    "apidoc.threads.step2": {
        "en": "Servers → Connect with VMOS Threads.",
        "es": "Servidores → Conectar con VMOS Threads.",
    },
    "apidoc.x.step1": {
        "en": "X Developer Portal: OAuth 2.0 app with PKCE.",
        "es": "Portal de X: app OAuth 2.0 con PKCE.",
    },
    "apidoc.x.step2": {
        "en": "Redirect URI: SITE_URL/oauth/x/callback.",
        "es": "URI de redirección: SITE_URL/oauth/x/callback.",
    },
    "apidoc.x.step3": {
        "en": "Servers: save Client ID/Secret → Connect with X.",
        "es": "Servidores: guarda Client ID/Secret → Conectar con X.",
    },
    "apidoc.x.extra": {
        "en": "Needs a paid write API plan. Config X: mark the account whose membership publishes for the others. Follower checks run on publish, at most once a week.",
        "es": "Hace falta plan de pago con escritura. Config X: marca la cuenta cuya membresía publica por las demás. Los seguidores se revisan al publicar, como máximo una vez por semana.",
    },
    "apidoc.dailymotion.step1": {
        "en": "Get API Key and Secret from Dailymotion (partner / developer app).",
        "es": "Obtén API Key y Secret en Dailymotion (app de partner / desarrollador).",
    },
    "apidoc.dailymotion.step2": {
        "en": "Studio → API keys: Callback URL = SITE_URL/oauth/dailymotion/callback.",
        "es": "Studio → API keys: Callback URL = SITE_URL/oauth/dailymotion/callback.",
    },
    "apidoc.dailymotion.step3": {
        "en": "Servers: save keys → Connect with Dailymotion and sign in.",
        "es": "Servidores: guarda las claves → Conectar con Dailymotion e inicia sesión.",
    },
    "apidoc.dailymotion.extra": {
        "en": "Uploads go to the connected channel.",
        "es": "Las subidas van al canal conectado.",
    },
    "apidoc.bilibili.step1": {
        "en": "Start here (Bilibili.com Open Platform, 投稿 — not Bilibili.tv): https://open.bilibili.com/doc?utm_source",
        "es": "Empieza aquí (Bilibili.com Open Platform / 投稿, no Bilibili.tv): https://open.bilibili.com/doc?utm_source",
    },
    "apidoc.bilibili.step2": {
        "en": "Create the app in that console. Copy Client ID and Client Secret. Register this exact redirect URI: SITE_URL/oauth/bilibili/callback",
        "es": "Crea la app en esa consola. Copia Client ID y Client Secret. Registra esta URI exacta: SITE_URL/oauth/bilibili/callback",
    },
    "apidoc.bilibili.step3": {
        "en": "Servers: save Client ID/Secret, then Connect with Bilibili (OAuth) or use Connect with QR code below. OAuth needs a certified company app. The QR session is a browser login, not Open Platform.",
        "es": "Servidores: guarda Client ID/Secret, luego Conectar con Bilibili (OAuth) o usa Conectar con código QR debajo. El OAuth pide una app de empresa certificada. El QR es un login del navegador, no Open Platform.",
    },
    "apidoc.bilibili.extra": {
        "en": "ffmpeg is required for the cover (a random 16:10 frame). Optional: BILIBILI_TID and BILIBILI_TAG in .env. QR web session publishes 稿件 with the scanned login. This is Bilibili.com only.",
        "es": "ffmpeg hace falta para la portada (un fotograma al azar 16:10). Opcional: BILIBILI_TID y BILIBILI_TAG en .env. La sesión QR publica 稿件 con el login escaneado. Esto es solo Bilibili.com.",
    },
    "apidoc.bilibili_tv.step1": {
        "en": "Create an account on bilibili.tv (international site, not member.bilibili.com).",
        "es": "Crea una cuenta en bilibili.tv (web internacional, no member.bilibili.com).",
    },
    "apidoc.bilibili_tv.step2": {
        "en": "Servers → Connect with email/password. The panel stores an isolated Chromium profile per account.",
        "es": "Servidores → Conectar con email/contraseña. Cada cuenta tiene un perfil Chromium aislado.",
    },
    "apidoc.bilibili_tv.step3": {
        "en": "Keep-alive every 3–5 days at staggered hours. If cookies expire it signs in again; if captcha/SMS appears, complete it yourself.",
        "es": "Keep-alive cada 3–5 días a horas distintas. Si caducan las cookies, vuelve a entrar; si pide captcha/SMS, lo completas tú.",
    },
    "apidoc.bilibili_tv.extra": {
        "en": "Publishes through studio.bilibili.tv with the saved browser session. Needs: pip install playwright && playwright install chromium. If the studio page changes or captcha appears, the post is not marked sent.",
        "es": "Publica por studio.bilibili.tv con la sesión del navegador. Hace falta: pip install playwright && playwright install chromium. Si cambia el estudio o sale captcha, el post no se marca como enviado.",
    },
    "apidoc.rumble.step1": {
        "en": "No public OAuth. Apply for the partner Upload API.",
        "es": "No hay OAuth público. Pide la Upload API de partners.",
    },
    "apidoc.rumble.step2": {
        "en": "Rumble gives an access token and a Channel ID (not the livestream chat URL).",
        "es": "Rumble da un access token y un Channel ID (no la URL de chat en vivo).",
    },
    "apidoc.rumble.step3": {
        "en": "Servers: save token and Channel ID. There is no Connect with Rumble button.",
        "es": "Servidores: guarda token y Channel ID. No hay botón Conectar con Rumble.",
    },
    "apidoc.rumble.extra": {
        "en": "If the token is revoked, paste a new one.",
        "es": "Si revocan el token, pega uno nuevo.",
    },
    "apidoc.snapchat.step1": {
        "en": "Snap Kit / Public Profile app (not Marketing/Ads). Scope: snapchat-profile-api only.",
        "es": "App Snap Kit / Perfil público (no Marketing/Ads). Permiso: solo snapchat-profile-api.",
    },
    "apidoc.snapchat.step2": {
        "en": "Redirect URI: SITE_URL/oauth/snapchat/callback.",
        "es": "URI de redirección: SITE_URL/oauth/snapchat/callback.",
    },
    "apidoc.snapchat.step3": {
        "en": "Servers: save Client ID/Secret → Connect with Snapchat.",
        "es": "Servidores: guarda Client ID/Secret → Conectar con Snapchat.",
    },
    "apidoc.snapchat.extra": {
        "en": "Needs OpenSSL (AES-256-CBC). Photos = Stories 24 h. Video > 55 s is trimmed to 55 s (Spotlight 6–55 s, min. 540×960).",
        "es": "Hace falta OpenSSL (AES-256-CBC). Fotos = Stories 24 h. Video > 55 s se recorta a 55 s (Spotlight 6–55 s, mín. 540×960).",
    },
    # ------------------------------------------------------------------
    # Proxys
    # ------------------------------------------------------------------
    "proxys.title": {"en": "Proxies", "es": "Proxys"},
    "proxys.intro": {
        "en": "Add proxies in any common format. Test each one to detect its country. OAuth, PPV host, Odysee, DTube, Bilibili.tv and Bilibili.com QR sessions use the linked proxy. VMOS accounts do not: the cloud phone’s own network is used.",
        "es": "Añade proxys en cualquier formato habitual. Prueba cada uno para detectar su país. Las cuentas OAuth, las de hosts PPV, Odysee, DTube, Bilibili.tv y la sesión QR de Bilibili.com sí usan el proxy vinculado. Las de VMOS no: sale la red del móvil en la nube.",
    },
    "proxys.info_btn": {"en": "About proxies", "es": "Información sobre proxys"},
    "proxys.add": {"en": "Add proxy", "es": "Añadir proxy"},
    "proxys.search": {"en": "Search proxies…", "es": "Buscar proxys…"},
    "proxys.empty": {"en": "No proxies yet.", "es": "Aún no hay proxys."},
    "proxys.modal_create": {"en": "New proxy", "es": "Nuevo proxy"},
    "proxys.modal_edit": {"en": "Edit proxy", "es": "Editar proxy"},
    "proxys.field_label": {"en": "Label (optional)", "es": "Etiqueta (opcional)"},
    "proxys.field_proxy": {"en": "Proxy", "es": "Proxy"},
    "proxys.field_notes": {"en": "Notes (optional)", "es": "Notas (opcional)"},
    "proxys.field_links": {
        "en": "Link to accounts",
        "es": "Vincular a cuentas",
    },
    "proxys.links_search": {
        "en": "Search account to add…",
        "es": "Buscar cuenta para añadir…",
    },
    "proxys.links_hint": {
        "en": "Only linked accounts appear here. Search to add more.",
        "es": "Aquí solo se ven las cuentas vinculadas. Busca para añadir más.",
    },
    "proxys.link_group": {"en": "Group: {name}", "es": "Grupo: {name}"},
    "proxys.link_account": {"en": "Account: {name}", "es": "Cuenta: {name}"},
    "proxys.links_none": {"en": "No links", "es": "Sin vínculos"},
    "proxys.formats_hint": {
        "en": "HTTP, HTTPS, SOCKS4 and SOCKS5: host:port · user:pass@host:port · host:port:user:pass · user:pass:host:port · http(s)/socks://user:pass@host:port",
        "es": "HTTP, HTTPS, SOCKS4 y SOCKS5: host:puerto · usuario:pass@host:puerto · host:puerto:usuario:pass · usuario:pass:host:puerto · http(s)/socks://usuario:pass@host:puerto",
    },
    "proxys.col_country": {"en": "Country", "es": "País"},
    "proxys.col_proxy": {"en": "Proxy", "es": "Proxy"},
    "proxys.col_status": {"en": "Status", "es": "Estado"},
    "proxys.col_last_check": {"en": "Last check", "es": "Última prueba"},
    "proxys.no_country": {"en": "Unknown", "es": "Desconocido"},
    "proxys.active": {"en": "Active", "es": "Activo"},
    "proxys.inactive": {"en": "Inactive", "es": "Inactivo"},
    "proxys.test": {"en": "Test", "es": "Probar"},
    "proxys.testing": {"en": "Testing…", "es": "Probando…"},
    "proxys.edit": {"en": "Edit", "es": "Editar"},
    "proxys.delete": {"en": "Delete", "es": "Eliminar"},
    "proxys.save": {"en": "Save", "es": "Guardar"},
    "proxys.cancel": {"en": "Cancel", "es": "Cancelar"},
    "proxys.test_ok": {
        "en": "OK — {country} ({ip})",
        "es": "OK — {country} ({ip})",
    },
    "proxys.test_fail": {"en": "Test failed", "es": "Prueba fallida"},
    "proxys.confirm_delete_title": {"en": "Delete proxy?", "es": "¿Eliminar proxy?"},
    "proxys.confirm_delete_body": {
        "en": "This proxy will be removed permanently.",
        "es": "Este proxy se eliminará de forma permanente.",
    },
    "proxys.check_ok": {"en": "OK", "es": "OK"},
    "proxys.check_fail": {"en": "Failed", "es": "Falló"},
    "proxys.check_pending": {"en": "Not tested", "es": "Sin probar"},
    "proxys.err.empty": {"en": "Proxy line is required.", "es": "La línea de proxy es obligatoria."},
    "proxys.err.invalid_format": {
        "en": "Unrecognized proxy format.",
        "es": "Formato de proxy no reconocido.",
    },
    "proxys.err.generic": {"en": "Could not save proxy.", "es": "No se pudo guardar el proxy."},
    "proxys.err.host_unresolved": {
        "en": "Could not resolve the proxy host. Check the address.",
        "es": "No se pudo resolver el host del proxy. Revisa la dirección.",
    },
    "proxys.err.timeout": {
        "en": "The proxy did not respond in time.",
        "es": "El proxy no respondió a tiempo.",
    },
    "proxys.err.refused": {
        "en": "The proxy refused the connection.",
        "es": "El proxy rechazó la conexión.",
    },
    "proxys.err.unreachable": {
        "en": "The proxy is unreachable from this server.",
        "es": "No hay ruta hacia el proxy desde este servidor.",
    },
    "proxys.err.reset": {
        "en": "The proxy closed the connection.",
        "es": "El proxy cerró la conexión.",
    },
    "proxys.err.auth": {
        "en": "The proxy requires a valid username and password.",
        "es": "El proxy pide un usuario y contraseña válidos.",
    },
    "proxys.err.denied": {
        "en": "The proxy denied access.",
        "es": "El proxy denegó el acceso.",
    },
    "proxys.err.ssl": {
        "en": "Secure connection to the proxy failed.",
        "es": "Falló la conexión segura con el proxy.",
    },
    "proxys.err.http_status": {
        "en": "The proxy returned an HTTP error.",
        "es": "El proxy devolvió un error HTTP.",
    },
    "proxys.err.socks_fail": {
        "en": "The SOCKS handshake with the proxy failed.",
        "es": "Falló el protocolo SOCKS con el proxy.",
    },
    "proxys.err.geo_failed": {
        "en": "Connected, but the country could not be detected.",
        "es": "Conectó, pero no se pudo detectar el país.",
    },
    "proxys.err.test_failed": {
        "en": "The proxy did not work. Check host, port and credentials.",
        "es": "El proxy no funcionó. Revisa host, puerto y credenciales.",
    },
    # ------------------------------------------------------------------
    # Membresías
    # ------------------------------------------------------------------
    "membresias.title": {"en": "Pricing", "es": "Precio"},
    "membresias.intro": {
        "en": "Pick the monthly plan that fits your publishing volume.",
        "es": "Elige el plan mensual que se ajusta a tu volumen de publicaciones.",
    },
    "membresias.current": {"en": "Your plan", "es": "Tu plan"},
    "membresias.no_plan": {"en": "No plan yet", "es": "Sin plan aún"},
    "membresias.per_month": {"en": "/ month", "es": "/ mes"},
    "membresias.free": {"en": "Free", "es": "Gratis"},
    "membresias.videos": {"en": "{n} videos", "es": "{n} videos"},
    "membresias.stats": {"en": "{n} stats queries", "es": "{n} consultas de estadísticas"},
    "membresias.any_platform": {
        "en": "Any connected platform",
        "es": "Cualquier plataforma conectada",
    },
    "membresias.cancel_anytime": {
        "en": "Cancel subscription anytime",
        "es": "Cancelar suscripción cuando quieras",
    },
    "membresias.featured": {"en": "Most chosen", "es": "Más elegido"},
    "membresias.invite_only": {"en": "Invite only", "es": "Solo invitados"},
    "membresias.choose": {"en": "Choose plan", "es": "Elegir plan"},
    "membresias.selected_badge": {"en": "Selected", "es": "Seleccionado"},
    "membresias.checkout_step": {
        "en": "Confirm your plan",
        "es": "Confirma tu plan",
    },
    "membresias.current_badge": {"en": "Current", "es": "Actual"},
    "membresias.checkout_title": {"en": "Pay {name}", "es": "Pagar {name}"},
    "membresias.checkout_hint": {
        "en": "Pay with one of the methods below, then register the purchase. An admin will confirm it.",
        "es": "Paga con uno de los métodos y registra la compra. Un admin la confirmará.",
    },
    "membresias.no_methods": {
        "en": "No payment methods are available yet.",
        "es": "Aún no hay medios de pago disponibles.",
    },
    "membresias.note": {"en": "Note (optional)", "es": "Nota (opcional)"},
    "membresias.submit_purchase": {"en": "Register purchase", "es": "Registrar compra"},
    "membresias.copied": {"en": "Copied", "es": "Copiado"},
    "membresias.copy": {"en": "Copy", "es": "Copiar"},
    "membresias.pay_to": {"en": "Pay to", "es": "Pagar a"},
    "membresias.plan.guest.name": {"en": "Guest Invite Plan 0", "es": "Plan Invitados 0"},
    "membresias.plan.guest.tagline": {
        "en": "For invited users. A gentle start to publish and check stats.",
        "es": "Para usuarios invitados. Un comienzo suave para publicar y ver estadísticas.",
    },
    "membresias.plan.standard.name": {"en": "Standard", "es": "Standard"},
    "membresias.plan.standard.tagline": {
        "en": "A solid monthly cadence for growing accounts.",
        "es": "Un ritmo mensual sólido para cuentas en crecimiento.",
    },
    "membresias.plan.plus.name": {"en": "Plus", "es": "Plus"},
    "membresias.plan.plus.tagline": {
        "en": "More videos and more room to read your numbers.",
        "es": "Más videos y más margen para leer tus números.",
    },
    "membresias.plan.enterprise.name": {"en": "Enterprise", "es": "Enterprise"},
    "membresias.plan.enterprise.tagline": {
        "en": "Serious volume for teams that publish every week.",
        "es": "Volumen serio para equipos que publican cada semana.",
    },
    "membresias.plan.premium.name": {"en": "Premium", "es": "Premium"},
    "membresias.plan.premium.tagline": {
        "en": "High output with stats to steer the strategy.",
        "es": "Alto rendimiento con estadísticas para dirigir la estrategia.",
    },
    "membresias.plan.ultra.name": {"en": "Ultra", "es": "Ultra"},
    "membresias.plan.ultra.tagline": {
        "en": "Maximum monthly capacity. No ceiling on ambition.",
        "es": "Capacidad mensual máxima. Sin techo para la ambición.",
    },
    "membresias.err.generic": {"en": "Could not complete that action.", "es": "No se pudo completar esa acción."},
    "membresias.err.name_required": {"en": "Name is required.", "es": "El nombre es obligatorio."},
    "membresias.err.invalid_plan": {"en": "That plan cannot be purchased.", "es": "Ese plan no se puede comprar."},
    "membresias.err.invalid_payment_method": {
        "en": "Choose a valid payment method.",
        "es": "Elige un medio de pago válido.",
    },
    "membresias.err.invalid_status": {"en": "Invalid status.", "es": "Estado no válido."},
    "membresias.err.not_found": {"en": "Not found.", "es": "No encontrado."},
    "membresias.err.create_failed": {"en": "Could not save.", "es": "No se pudo guardar."},
    "membresias.err.insufficient_wallet": {
        "en": "Not enough wallet balance.",
        "es": "Saldo a favor insuficiente.",
    },
    "membresias.err.invalid_amount": {
        "en": "Enter a valid USD amount.",
        "es": "Introduce un importe en USD válido.",
    },
    "membresias.err.user_required": {"en": "User not found.", "es": "Usuario no encontrado."},
    "membresias.err.credit_tiktok_only": {
        "en": "Wallet credit can only be added to TikTok users.",
        "es": "El saldo solo se puede añadir a usuarios TikTok.",
    },
    "membresias.err.no_plan": {
        "en": "Choose a plan on Pricing before publishing or querying stats.",
        "es": "Elige un plan en Precio para publicar o consultar estadísticas.",
    },
    "membresias.err.quota_videos": {
        "en": "You have used all videos included in your plan for this period.",
        "es": "Ya usaste todos los videos de tu plan en este periodo.",
    },
    "membresias.err.quota_stats": {
        "en": "You have used all stats queries included in your plan for this period.",
        "es": "Ya usaste todas las consultas de estadísticas de tu plan en este periodo.",
    },
    "membresias.quota_videos": {
        "en": "Videos {used} / {limit}",
        "es": "Videos {used} / {limit}",
    },
    "membresias.quota_stats": {
        "en": "Stats queries {used} / {limit}",
        "es": "Consultas {used} / {limit}",
    },
    "membresias.wallet": {"en": "Wallet", "es": "Saldo a favor"},
    "membresias.wallet_balance": {"en": "Credit: USD {n}", "es": "Saldo a favor: USD {n}"},
    "membresias.unused_credit": {
        "en": "Unused plan value: USD {n}",
        "es": "Valor no usado del plan: USD {n}",
    },
    "membresias.cancel_plan": {"en": "Cancel plan", "es": "Cancelar plan"},
    "membresias.cancel_ok": {
        "en": "Plan cancelled. Unused value was added to your wallet.",
        "es": "Plan cancelado. El valor no usado pasó a tu saldo a favor.",
    },
    "membresias.quote_price": {"en": "Plan price: USD {n}", "es": "Precio del plan: USD {n}"},
    "membresias.quote_credit": {
        "en": "Credit from current plan: USD {n}",
        "es": "Crédito del plan actual: USD {n}",
    },
    "membresias.quote_wallet": {
        "en": "Wallet credit applied: USD {n}",
        "es": "Saldo aplicado a favor: USD {n}",
    },
    "membresias.quote_due": {"en": "Amount to pay: USD {n}", "es": "Importe a pagar: USD {n}"},
    "membresias.quote_leftover": {
        "en": "Leftover credit to wallet: USD {n}",
        "es": "Sobrante a saldo a favor: USD {n}",
    },
    "membresias.use_wallet": {"en": "Use wallet credit", "es": "Usar saldo a favor"},
    "membresias.pay_covered": {
        "en": "Covered by wallet. No extra payment needed.",
        "es": "Cubierto con saldo a favor. No hace falta pagar de más.",
    },
    "membresias.checkout_instant_ok": {
        "en": "Plan updated. Unused value was converted to wallet credit.",
        "es": "Plan actualizado. El valor no usado se convirtió en saldo a favor.",
    },
    # ------------------------------------------------------------------
    # Pagos
    # ------------------------------------------------------------------
    "pagos.title": {"en": "Payments", "es": "Pagos"},
    "pagos.head_title": {"en": "Payments-Recharge (USD)", "es": "Pagos-Recarga (USD)"},
    "pagos.intro": {
        "en": "Purchase history for your memberships.",
        "es": "Historial de compras de tus membresías.",
    },
    "pagos.admin_intro": {
        "en": "Confirm payments and manage the methods customers can use.",
        "es": "Confirma pagos y gestiona los medios que podrán usar los clientes.",
    },
    "pagos.info_btn": {"en": "About payments", "es": "Información sobre pagos"},
    "pagos.empty": {"en": "No purchases yet.", "es": "Aún no hay compras."},
    "pagos.methods_title": {"en": "Payment methods", "es": "Medios de pago"},
    "pagos.methods_intro": {
        "en": "Add the channels with the lightest requirements: Binance Pay, USDT, Stripe, PayPal…",
        "es": "Añade los canales con menos requisitos: Binance Pay, USDT, Stripe, PayPal…",
    },
    "pagos.add_method": {"en": "Add method", "es": "Añadir medio"},
    "pagos.modal_create": {"en": "New payment method", "es": "Nuevo medio de pago"},
    "pagos.modal_edit": {"en": "Edit payment method", "es": "Editar medio de pago"},
    "pagos.field_kind": {"en": "Type", "es": "Tipo"},
    "pagos.field_name": {"en": "Display name", "es": "Nombre"},
    "pagos.field_pay_to": {"en": "Pay to (wallet, Pay ID, email…)", "es": "Pagar a (wallet, Pay ID, email…)"},
    "pagos.field_instructions": {"en": "Instructions", "es": "Instrucciones"},
    "pagos.field_notes": {"en": "Internal notes", "es": "Notas internas"},
    "pagos.save": {"en": "Save", "es": "Guardar"},
    "pagos.cancel": {"en": "Cancel", "es": "Cancelar"},
    "pagos.edit": {"en": "Edit", "es": "Editar"},
    "pagos.delete": {"en": "Delete", "es": "Eliminar"},
    "pagos.confirm_delete_title": {"en": "Delete payment method?", "es": "¿Eliminar medio de pago?"},
    "pagos.confirm_delete_body": {
        "en": "Customers will no longer see this method.",
        "es": "Los clientes ya no verán este medio.",
    },
    "pagos.methods_empty": {"en": "No payment methods yet.", "es": "Aún no hay medios de pago."},
    "pagos.status.pending": {"en": "Pending", "es": "Pendiente"},
    "pagos.status.paid": {"en": "Paid", "es": "Pagado"},
    "pagos.status.rejected": {"en": "Rejected", "es": "Rechazado"},
    "pagos.status.cancelled": {"en": "Cancelled", "es": "Cancelado"},
    "pagos.mark_paid": {"en": "Mark paid", "es": "Marcar pagado"},
    "pagos.mark_rejected": {"en": "Reject", "es": "Rechazar"},
    "pagos.col_when": {"en": "Date", "es": "Fecha"},
    "pagos.col_plan": {"en": "Plan", "es": "Plan"},
    "pagos.col_user": {"en": "User", "es": "Usuario"},
    "pagos.col_method": {"en": "Method", "es": "Medio"},
    "pagos.col_amount": {"en": "Amount", "es": "Importe"},
    "pagos.col_status": {"en": "Status", "es": "Estado"},
    "pagos.filter_paid": {"en": "Paid", "es": "Pagos"},
    "pagos.kind.binance_pay": {"en": "Binance Pay", "es": "Binance Pay"},
    "pagos.kind.binance_transfer": {
        "en": "Binance transfer (Pay ID)",
        "es": "Transferencia Binance (Pay ID)",
    },
    "pagos.kind.usdt_trc20": {"en": "USDT TRC-20", "es": "USDT TRC-20"},
    "pagos.kind.usdt_bep20": {"en": "USDT BEP-20", "es": "USDT BEP-20"},
    "pagos.kind.stripe": {"en": "Stripe (cards)", "es": "Stripe (tarjetas)"},
    "pagos.kind.paypal": {"en": "PayPal", "es": "PayPal"},
    "pagos.kind.wise": {"en": "Wise", "es": "Wise"},
    "pagos.kind.custom": {"en": "Other", "es": "Otro"},
    "pagos.kind.wallet": {"en": "Wallet", "es": "Saldo a favor"},
    "pagos.wallet_hint": {
        "en": "Your wallet credit is applied first. Pay only the remainder with another method.",
        "es": "Tu saldo a favor se aplica primero. El resto se paga con otro medio.",
    },
    "pagos.wallet_title": {"en": "Wallet credit", "es": "Saldo a favor"},
    "pagos.wallet_available": {"en": "Available balance", "es": "Saldo disponible"},
    "pagos.wallet_balance": {"en": "Available: USD {n}", "es": "Saldo disponible: USD {n}"},
    "pagos.use_wallet": {"en": "Use available balance", "es": "Usar saldo disponible"},
    "pagos.recharge": {"en": "Recharge", "es": "Recargar"},
    "pagos.recharge_title": {"en": "Add wallet credit", "es": "Recargar saldo a favor"},
    "pagos.recharge_amount": {"en": "Recharge (USD)", "es": "Recarga (USD)"},
    "pagos.recharge_method": {"en": "Payment method", "es": "Medio de pago"},
    "pagos.recharge_method_pick": {
        "en": "Select method",
        "es": "Seleccionar medio",
    },
    "pagos.recharge_method_required": {
        "en": "Select a payment method.",
        "es": "Selecciona un medio de pago.",
    },
    "pagos.recharge_ok": {
        "en": "Recharge registered. We’ll add the credit after confirming the payment.",
        "es": "Recarga registrada. El saldo se añadirá al confirmar el pago.",
    },
    "pagos.recharge_checkout_title": {
        "en": "Payment instructions",
        "es": "Instrucciones de pago",
    },
    "pagos.recharge_confirm": {
        "en": "I’ve paid — register",
        "es": "Ya pagué — registrar",
    },
    "pagos.kind_wallet_topup": {"en": "Wallet top-up", "es": "Recarga de saldo"},
    "pagos.ledger_title": {"en": "Wallet activity", "es": "Movimientos del saldo"},
    "pagos.ledger_empty": {"en": "No wallet movements yet.", "es": "Aún no hay movimientos de saldo."},
    "pagos.reason.admin_credit": {"en": "Admin adjustment", "es": "Ajuste de administrador"},
    "pagos.reason.plan_unused": {"en": "Unused plan credit", "es": "Crédito de plan no usado"},
    "pagos.reason.plan_pay": {"en": "Plan payment", "es": "Pago de plan"},
    "pagos.reason.plan_cancel": {"en": "Plan cancellation", "es": "Cancelación de plan"},
    "pagos.reason.recharge": {"en": "Top-up", "es": "Recarga"},
    "team.add_credit": {"en": "Add credit", "es": "Añadir saldo"},
    "team.add_credit_title": {"en": "Add wallet credit", "es": "Añadir saldo a favor"},
    "team.add_credit_amount": {"en": "Amount (USD, + or −)", "es": "Importe (USD, + o −)"},
    "team.add_credit_note": {"en": "Note", "es": "Nota"},
    "team.add_credit_ok": {"en": "Wallet updated.", "es": "Saldo actualizado."},
    "pagos.purchase_ok": {
        "en": "Purchase registered. We’ll confirm it after checking the payment.",
        "es": "Compra registrada. La confirmaremos al verificar el pago.",
    },
    # ------------------------------------------------------------------
    # Extractor
    # ------------------------------------------------------------------
    "nav.extractor": {"en": "Extractor", "es": "Extractor"},
    "nav.proxys": {"en": "Proxies", "es": "Proxys"},
    "nav.config_x": {"en": "Config X", "es": "Config X"},
    # ------------------------------------------------------------------
    # Config X (app de X con membresía que publica por las demás)
    # ------------------------------------------------------------------
    "configx.title": {"en": "Config X", "es": "Config X"},
    "configx.intro": {
        "en": "Mark the connected X account whose paid developer app publishes for the others. Posts without “Use own X API” go through that app. Follower checks run when that account publishes, at most once a week.",
        "es": "Marca la cuenta de X conectada cuya app de desarrollador (membresía de pago) publica por las demás. Los posts sin «Usar API propia de X» salen por esa app. Los seguidores se revisan al publicar esa cuenta, como máximo una vez por semana.",
    },
    "configx.info_btn": {"en": "About Config X", "es": "Acerca de Config X"},
    "configx.sources_title": {
        "en": "Apps that pay the API",
        "es": "Apps que pagan la API",
    },
    "configx.sources_info_btn": {
        "en": "About the account that pays the API",
        "es": "Acerca de la cuenta que paga la API",
    },
    "configx.sources_hint": {
        "en": "Add the connected X account whose developer app has the paid write plan. Accounts without “Use own X API” publish through these apps (if there are several, the one with the most posts left in 24 hours is used first). Each app stops at 9,900 posts / 24 h.",
        "es": "Añade la cuenta de X conectada cuya app de desarrollador tiene el plan de pago. Las cuentas sin «Usar API propia de X» publican por estas apps (si hay varias, se usa primero la que más hueco tenga en 24 h). Cada app se corta a 9.900 posts / 24 h.",
    },
    "configx.account_label": {"en": "X account", "es": "Cuenta de X"},
    "configx.sources_form_hint": {
        "en": "Choose the account whose X developer membership should publish for the others. There is no internal wallet: X already billed the app plan.",
        "es": "Elige la cuenta cuya membresía de desarrollador de X publica por las demás. No hay saldo interno: el plan de la app ya lo cobró X.",
    },
    "configx.save": {"en": "Save", "es": "Guardar"},
    "configx.saved": {"en": "Saved.", "es": "Guardado."},
    "configx.no_x_accounts": {
        "en": "No X accounts connected yet. Connect them from Servers with “Connect with X”.",
        "es": "Aún no hay cuentas de X conectadas. Conéctalas desde Servidores con «Conectar con X».",
    },
    "configx.active": {"en": "Active", "es": "Activa"},
    "configx.inactive": {"en": "Inactive", "es": "Inactiva"},
    "configx.posts_24h_label": {"en": "Posts (24 h)", "es": "Posts (24 h)"},
    "configx.cap_badge": {"en": "Daily cap reached", "es": "Tope diario alcanzado"},
    "configx.delete_confirm": {
        "en": "Remove this app from Config X? It will no longer be used to publish for the other accounts.",
        "es": "¿Quitar esta app de Config X? Ya no se usará para publicar por las demás cuentas.",
    },
    "configx.err.bad_amount": {
        "en": "Enter a valid amount.",
        "es": "Ingresa un monto válido.",
    },
    "configx.err.account_not_found": {
        "en": "That X account was not found.",
        "es": "No se encontró esa cuenta de X.",
    },
    "configx.err.generic": {
        "en": "Something went wrong. Try again.",
        "es": "Algo salió mal. Inténtalo de nuevo.",
    },
    "configx.checks_title": {
        "en": "Accounts that already qualify to earn",
        "es": "Cuentas que ya cumplen para ganar",
    },
    "configx.checks_info_btn": {
        "en": "About qualifying to earn",
        "es": "Acerca de cumplir para ganar",
    },
    "configx.checks_hint": {
        "en": "When an X account publishes, the panel queries followers if that account was not checked in the last 7 days. X also requires Premium and 5M organic impressions in 3 months to share revenue; impressions are not exposed by the API, so verify them in X before paying.",
        "es": "Al publicar una cuenta de X, se consultan seguidores si esa cuenta no se revisó en los últimos 7 días. X además exige Premium y 5M de impresiones orgánicas en 3 meses para repartir ingresos; la API no expone impresiones, así que verifícalas en X antes de pagar.",
    },
    "configx.min_followers_label": {
        "en": "Minimum followers to qualify",
        "es": "Mínimo de seguidores para cumplir",
    },
    "configx.check_now": {"en": "Check now", "es": "Comprobar ahora"},
    "configx.checking": {"en": "Checking accounts…", "es": "Comprobando cuentas…"},
    "configx.check_done": {
        "en": "Check finished: {n} accounts, {meets} already qualify.",
        "es": "Chequeo terminado: {n} cuentas, {meets} ya cumplen.",
    },
    "configx.last_check": {
        "en": "Last check: {date}",
        "es": "Última revisión: {date}",
    },
    "configx.col_account": {"en": "Account", "es": "Cuenta"},
    "configx.col_followers": {"en": "Followers", "es": "Seguidores"},
    "configx.col_posts": {"en": "Posts", "es": "Publicaciones"},
    "configx.col_meets": {"en": "Qualifies", "es": "Cumple"},
    "configx.col_checked": {"en": "Last check", "es": "Última revisión"},
    "configx.col_date": {"en": "Date", "es": "Fecha"},
    "configx.col_video": {"en": "Video", "es": "Video"},
    "configx.col_cost": {"en": "Cost", "es": "Costo"},
    "configx.meets_yes": {"en": "Qualifies ✔", "es": "Ya cumple ✔"},
    "configx.meets_no": {"en": "Not yet", "es": "Aún no"},
    "configx.never_checked": {"en": "Never", "es": "Nunca"},
    "configx.source_badge": {"en": "Pays API", "es": "Paga la API"},
    "configx.usage_title": {"en": "Recent Config X posts", "es": "Posts recientes de Config X"},
    "configx.usage_empty": {
        "en": "No posts have used Config X yet.",
        "es": "Ninguna publicación ha usado Config X todavía.",
    },
    "pub.x_use_funding": {
        "en": "Use Config X apps ({name}) for this X post",
        "es": "Usar apps de Config X ({name}) para esta publicación en X",
    },
    "pub.x_use_funding_hint": {
        "en": "Checked: this post uses a Config X developer app (posts split across those apps, 9,900 / 24 h per app). Uncheck it only if this account has its own X API keys.",
        "es": "Marcado: esta publicación usa una app de Config X (posts repartidos entre esas apps, 9.900 / 24 h por app). Desmárcalo solo si esta cuenta tiene su propia API de X.",
    },
    "nav.membresias": {"en": "Pricing", "es": "Precio"},
    "nav.pagos": {"en": "Payments", "es": "Pagos"},
    "extractor.title": {"en": "Video extractor", "es": "Extractor de videos"},
    "extractor.subtitle": {
        "en": "Take videos from one server and spread them to the account's other servers. Default pace: 5 per cycle, every 30–40 minutes (it varies). Snapchat is clipped to 55 s; other servers only get videos longer than 1 minute. Large files are compressed. When a video has been sent or skipped on every destination, its file is deleted from this server so nothing is left behind.",
        "es": "Toma los videos de un servidor y repártelos a los demás de la cuenta. Ritmo: 5 por ciclo, cada 30–40 minutos (varía). Snapchat se recorta a 55 s; en el resto solo se toman videos de más de 1 minuto. Los archivos pesados se comprimen. Cuando un video ya se envió u omitió en todos los destinos, su archivo se borra de este servidor para no dejar nada huérfano.",
    },
    "extractor.info_btn": {
        "en": "What is the extractor?",
        "es": "¿Qué es el extractor?",
    },
    "extractor.step1_title": {
        "en": "Choose source",
        "es": "Elegir origen",
    },
    "extractor.step1_info_btn": {
        "en": "How to choose the source",
        "es": "Cómo elegir el origen",
    },
    "extractor.step1_hint": {
        "en": "Pick the server and the account to extract from. Snapchat is not listed here: its clips are 55 s and the other servers need more than 1 minute.",
        "es": "Elige el servidor y la cuenta de donde se extrae. Snapchat no aparece: sus clips son de 55 s y los demás servidores piden más de 1 minuto.",
    },
    "extractor.step2_title": {
        "en": "Scan server",
        "es": "Escanear servidor",
    },
    "extractor.step2_info_btn": {
        "en": "How to scan the server",
        "es": "Cómo escanear el servidor",
    },
    "extractor.step2_hint": {
        "en": "Check how many videos the source server has and where they can go.",
        "es": "Mira cuántos videos tiene el servidor origen y a dónde pueden ir.",
    },
    "extractor.step3_title": {
        "en": "Distribute",
        "es": "Repartir",
    },
    "extractor.step3_info_btn": {
        "en": "How to configure distribution",
        "es": "Cómo configurar el reparto",
    },
    "extractor.step3_hint": {
        "en": "Comes preset: 5 videos per cycle. The wait between cycles varies from 30 to 40 minutes (plus extra seconds). Between videos the pause also varies, from seconds up to a couple of minutes. Snapchat is clipped to 55 s; other servers skip anything under 60 s. Heavy files are compressed (Instagram 290 MB, others 450 MB).",
        "es": "Viene predeterminado: 5 videos por ciclo. La espera entre ciclos varía de 30 a 40 minutos (con segundos sueltos). Entre videos la pausa también varía, de segundos a un par de minutos. Snapchat se recorta a 55 s; en los demás no se coge nada de menos de 1 minuto. Los archivos pesados se comprimen (Instagram 290 MB, el resto 450 MB).",
    },
    "extractor.platform_label": {"en": "Source server", "es": "Servidor origen"},
    "extractor.platform_pick": {"en": "Choose server", "es": "Elegir servidor"},
    "extractor.account_label": {"en": "Account", "es": "Cuenta"},
    "extractor.account_pick": {"en": "Choose account", "es": "Elegir cuenta"},
    "extractor.account_first": {
        "en": "Choose a server first.",
        "es": "Primero elige un servidor.",
    },
    "extractor.kind_platform": {"en": "Server", "es": "Servidor"},
    "extractor.kind_account": {"en": "Account", "es": "Cuenta"},
    "extractor.scan_btn": {"en": "Scan server", "es": "Escanear servidor"},
    "extractor.scanning": {
        "en": "Checking API...",
        "es": "Comprobando API...",
    },
    "extractor.scan_total": {
        "en": "Videos found on {source}: {total}",
        "es": "Videos encontrados en {source}: {total}",
    },
    "extractor.scan_targets": {
        "en": "They will be spread to:",
        "es": "Se repartirán a:",
    },
    "extractor.scan_pending": {"en": "{count} pending", "es": "{count} pendientes"},
    "extractor.scan_cap": {
        "en": "max {count}/cycle",
        "es": "máx {count}/ciclo",
    },
    "extractor.scan_conflict": {
        "en": "There is already an extraction for this account and server. Delete or finish it before creating another one.",
        "es": "Ya hay una extracción para esta cuenta y servidor. Elimínala o espera a que termine antes de crear otra.",
    },
    "extractor.scan_no_videos": {
        "en": "No published videos found on this server for that account.",
        "es": "No se encontraron videos publicados en este servidor para esa cuenta.",
    },
    "extractor.scan_no_targets": {
        "en": "This account has no other linked servers to distribute to.",
        "es": "Esta cuenta no tiene otros servidores vinculados a donde repartir.",
    },
    "extractor.batch_label": {
        "en": "Videos per cycle",
        "es": "Videos por ciclo",
    },
    "extractor.interval_label": {
        "en": "Every how many minutes (varies 30–40)",
        "es": "Cada cuántos minutos (varía 30–40)",
    },
    "extractor.rest_label": {
        "en": "Rest between videos (seconds, varies)",
        "es": "Descanso entre videos (segundos, varía)",
    },
    "extractor.start_btn": {"en": "Start extraction", "es": "Iniciar extracción"},
    "extractor.starting": {"en": "Starting...", "es": "Iniciando..."},
    "extractor.jobs_title": {"en": "Extractions", "es": "Extracciones"},
    "extractor.jobs_search": {
        "en": "Search by account, server or status…",
        "es": "Buscar por cuenta, servidor o estado…",
    },
    "extractor.jobs_no_results": {
        "en": "No extractions match that search.",
        "es": "Ninguna extracción coincide con esa búsqueda.",
    },
    "extractor.jobs_pagination": {
        "en": "Extractions pagination",
        "es": "Paginación de extracciones",
    },
    "extractor.status_running": {"en": "Running", "es": "En curso"},
    "extractor.status_paused": {"en": "Paused", "es": "Pausada"},
    "extractor.status_done": {"en": "Completed", "es": "Completada"},
    "extractor.status_error": {"en": "Error", "es": "Error"},
    "extractor.progress": {
        "en": "{done} of {total} deliveries",
        "es": "{done} de {total} envíos",
    },
    "extractor.job_config": {
        "en": "{batch} per cycle · every {interval} min (varies) · rest varies",
        "es": "{batch} por ciclo · cada {interval} min (varía) · descanso variable",
    },
    "extractor.job_effective": {
        "en": "current batch: {count}",
        "es": "lote actual: {count}",
    },
    "extractor.platform_down_chip": {"en": "not accepting", "es": "no acepta"},
    "extractor.platform_paused_chip": {"en": "paused", "es": "pausado"},
    "extractor.target_pause": {"en": "Pause {platform}", "es": "Pausar {platform}"},
    "extractor.target_resume": {"en": "Resume {platform}", "es": "Reanudar {platform}"},
    "extractor.pause_btn": {"en": "Pause", "es": "Pausar"},
    "extractor.resume_btn": {"en": "Resume", "es": "Reanudar"},
    "extractor.log_btn": {"en": "Log", "es": "Registro"},
    "extractor.delete_btn": {"en": "Delete", "es": "Eliminar"},
    "extractor.log_empty": {"en": "No events yet.", "es": "Aún no hay eventos."},
    "extractor.confirm_title": {
        "en": "Delete extraction",
        "es": "Eliminar extracción",
    },
    "extractor.confirm_body": {
        "en": "Delete the extraction of {source} for {account}? Already published videos stay published; only the schedule and its log are removed.",
        "es": "¿Eliminar la extracción de {source} de {account}? Los videos ya publicados se conservan; solo se borra la programación y su registro.",
    },
    "extractor.confirm_cancel": {"en": "Cancel", "es": "Cancelar"},
    "extractor.confirm_delete": {"en": "Delete", "es": "Eliminar"},
    "extractor.deleted": {"en": "Extraction deleted.", "es": "Extracción eliminada."},
    "extractor.created_ok": {
        "en": "Extraction started.",
        "es": "Extracción iniciada.",
    },
    "extractor.err_platform": {
        "en": "Choose a valid server (\"All\" is not allowed).",
        "es": "Elige un servidor válido (no se permite \"Todos\").",
    },
    "extractor.err_account": {
        "en": "Choose a valid account.",
        "es": "Elige una cuenta válida.",
    },
    "extractor.err_source_unlinked": {
        "en": "That account is not linked to the selected server.",
        "es": "Esa cuenta no está vinculada al servidor elegido.",
    },
    "extractor.err_api": {
        "en": "{platform} API is not ready: {detail}",
        "es": "La API de {platform} no está lista: {detail}",
    },
    "extractor.err_no_targets": {
        "en": "The account has no other servers to distribute to.",
        "es": "La cuenta no tiene otros servidores a donde repartir.",
    },
    "extractor.err_batch": {
        "en": "Videos per cycle must be between {min} and {max}.",
        "es": "Los videos por ciclo deben estar entre {min} y {max}.",
    },
    "extractor.err_interval": {
        "en": "The interval must be between {min} and {max} minutes.",
        "es": "El intervalo debe estar entre {min} y {max} minutos.",
    },
    "extractor.err_rest": {
        "en": "The rest must be between {min} and {max} seconds.",
        "es": "El descanso debe estar entre {min} y {max} segundos.",
    },
    "extractor.err_duplicate": {
        "en": "There is already an extraction for this account and source server.",
        "es": "Ya existe una extracción para esta cuenta y este servidor origen.",
    },
    "extractor.err_no_videos": {
        "en": "The source server has no published videos for that account.",
        "es": "El servidor origen no tiene videos publicados para esa cuenta.",
    },
    "extractor.network_error": {
        "en": "Network error. Please try again.",
        "es": "Error de red. Inténtalo de nuevo.",
    },
    "extractor.ev_created": {
        "en": "Extraction created: {total} videos from {source} to {targets}.",
        "es": "Extracción creada: {total} videos de {source} hacia {targets}.",
    },
    "extractor.ev_cycle_done": {
        "en": "Cycle finished: {videos} videos processed ({ok} ok, {fail} failed).",
        "es": "Ciclo completado: {videos} videos procesados ({ok} ok, {fail} fallidos).",
    },
    "extractor.ev_lowered_memory": {
        "en": "High memory ({mem}%): batch lowered from {prev} to {new} videos per cycle.",
        "es": "Memoria alta ({mem}%): tocó bajar el lote de {prev} a {new} videos por ciclo.",
    },
    "extractor.ev_lowered_slow": {
        "en": "Server responding slowly: batch lowered from {prev} to {new} videos per cycle.",
        "es": "El servidor responde lento: tocó bajar el lote de {prev} a {new} videos por ciclo.",
    },
    "extractor.ev_raised": {
        "en": "Server stable again: batch raised to {new} videos per cycle.",
        "es": "Servidor estable de nuevo: el lote subió a {new} videos por ciclo.",
    },
    "extractor.ev_platform_down": {
        "en": "{platform} stopped accepting publications: {error}. Deliveries to that server are paused.",
        "es": "{platform} dejó de aceptar publicaciones: {error}. Se pausan los envíos a ese servidor.",
    },
    "extractor.ev_platform_retry": {
        "en": "Retrying deliveries to {platform}.",
        "es": "Reintentando envíos a {platform}.",
    },
    "extractor.ev_platform_recovered": {
        "en": "{platform} is accepting publications again.",
        "es": "{platform} volvió a aceptar publicaciones.",
    },
    "extractor.ev_all_down": {
        "en": "Every target server is rejecting publications. Extraction marked as error.",
        "es": "Todos los servidores destino están rechazando publicaciones. La extracción quedó en error.",
    },
    "extractor.ev_postponed": {
        "en": "Critical memory ({mem}%): cycle postponed 60 seconds.",
        "es": "Memoria crítica ({mem}%): ciclo pospuesto 60 segundos.",
    },
    "extractor.ev_done": {
        "en": "Extraction completed: every video was distributed.",
        "es": "Extracción completada: todos los videos fueron repartidos.",
    },
    "extractor.ev_paused": {"en": "Extraction paused.", "es": "Extracción pausada."},
    "extractor.ev_target_paused": {
        "en": "Deliveries to {platform} paused.",
        "es": "Envíos a {platform} pausados.",
    },
    "extractor.ev_target_resumed": {
        "en": "Deliveries to {platform} resumed.",
        "es": "Envíos a {platform} reanudados.",
    },
    "extractor.ev_resumed": {
        "en": "Extraction resumed.",
        "es": "Extracción reanudada.",
    },
    "extractor.note_lowered": {
        "en": "Had to lower it to {count} videos per cycle",
        "es": "Tocó bajarlo a {count} videos por ciclo",
    },
    "extractor.note_partial": {
        "en": "Batch at {count} of {total} while it recovers",
        "es": "Lote en {count} de {total} mientras se recupera",
    },
    "extractor.note_no_targets": {
        "en": "No target servers.",
        "es": "Sin servidores destino.",
    },
    "extractor.note_all_down": {
        "en": "All target servers rejected deliveries",
        "es": "Todos los servidores destino rechazaron los envíos",
    },
    "extractor.note_targets_paused": {
        "en": "All target servers are paused",
        "es": "Todos los servidores destino están pausados",
    },
    "extractor.log_skipped": {
        "en": "Skipped: this server does not support this content type.",
        "es": "Omitido: este servidor no soporta este tipo de contenido.",
    },
    "extractor.skip_photo": {
        "en": "Skipped: the extractor only takes videos.",
        "es": "Omitido: el extractor solo toma videos.",
    },
    "extractor.skip_short": {
        "en": "Skipped: shorter than 1 minute.",
        "es": "Omitido: dura menos de 1 minuto.",
    },
    "extractor.skip_snapchat_short": {
        "en": "Skipped: Snapchat needs at least 5 seconds.",
        "es": "Omitido: Snapchat pide al menos 5 segundos.",
    },
}


def resolve_lang(request: Request) -> str:
    """Inglés por defecto. Usuario publicador siempre español."""
    try:
        uid = request.session.get("user_id")
        if uid:
            import db as _db

            user = _db.get_user_by_id(str(uid))
            if user and _db.user_is_publisher_mode(user):
                return "es"
    except Exception:
        pass
    session_lang = request.session.get("lang")
    if session_lang in LANGUAGES:
        return session_lang
    return DEFAULT_LANG


def register_path(lang: str | None = None) -> str:
    code = lang if lang in LANGUAGES else DEFAULT_LANG
    return "/registro" if code == "es" else "/register"


_PROVIDER_ERROR_HINTS: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (
        ("dailymotion",),
        ("can't use 'me'", "no user authenticated"),
        "pub.dailymotion.err_no_user",
    ),
    (("dailymotion",), ("missing_profile",), "pub.dailymotion.err_no_profile"),
    (
        ("dailymotion",),
        ("v2 tokens require", "valid v2 authentication"),
        "pub.dailymotion.err_v2_auth",
    ),
    (("youtube",), ("invalid credentials", "401"), "pub.youtube.err_creds"),
    (
        ("facebook",),
        (
            "cannot call api for app",
            "on behalf of user",
            "cannot call this api",
        ),
        "pub.facebook.err_dev_mode",
    ),
)


def explain_provider_error(platform: str, raw: str, lang: str | None = None) -> str:
    """Traduce fallos conocidos de la API al idioma del panel (sin pegar el inglés)."""
    blob = (raw or "").strip().lower()
    pid = (platform or "").strip().lower()
    for plats, needles, key in _PROVIDER_ERROR_HINTS:
        if pid not in plats:
            continue
        if any(n in blob for n in needles):
            return t(key, lang)
    generic = t(f"pub.{pid}.err_generic", lang) if pid else ""
    if generic and generic != f"pub.{pid}.err_generic":
        return generic
    return t("pub.api_error_generic", lang)


def t(key: str, lang: str | None = None, **kwargs: object) -> str:
    lang = lang or DEFAULT_LANG
    if lang not in LANGUAGES:
        lang = DEFAULT_LANG
    entry = MESSAGES.get(key, {})
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        return text.format(**kwargs)
    return text


def page_context(request: Request, **extra: object) -> dict[str, object]:
    lang = resolve_lang(request)
    return {
        "lang": lang,
        "languages": LANGUAGES,
        "t": lambda key, **kw: t(key, lang, **kw),
        "register_path": register_path(lang),
        "site_description": t("site.description", lang),
        "hero_title": t("site.hero_title", lang),
        "hero_subtitle": t("site.hero_subtitle", lang),
        **extra,
    }
