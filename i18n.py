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
    "nav.api_docs": {"en": "API Document", "es": "API Documento"},
    "nav.publications": {"en": "Publications", "es": "Publicaciones"},
    "nav.team": {"en": "Team", "es": "Equipo"},
    "nav.tiktok_accounts": {"en": "TikTok Accounts", "es": "Cuentas TikTok"},
    "nav.servers": {"en": "Servers", "es": "Servidores"},
    "nav.panel": {"en": "Panel", "es": "Panel"},
    "panel.title": {"en": "Admin panel", "es": "Panel de administración"},
    "panel.title_prefix": {"en": "Panel of", "es": "Panel de"},
    "panel.page_hint": {
        "en": "Notification email: used for password reset and publication failure alerts. Password: we send a reset link to that email.",
        "es": "Correo de notificaciones: se usa para cambiar contraseña y alertas si falla una publicación. Contraseña: enviamos el enlace de restablecimiento a ese correo.",
    },
    "panel.current_user": {"en": "User", "es": "Usuario"},
    "panel.email_section": {"en": "Notification email", "es": "Correo de notificaciones"},
    "panel.email_info_btn": {
        "en": "What is this email for?",
        "es": "¿Para qué sirve este correo?",
    },
    "panel.email_hint": {
        "en": "This is the email address where the panel sends important messages: links to reset your password and alerts when a scheduled publication fails. Use an inbox you check regularly.",
        "es": "Es el correo donde el panel te envía avisos importantes: enlaces para restablecer tu contraseña y alertas si falla una publicación programada. Usa una bandeja que revises con frecuencia.",
    },
    "panel.email_ph": {"en": "admin@example.com", "es": "admin@ejemplo.com"},
    "panel.email_save": {"en": "Save", "es": "Guardar"},
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
        "en": "We will send a reset link to your notification email.",
        "es": "Enviaremos un enlace de restablecimiento a tu correo de notificaciones.",
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
        "en": "Email saved.",
        "es": "Correo guardado.",
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
        "en": "Choose a new administrator password.",
        "es": "Elige una nueva contraseña de administrador.",
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
    "platform.facebook": {"en": "Facebook", "es": "Facebook"},
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
    "servers.modal_api_credentials": {
        "en": "API credentials",
        "es": "Credenciales de API",
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
        "en": "Redirect URI in the TikTok developer portal:",
        "es": "Redirect URI en el portal de desarrolladores de TikTok:",
    },
    "servers.connect_with_tiktok": {"en": "Connect with TikTok", "es": "Conectar con TikTok"},
    "servers.oauth_missing": {
        "en": "Save the TikTok Client Key and Client Secret first, then connect an account.",
        "es": "Guarda primero el Client Key y el Client Secret de TikTok, luego conecta una cuenta.",
    },
    "servers.linked_accounts": {"en": "Linked accounts", "es": "Cuentas vinculadas"},
    "servers.no_accounts": {
        "en": "No accounts connected yet. Use the connect button above.",
        "es": "Aún no hay cuentas conectadas. Usa el botón de conectar arriba.",
    },
    "servers.connected": {"en": "Connected", "es": "Conectada"},
    "servers.team_user": {"en": "Team user:", "es": "Usuario del equipo:"},
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
        "en": "Authorized redirect URI in Google Cloud:",
        "es": "URI de redirección autorizada en Google Cloud:",
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
        "en": "OAuth redirect URI in Meta App Dashboard:",
        "es": "URI de redirección OAuth en Meta App Dashboard:",
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
        "en": "Valid OAuth redirect URI in Meta App Dashboard:",
        "es": "URI de redirección OAuth válida en Meta App Dashboard:",
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
        "en": "Save the X Client ID and Client Secret first (developer.x.com → OAuth 2.0 confidential client).",
        "es": "Guarda primero el Client ID y el Client Secret de X (developer.x.com → cliente confidencial OAuth 2.0).",
    },
    "servers.x_redirect_hint": {
        "en": "Callback URI / Redirect URL in the X developer portal:",
        "es": "Callback URI / Redirect URL en el portal de desarrolladores de X:",
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
        "en": "Save the Dailymotion API Key and API Secret first (Dailymotion Studio → API keys).",
        "es": "Guarda primero la API Key y el API Secret de Dailymotion (Dailymotion Studio → API keys).",
    },
    "servers.dailymotion_redirect_hint": {
        "en": "Callback URL in Dailymotion Studio:",
        "es": "Callback URL en Dailymotion Studio:",
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
        "en": "Callback URL in Bilibili Open Platform:",
        "es": "Callback URL en Bilibili Open Platform:",
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
        "en": "Redirect URI in Snap Business Manager:",
        "es": "Redirect URI en Snap Business Manager:",
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
    "servers.accounts_edit_servers_info_title": {
        "en": "Edit servers",
        "es": "Editar servidores",
    },
    "servers.accounts_edit_servers_hint": {
        "en": "Pick a server to review credentials, test the API, and fix issues before publishing.",
        "es": "Elige un servidor para revisar credenciales, probar la API y corregir errores antes de publicar.",
    },
    "servers.accounts_server_linked": {"en": "Linked", "es": "Vinculado"},
    "servers.accounts_server_not_linked": {"en": "Not linked", "es": "Sin vincular"},
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
    "api.save": {"en": "Save API", "es": "Guardar API"},
    "api.test": {"en": "Test API", "es": "Probar API"},
    "api.test_all": {"en": "Test all APIs", "es": "Probar todas las APIs"},
    "api.section": {"en": "API credentials", "es": "Credenciales de API"},
    "api.saved": {"en": "API credentials saved.", "es": "Credenciales de API guardadas."},
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
    "api.field.extra.rumble": {
        "en": "Channel ID (required to publish)",
        "es": "Channel ID (obligatorio para publicar)",
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
        "en": "Requires <code>comment.list</code> and <code>comment.reply</code> scopes.",
        "es": "Requiere los alcances <code>comment.list</code> y <code>comment.reply</code>.",
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
        "en": "File exceeds the maximum size (100 MB).",
        "es": "El archivo supera el tamaño máximo (100 MB).",
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
        "en": "No TikTok accounts are registered. Connect one under Servers.",
        "es": "No hay cuentas TikTok registradas. Conecta una en Servidores.",
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
    "pub.log_status_ok": {"en": "OK", "es": "OK"},
    "pub.log_status_fail": {"en": "Failed", "es": "Falló"},
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
        "en": "Saved locally. {ok} OK, {fail} failed — see log below.",
        "es": "Guardado localmente. {ok} OK, {fail} fallaron — revisa el registro.",
    },
    "pub.flash.all_ok": {
        "en": "Published to {n} platform(s).",
        "es": "Publicado en {n} plataforma(s).",
    },
    "pub.upload_media_hint": {
        "en": "Video or photo — each platform uses what its API allows.",
        "es": "Video o foto — cada plataforma usa lo que su API permita.",
    },
    "footer.about": {"en": "About", "es": "Nosotros"},
    "footer.privacy": {"en": "Privacy Policy", "es": "Política de privacidad"},
    "footer.terms": {"en": "Terms of Service", "es": "Términos de servicio"},
    "footer.deletion": {"en": "Data Deletion", "es": "Eliminación de datos"},
    "footer.support": {"en": "Support", "es": "Soporte"},
    "footer.not_affiliated": {
        "en": "Not affiliated with TikTok Inc.",
        "es": "No afiliado a TikTok Inc.",
    },
    "site.description": {
        "en": (
            "Manage scheduled posts, track performance statistics, and grow your audience "
            "from a single, powerful dashboard powered by the official TikTok API."
        ),
        "es": (
            "Gestiona publicaciones programadas, sigue estadísticas de rendimiento y haz crecer "
            "tu audiencia desde un solo panel potente con la API oficial de TikTok."
        ),
    },
    "site.hero_title": {
        "en": "Optimize Your TikTok Content & Analytics",
        "es": "Optimiza tu contenido y analíticas de TikTok",
    },
    "site.hero_subtitle": {
        "en": (
            "Manage scheduled posts, track performance statistics, and grow your audience "
            "from a single, powerful dashboard."
        ),
        "es": (
            "Gestiona publicaciones programadas, sigue estadísticas de rendimiento y haz crecer "
            "tu audiencia desde un solo panel."
        ),
    },
    "landing.learn_more": {"en": "Learn more", "es": "Saber más"},
    "landing.built_for": {
        "en": "Built for creators and teams",
        "es": "Hecho para creadores y equipos",
    },
    "landing.feature1.title": {
        "en": "Efficient Video Management",
        "es": "Gestión eficiente de videos",
    },
    "landing.feature1.body": {
        "en": "Schedule and publish your video content seamlessly across your connected TikTok accounts from one dashboard.",
        "es": "Programa y publica tu contenido en video de forma fluida en tus cuentas TikTok conectadas desde un solo panel.",
    },
    "landing.feature1.scope": {"en": "Scopes:", "es": "Alcances:"},
    "landing.feature2.title": {
        "en": "Performance Metrics & Insights",
        "es": "Métricas e insights de rendimiento",
    },
    "landing.feature2.body": {
        "en": "Track views, likes, shares, and audience growth in real time to optimize your content strategy.",
        "es": "Sigue vistas, me gusta, compartidos y crecimiento de audiencia en tiempo real para optimizar tu estrategia de contenido.",
    },
    "landing.feature2.scope": {
        "en": "Analytics via authorized TikTok API",
        "es": "Analíticas vía API autorizada de TikTok",
    },
    "landing.feature3.title": {
        "en": "Comment Inbox & Replies",
        "es": "Bandeja de comentarios y respuestas",
    },
    "landing.feature3.body": {
        "en": "Read recent comments on your posts and reply directly from the panel without switching apps.",
        "es": "Lee comentarios recientes en tus publicaciones y responde directamente desde el panel sin cambiar de app.",
    },
    "landing.feature3.scope": {"en": "Scopes:", "es": "Alcances:"},
    "landing.api.title": {
        "en": "Official TikTok API integration",
        "es": "Integración oficial con la API de TikTok",
    },
    "landing.api.p1": {
        "en": (
            "{site_name} uses <strong>TikTok for Developers</strong> (Login Kit and approved products) "
            "only after the account owner grants permission. Access is limited to authorized team members. "
            "Data from TikTok is used solely to provide the features above and is never sold to third parties."
        ),
        "es": (
            "{site_name} usa <strong>TikTok for Developers</strong> (Login Kit y productos aprobados) "
            "solo después de que el titular de la cuenta otorgue permiso. El acceso está limitado a "
            "miembros autorizados del equipo. Los datos de TikTok se usan únicamente para ofrecer las "
            "funciones anteriores y nunca se venden a terceros."
        ),
    },
    "landing.api.p2": {
        "en": "Read our Privacy Policy and Terms of Service.",
        "es": "Lee nuestra Política de privacidad y Términos de servicio.",
    },
    "login.dashboard": {"en": "Creator Dashboard.", "es": "Panel de creador."},
    "login.tagline": {
        "en": "Manage your TikTok presence effortlessly. Schedule videos, monitor analytics, and engage with your community, all in one place.",
        "es": "Gestiona tu presencia en TikTok sin complicaciones. Programa videos, monitoriza analíticas e interactúa con tu comunidad, todo en un solo lugar.",
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
    "login.error": {
        "en": "Invalid username or password",
        "es": "Usuario o contraseña incorrectos",
    },
    "legal.last_updated": {"en": "Last updated:", "es": "Última actualización:"},
    "legal.about_title": {"en": "About Us", "es": "Sobre nosotros"},
    "legal.privacy_title": {"en": "Privacy Policy", "es": "Política de privacidad"},
    "legal.terms_title": {"en": "Terms of Service", "es": "Términos de servicio"},
    "legal.deletion_title": {"en": "Data Deletion", "es": "Eliminación de datos"},
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
        "en": "No TikTok account is linked to your profile. Ask an administrator to assign one in Team.",
        "es": "No hay cuenta TikTok vinculada a tu perfil. Pide a un administrador que te asigne una en Equipo.",
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
    "apidoc.intro": {
        "en": "What each server needs so publishing works. All of these have a real API. Tokens marked Automatic are refreshed by the panel when you publish; you do not paste a new token by hand.",
        "es": "Qué hay que hacer en cada servidor para que la publicación funcione. Todas estas redes tienen API real. Si el token es Automático, el panel lo renueva al publicar; no hace falta pegar uno nuevo a mano.",
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
    "apidoc.token.auto": {"en": "Automatic", "es": "Automático"},
    "apidoc.token.manual": {"en": "Manual", "es": "Manual"},
    "apidoc.extra_none": {"en": "None", "es": "Ninguno"},
    "apidoc.tiktok.step1": {
        "en": "Create an app in TikTok for Developers (developers.tiktok.com).",
        "es": "Crea una app en TikTok for Developers (developers.tiktok.com).",
    },
    "apidoc.tiktok.step2": {
        "en": "Enable Login Kit and Content Posting API (user.info.basic, video.upload, video.publish).",
        "es": "Activa Login Kit y Content Posting API (user.info.basic, video.upload, video.publish).",
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
        "en": "A paid X API plan with write access is required to publish. Photos, GIF and short video.",
        "es": "Hace falta un plan de pago de la API de X con permiso de escritura para publicar. Fotos, GIF y video corto.",
    },
    "apidoc.dailymotion.step1": {
        "en": "Get an API Key and API Secret from Dailymotion (partner / developer app).",
        "es": "En Dailymotion obtén API Key y API Secret (app de partner / desarrollador).",
    },
    "apidoc.dailymotion.step2": {
        "en": "Register the redirect URI: SITE_URL/oauth/dailymotion/callback.",
        "es": "Registra la URI de redirección: SITE_URL/oauth/dailymotion/callback.",
    },
    "apidoc.dailymotion.step3": {
        "en": "In Servers, save the keys, then Connect with Dailymotion.",
        "es": "En Servidores guarda las claves y pulsa Conectar con Dailymotion.",
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
    # Extractor
    # ------------------------------------------------------------------
    "nav.extractor": {"en": "Extractor", "es": "Extractor"},
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
    session_lang = request.session.get("lang")
    if session_lang in LANGUAGES:
        return session_lang

    accept = request.headers.get("accept-language", "")
    for part in accept.split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in LANGUAGES:
            return code
    return DEFAULT_LANG


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
        "site_description": t("site.description", lang),
        "hero_title": t("site.hero_title", lang),
        "hero_subtitle": t("site.hero_subtitle", lang),
        **extra,
    }
