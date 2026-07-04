"""
Turnos Service — Business logic for schedule management (S3_HU01).

Responsibilities:
  - Overlap validation before turno insertion
  - Role-based permission checks (only lider_cuadrilla can write)
  - Orchestration of validated turno creation

All network error handling lives here, not in views.
"""

from datetime import datetime


class TurnoResult:
    """Immutable result of a turno operation."""

    def __init__(self, success, turno=None, error=""):
        self.success = success
        self.turno = turno
        self.error = error


def puede_editar_turnos(rol):
    """Only lider_cuadrilla has write permissions on the calendar.

    Returns:
        bool: True if the role can create/delete turnos.
    """
    return rol == "lider_cuadrilla"


def hay_solapamiento(turnos_existentes, usuario_id, inicio_hora, fin_hora, dia_semana):
    """Check whether a new time block overlaps with existing ones for the same user.

    Two blocks overlap when they share the same dia_semana AND their time
    intervals intersect: new_start < existing_end AND new_end > existing_start.

    Args:
        turnos_existentes: list of turno dicts from the repository.
        usuario_id: the user whose schedule to check.
        inicio_hora: ISO timestamp string for the new block start.
        fin_hora: ISO timestamp string for the new block end.
        dia_semana: weekday int (0=Mon .. 6=Sun).

    Returns:
        bool: True if there IS an overlap (block must be rejected).
    """
    new_start = _parse_time(inicio_hora)
    new_end = _parse_time(fin_hora)

    for turno in turnos_existentes:
        if turno["usuario_id"] != usuario_id:
            continue
        if turno["dia_semana"] != dia_semana:
            continue

        existing_start = _parse_time(turno["inicio_hora"])
        existing_end = _parse_time(turno["fin_hora"])

        # Interval overlap condition
        if new_start < existing_end and new_end > existing_start:
            return True

    return False


def crear_turno_validado(repository, usuario_id, cuadrilla_id, inicio_hora, fin_hora, dia_semana):
    """Orchestrate validated turno creation.

    Steps:
      1. Fetch existing turnos for the cuadrilla
      2. Check overlap for this user on this day
      3. If overlap → return error (no network call)
      4. If clear → insert via repository

    Args:
        repository: DataRepository implementation.
        usuario_id: UUID string of the user.
        cuadrilla_id: UUID string of the cuadrilla.
        inicio_hora: ISO timestamp string.
        fin_hora: ISO timestamp string.
        dia_semana: weekday int (0-6).

    Returns:
        TurnoResult with success/error state.
    """
    # Early return: invalid time range
    if inicio_hora >= fin_hora:
        return TurnoResult(
            success=False,
            error="La hora de inicio debe ser anterior a la hora de fin.",
        )

    try:
        turnos_existentes = repository.get_turnos_by_cuadrilla(cuadrilla_id)
    except Exception:
        return TurnoResult(
            success=False,
            error="Error de red. No se pudo consultar los turnos.",
        )

    if hay_solapamiento(turnos_existentes, usuario_id, inicio_hora, fin_hora, dia_semana):
        return TurnoResult(
            success=False,
            error="Bloque horario ya asignado",
        )

    try:
        turno = repository.create_turno(
            usuario_id=usuario_id,
            cuadrilla_id=cuadrilla_id,
            inicio_hora=inicio_hora,
            fin_hora=fin_hora,
            dia_semana=dia_semana,
        )
        return TurnoResult(success=True, turno=turno)
    except Exception:
        return TurnoResult(
            success=False,
            error="Error de red. No se pudo guardar el turno.",
        )


def eliminar_turno(repository, turno_id):
    """Delete a turno with network error handling.

    Returns:
        TurnoResult with success/error state.
    """
    try:
        repository.delete_turno(turno_id)
        return TurnoResult(success=True)
    except Exception:
        return TurnoResult(
            success=False,
            error="Error de red. No se pudo eliminar el turno.",
        )


# ── Private helpers ──────────────────────────────────────────────

def _parse_time(timestamp_str):
    """Parse an ISO timestamp string to a datetime for comparison.

    Handles both full ISO 8601 with timezone and naive timestamps.
    """
    if not timestamp_str:
        return datetime.min

    # Strip timezone suffix for consistent comparison
    clean = timestamp_str.replace("Z", "+00:00")

    # Try full ISO with timezone first
    try:
        return datetime.fromisoformat(clean)
    except ValueError:
        pass

    # Fallback: try without timezone
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    return datetime.min
