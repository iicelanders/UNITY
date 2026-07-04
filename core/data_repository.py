"""
Data Repository — Abstract interface for all data operations.

Follows the Dependency Inversion Principle (SOLID-D):
Views depend on this abstraction, not on concrete Supabase or mock implementations.
When switching from MockRepository to SupabaseRepository, no view code changes.

NOTE: All type annotations use plain 'list' and 'dict' (no subscripts)
to ensure full compatibility with Python 3.9 runtime evaluation.
"""

from typing import Protocol


class AuthResult:
    """Immutable result of an authentication operation."""

    def __init__(
        self,
        success: bool,
        user_id: str = "",
        email: str = "",
        error: str = "",
    ):
        self.success = success
        self.user_id = user_id
        self.email = email
        self.error = error


class DataRepository(Protocol):
    """Protocol defining every data operation the UNITY app needs."""

    # ── Auth ──────────────────────────────────────────────────────
    def sign_up(self, email: str, password: str) -> AuthResult: ...
    def sign_in(self, email: str, password: str) -> AuthResult: ...
    def sign_out(self) -> None: ...
    def get_current_user_id(self): ...

    # ── Profiles ──────────────────────────────────────────────────
    def get_profile(self, user_id: str): ...
    def create_profile(
        self,
        user_id: str,
        nombre_completo: str,
        habilidades: list,
        disponibilidad: str,
    ) -> dict: ...
    def update_profile(self, user_id: str, data: dict) -> dict:
        """Update editable fields on an existing profile (e.g. disponibilidad)."""
        ...
    def update_tour_completed(self, user_id: str) -> None:
        """Mark the onboarding tour as completed for this user."""
        ...

    # ── SOS Alerts ────────────────────────────────────────────────
    def create_alert(
        self, user_id: str, latitud: float, longitud: float,
        tipo_emergencia: str = "",
    ) -> dict: ...
    def get_active_alerts(self) -> list: ...
    def get_user_alerts(self, user_id: str) -> list: ...
    def resolve_alert(self, alert_id: str) -> bool: ...
    def get_user_active_alert(self, user_id: str): ...

    # ── Equipment ─────────────────────────────────────────────────
    def get_inventory(self) -> list: ...
    def assign_material(
        self, herramienta_id: str, usuario_asignado: str, cantidad: int
    ) -> dict: ...
    def get_assignments(self) -> list: ...

    # ── Dashboard ─────────────────────────────────────────────────
    def get_total_volunteers(self) -> int: ...
    def get_active_alerts_count(self) -> int: ...
    def get_critical_tools(self) -> list: ...
    def get_all_volunteers(self) -> list: ...

    # ── Cuadrillas (S3) ──────────────────────────────────────────
    def get_cuadrilla(self, cuadrilla_id: str) -> dict:
        """Return a single cuadrilla by ID, or None."""
        ...
    def get_cuadrillas(self) -> list:
        """Return all cuadrillas."""
        ...

    # ── Turnos (S3_HU01) ─────────────────────────────────────────
    def get_turnos_by_cuadrilla(self, cuadrilla_id: str) -> list:
        """Return all turnos for a given cuadrilla."""
        ...
    def create_turno(
        self, usuario_id: str, cuadrilla_id: str,
        inicio_hora: str, fin_hora: str, dia_semana: int,
    ) -> dict:
        """Insert a new turno. Returns the created record."""
        ...
    def delete_turno(self, turno_id: str) -> bool:
        """Delete a turno by ID. Returns True on success."""
        ...

    # ── Chat (S3_HU02) ───────────────────────────────────────────
    def get_mensajes_chat(self, cuadrilla_id: str, after_timestamp: str) -> list:
        """Return messages for a cuadrilla after the given timestamp.

        Pass an empty string to get all messages.
        """
        ...
    def send_mensaje_chat(
        self, cuadrilla_id: str, usuario_id: str,
        texto_mensaje: str, es_alerta: bool = False,
    ) -> dict:
        """Insert a chat message. Returns the created record."""
        ...

