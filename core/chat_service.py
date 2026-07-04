"""
Chat Service — Business logic for squad chat coordination (S3_HU02).

Responsibilities:
  - Access validation (Early Return for null cuadrilla_id)
  - Message fetching with timestamp-based filtering
  - Connection state management for polling resilience
  - Message sending with validation

All polling orchestration and network error management lives here.
"""


# ── Connection state constants ───────────────────────────────────

ESTADO_CONECTADO = "ok"
ESTADO_RECONECTANDO = "reconectando"

# Number of consecutive failures before showing "Buscando conexión..."
MAX_CICLOS_SILENCIOSOS = 3


class ChatResult:
    """Immutable result of a chat operation."""

    def __init__(self, success, data=None, error=""):
        self.success = success
        self.data = data
        self.error = error


def puede_acceder_chat(cuadrilla_id):
    """Early Return check: user must have a valid cuadrilla_id.

    Args:
        cuadrilla_id: the user's cuadrilla_id from their profile.

    Returns:
        bool: True if the user can access chat.
    """
    if not cuadrilla_id:
        return False
    if str(cuadrilla_id).strip() == "":
        return False
    return True


def obtener_mensajes_nuevos(repository, cuadrilla_id, ultimo_timestamp):
    """Fetch new messages since the last known timestamp.

    Args:
        repository: DataRepository implementation.
        cuadrilla_id: UUID string of the cuadrilla.
        ultimo_timestamp: ISO timestamp string of the last received message.
            Empty string fetches all messages.

    Returns:
        ChatResult with messages list in .data or error.
    """
    try:
        mensajes = repository.get_mensajes_chat(cuadrilla_id, ultimo_timestamp)
        return ChatResult(success=True, data=mensajes)
    except Exception:
        return ChatResult(success=False, error="Error al obtener mensajes")


def enviar_mensaje(repository, cuadrilla_id, usuario_id, texto):
    """Validate and send a chat message.

    Args:
        repository: DataRepository implementation.
        cuadrilla_id: UUID string of the cuadrilla.
        usuario_id: UUID string of the sender.
        texto: message text content.

    Returns:
        ChatResult with the created message in .data or error.
    """
    # Early return: empty message
    texto_limpio = texto.strip() if texto else ""
    if not texto_limpio:
        return ChatResult(success=False, error="El mensaje no puede estar vacío")

    try:
        mensaje = repository.send_mensaje_chat(
            cuadrilla_id=cuadrilla_id,
            usuario_id=usuario_id,
            texto_mensaje=texto_limpio,
            es_alerta=False,
        )
        return ChatResult(success=True, data=mensaje)
    except Exception:
        return ChatResult(
            success=False,
            error="Error de red. Mensaje no enviado.",
        )


def gestionar_estado_conexion(ciclos_fallidos):
    """Determine connection state based on consecutive failure count.

    Per SRS S3_HU02:
    - 0-2 failures: silently discard, state = 'ok'
    - 3+ failures: show warning banner, state = 'reconectando'

    Args:
        ciclos_fallidos: number of consecutive polling failures.

    Returns:
        str: ESTADO_CONECTADO or ESTADO_RECONECTANDO.
    """
    if ciclos_fallidos >= MAX_CICLOS_SILENCIOSOS:
        return ESTADO_RECONECTANDO
    return ESTADO_CONECTADO


def enviar_alerta_chat(repository, cuadrilla_id, usuario_id, texto_alerta):
    """Send a highlighted alert message to the squad chat (S3_HU04).

    This is used by the SOS flow to inject a distinguished message
    into the cuadrilla's chat.

    Args:
        repository: DataRepository implementation.
        cuadrilla_id: UUID string of the cuadrilla.
        usuario_id: UUID string of the alert sender.
        texto_alerta: alert description text.

    Returns:
        ChatResult with the created message in .data or error.
    """
    if not puede_acceder_chat(cuadrilla_id):
        return ChatResult(
            success=False,
            error="Usuario sin cuadrilla asignada",
        )

    try:
        mensaje = repository.send_mensaje_chat(
            cuadrilla_id=cuadrilla_id,
            usuario_id=usuario_id,
            texto_mensaje=texto_alerta,
            es_alerta=True,
        )
        return ChatResult(success=True, data=mensaje)
    except Exception:
        return ChatResult(
            success=False,
            error="No se pudo notificar a la cuadrilla",
        )
