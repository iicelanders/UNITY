"""
SOS Service — Business logic for enhanced emergency reporting (S3_HU03 + S3_HU04).

Responsibilities:
  - Coordinate interpolation: pixel click → lat/lon via linear mapping
  - Input validation with Early Return for missing data
  - Dual transactional insertion: alertas_sos + mensajes_chat
  - Partial failure handling per SRS §2.4

All network error handling and coordinate math lives here, not in views.
"""

from core.chat_service import enviar_alerta_chat


# ── Bounding box for Concepción zone (matching sos_view.py §4.2) ─

BOUNDING_BOX = {
    "lat_min": -36.8500,
    "lat_max": -36.8000,
    "lon_min": -73.0800,
    "lon_max": -73.0000,
}

TIPOS_EMERGENCIA = [
    "Obstrucción de Ruta",
    "Falta de Suministros",
    "Falta de Información",
    "Emergencia Médica",
    "Riesgo Climático",
    "Humo Denso",
    "Pavesa o Nuevo Foco",
    "Caída de Árboles o Colapso Estructural",
    "Seguridad Personal",
]


class SOSResult:
    """Immutable result of an SOS operation."""

    def __init__(self, success, alerta=None, error="", alerta_creada_sin_chat=False):
        self.success = success
        self.alerta = alerta
        self.error = error
        # True when alert was saved but chat notification failed (partial failure)
        self.alerta_creada_sin_chat = alerta_creada_sin_chat


def interpolar_coordenadas(click_x, click_y, image_width, image_height, bounding_box=None):
    """Convert pixel coordinates from a map click to geographic lat/lon.

    Uses linear interpolation within the bounding box.

    Args:
        click_x: X pixel position of the click (0 = left edge).
        click_y: Y pixel position of the click (0 = top edge).
        image_width: total width of the map image in pixels.
        image_height: total height of the map image in pixels.
        bounding_box: dict with lat_min, lat_max, lon_min, lon_max.
            Defaults to BOUNDING_BOX (Concepción).

    Returns:
        tuple: (latitud, longitud) as floats.
    """
    if bounding_box is None:
        bounding_box = BOUNDING_BOX

    # Guard against division by zero
    if image_width <= 0 or image_height <= 0:
        return (bounding_box["lat_min"], bounding_box["lon_min"])

    # Normalize click position to [0, 1]
    ratio_x = click_x / image_width
    ratio_y = click_y / image_height

    # Clamp to [0, 1]
    ratio_x = max(0.0, min(1.0, ratio_x))
    ratio_y = max(0.0, min(1.0, ratio_y))

    # Interpolate: X → longitude, Y → latitude
    # Y is inverted: top of image = lat_max, bottom = lat_min
    longitud = bounding_box["lon_min"] + ratio_x * (
        bounding_box["lon_max"] - bounding_box["lon_min"]
    )
    latitud = bounding_box["lat_max"] - ratio_y * (
        bounding_box["lat_max"] - bounding_box["lat_min"]
    )

    return (round(latitud, 6), round(longitud, 6))


def validar_datos_emergencia(latitud, longitud, tipo_emergencia):
    """Early Return validation for emergency data.

    Returns:
        SOSResult: success=True if valid, success=False with error if not.
    """
    if latitud is None or longitud is None:
        return SOSResult(
            success=False,
            error="Selecciona una ubicación en el mapa antes de enviar.",
        )

    if not tipo_emergencia or tipo_emergencia.strip() == "":
        return SOSResult(
            success=False,
            error="Selecciona un tipo de emergencia.",
        )

    if tipo_emergencia not in TIPOS_EMERGENCIA:
        return SOSResult(
            success=False,
            error="El tipo de emergencia seleccionado no es válido.",
        )

    return SOSResult(success=True)


def crear_alerta_con_notificacion(
    repository, user_id, latitud, longitud, tipo_emergencia, cuadrilla_id
):
    """Dual transactional insert: alertas_sos + mensajes_chat.

    Per SRS §2.4:
    - First, insert into alertas_sos
    - Then, inject a highlighted message into mensajes_chat
    - If the chat insertion fails, report partial failure
      (alert was saved but cuadrilla was not notified)

    Args:
        repository: DataRepository implementation.
        user_id: UUID string of the alerting user.
        latitud: geographic latitude.
        longitud: geographic longitude.
        tipo_emergencia: emergency category string.
        cuadrilla_id: UUID string of the user's cuadrilla (may be None).

    Returns:
        SOSResult with the created alert and partial failure flag.
    """
    # Step 1: Validate inputs
    validacion = validar_datos_emergencia(latitud, longitud, tipo_emergencia)
    if not validacion.success:
        return validacion

    # Step 2: Insert alert into alertas_sos
    try:
        alerta = repository.create_alert(
            user_id=user_id,
            latitud=latitud,
            longitud=longitud,
            tipo_emergencia=tipo_emergencia,
        )
    except Exception:
        return SOSResult(
            success=False,
            error="Error de red. No se pudo enviar la alerta. Reintenta el envío.",
        )

    # Step 3: Inject notification into cuadrilla chat (if user has cuadrilla)
    if not cuadrilla_id:
        # No cuadrilla — alert saved, no chat notification possible
        return SOSResult(success=True, alerta=alerta)

    texto_alerta = (
        f"🚨 ALERTA SOS — {tipo_emergencia}\n"
        f"Ubicación: ({latitud:.4f}, {longitud:.4f})"
    )

    chat_result = enviar_alerta_chat(
        repository=repository,
        cuadrilla_id=cuadrilla_id,
        usuario_id=user_id,
        texto_alerta=texto_alerta,
    )

    if not chat_result.success:
        # Partial failure: alert saved but chat notification failed
        return SOSResult(
            success=True,
            alerta=alerta,
            alerta_creada_sin_chat=True,
            error=(
                "La alerta fue procesada pero la notificación "
                "interna a la cuadrilla no pudo sincronizarse."
            ),
        )

    return SOSResult(success=True, alerta=alerta)
