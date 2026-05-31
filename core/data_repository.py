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
        self, user_id: str, latitud: float, longitud: float
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
