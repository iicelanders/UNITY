"""
Supabase Client Wrapper — Agnostic dependency layer.

Currently a placeholder. When Supabase credentials are configured in .env,
replace MockRepository with this class in main.py.

This wrapper isolates the Supabase SDK so that if the library changes,
only this file needs updating — no view code is affected.

NOTE: All type annotations use plain types (no subscripts)
to ensure full compatibility with Python 3.9 runtime.
"""

import os

from dotenv import load_dotenv

from core.data_repository import AuthResult

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def is_supabase_configured():
    """Check whether real Supabase credentials are present."""
    return (
        bool(SUPABASE_URL)
        and bool(SUPABASE_KEY)
        and SUPABASE_URL != "your_supabase_url_here"
    )


class SupabaseRepository:
    """Supabase implementation of the DataRepository protocol.

    TODO: implement each method using `supabase.Client` when credentials
    are ready.  The method signatures mirror MockRepository exactly.
    """

    def __init__(self):
        if not is_supabase_configured():
            raise RuntimeError(
                "Supabase no está configurado. "
                "Completa SUPABASE_URL y SUPABASE_KEY en .env"
            )
        # Lazy import to avoid errors when supabase isn't installed yet
        from supabase import create_client  # type: ignore

        self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self._current_user_id = None

    # ── Auth ──────────────────────────────────────────────────────

    def sign_up(self, email, password):
        try:
            response = self._client.auth.sign_up(
                {"email": email, "password": password}
            )
            # Supabase may return a user without a session if email
            # confirmation is enabled. In that case, try auto-sign-in.
            if response.session:
                uid = str(response.user.id) if response.user else ""
                self._current_user_id = uid
                return AuthResult(success=True, user_id=uid, email=email)

            if response.user:
                # Attempt immediate sign-in (works when auto-confirm is on
                # or when the project skips email verification)
                try:
                    return self.sign_in(email, password)
                except Exception:
                    uid = str(response.user.id)
                    self._current_user_id = uid
                    return AuthResult(success=True, user_id=uid, email=email)

            return AuthResult(
                success=False,
                error="No se pudo crear la cuenta. Intenta de nuevo.",
            )
        except Exception as exc:
            return AuthResult(success=False, error=str(exc))

    def sign_in(self, email, password):
        try:
            response = self._client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            uid = str(response.user.id) if response.user else ""
            self._current_user_id = uid
            return AuthResult(success=True, user_id=uid, email=email)
        except Exception as exc:
            return AuthResult(success=False, error=str(exc))

    def sign_out(self):
        self._client.auth.sign_out()
        self._current_user_id = None

    def get_current_user_id(self):
        return self._current_user_id

    # ── Profiles ──────────────────────────────────────────────────

    def get_profile(self, user_id):
        result = (
            self._client.table("perfiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_profile(self, user_id, nombre_completo, habilidades, disponibilidad):
        data = {
            "id": user_id,
            "nombre_completo": nombre_completo,
            "habilidades": habilidades,
            "disponibilidad": disponibilidad,
            "rol": "voluntario",
            "tour_completado": False,
        }
        result = self._client.table("perfiles").insert(data).execute()
        return result.data[0]

    def update_profile(self, user_id, data):
        result = (
            self._client.table("perfiles")
            .update(data)
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else {}

    def update_tour_completed(self, user_id):
        self._client.table("perfiles").update(
            {"tour_completado": True}
        ).eq("id", user_id).execute()

    # ── SOS Alerts ────────────────────────────────────────────────

    def create_alert(self, user_id, latitud, longitud):
        data = {
            "usuario_id": user_id,
            "latitud": latitud,
            "longitud": longitud,
        }
        result = self._client.table("alertas_sos").insert(data).execute()
        return result.data[0]

    def get_active_alerts(self):
        result = (
            self._client.table("alertas_sos")
            .select("*, perfiles(nombre_completo)")
            .eq("resuelta", False)
            .execute()
        )
        return result.data

    def get_user_alerts(self, user_id):
        result = (
            self._client.table("alertas_sos")
            .select("*")
            .eq("usuario_id", user_id)
            .execute()
        )
        return result.data

    def resolve_alert(self, alert_id):
        self._client.table("alertas_sos").update({"resuelta": True}).eq(
            "id", alert_id
        ).execute()
        return True

    def get_user_active_alert(self, user_id):
        """Return the first non-resolved alert for this user, or None."""
        result = (
            self._client.table("alertas_sos")
            .select("*")
            .eq("usuario_id", user_id)
            .eq("resuelta", False)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    # ── Equipment ─────────────────────────────────────────────────

    def get_inventory(self):
        result = self._client.table("inventario_herramientas").select("*").execute()
        return result.data

    def assign_material(self, herramienta_id, usuario_asignado, cantidad):
        try:
            # Insert assignment
            assignment_data = {
                "herramienta_id": herramienta_id,
                "usuario_asignado": usuario_asignado,
                "cantidad": cantidad,
            }
            result = (
                self._client.table("entregas_material")
                .insert(assignment_data)
                .execute()
            )

            # Deduct stock (§6.8 — sequential operations)
            tool = (
                self._client.table("inventario_herramientas")
                .select("cantidad_disponible")
                .eq("id", herramienta_id)
                .execute()
            )
            new_qty = tool.data[0]["cantidad_disponible"] - cantidad
            self._client.table("inventario_herramientas").update(
                {"cantidad_disponible": new_qty}
            ).eq("id", herramienta_id).execute()

            return result.data[0]
        except ValueError:
            # Re-raise business logic errors as-is
            raise
        except Exception as exc:
            # Network / server errors — propagate with clear type
            raise ConnectionError(
                "Falla de Conexión con el Servidor: "
                "Los cambios no pudieron ser sincronizados. "
                "Verifica tu conexión a internet e intenta de nuevo."
            ) from exc

    def get_assignments(self):
        result = (
            self._client.table("entregas_material")
            .select("*, inventario_herramientas(nombre_herramienta), perfiles(nombre_completo)")
            .execute()
        )
        return result.data

    # ── Dashboard ─────────────────────────────────────────────────

    def get_total_volunteers(self):
        result = (
            self._client.table("perfiles")
            .select("id", count="exact")
            .execute()
        )
        return result.count or 0

    def get_active_alerts_count(self):
        result = (
            self._client.table("alertas_sos")
            .select("id", count="exact")
            .eq("resuelta", False)
            .execute()
        )
        return result.count or 0

    def get_critical_tools(self):
        result = self._client.table("inventario_herramientas").select("*").execute()
        return [
            t
            for t in result.data
            if t["cantidad_total"] > 0
            and t["cantidad_disponible"] / t["cantidad_total"] < 0.3
        ]

    def get_all_volunteers(self):
        result = self._client.table("perfiles").select("*").execute()
        return result.data
