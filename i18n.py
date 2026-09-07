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
    "nav.server_conditions": {"en": "Server conditions", "es": "Condiciones de servidores"},
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
    "platform.bilibili": {"en": "Bilibili", "es": "Bilibili"},
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
        "en": "Video only. Hive username + posting WIF. The file goes to the DTube IPFS cluster, then a Hive post is broadcast. Not a PPV host API.",
        "es": "Solo video. Usuario Hive + posting WIF. El archivo va al cluster IPFS de DTube y luego se emite un post en Hive. No es una API de host PPV.",
    },
    "servers.intro": {
        "en": "Connect creator accounts on each platform. TikTok is available now; more platforms are coming soon.",
        "es": "Conecta cuentas de creador en cada plataforma. TikTok ya está disponible; más plataformas llegarán pronto.",
    },
    "servers.coming_soon": {"en": "Coming soon", "es": "Próximamente"},
    "servers.accounts_btn": {"en": "Accounts", "es": "Cuentas"},
    "servers.accounts_add": {"en": "Add account", "es": "Agregar cuenta"},
    "servers.platform_configure": {
        "en": "Configure server",
        "es": "Configurar servidor",
    },
    "servers.modal_accounts_title": {
        "en": "{platform} accounts · API credentials",
        "es": "Cuentas de {platform} · Credenciales de API",
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
        "en": "Paste the API key from the host dashboard (Settings / API). MixDrop also needs the account email; Streamtape needs the API login.",
        "es": "Pega la API key del panel del host (Settings / API). MixDrop también pide el email de la cuenta; Streamtape el API login.",
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
        "en": "Odysee has no public OAuth for third-party apps. Sign in with the email and password of the Odysee account. The panel keeps the auth token, not the password. Channel claim ID is optional.",
        "es": "Odysee no ofrece OAuth público para apps de terceros. Entra con el email y la contraseña de la cuenta de Odysee. El panel guarda el auth token, no la contraseña. El claim ID del canal es opcional.",
    },
    "servers.chain_hint_dtube": {
        "en": "DTube posts on Hive. Use the Hive username and the posting WIF (not the master key). The video is uploaded to the DTube IPFS cluster, then a real Hive comment is broadcast. Do not paste the owner key.",
        "es": "DTube publica en Hive. Usa el usuario de Hive y el posting WIF (no la clave master). El video se sube al cluster IPFS de DTube y luego se emite un comentario real en Hive. No pegues la owner key.",
    },
    "servers.chain_field_email": {"en": "Odysee email", "es": "Email de Odysee"},
    "servers.chain_field_password": {
        "en": "Odysee password",
        "es": "Contraseña de Odysee",
    },
    "servers.chain_field_hive": {"en": "Hive username", "es": "Usuario de Hive"},
    "servers.chain_field_wif": {"en": "Posting WIF", "es": "Posting WIF"},
    "servers.chain_field_channel": {
        "en": "Channel claim ID (optional)",
        "es": "Claim ID del canal (opcional)",
    },
    "servers.chain_save": {"en": "Save account", "es": "Guardar cuenta"},
    "servers.chain_saved": {
        "en": "Account saved ({name}).",
        "es": "Cuenta guardada ({name}).",
    },
    "servers.chain_missing": {
        "en": "Odysee needs email and password. DTube needs Hive username and posting WIF.",
        "es": "Odysee pide email y contraseña. DTube pide usuario de Hive y posting WIF.",
    },
    "servers.chain_test": {"en": "Test API", "es": "Probar API"},
    "servers.chain_badge_odysee": {"en": "LBRY", "es": "LBRY"},
    "servers.chain_badge_dtube": {"en": "Hive", "es": "Hive"},
    "servers.chain_badge": {"en": "Chain", "es": "Cadena"},
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
        "en": "Save this account’s X Client ID and Secret, or connect using Config X (the account that pays for the API).",
        "es": "Guarda el Client ID y el Secret de esta cuenta, o conéctala con la API de Config X (la cuenta que paga la API).",
    },
    "servers.x_api_inherit_hint": {
        "en": "X is the exception: other names can connect with the Config X app (the account that pays for the API). Only save Client ID and Secret here if this name should spend from its own X API when you uncheck “Use Config X balance” at publish time.",
        "es": "X es la excepción: los demás nombres pueden conectarse con la app de Config X (la cuenta que paga la API). Guarda Client ID y Secret aquí solo si este nombre debe gastar de su propia API de X cuando desmarques «Usar saldo de Config X» al publicar.",
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
        "en": "Save the Bilibili Client ID and Client Secret first (open.bilibili.com).",
        "es": "Guarda primero el Client ID y el Client Secret de Bilibili (open.bilibili.com).",
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
        "en": "Paste this exact Redirect URI in Snap Business Manager (SITE_URL/oauth/snapchat/callback).",
        "es": "Pega esta Redirect URI exacta en Snap Business Manager (SITE_URL/oauth/snapchat/callback).",
    },
    "servers.snapchat_connected": {
        "en": "Connected {name} successfully.",
        "es": "Se conectó {name} correctamente.",
    },
    "servers.snapchat_no_code": {
        "en": "Snapchat did not return an authorization code.",
        "es": "Snapchat no devolvió un código de autorización.",
    },
    "servers.disconnect_error": {
        "en": "Could not disconnect.",
        "es": "No se pudo desconectar.",
    },
    "servers.network_error": {"en": "Network error.", "es": "Error de red."},
    "servers.groups_title": {"en": "Join accounts", "es": "Juntar cuentas"},
    "servers.groups_optional": {"en": "Optional", "es": "Opcional"},
    "servers.groups_auto_hint": {
        "en": "Accounts with the same name are linked automatically. Manual groups below are optional.",
        "es": "Las cuentas con el mismo nombre se vinculan solas. Los grupos manuales de abajo son opcionales.",
    },
    "servers.groups_auto_title": {
        "en": "Automatic links",
        "es": "Vinculaciones automáticas",
    },
    "servers.groups_auto_empty": {
        "en": "Create accounts with the same name on different servers to link them.",
        "es": "Crea cuentas con el mismo nombre en distintos servidores para vincularlas.",
    },
    "servers.groups_manual_title": {
        "en": "Manual groups (optional)",
        "es": "Grupos manuales (opcional)",
    },
    "servers.groups_info_title": {
        "en": "About joining accounts",
        "es": "Información de juntar cuentas",
    },
    "servers.groups_hint": {
        "en": "Accounts with the same name publish together on every linked server. Each name can only exist once per server. Manual groups let you join accounts with different names.",
        "es": "Las cuentas con el mismo nombre publican juntas en cada servidor vinculado. Cada nombre solo puede existir una vez por servidor. Los grupos manuales permiten juntar cuentas con nombres distintos.",
    },
    "servers.groups_create": {"en": "Create", "es": "Crear"},
    "servers.groups_name": {"en": "Name", "es": "Nombre"},
    "servers.groups_view_linked": {"en": "View linked", "es": "Ver vinculados"},
    "servers.groups_linked_servers": {
        "en": "Linked servers",
        "es": "Servidores vinculados",
    },
    "servers.groups_search": {"en": "Search", "es": "Buscar"},
    "servers.groups_search_ph": {
        "en": "Search by account name…",
        "es": "Buscar por nombre de cuenta…",
    },
    "servers.groups_accounts": {"en": "Accounts", "es": "Cuentas"},
    "servers.groups_account_default": {
        "en": "Configured account",
        "es": "Cuenta configurada",
    },
    "servers.groups_picks_empty": {
        "en": "No linked accounts available. Create accounts and link at least one server to each.",
        "es": "No hay cuentas vinculadas. Crea cuentas y vincula al menos un servidor a cada una.",
    },
    "servers.groups_picks_all_taken": {
        "en": "All accounts are already assigned to another group.",
        "es": "Todas las cuentas ya están asignadas a otro grupo.",
    },
    "servers.groups_picks_taken": {
        "en": "Already in another group",
        "es": "Ya agrupado",
    },
    "servers.groups_picks_unlinked": {
        "en": "No linked servers",
        "es": "Sin vinculados",
    },
    "servers.groups_platforms": {"en": "Servers", "es": "Servidores"},
    "servers.groups_empty": {
        "en": "No manual groups yet.",
        "es": "Aún no hay grupos manuales.",
    },
    "servers.groups_list_search": {
        "en": "Search by group or account name...",
        "es": "Buscar por nombre de grupo o cuenta...",
    },
    "servers.groups_pagination": {
        "en": "Account groups pagination",
        "es": "Paginación de grupos de cuentas",
    },
    "servers.groups_saved": {"en": "Group saved.", "es": "Grupo guardado."},
    "servers.groups_deleted": {"en": "Group deleted.", "es": "Grupo eliminado."},
    "servers.groups_name_required": {"en": "Enter a name.", "es": "Escribe un nombre."},
    "servers.groups_platforms_required": {
        "en": "Select at least one account.",
        "es": "Selecciona al menos una cuenta.",
    },
    "servers.groups_name_taken": {
        "en": "That name is already in use.",
        "es": "Ese nombre ya está en uso.",
    },
    "servers.groups_name_account_conflict": {
        "en": "That name is already used by an account. Choose a different group name.",
        "es": "Ese nombre ya existe en Cuentas. Elige otro nombre para el grupo.",
    },
    "servers.groups_members_not_linked": {
        "en": "Each account in the group must have at least one linked server.",
        "es": "Cada cuenta del grupo debe tener al menos un servidor vinculado.",
    },
    "servers.groups_not_found": {"en": "Group not found.", "es": "Grupo no encontrado."},
    "servers.groups_save_fail": {
        "en": "Could not save the group.",
        "es": "No se pudo guardar el grupo.",
    },
    "servers.groups_edit": {"en": "Edit", "es": "Editar"},
    "servers.groups_delete": {"en": "Delete group", "es": "Eliminar grupo"},
    "servers.groups_toggle": {
        "en": "Enable or disable group",
        "es": "Activar o desactivar grupo",
    },
    "servers.groups_confirm_delete": {
        "en": "Delete this account group?",
        "es": "¿Eliminar este grupo de cuentas?",
    },
    "servers.groups_modal_create": {
        "en": "New account group",
        "es": "Nuevo grupo de cuentas",
    },
    "servers.groups_modal_edit": {"en": "Edit group", "es": "Editar grupo"},
    "servers.groups_accounts_edit": {
        "en": "Group accounts (uncheck to remove)",
        "es": "Cuentas grupo (desmarca para quitar)",
    },
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
    "servers.accounts_group_name_conflict": {
        "en": "That name is already used by a group in Join accounts. Choose a different name.",
        "es": "Ese nombre ya existe en Juntar cuentas. Elige otro nombre para la cuenta.",
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
        "en": "What each platform allows",
        "es": "Qué permite cada plataforma",
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
        "en": "Videos only (稿件). Connect a Bilibili account. Needs ffmpeg for the cover.",
        "es": "Solo video (稿件). Conecta una cuenta de Bilibili. Hace falta ffmpeg para la portada.",
    },
    "limits.note.rumble": {
        "en": "No public OAuth. Partner Upload API: access token + Channel ID. Videos only.",
        "es": "Sin OAuth público. Upload API de partners: access token y Channel ID. Solo video.",
    },
    "limits.note.snapchat": {
        "en": "Public Profile: photos as 24h Stories; MP4 5–60 s (Spotlight 6–60 s, min. 540×960). Needs OpenSSL.",
        "es": "Perfil público: fotos como Stories de 24 h; MP4 5–60 s (Spotlight 6–60 s, mín. 540×960). Hace falta OpenSSL.",
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
    "api.chain.need_account": {
        "en": "Connect this network in Servers first.",
        "es": "Primero conecta esta red en Servidores.",
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
        "en": "Drag & drop your video here",
        "es": "Arrastra y suelta tu video aquí",
    },
    "pub.browse_files": {"en": "Browse files", "es": "Explorar archivos"},
    "pub.remove_file": {"en": "Remove file", "es": "Quitar archivo"},
    "pub.captions_uploading": {
        "en": "Uploading temporary video…",
        "es": "Subiendo video temporal…",
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
    "pub.caption": {"en": "Caption", "es": "Descripción"},
    "pub.caption_ph": {
        "en": "Write a caption, hashtags, or notes…",
        "es": "Escribe una descripción, hashtags o notas…",
    },
    "pub.title_internal": {"en": "Title (internal)", "es": "Título (interno)"},
    "pub.field_title": {"en": "Video title", "es": "Título del video"},
    "pub.title_ph": {
        "en": "Video title for your dashboard",
        "es": "Título del video para tu panel",
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
    "pub.log_view": {"en": "View", "es": "Ver"},
    "pub.log_modal_platforms": {"en": "Platforms", "es": "Plataformas"},
    "pub.log_modal_status": {"en": "Status", "es": "Estado"},
    "pub.log_modal_errors": {"en": "Errors", "es": "Errores"},
    "pub.log_platforms_n": {
        "en": "{n} platforms",
        "es": "{n} plataformas",
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
        "en": "Facebook publish failed: {error}",
        "es": "Falló la publicación en Facebook: {error}",
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
    "pub.x.upload_fail": {
        "en": "X publish failed: {error}",
        "es": "Falló la publicación en X: {error}",
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
        "en": "Config X has no API app keys. Save Client ID and Secret on the X account that pays for the API.",
        "es": "Config X no tiene claves de API. Guarda el Client ID y el Secret en la cuenta de X que paga la API.",
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
    "pub.dtube.ok": {
        "en": "Published on DTube: {url}",
        "es": "Publicado en DTube: {url}",
    },
    "pub.dtube.upload_fail": {
        "en": "DTube publish failed: {error}",
        "es": "Falló la publicación en DTube: {error}",
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
    "pub.snapchat.bad_duration": {
        "en": "Snapchat videos must be 5–60 seconds (Spotlight needs 6–60).",
        "es": "Los videos de Snapchat deben durar 5–60 segundos (Spotlight exige 6–60).",
    },
    "pub.snapchat.bad_size": {
        "en": "Snapchat video must be at least 540×960 px.",
        "es": "El video de Snapchat debe medir al menos 540×960 px.",
    },
    "pub.snapchat.need_openssl": {
        "en": "OpenSSL is required to encrypt media for the Snapchat Public Profile API.",
        "es": "Hace falta OpenSSL para cifrar el media de la Public Profile API de Snapchat.",
    },
    "pub.flash.no_platforms": {
        "en": "Select at least one platform.",
        "es": "Selecciona al menos una plataforma.",
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
        "en": "These videos stay available until an admin republishes the remaining platforms or cancels.",
        "es": "Estos videos siguen disponibles hasta que un admin republica en las plataformas restantes o cancela.",
    },
    "pub.pending_col_actions": {"en": "Actions", "es": "Acciones"},
    "pub.retry_btn": {"en": "Republish remaining", "es": "Republicar restantes"},
    "pub.cancel_pending_btn": {"en": "Cancel remaining", "es": "Cancelar restantes"},
    "pub.cancel_pending_confirm": {
        "en": "Cancel the remaining platforms for this video?",
        "es": "¿Cancelar las plataformas restantes de este video?",
    },
    "pub.pending_cancelled_log": {
        "en": "Remaining publish cancelled by an admin.",
        "es": "Publicación restante cancelada por un administrador.",
    },
    "pub.flash.retry_all_ok": {
        "en": "Republished to {n} remaining platform(s).",
        "es": "Republicado en {n} plataforma(s) restante(s).",
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
    "mode.basic": {"en": "Basic mode", "es": "Modo básico"},
    "mode.admin": {"en": "Admin mode", "es": "Modo admin"},
    "mode.tiktok": {"en": "TikTok user", "es": "Usuario TikTok"},
    "mode.supervisor": {"en": "Supervisor mode", "es": "Modo supervisor"},
    "mode.videos_only": {"en": "Videos only", "es": "Solo videos"},
    "mode.videos_comments": {"en": "Videos & comments", "es": "Videos y comentarios"},
    "mode.videos_comments_stats": {
        "en": "Videos, comments & stats",
        "es": "Videos, comentarios y estadísticas",
    },
    "mode.basic.hint": {
        "en": "Default: minimal access until permissions are configured.",
        "es": "Por defecto: acceso mínimo hasta configurar permisos.",
    },
    "mode.admin.hint": {
        "en": "High permission level in the app (separate from site administrator account).",
        "es": "Nivel alto de permisos en la app (aparte de la cuenta administradora del sitio).",
    },
    "mode.tiktok.hint": {
        "en": "Admin-like workspace: publish, stats and team, without server credentials.",
        "es": "Espacio tipo admin: publicar, estadísticas y equipo, sin credenciales de servidores.",
    },
    "mode.supervisor.hint": {
        "en": "Content and workflow oversight.",
        "es": "Supervisión de contenido y flujo de trabajo.",
    },
    "mode.videos_only.hint": {
        "en": "Publish and manage videos only.",
        "es": "Publicar y gestionar videos solamente.",
    },
    "mode.videos_comments.hint": {
        "en": "Videos plus comment interaction.",
        "es": "Videos más interacción con comentarios.",
    },
    "mode.videos_comments_stats.hint": {
        "en": "Videos, comments, and analytics.",
        "es": "Videos, comentarios y analíticas.",
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
        "en": "Official API limits for each connected account (YouTube is per Google Cloud project). Going over them can pause publishing or flag the account. The Safe column is a conservative pace so you do not abuse the API. Networks change these numbers; stay under Safe, not at the hard ceiling. VMOS Cloud is an alternative for TikTok, Instagram, Facebook, YouTube, X, Threads and Snapchat: those official caps do not apply; the cloud phone and the app’s own limits do. Panel proxies are not used on VMOS accounts. Proven PPV hosts (DoodStream, StreamWish, FileMoon, MixDrop, Streamtape, VOE, Vidoza, LuluStream) have no social quota: the host’s upload and unique-view rules apply, payouts stay on the host, and a linked proxy is used like OAuth. Names ending in (pago) — Loadvid, VidSonic, FlyFile, VenVo — are newer trial hosts to test whether they actually pay. Odysee uses LBRY (email/password, TUS upload). DTube uses Hive + IPFS (username + posting WIF). Neither is a PPV host.",
        "es": "Límites oficiales de la API de cada cuenta conectada (YouTube es por proyecto de Google Cloud). Pasarse puede pausar la publicación o marcar la cuenta. La columna Uso seguro es un ritmo conservador para no abusar. Las redes cambian estas cifras; quédate en Uso seguro, no en el tope máximo. VMOS Cloud es una alternativa para TikTok, Instagram, Facebook, YouTube, X, Threads y Snapchat: esos topes oficiales no aplican; rigen el móvil en la nube y los límites de la app. Las cuentas VMOS no usan el proxy del panel. Los hosts PPV contrastados (DoodStream, StreamWish, FileMoon, MixDrop, Streamtape, VOE, Vidoza, LuluStream) no tienen cuota de red social: rigen subidas y vistas únicas del host, el cobro es en el host y el proxy vinculado se usa como en OAuth. Los que llevan (pago) — Loadvid, VidSonic, FlyFile, VenVo — son hosts más nuevos, de prueba, para ver si realmente pagan. Odysee usa LBRY (email/contraseña, subida TUS). DTube usa Hive + IPFS (usuario + posting WIF). Ninguna es un host PPV.",
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
        "en": "Alternative to official OAuth for TikTok, Instagram, Facebook, YouTube, X, Threads and Snapchat. In Servers, Connect with VMOS: Access Key, Secret, padCode and template/scriptId. The panel uploads the file to the pad and runs the template. Dailymotion, Bilibili and Rumble stay on their APIs. Panel proxies are not used.",
        "es": "Alternativa al OAuth oficial para TikTok, Instagram, Facebook, YouTube, X, Threads y Snapchat. En Servidores, Conectar con VMOS: Access Key, Secret, padCode y plantilla/scriptId. El panel sube el archivo al pad y lanza la plantilla. Dailymotion, Bilibili y Rumble siguen por su API. No se usa el proxy del panel.",
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
        "en": "Connect in Servers with Hive username and posting WIF (never the owner key). Video goes to cluster.d.tube then a real Hive post. Linked proxies are used. Stats/comments in this panel stay local.",
        "es": "En Servidores conecta con usuario Hive y posting WIF (nunca la owner key). El video va a cluster.d.tube y luego un post real en Hive. Se usa el proxy vinculado. Estadísticas y comentarios de este panel siguen siendo locales.",
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
        "en": "Page quality and spam filters can still block bursts even with quota left. Photos and long videos share the Page; space everything. Tokens are Page tokens, renewed automatically in this panel.",
        "es": "La calidad de la Página y el anti-spam pueden bloquear ráfagas aunque quede cupo. Fotos y videos largos comparten la Página; espacia todo. Los tokens son de Página; este panel los renueva solo.",
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
        "en": "Public Profile API. No simple public “X videos/day” number. Stories last 24 hours. Spotlight videos must be 6–60 s (this panel: MP4 5–60 s, min. 540×960).",
        "es": "API de perfil público. No hay un “X videos/día” público simple. Las Stories duran 24 horas. Spotlight: 6–60 s (este panel: MP4 5–60 s, mín. 540×960).",
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
    "apidoc.intro": {
        "en": "What each server needs so publishing works. Official OAuth (or Rumble’s partner API) is the default. Saving Client ID/Secret only stores the app: the server stays unlinked until you click Connect and sign in; Disconnect or Remove API unlinks it, and connecting another account on the same card replaces the previous one. Register SITE_URL/oauth/{platform}/callback in each developer console. VMOS Cloud is an alternative for TikTok, Instagram, Facebook, YouTube, X, Threads and Snapchat: connect from Servers without pasting social access tokens. Proven PPV hosts (DoodStream, StreamWish, FileMoon, MixDrop, Streamtape, VOE, Vidoza, LuluStream) use an API key from the host dashboard, not OAuth; video only. Names with (pago) — Loadvid, VidSonic, FlyFile, VenVo — are trial hosts to verify payouts. Odysee signs in with email/password (LBRY auth token, TUS). DTube uses Hive username + posting WIF and the IPFS cluster. Tokens marked Automatic are refreshed by the panel on OAuth accounts; VMOS, PPV hosts, Odysee and DTube do not use those tokens.",
        "es": "Qué hay que hacer en cada servidor para que la publicación funcione. El camino por defecto es OAuth oficial (o la API de partners de Rumble). Guardar Client ID/Secret solo guarda la app: el servidor sigue sin vincular hasta que pulses Conectar e inicies sesión; Desconectar o Quitar API lo desvincula, y conectar otra cuenta en la misma ficha reemplaza la anterior. Registra SITE_URL/oauth/{plataforma}/callback en cada consola de desarrollador. VMOS Cloud es una alternativa para TikTok, Instagram, Facebook, YouTube, X, Threads y Snapchat: se conecta desde Servidores sin pegar tokens de esas redes. Los hosts PPV contrastados (DoodStream, StreamWish, FileMoon, MixDrop, Streamtape, VOE, Vidoza, LuluStream) usan API key del panel del host, no OAuth; solo video. Los que llevan (pago) — Loadvid, VidSonic, FlyFile, VenVo — son de prueba para ver si pagan. Odysee entra con email/contraseña (auth token LBRY, TUS). DTube usa usuario Hive + posting WIF y el cluster IPFS. Si el token es Automático, el panel lo renueva en cuentas OAuth; VMOS, hosts PPV, Odysee y DTube no usan esos tokens.",
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
    "apidoc.token.auto": {"en": "Automatic", "es": "Automático"},
    "apidoc.token.manual": {"en": "Manual", "es": "Manual"},
    "apidoc.token.none": {"en": "Not used", "es": "No aplica"},
    "apidoc.vmos.name": {"en": "VMOS Cloud (alternative)", "es": "VMOS Cloud (alternativa)"},
    "apidoc.vmos.step1": {
        "en": "In VMOS Cloud (vmoscloud.com), open Developer → API and copy Access Key ID and Secret Access Key.",
        "es": "En VMOS Cloud (vmoscloud.com) abre Developer → API y copia Access Key ID y Secret Access Key.",
    },
    "apidoc.vmos.step2": {
        "en": "Create a cloud phone, install the social app, sign in, and copy the padCode.",
        "es": "Crea un móvil en la nube, instala la app de la red, inicia sesión y copia el padCode.",
    },
    "apidoc.vmos.step3": {
        "en": "Create an RPA template that posts from a file/path or URL, and copy its template/scriptId.",
        "es": "Crea una plantilla RPA que publique desde un archivo/ruta o URL y copia su template/scriptId.",
    },
    "apidoc.vmos.step4": {
        "en": "In Servers, open that network’s accounts and Connect with VMOS. Save Access Key, Secret, padCode and the template. Test VMOS before publishing.",
        "es": "En Servidores abre las cuentas de esa red y pulsa Conectar con VMOS. Guarda Access Key, Secret, padCode y la plantilla. Prueba VMOS antes de publicar.",
    },
    "apidoc.vmos.extra": {
        "en": "Covers TikTok, Instagram, Facebook, YouTube, X, Threads and Snapchat. The panel picks VMOS or OAuth from how that account+network is linked. Without a template the post is not marked sent. Dailymotion, Bilibili and Rumble stay on their APIs. Panel proxies are not used. Stats/comments stay local to this panel.",
        "es": "Cubre TikTok, Instagram, Facebook, YouTube, X, Threads y Snapchat. El panel elige VMOS u OAuth según cómo esté unida esa cuenta+red. Sin plantilla no se marca como enviado. Dailymotion, Bilibili y Rumble siguen por su API. No se usa el proxy del panel. Estadísticas y comentarios siguen siendo locales de este panel.",
    },
    "apidoc.vmos_alt": {
        "en": "Alternative: in Servers, Connect with VMOS for this network (Access Key, Secret, padCode and template) instead of official OAuth.",
        "es": "Alternativa: en Servidores, Conectar con VMOS en esta red (Access Key, Secret, padCode y plantilla) en lugar del OAuth oficial.",
    },
    "apidoc.filehost.step1": {
        "en": "Create an account on {name} and open Settings / API in its dashboard. Copy the API key (MixDrop also copies the account email; Streamtape the API login).",
        "es": "Crea una cuenta en {name} y abre Settings / API en su panel. Copia la API key (MixDrop también el email de la cuenta; Streamtape el API login).",
    },
    "apidoc.filehost.step2": {
        "en": "In Servers, open {name} accounts and Connect. Paste the key (and extra field if asked). Test the API before publishing.",
        "es": "En Servidores abre las cuentas de {name} y pulsa Conectar. Pega la key (y el campo extra si lo pide). Prueba la API antes de publicar.",
    },
    "apidoc.filehost.step3": {
        "en": "Publish a video from this panel. The host returns a watch URL. Ads and payouts stay on {name}; this panel does not pay PPV.",
        "es": "Publica un video desde este panel. El host devuelve una URL. Anuncios y pagos siguen en {name}; este panel no paga PPV.",
    },
    "apidoc.filehost.extra": {
        "en": "No OAuth. Video only. You send viewers; unique views, country rates, AdBlock/VPN and fake traffic follow the host’s rules. Linked proxies are used. Stats/comments in this panel stay local.",
        "es": "Sin OAuth. Solo video. Tú mandas el tráfico; vistas únicas, tarifas por país, AdBlock/VPN y tráfico falso siguen las reglas del host. Se usa el proxy vinculado. Estadísticas y comentarios de este panel siguen siendo locales.",
    },
    "apidoc.filehost.trial": {
        "en": "(pago) = trial host: newer / less proven. Use it to check whether they actually pay. Do not rely on them like DoodStream or MixDrop yet.",
        "es": "(pago) = host de prueba: más nuevo o menos contrastado. Sirve para ver si realmente pagan. Aún no los trates como DoodStream o MixDrop.",
    },
    "apidoc.odysee.step1": {
        "en": "Create an Odysee account (odysee.com). There is no public OAuth for third-party apps.",
        "es": "Crea una cuenta en Odysee (odysee.com). No hay OAuth público para apps de terceros.",
    },
    "apidoc.odysee.step2": {
        "en": "In Servers, open Odysee accounts and Connect. Sign in with email and password. The panel stores the auth token, not the password. Channel claim ID is optional.",
        "es": "En Servidores abre las cuentas de Odysee y pulsa Conectar. Entra con email y contraseña. El panel guarda el auth token, no la contraseña. El claim ID del canal es opcional.",
    },
    "apidoc.odysee.step3": {
        "en": "Publish a video. The panel requests a TUS upload, sends the file in 50 MB chunks, then stream_create via asynqueries. Do not mark sent unless Odysee returns a claim URL.",
        "es": "Publica un video. El panel pide una subida TUS, envía el archivo en trozos de 50 MB y luego stream_create por asynqueries. No marques enviado si Odysee no devuelve una URL de claim.",
    },
    "apidoc.odysee.extra": {
        "en": "Needs LBC in the Odysee wallet for the bid. Video only. Linked proxies are used. Stats/comments in this panel stay local.",
        "es": "Hace falta LBC en el monedero de Odysee para el bid. Solo video. Se usa el proxy vinculado. Estadísticas y comentarios de este panel siguen siendo locales.",
    },
    "apidoc.dtube.step1": {
        "en": "Use a Hive account (not a PPV API key). Export the posting WIF from a Hive wallet. Never use the owner key.",
        "es": "Usa una cuenta Hive (no una API key PPV). Exporta el posting WIF desde un monedero Hive. Nunca uses la owner key.",
    },
    "apidoc.dtube.step2": {
        "en": "In Servers, open DTube accounts and Connect. Save Hive username and posting WIF. Test before publishing.",
        "es": "En Servidores abre las cuentas de DTube y pulsa Conectar. Guarda el usuario Hive y el posting WIF. Prueba antes de publicar.",
    },
    "apidoc.dtube.step3": {
        "en": "Publish a video. The file is uploaded to the DTube IPFS cluster; then a Hive comment with DTube json_metadata is broadcast. Do not mark sent unless Hive accepted the transaction.",
        "es": "Publica un video. El archivo se sube al cluster IPFS de DTube; luego se emite un comentario Hive con json_metadata de DTube. No marques enviado si Hive no aceptó la transacción.",
    },
    "apidoc.dtube.extra": {
        "en": "Needs Hive resource credits. Video only. Linked proxies are used. Stats/comments in this panel stay local.",
        "es": "Hacen falta resource credits de Hive. Solo video. Se usa el proxy vinculado. Estadísticas y comentarios de este panel siguen siendo locales.",
    },
    "apidoc.extra_none": {"en": "None", "es": "Ninguno"},
    "apidoc.tiktok.step1": {
        "en": "Create an app in TikTok for Developers (developers.tiktok.com).",
        "es": "Crea una app en TikTok for Developers (developers.tiktok.com).",
    },
    "apidoc.tiktok.step2": {
        "en": "Enable Login Kit and Content Posting API (user.info.basic, video.upload).",
        "es": "Activa Login Kit y Content Posting API (user.info.basic, video.upload).",
    },
    "apidoc.tiktok.step3": {
        "en": "Register the redirect URI: SITE_URL/oauth/tiktok/callback.",
        "es": "Registra la URI de redirección: SITE_URL/oauth/tiktok/callback.",
    },
    "apidoc.tiktok.step4": {
        "en": "In Servers, save the Client Key and Client Secret, then Connect with TikTok.",
        "es": "En Servidores guarda el Client Key y el Client Secret y pulsa Conectar con TikTok.",
    },
    "apidoc.tiktok.extra": {
        "en": "TikTok must approve Content Posting before Direct Post. Videos only; no photos.",
        "es": "TikTok tiene que aprobar Content Posting para el envío directo. Solo video; no fotos.",
    },
    "apidoc.youtube.step1": {
        "en": "In Google Cloud, create a Web OAuth client and enable YouTube Data API v3.",
        "es": "En Google Cloud crea un cliente OAuth web y activa YouTube Data API v3.",
    },
    "apidoc.youtube.step2": {
        "en": "Add the redirect URI: SITE_URL/oauth/youtube/callback.",
        "es": "Añade la URI de redirección: SITE_URL/oauth/youtube/callback.",
    },
    "apidoc.youtube.step3": {
        "en": "In Servers, save Client ID and Client Secret, then Connect with YouTube.",
        "es": "En Servidores guarda Client ID y Client Secret y pulsa Conectar con YouTube.",
    },
    "apidoc.youtube.extra": {
        "en": "Videos only. Clips of 3 minutes or less upload as Shorts. Google may show an unverified-app warning until the OAuth consent screen is verified.",
        "es": "Solo video. Los de 3 minutos o menos se suben como Shorts. Google puede mostrar aviso de app no verificada hasta verificar la pantalla de consentimiento.",
    },
    "apidoc.instagram.step1": {
        "en": "In Meta for Developers, add Instagram and use Business Login.",
        "es": "En Meta for Developers añade Instagram y usa Business Login.",
    },
    "apidoc.instagram.step2": {
        "en": "Register the redirect URI: SITE_URL/oauth/instagram/callback.",
        "es": "Registra la URI de redirección: SITE_URL/oauth/instagram/callback.",
    },
    "apidoc.instagram.step3": {
        "en": "Connect a professional Instagram account (Business or Creator), not a personal one.",
        "es": "La cuenta de Instagram debe ser profesional (Business o Creador), no personal.",
    },
    "apidoc.instagram.step4": {
        "en": "In Servers, save App ID and App Secret, then Connect with Instagram.",
        "es": "En Servidores guarda App ID y App Secret y pulsa Conectar con Instagram.",
    },
    "apidoc.instagram.extra": {
        "en": "Photos need a public https SITE_URL (not localhost): Instagram downloads the file from that URL. Video = Reels.",
        "es": "Las fotos necesitan un SITE_URL público https (no localhost): Instagram descarga el archivo desde esa URL. El video se publica como Reels.",
    },
    "apidoc.facebook.step1": {
        "en": "In Meta for Developers, add Facebook Login with pages_show_list and pages_manage_posts.",
        "es": "En Meta for Developers añade Facebook Login con pages_show_list y pages_manage_posts.",
    },
    "apidoc.facebook.step2": {
        "en": "Register the redirect URI: SITE_URL/oauth/facebook/callback.",
        "es": "Registra la URI de redirección: SITE_URL/oauth/facebook/callback.",
    },
    "apidoc.facebook.step3": {
        "en": "In Servers, save App ID and App Secret, then Connect with Facebook and choose Pages.",
        "es": "En Servidores guarda App ID y App Secret, pulsa Conectar con Facebook y elige las Páginas.",
    },
    "apidoc.facebook.extra": {
        "en": "Pages only (not personal profiles). Photos and videos.",
        "es": "Solo Páginas (no perfiles personales). Fotos y videos.",
    },
    "apidoc.threads.step1": {
        "en": "In VMOS Cloud, create a cloud phone, install Threads, sign in, then copy Access Key, Secret and padCode from Developer → API.",
        "es": "En VMOS Cloud crea un móvil, instala Threads, inicia sesión y copia Access Key, Secret y padCode en Developer → API.",
    },
    "apidoc.threads.step2": {
        "en": "In Servers, open Threads accounts and Connect with VMOS Threads.",
        "es": "En Servidores abre Cuentas de Threads y pulsa Conectar con VMOS Threads.",
    },
    "apidoc.x.step1": {
        "en": "In the X Developer Portal, create an OAuth 2.0 app with PKCE.",
        "es": "En el portal de desarrolladores de X crea una app OAuth 2.0 con PKCE.",
    },
    "apidoc.x.step2": {
        "en": "Register the redirect URI: SITE_URL/oauth/x/callback.",
        "es": "Registra la URI de redirección: SITE_URL/oauth/x/callback.",
    },
    "apidoc.x.step3": {
        "en": "In Servers, save Client ID and Client Secret, then Connect with X.",
        "es": "En Servidores guarda Client ID y Client Secret y pulsa Conectar con X.",
    },
    "apidoc.x.extra": {
        "en": "A paid X API plan with write access is required to publish. Photos, GIF and short video. Config X (sidebar): pick one connected X account as the recharge account that pays the API. Recharge it, set the cost per post, and the panel tracks recharged / spent / available. When you publish to other X accounts with the checkbox on, the cost is deducted from that recharge account instead of spending on every account. Uncheck it to spend from the posting account itself (for accounts where you already pay). Every day at 4 AM (panel time) the panel queries X and marks which accounts already meet the follower threshold so you only pay the subscription on those. X does not expose your API bill or impressions; the balance is panel accounting, and impressions/Premium must still be checked on X before you pay.",
        "es": "Hace falta un plan de pago de la API de X con permiso de escritura para publicar. Fotos, GIF y video corto. Config X (barra lateral): eliges una cuenta de X conectada como la que recarga y paga la API. La recargas, defines el costo por publicación y el panel muestra recargado / gastado / disponible. Al publicar en las demás cuentas de X con el checkbox activado, el costo se descuenta de esa cuenta de recarga y no de cada cuenta. Desmárcalo para gastar del saldo de la propia cuenta que publica (las que ya pagas). Todos los días a las 4 am (hora del panel) se consulta X y se marcan las cuentas que ya cumplen el mínimo de seguidores, para pagar la suscripción solo en esas. X no expone tu factura de API ni las impresiones; el saldo es contabilidad del panel, y las impresiones/Premium hay que verificarlas en X antes de pagar.",
    },
    "apidoc.dailymotion.step1": {
        "en": "Get an API Key and API Secret from Dailymotion (partner / developer app).",
        "es": "En Dailymotion obtén API Key y API Secret (app de partner / desarrollador).",
    },
    "apidoc.dailymotion.step2": {
        "en": "In Dailymotion Studio → API keys, set Callback URL to SITE_URL/oauth/dailymotion/callback.",
        "es": "En Dailymotion Studio → API keys pon Callback URL = SITE_URL/oauth/dailymotion/callback.",
    },
    "apidoc.dailymotion.step3": {
        "en": "In Servers, save the keys, then Connect with Dailymotion and sign in.",
        "es": "En Servidores guarda las claves y pulsa Conectar con Dailymotion e inicia sesión.",
    },
    "apidoc.dailymotion.extra": {
        "en": "Videos only. Uploads go to the connected channel.",
        "es": "Solo video. Las subidas van al canal conectado.",
    },
    "apidoc.bilibili.step1": {
        "en": "Create an app on Bilibili Open Platform (投稿).",
        "es": "Crea una app en Bilibili Open Platform (投稿).",
    },
    "apidoc.bilibili.step2": {
        "en": "Register the redirect URI: SITE_URL/oauth/bilibili/callback.",
        "es": "Registra la URI de redirección: SITE_URL/oauth/bilibili/callback.",
    },
    "apidoc.bilibili.step3": {
        "en": "In Servers, save Client ID and Client Secret, then Connect with Bilibili.",
        "es": "En Servidores guarda Client ID y Client Secret y pulsa Conectar con Bilibili.",
    },
    "apidoc.bilibili.extra": {
        "en": "Install ffmpeg on the server (needed for the cover). Optional: BILIBILI_TID and BILIBILI_TAG in .env. Videos only.",
        "es": "Instala ffmpeg en el servidor (hace falta para la portada). Opcional: BILIBILI_TID y BILIBILI_TAG en .env. Solo video.",
    },
    "apidoc.rumble.step1": {
        "en": "Rumble has no public OAuth. Apply to their partner Upload API.",
        "es": "Rumble no tiene OAuth público. Hay que entrar en su Upload API de partners.",
    },
    "apidoc.rumble.step2": {
        "en": "Rumble issues an access token and a Channel ID (not a livestream chat URL).",
        "es": "Rumble te da un access token y un Channel ID (no la URL de chat en vivo).",
    },
    "apidoc.rumble.step3": {
        "en": "In Servers, save the token and Channel ID. There is no Connect with Rumble button.",
        "es": "En Servidores guarda el token y el Channel ID. No hay botón Conectar con Rumble.",
    },
    "apidoc.rumble.extra": {
        "en": "If Rumble revokes the token, paste a new one. Videos only.",
        "es": "Si Rumble revoca el token, pega uno nuevo. Solo video.",
    },
    "apidoc.snapchat.step1": {
        "en": "In Snap Business Manager, create an app with Public Profile API (Stories / Spotlight).",
        "es": "En Snap Business Manager crea una app con Public Profile API (Stories / Spotlight).",
    },
    "apidoc.snapchat.step2": {
        "en": "Register the redirect URI: SITE_URL/oauth/snapchat/callback.",
        "es": "Registra la URI de redirección: SITE_URL/oauth/snapchat/callback.",
    },
    "apidoc.snapchat.step3": {
        "en": "In Servers, save Client ID and Client Secret, then Connect with Snapchat.",
        "es": "En Servidores guarda Client ID y Client Secret y pulsa Conectar con Snapchat.",
    },
    "apidoc.snapchat.extra": {
        "en": "OpenSSL must be installed (AES-256-CBC). Photos = Stories (24 h). Video: MP4 5–60 s (Spotlight 6–60 s, min. 540×960).",
        "es": "Hace falta OpenSSL instalado (AES-256-CBC). Fotos = Stories (24 h). Video: MP4 5–60 s (Spotlight 6–60 s, mín. 540×960).",
    },
    # ------------------------------------------------------------------
    # Proxys
    # ------------------------------------------------------------------
    "proxys.title": {"en": "Proxies", "es": "Proxys"},
    "proxys.intro": {
        "en": "Add proxies in any common format. Test each one to detect its country. OAuth, PPV host, Odysee and DTube accounts use the linked proxy. VMOS accounts do not: the cloud phone’s own network is used.",
        "es": "Añade proxys en cualquier formato habitual. Prueba cada uno para detectar su país. Las cuentas OAuth, las de hosts PPV, Odysee y DTube sí usan el proxy vinculado. Las de VMOS no: sale la red del móvil en la nube.",
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
    # Config X (cuenta X que recarga y paga la API por las demás)
    # ------------------------------------------------------------------
    "configx.title": {"en": "Config X", "es": "Config X"},
    "configx.intro": {
        "en": "Pick one X account whose balance pays for publishing on every other X account. Recharge that account, track how much has been spent and how much is left, and get a daily check at 4 AM (panel time) that tells you which X accounts already meet the requirements to start earning, so you only pay the subscription on those.",
        "es": "Elige una cuenta de X cuyo saldo paga las publicaciones de todas las demás cuentas de X. Recarga esa cuenta, mira cuánto saldo se ha gastado y cuánto queda, y recibe un chequeo diario a las 4 am (hora del panel) que te dice qué cuentas de X ya cumplen los requisitos para empezar a ganar, para pagar la suscripción solo en esas.",
    },
    "configx.info_btn": {"en": "About Config X", "es": "Acerca de Config X"},
    "configx.sources_title": {
        "en": "Account that recharges (pays the API)",
        "es": "Cuenta que recarga (paga la API)",
    },
    "configx.sources_hint": {
        "en": "Choose which connected X account holds the balance. Every publish to X made with the checkbox enabled deducts the cost per post from this balance instead of spending on each account.",
        "es": "Elige qué cuenta de X conectada tiene el saldo. Cada publicación en X hecha con el checkbox activado descuenta el costo por publicación de este saldo, en vez de gastar en cada cuenta.",
    },
    "configx.account_label": {"en": "X account", "es": "Cuenta de X"},
    "configx.cost_label": {"en": "Cost per post (USD)", "es": "Costo por publicación (USD)"},
    "configx.cost_hint": {
        "en": "Set the cost each post deducts from the balance. Use 0 if you only want to count posts without deducting money.",
        "es": "Define cuánto descuenta del saldo cada publicación. Usa 0 si solo quieres contar publicaciones sin descontar dinero.",
    },
    "configx.save": {"en": "Save", "es": "Guardar"},
    "configx.saved": {"en": "Saved.", "es": "Guardado."},
    "configx.no_x_accounts": {
        "en": "No X accounts connected yet. Connect them from Servers with “Connect with X”.",
        "es": "Aún no hay cuentas de X conectadas. Conéctalas desde Servidores con «Conectar con X».",
    },
    "configx.active": {"en": "Active", "es": "Activa"},
    "configx.inactive": {"en": "Inactive", "es": "Inactiva"},
    "configx.recharged_label": {"en": "Recharged", "es": "Recargado"},
    "configx.spent_label": {"en": "Spent", "es": "Gastado"},
    "configx.available_label": {"en": "Available", "es": "Disponible"},
    "configx.recharge_ph": {"en": "Amount (USD)", "es": "Monto (USD)"},
    "configx.recharge_btn": {"en": "Recharge", "es": "Recargar"},
    "configx.recharged": {
        "en": "Recharge of {amount} applied to {name}.",
        "es": "Recarga de {amount} aplicada a {name}.",
    },
    "configx.delete_confirm": {
        "en": "Remove this recharge account? Its balance history is deleted too.",
        "es": "¿Quitar esta cuenta de recarga? Su historial de saldo también se elimina.",
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
    "configx.checks_hint": {
        "en": "Every day at 4 AM (panel time) the panel queries the X API for each connected account and marks the ones that reach the follower threshold. X also requires Premium and 5M organic impressions in 3 months to share revenue; impressions are not exposed by the API, so verify them in X before paying.",
        "es": "Todos los días a las 4 am (hora del panel) se consulta la API de X para cada cuenta conectada y se marcan las que llegan al mínimo de seguidores. X además exige Premium y 5M de impresiones orgánicas en 3 meses para repartir ingresos; la API no expone impresiones, así que verifícalas en X antes de pagar.",
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
        "en": "Last daily check: {date}",
        "es": "Último chequeo diario: {date}",
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
    "configx.source_badge": {"en": "Recharges", "es": "Recarga"},
    "configx.usage_title": {"en": "Recent spending", "es": "Consumo reciente"},
    "configx.usage_empty": {
        "en": "No posts have used the Config X balance yet.",
        "es": "Ninguna publicación ha usado el saldo de Config X todavía.",
    },
    "pub.x_use_funding": {
        "en": "Use Config X balance ({name}) for this X post",
        "es": "Usar saldo de Config X ({name}) para esta publicación en X",
    },
    "pub.x_use_funding_hint": {
        "en": "Checked: this post uses the Config X developer app (and its balance). Uncheck it only if this account has its own X API keys and should spend from that app.",
        "es": "Marcado: esta publicación usa la app de Config X (y su saldo). Desmárcalo solo si esta cuenta tiene su propia API de X y debe gastar de esa app.",
    },
    "nav.membresias": {"en": "Pricing", "es": "Precio"},
    "nav.pagos": {"en": "Payments", "es": "Pagos"},
    "extractor.title": {"en": "Video extractor", "es": "Extractor de videos"},
    "extractor.subtitle": {
        "en": "Pull the videos from one server and spread them to the account's other servers, at your own pace.",
        "es": "Toma los videos de un servidor y repártelos a los demás servidores de la cuenta, al ritmo que definas.",
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
        "en": "Pick the server and the account to extract from. \"All\" is not allowed here.",
        "es": "Elige el servidor y la cuenta de donde se extrae. Aquí no se permite \"Todos\".",
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
        "en": "Set how many videos per cycle, how often, and the rest between videos. If the server runs low on resources the batch lowers automatically and goes back up when it recovers.",
        "es": "Define cuántos videos por ciclo, cada cuánto, y el descanso entre videos. Si el servidor se queda sin recursos, el lote baja automáticamente y vuelve a subir cuando se recupera.",
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
        "en": "Every how many minutes",
        "es": "Cada cuántos minutos",
    },
    "extractor.rest_label": {
        "en": "Rest between videos (seconds)",
        "es": "Descanso entre videos (segundos)",
    },
    "extractor.start_btn": {"en": "Start extraction", "es": "Iniciar extracción"},
    "extractor.starting": {"en": "Starting...", "es": "Iniciando..."},
    "extractor.jobs_title": {"en": "Extractions", "es": "Extracciones"},
    "extractor.status_running": {"en": "Running", "es": "En curso"},
    "extractor.status_paused": {"en": "Paused", "es": "Pausada"},
    "extractor.status_done": {"en": "Completed", "es": "Completada"},
    "extractor.status_error": {"en": "Error", "es": "Error"},
    "extractor.progress": {
        "en": "{done} of {total} deliveries",
        "es": "{done} de {total} envíos",
    },
    "extractor.job_config": {
        "en": "{batch} per cycle · every {interval} min · rest {rest}s",
        "es": "{batch} por ciclo · cada {interval} min · descanso {rest}s",
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
}


def resolve_lang(request: Request) -> str:
    """Inglés por defecto. Solo cambia si eligió idioma (sesión)."""
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
