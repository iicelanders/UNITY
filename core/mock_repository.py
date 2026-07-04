"""
Mock Repository — In-memory implementation with example data.

Fully satisfies the DataRepository protocol so the app can run
without Supabase. Swap for SupabaseRepository when ready.

Demo accounts seeded automatically:
  voluntario@unity.cl / 123456
  lider@unity.cl      / 123456
  comando@unity.cl    / 123456

NOTE: All type annotations use plain types (no subscripts like list[str])
to ensure full compatibility with Python 3.9 runtime.
"""

import hashlib
import uuid
from datetime import datetime

from core.data_repository import AuthResult


class MockRepository:
    """In-memory data store pre-loaded with example data."""

    def __init__(self):
        self._current_user_id = None
        self._users = {}
        self._profiles = {}
        self._alerts = []
        self._inventory = []
        self._assignments = []
        self._cuadrillas = []
        self._turnos = []
        self._mensajes = []
        self._seed_data()

    # ── Seed ──────────────────────────────────────────────────────

    def _seed_data(self):
        cuadrilla_alpha_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        cuadrilla_bravo_id = "b2c3d4e5-f6a7-8901-bcde-f12345678901"

        # Cuadrillas
        self._cuadrillas.append(
            {
                "id": cuadrilla_alpha_id,
                "nombre_cuadrilla": "Cuadrilla Alpha",
            }
        )
        self._cuadrillas.append(
            {
                "id": cuadrilla_bravo_id,
                "nombre_cuadrilla": "Cuadrilla Bravo",
            }
        )

        # Role → cuadrilla mapping for demo users
        cuadrilla_by_role = {
            "voluntario": cuadrilla_alpha_id,
            "lider_cuadrilla": cuadrilla_alpha_id,
            "comando": cuadrilla_bravo_id,
        }

        demo_users = [
            {
                "email": "voluntario@unity.cl",
                "password": "123456",
                "nombre": "Ana García",
                "rol": "voluntario",
                "habilidades": ["Primeros auxilios", "Logística"],
                "disponibilidad": "Mañana (8:00-12:00)",
            },
            {
                "email": "lider@unity.cl",
                "password": "123456",
                "nombre": "Carlos Muñoz",
                "rol": "lider_cuadrilla",
                "habilidades": ["Construcción", "Transporte"],
                "disponibilidad": "Completo (8:00-18:00)",
            },
            {
                "email": "comando@unity.cl",
                "password": "123456",
                "nombre": "María Soto",
                "rol": "comando",
                "habilidades": ["Comunicaciones", "Logística"],
                "disponibilidad": "Completo (8:00-18:00)",
            },
        ]

        for user in demo_users:
            uid = str(uuid.uuid4())
            pw_hash = hashlib.sha256(user["password"].encode()).hexdigest()
            self._users[user["email"]] = {
                "id": uid,
                "email": user["email"],
                "password_hash": pw_hash,
            }
            assigned_cuadrilla = cuadrilla_by_role.get(user["rol"], "")
            self._profiles[uid] = {
                "id": uid,
                "nombre_completo": user["nombre"],
                "habilidades": user["habilidades"],
                "disponibilidad": user["disponibilidad"],
                "rol": user["rol"],
                "cuadrilla_id": assigned_cuadrilla,
                "tour_completado": True,
                "creado_en": datetime.now().isoformat(),
            }


        # Inventory
        tools = [
            ("Palas", 20, 15),
            ("Cascos", 30, 22),
            ("Botiquines", 15, 8),
            ("Radios", 10, 4),
            ("Linternas", 25, 18),
            ("Guantes", 50, 35),
        ]
        for name, total, available in tools:
            self._inventory.append(
                {
                    "id": str(uuid.uuid4()),
                    "nombre_herramienta": name,
                    "cantidad_total": total,
                    "cantidad_disponible": available,
                }
            )

        # One sample active alert
        first_uid = list(self._profiles.keys())[0]
        self._alerts.append(
            {
                "id": str(uuid.uuid4()),
                "usuario_id": first_uid,
                "latitud": -36.8271,
                "longitud": -73.0503,
                "tipo_emergencia": "",
                "resuelta": False,
                "fecha_alerta": datetime.now().isoformat(),
                "nombre_usuario": "Ana García",
            }
        )

        # Sample chat messages
        lider_uid = list(self._profiles.keys())[1]
        self._mensajes.append(
            {
                "id": str(uuid.uuid4()),
                "cuadrilla_id": cuadrilla_alpha_id,
                "usuario_id": lider_uid,
                "texto_mensaje": "Bienvenidos al chat de Cuadrilla Alpha.",
                "es_alerta": False,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._mensajes.append(
            {
                "id": str(uuid.uuid4()),
                "cuadrilla_id": cuadrilla_alpha_id,
                "usuario_id": first_uid,
                "texto_mensaje": "¡Hola equipo! Lista para la jornada.",
                "es_alerta": False,
                "timestamp": datetime.now().isoformat(),
            }
        )

    # ── Auth ──────────────────────────────────────────────────────

    def sign_up(self, email, password):
        if email in self._users:
            return AuthResult(success=False, error="El correo ya está registrado")

        uid = str(uuid.uuid4())
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        self._users[email] = {"id": uid, "email": email, "password_hash": pw_hash}
        self._current_user_id = uid
        return AuthResult(success=True, user_id=uid, email=email)

    def sign_in(self, email, password):
        user = self._users.get(email)
        if not user:
            return AuthResult(success=False, error="Usuario no encontrado")

        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if user["password_hash"] != pw_hash:
            return AuthResult(success=False, error="Contraseña incorrecta")

        self._current_user_id = user["id"]
        return AuthResult(success=True, user_id=user["id"], email=email)

    def sign_out(self):
        self._current_user_id = None

    def get_current_user_id(self):
        return self._current_user_id

    # ── Profiles ──────────────────────────────────────────────────

    def get_profile(self, user_id):
        return self._profiles.get(user_id)

    def create_profile(self, user_id, nombre_completo, habilidades, disponibilidad):
        profile = {
            "id": user_id,
            "nombre_completo": nombre_completo,
            "habilidades": habilidades,
            "disponibilidad": disponibilidad,
            "rol": "voluntario",
            "tour_completado": False,
            "creado_en": datetime.now().isoformat(),
        }
        self._profiles[user_id] = profile
        return profile

    def update_profile(self, user_id, data):
        profile = self._profiles.get(user_id)
        if not profile:
            raise ValueError("Perfil no encontrado")
        for key, value in data.items():
            if key in profile:
                profile[key] = value
        return profile

    def update_tour_completed(self, user_id):
        profile = self._profiles.get(user_id)
        if profile:
            profile["tour_completado"] = True

    # ── SOS Alerts ────────────────────────────────────────────────

    def create_alert(self, user_id, latitud, longitud, tipo_emergencia=""):
        profile = self._profiles.get(user_id, {})
        alert = {
            "id": str(uuid.uuid4()),
            "usuario_id": user_id,
            "latitud": latitud,
            "longitud": longitud,
            "tipo_emergencia": tipo_emergencia,
            "resuelta": False,
            "fecha_alerta": datetime.now().isoformat(),
            "nombre_usuario": profile.get("nombre_completo", "Desconocido"),
        }
        self._alerts.append(alert)
        return alert

    def get_active_alerts(self):
        return [a for a in self._alerts if not a["resuelta"]]

    def get_user_alerts(self, user_id):
        return [a for a in self._alerts if a["usuario_id"] == user_id]

    def resolve_alert(self, alert_id):
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["resuelta"] = True
                return True
        return False

    def get_user_active_alert(self, user_id):
        """Return the first non-resolved alert for this user, or None."""
        for alert in self._alerts:
            if alert["usuario_id"] == user_id and not alert["resuelta"]:
                return alert
        return None

    # ── Equipment ─────────────────────────────────────────────────

    def get_inventory(self):
        return [item.copy() for item in self._inventory]

    def assign_material(self, herramienta_id, usuario_asignado, cantidad):
        tool = next((t for t in self._inventory if t["id"] == herramienta_id), None)
        if not tool:
            raise ValueError("Herramienta no encontrada")
        if cantidad > tool["cantidad_disponible"]:
            raise ValueError(
                f"Stock insuficiente. Disponible: {tool['cantidad_disponible']}"
            )

        tool["cantidad_disponible"] -= cantidad

        profile = self._profiles.get(usuario_asignado, {})
        assignment = {
            "id": str(uuid.uuid4()),
            "herramienta_id": herramienta_id,
            "nombre_herramienta": tool["nombre_herramienta"],
            "usuario_asignado": usuario_asignado,
            "nombre_usuario": profile.get("nombre_completo", "Desconocido"),
            "cantidad": cantidad,
            "fecha_entrega": datetime.now().isoformat(),
        }
        self._assignments.append(assignment)
        return assignment

    def get_assignments(self):
        return [a.copy() for a in self._assignments]

    # ── Dashboard ─────────────────────────────────────────────────

    def get_total_volunteers(self):
        return len(self._profiles)

    def get_active_alerts_count(self):
        return len(self.get_active_alerts())

    def get_critical_tools(self):
        """Tools with < 30 % availability are considered critical."""
        critical = []
        for tool in self._inventory:
            if tool["cantidad_total"] > 0:
                ratio = tool["cantidad_disponible"] / tool["cantidad_total"]
                if ratio < 0.3:
                    critical.append(tool.copy())
        return critical

    def get_all_volunteers(self):
        return list(self._profiles.values())

    # ── Cuadrillas (S3) ──────────────────────────────────────────

    def get_cuadrilla(self, cuadrilla_id):
        """Return a single cuadrilla by ID, or None."""
        for cuadrilla in self._cuadrillas:
            if cuadrilla["id"] == cuadrilla_id:
                return cuadrilla.copy()
        return None

    def get_cuadrillas(self):
        """Return all cuadrillas."""
        return [c.copy() for c in self._cuadrillas]

    # ── Turnos (S3_HU01) ─────────────────────────────────────────

    def get_turnos_by_cuadrilla(self, cuadrilla_id):
        """Return all turnos for a given cuadrilla."""
        result = []
        for turno in self._turnos:
            if turno["cuadrilla_id"] == cuadrilla_id:
                entry = turno.copy()
                profile = self._profiles.get(turno["usuario_id"], {})
                entry["nombre_usuario"] = profile.get(
                    "nombre_completo", "Desconocido"
                )
                result.append(entry)
        return result

    def create_turno(self, usuario_id, cuadrilla_id, inicio_hora, fin_hora, dia_semana):
        """Insert a new turno. Returns the created record."""
        turno = {
            "id": str(uuid.uuid4()),
            "usuario_id": usuario_id,
            "cuadrilla_id": cuadrilla_id,
            "inicio_hora": inicio_hora,
            "fin_hora": fin_hora,
            "dia_semana": dia_semana,
        }
        self._turnos.append(turno)

        profile = self._profiles.get(usuario_id, {})
        result = turno.copy()
        result["nombre_usuario"] = profile.get("nombre_completo", "Desconocido")
        return result

    def delete_turno(self, turno_id):
        """Delete a turno by ID. Returns True on success."""
        for i, turno in enumerate(self._turnos):
            if turno["id"] == turno_id:
                self._turnos.pop(i)
                return True
        return False

    # ── Chat (S3_HU02) ───────────────────────────────────────────

    def get_mensajes_chat(self, cuadrilla_id, after_timestamp):
        """Return messages for a cuadrilla after the given timestamp.

        Pass an empty string to get all messages.
        """
        result = []
        for msg in self._mensajes:
            if msg["cuadrilla_id"] != cuadrilla_id:
                continue
            if after_timestamp and msg["timestamp"] <= after_timestamp:
                continue
            entry = msg.copy()
            profile = self._profiles.get(msg["usuario_id"], {})
            entry["nombre_usuario"] = profile.get(
                "nombre_completo", "Desconocido"
            )
            result.append(entry)
        result.sort(key=lambda m: m["timestamp"])
        return result

    def send_mensaje_chat(
        self, cuadrilla_id, usuario_id, texto_mensaje, es_alerta=False
    ):
        """Insert a chat message. Returns the created record."""
        mensaje = {
            "id": str(uuid.uuid4()),
            "cuadrilla_id": cuadrilla_id,
            "usuario_id": usuario_id,
            "texto_mensaje": texto_mensaje,
            "es_alerta": es_alerta,
            "timestamp": datetime.now().isoformat(),
        }
        self._mensajes.append(mensaje)

        profile = self._profiles.get(usuario_id, {})
        result = mensaje.copy()
        result["nombre_usuario"] = profile.get("nombre_completo", "Desconocido")
        return result
