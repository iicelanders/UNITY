"""
main.py — UNITY App entry point.

Orchestrates routing, authentication flow, and role-based navigation.
Implements:
  - §6.3: Dynamic NavigationBar based on user role
  - §6.4: Auth flow with profile check
  - §6.5: Mandatory onboarding before app access
  - §6.10: Persistent logout button in AppBar
  - S2_HU03: Global FAB S.O.S (persistent across all tabs)
  - S2_HU04: S.O.S confirmation dialog + async coordinate simulation
  - S2_HU01: Interactive onboarding tour with overlay (§4.4, §4.6)
  - §4.1: Returning user flow with read-only profile fields
"""

import random

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography
from core.mock_repository import MockRepository
from core.supabase_client import is_supabase_configured

# Choose data source: MockRepository for development, SupabaseRepository when ready
if is_supabase_configured():
    from core.supabase_client import SupabaseRepository
    repository = SupabaseRepository()
else:
    repository = MockRepository()

# ── Navigation definitions per role (§6.3) ─────────────────────
# Sprint 3: Added Turnos, Chat, and SOS Report tabs for all roles.
# SOS send remains a global FAB (S2_HU03); SOS Report is the enhanced view.

ROLE_TABS = {
    "voluntario": [
        {"label": "Turnos", "icon": ft.icons.CALENDAR_TODAY_OUTLINED, "route": "turnos"},
        {"label": "Chat", "icon": ft.icons.CHAT_OUTLINED, "route": "chat"},
        {"label": "Perfil", "icon": ft.icons.PERSON_OUTLINED, "route": "profile_display"},
    ],
    "lider_cuadrilla": [
        {"label": "Turnos", "icon": ft.icons.CALENDAR_TODAY_OUTLINED, "route": "turnos"},
        {"label": "Chat", "icon": ft.icons.CHAT_OUTLINED, "route": "chat"},
        {"label": "Equipos", "icon": ft.icons.BUILD_OUTLINED, "route": "equipment"},
        {"label": "Perfil", "icon": ft.icons.PERSON_OUTLINED, "route": "profile_display"},
    ],
    "comando": [
        {"label": "Turnos", "icon": ft.icons.CALENDAR_TODAY_OUTLINED, "route": "turnos"},
        {"label": "Chat", "icon": ft.icons.CHAT_OUTLINED, "route": "chat"},
        {"label": "Equipos", "icon": ft.icons.BUILD_OUTLINED, "route": "equipment"},
        {"label": "Dashboard", "icon": ft.icons.DASHBOARD_OUTLINED, "route": "dashboard"},
        {"label": "Perfil", "icon": ft.icons.PERSON_OUTLINED, "route": "profile_display"},
    ],
}


def main(page):
    # ── Page config ───────────────────────────────────────────────
    page.title = "UNITY — Voluntariado"
    page.window.width = 414
    page.window.height = 896
    page.bgcolor = Colors.BACKGROUND_PRIMARY
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=Colors.ACCENT_PRIMARY,
    )
    page.padding = 0

    # ── App state ─────────────────────────────────────────────────
    state = {
        "user_id": None,
        "user_email": None,
        "role": None,
        "cuadrilla_id": None,  # S3: loaded from profile on auth
        "current_tab": 0,
        "tour_active": False,
        "tour_step": 0,
    }

    # ── View builders (lazy imports to avoid circular deps) ──────

    def _build_content_for_route(route_name):
        """Build the content Column for a given tab route."""
        from views.equipment_view import build_equipment_view
        from views.dashboard_view import build_dashboard_view
        from views.profile_view import build_profile_display_view
        from views.turnos_view import build_turnos_view
        from views.chat_view import build_chat_view
        from views.sos_view import build_sos_report_view

        uid = state["user_id"]
        cid = state["cuadrilla_id"]
        rol = state.get("role", "voluntario")

        if route_name == "turnos":
            return build_turnos_view(page, repository, uid, cid, rol)
        if route_name == "chat":
            return build_chat_view(page, repository, uid, cid)
        if route_name == "equipment":
            return build_equipment_view(page, repository, uid)
        if route_name == "dashboard":
            return build_dashboard_view(page, repository, uid)
        if route_name == "sos_report":
            return build_sos_report_view(page, repository, uid, cid)
        if route_name == "profile_display":
            return build_profile_display_view(
                page, repository, uid,
                user_email=state.get("user_email", ""),
                viewer_role=rol,
            )
        return ft.Text("Vista no encontrada", color=Colors.DANGER)

    # ── Navigation ────────────────────────────────────────────────

    def _build_navigation_bar():
        """Build the bottom NavigationBar for the current role."""
        role = state["role"] or "voluntario"
        tabs = ROLE_TABS.get(role, ROLE_TABS["voluntario"])

        return ft.NavigationBar(
            selected_index=state["current_tab"],
            bgcolor=Colors.BACKGROUND_SECONDARY,
            indicator_color=Colors.ACCENT_PRIMARY,
            on_change=_handle_tab_change,
            destinations=[
                ft.NavigationBarDestination(
                    icon=tab["icon"],
                    label=tab["label"],
                )
                for tab in tabs
            ],
        )

    def _handle_tab_change(e):
        state["current_tab"] = e.control.selected_index
        _navigate_to_main_view()

    def _build_app_bar():
        """Persistent AppBar with logout (§6.10)."""
        profile = repository.get_profile(state["user_id"])
        name = profile["nombre_completo"] if profile else "UNITY"

        return ft.AppBar(
            leading=ft.Icon(ft.icons.PEOPLE_ALT_ROUNDED, color=Colors.ACCENT_PRIMARY),
            title=ft.Text(
                name,
                color=Colors.TEXT_PRIMARY,
                size=Typography.BODY_LARGE,
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            actions=[
                ft.IconButton(
                    icon=ft.icons.LOGOUT,
                    icon_color=Colors.TEXT_SECONDARY,
                    tooltip="Cerrar sesión",
                    on_click=_handle_logout,
                ),
            ],
        )

    def _handle_logout(e):
        repository.sign_out()
        state["user_id"] = None
        state["user_email"] = None
        state["role"] = None
        state["cuadrilla_id"] = None
        state["current_tab"] = 0
        state["tour_active"] = False
        state["tour_step"] = 0
        page.floating_action_button = None
        page.go("/auth")

    # ── S.O.S FAB (S2_HU03 — Global, persistent across tabs) ─────
    # Supports both sending new alerts AND cancelling active ones.

    def _build_sos_fab():
        """Create the S.O.S FAB — dynamically switches between Send and Cancel."""
        active_alert = None
        try:
            active_alert = repository.get_user_active_alert(state["user_id"])
            print(f"[SOS] Active alert check: {active_alert}")
        except Exception as exc:
            print(f"[SOS] Error checking active alert: {exc}")

        if active_alert:
            return ft.FloatingActionButton(
                icon=ft.icons.CANCEL_ROUNDED,
                bgcolor=Colors.WARNING_DARK,
                tooltip="Cancelar Alerta Activa",
                on_click=lambda e, a=active_alert: _handle_cancel_press(a),
                shape=ft.CircleBorder(),
            )

        return ft.FloatingActionButton(
            icon=ft.icons.WARNING_ROUNDED,
            bgcolor=Colors.DANGER,
            tooltip="Enviar Alerta S.O.S",
            on_click=_handle_sos_press,
            shape=ft.CircleBorder(),
        )

    def _refresh_sos_fab():
        """Rebuild the FAB and push it to the current page and view."""
        fab = _build_sos_fab()
        page.floating_action_button = fab
        if page.views:
            page.views[-1].floating_action_button = fab
        page.update()

    # ── S.O.S Report BottomSheet (S3_HU03 + HU04) ──────────────────

    def _handle_sos_press(e):
        """Handle FAB click — open BottomSheet with interactive report form."""
        if state["tour_active"]:
            # §4.6: absolute block during tour — do nothing
            return

        from core.sos_service import (
            TIPOS_EMERGENCIA,
            interpolar_coordenadas,
            crear_alerta_con_notificacion,
        )

        # ── Mutable state for the report form ────────────────────
        report_coords = {"lat": None, "lon": None}

        MAP_W = 400
        MAP_H = 400
        PIN_SIZE = 32

        # ── Form widgets ─────────────────────────────────────────

        tipo_dropdown = ft.Dropdown(
            label="Tipo de Emergencia",
            prefix_icon=ft.icons.WARNING_AMBER_OUTLINED,
            bgcolor=Colors.BACKGROUND_SECONDARY,
            border_color=Colors.BORDER,
            focused_border_color=Colors.ACCENT_PRIMARY,
            color=Colors.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
            border_radius=BorderRadius.MD,
            text_size=Typography.BODY_LARGE,
            width=MAP_W,
            options=[ft.dropdown.Option(t) for t in TIPOS_EMERGENCIA],
        )

        error_text = ft.Text(
            value="", color=Colors.DANGER, size=Typography.BODY, visible=False,
        )

        coords_text = ft.Text(
            "Toca el mapa para seleccionar ubicación",
            size=Typography.CAPTION,
            color=Colors.TEXT_TERTIARY,
            text_align=ft.TextAlign.CENTER,
        )

        pin_marker = ft.Container(
            content=ft.Icon(ft.icons.LOCATION_ON, color=Colors.DANGER, size=PIN_SIZE),
            left=MAP_W / 2 - PIN_SIZE / 2,
            top=MAP_H / 2 - PIN_SIZE,
            visible=False,
            animate_position=ft.animation.Animation(
                duration=200, curve=ft.AnimationCurve.EASE_OUT,
            ),
        )

        # ── Map click handler ────────────────────────────────────

        def _on_map_tap(e):
            report_coords["lat"], report_coords["lon"] = interpolar_coordenadas(
                e.local_x, e.local_y, MAP_W, MAP_H,
            )
            pin_marker.left = e.local_x - PIN_SIZE / 2
            pin_marker.top = e.local_y - PIN_SIZE
            pin_marker.visible = True
            coords_text.value = (
                f"Lat: {report_coords['lat']:.4f}, "
                f"Lon: {report_coords['lon']:.4f}"
            )
            coords_text.color = Colors.TEXT_SECONDARY
            error_text.visible = False
            page.update()

        # ── Grid lines for map background ────────────────────────

        grid_lines = []
        grid_count = 6
        for i in range(1, grid_count):
            grid_lines.append(ft.Container(
                width=1, height=MAP_H, bgcolor=Colors.DIVIDER,
                left=(MAP_W / grid_count) * i, top=0,
            ))
            grid_lines.append(ft.Container(
                width=MAP_W, height=1, bgcolor=Colors.DIVIDER,
                left=0, top=(MAP_H / grid_count) * i,
            ))

        map_container = ft.Container(
            content=ft.Stack(
                controls=[
                    # Map background image
                    ft.Image(
                        src="/mapa_concepcion.png",
                        width=MAP_W,
                        height=MAP_H,
                        fit=ft.ImageFit.COVER,
                    ),
                    *grid_lines,
                    ft.GestureDetector(
                        content=ft.Container(
                            width=MAP_W,
                            height=MAP_H,
                            bgcolor=ft.colors.TRANSPARENT,
                        ),
                        on_tap_down=_on_map_tap,
                    ),
                    pin_marker,
                ],
                width=MAP_W,
                height=MAP_H,
            ),
            width=MAP_W,
            height=MAP_H,
            bgcolor=Colors.BACKGROUND_TERTIARY,
            border_radius=BorderRadius.MD,
            border=ft.border.all(1, Colors.BORDER),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        # ── Send handler (dual transactional insert) ─────────────

        def _on_send_report(e):
            tipo = tipo_dropdown.value
            result = crear_alerta_con_notificacion(
                repository=repository,
                user_id=state["user_id"],
                latitud=report_coords["lat"],
                longitud=report_coords["lon"],
                tipo_emergencia=tipo,
                cuadrilla_id=state["cuadrilla_id"],
            )

            if not result.success:
                error_text.value = result.error
                error_text.visible = True
                page.update()
                return

            # Close sheet first
            bottom_sheet.open = False
            page.update()

            if result.alerta_creada_sin_chat:
                _show_sos_snackbar(
                    result.error, ft.icons.WARNING_AMBER, Colors.WARNING, 5000,
                )
            else:
                _show_sos_snackbar(
                    "Reporte de emergencia enviado exitosamente",
                    ft.icons.CHECK_CIRCLE, Colors.SUCCESS, 3000,
                )
            _refresh_sos_fab()

        def _on_cancel(e):
            bottom_sheet.open = False
            page.update()

        # ── BottomSheet layout ───────────────────────────────────

        sheet_content = ft.Container(
            content=ft.Column(
                controls=[
                    # Handle bar
                    ft.Container(
                        content=ft.Container(
                            width=40, height=4,
                            bgcolor=Colors.TEXT_TERTIARY,
                            border_radius=BorderRadius.FULL,
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=Spacing.SM, bottom=Spacing.MD),
                    ),
                    # Title
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.CRISIS_ALERT, color=Colors.DANGER, size=28),
                            ft.Text(
                                "  Reporte de Emergencia",
                                size=Typography.TITLE,
                                weight=ft.FontWeight.W_600,
                                color=Colors.DANGER,
                            ),
                        ],
                    ),
                    ft.Container(height=Spacing.MD),
                    # Tipo de emergencia
                    tipo_dropdown,
                    ft.Container(height=Spacing.MD),
                    # Map
                    ft.Text(
                        "Ubicación de la Emergencia",
                        size=Typography.SUBTITLE,
                        weight=ft.FontWeight.W_500,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Container(height=Spacing.SM),
                    map_container,
                    ft.Container(height=Spacing.XS),
                    coords_text,
                    ft.Container(height=Spacing.MD),
                    # Error display
                    error_text,
                    # Actions
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                text="Cancelar",
                                on_click=_on_cancel,
                                style=ft.ButtonStyle(
                                    color=Colors.TEXT_SECONDARY,
                                    shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                                    side=ft.BorderSide(1, Colors.BORDER),
                                ),
                                height=44,
                                expand=True,
                            ),
                            ft.ElevatedButton(
                                text="Enviar Reporte",
                                icon=ft.icons.SEND,
                                on_click=_on_send_report,
                                bgcolor=Colors.DANGER,
                                color=Colors.TEXT_ON_ACCENT,
                                height=44,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                                ),
                            ),
                        ],
                        spacing=Spacing.MD,
                    ),
                    ft.Container(height=Spacing.LG),
                ],
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colors.BACKGROUND_PRIMARY,
            border_radius=ft.border_radius.only(
                top_left=BorderRadius.LG,
                top_right=BorderRadius.LG,
            ),
            padding=ft.padding.symmetric(
                horizontal=Spacing.LG, vertical=Spacing.SM,
            ),
        )

        bottom_sheet = ft.BottomSheet(
            content=sheet_content,
            open=True,
        )
        page.overlay.append(bottom_sheet)
        page.update()

    def _show_sos_snackbar(message, icon, color, duration):
        """Themed SnackBar for SOS results."""
        page.snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(f"  {message}", color=Colors.TEXT_PRIMARY),
                ],
            ),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            duration=duration,
        )
        page.snack_bar.open = True
        page.update()

    # ── S.O.S Cancellation Dialog ─────────────────────────────────

    def _handle_cancel_press(active_alert):
        """Handle Cancel FAB click — show cancellation confirmation dialog."""
        if state["tour_active"]:
            return

        def _confirm_cancel(e):
            dialog.open = False
            page.update()
            _cancel_active_alert(active_alert["id"])

        def _dismiss_cancel(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.INFO_ROUNDED, color=Colors.WARNING, size=28),
                    ft.Text(
                        "  Cancelar Alerta Activa",
                        size=Typography.SUBTITLE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.WARNING,
                    ),
                ],
            ),
            content=ft.Container(
                content=ft.Text(
                    "¿Enviaste la alerta por accidente?\n\n"
                    "Al cancelar, se marcará como resuelta y "
                    "el Centro de Comando será notificado.",
                    size=Typography.BODY_LARGE,
                    color=Colors.TEXT_PRIMARY,
                ),
                width=300,
                padding=ft.padding.symmetric(vertical=Spacing.SM),
            ),
            actions=[
                ft.OutlinedButton(
                    text="Mantener activa",
                    on_click=_dismiss_cancel,
                    style=ft.ButtonStyle(
                        color=Colors.TEXT_SECONDARY,
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                        side=ft.BorderSide(1, Colors.BORDER),
                    ),
                    height=42,
                ),
                ft.ElevatedButton(
                    text="Cancelar alerta",
                    icon=ft.icons.CANCEL,
                    on_click=_confirm_cancel,
                    bgcolor=Colors.WARNING_DARK,
                    color=Colors.TEXT_ON_ACCENT,
                    height=42,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=Colors.BACKGROUND_PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.LG),
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def _cancel_active_alert(alert_id):
        """Mark an active alert as resolved (cancelled by user)."""
        try:
            print(f"[SOS] Cancelling alert {alert_id}")
            repository.resolve_alert(alert_id)
            print("[SOS] Alert cancelled successfully")
            page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE, color=Colors.SUCCESS, size=20),
                        ft.Text(
                            "  Alerta cancelada correctamente",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ],
                ),
                bgcolor=Colors.BACKGROUND_SECONDARY,
                duration=3000,
            )
            page.snack_bar.open = True
        except Exception as exc:
            print(f"[SOS] Error cancelling alert: {exc}")
            page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.ERROR_OUTLINE, color=Colors.DANGER, size=20),
                        ft.Text(
                            "  Error al cancelar. Intenta de nuevo.",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ],
                ),
                bgcolor=Colors.BACKGROUND_SECONDARY,
                duration=3000,
            )
            page.snack_bar.open = True
        _refresh_sos_fab()

    # ── Interactive Tour (S2_HU01 — §4.4, §4.6) ─────────────────

    tour_overlay = ft.Container(visible=False)  # Placeholder, rebuilt dynamically

    def _start_tour():
        """Activate the onboarding tour overlay."""
        state["tour_active"] = True
        state["tour_step"] = 0
        _build_tour_step()

    def _build_tour_step():
        """Build the current tour step overlay."""
        step = state["tour_step"]

        tour_texts = [
            {
                "title": "Emergencias de Terreno",
                "body": "Presiona este botón para enviar tu ubicación "
                        "exacta al Comando de forma inmediata.",
                "icon": ft.icons.WARNING_ROUNDED,
                "icon_color": Colors.DANGER,
            },
            {
                "title": "Tu Información",
                "body": "Usa este menú inferior para acceder a tus datos, "
                        "estado y asignaciones.",
                "icon": ft.icons.PERSON_OUTLINED,
                "icon_color": Colors.ACCENT_PRIMARY,
            },
        ]

        if step >= len(tour_texts):
            _end_tour()
            return

        info = tour_texts[step]
        is_last = step == len(tour_texts) - 1

        def _advance(e):
            state["tour_step"] += 1
            _build_tour_step()

        def _skip_tour(e):
            _end_tour()

        # Build the BottomSheet-like card
        tour_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    info["icon"],
                                    color=info["icon_color"],
                                    size=36,
                                ),
                                bgcolor=Colors.BACKGROUND_TERTIARY,
                                border_radius=BorderRadius.FULL,
                                width=56,
                                height=56,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        info["title"],
                                        size=Typography.SUBTITLE,
                                        weight=ft.FontWeight.W_600,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        f"Paso {step + 1} de {len(tour_texts)}",
                                        size=Typography.CAPTION,
                                        color=Colors.TEXT_TERTIARY,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=Spacing.MD,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Text(
                        info["body"],
                        size=Typography.BODY_LARGE,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(height=Spacing.MD),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                text="Saltar introducción",
                                on_click=_skip_tour,
                                style=ft.ButtonStyle(
                                    color=Colors.TEXT_TERTIARY,
                                ),
                            ),
                            ft.ElevatedButton(
                                text="Finalizar" if is_last else "Siguiente",
                                icon=ft.icons.CHECK if is_last else ft.icons.ARROW_FORWARD,
                                on_click=_advance,
                                bgcolor=Colors.ACCENT_PRIMARY,
                                color=Colors.TEXT_ON_ACCENT,
                                height=42,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(
                                        radius=BorderRadius.MD
                                    ),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
            ),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            border_radius=ft.border_radius.only(
                top_left=BorderRadius.XL,
                top_right=BorderRadius.XL,
            ),
            padding=ft.padding.all(Spacing.LG),
            margin=ft.margin.only(top=Spacing.SM),
        )

        # Full-screen overlay that blocks interaction (QA_02, §4.6)
        tour_overlay.content = ft.Column(
            controls=[
                ft.Container(expand=True),  # Spacer pushes card to bottom
                tour_card,
            ],
            expand=True,
        )
        tour_overlay.bgcolor = "#000000B0"  # Semi-transparent dark overlay
        tour_overlay.visible = True
        tour_overlay.expand = True
        # Use on_click on the overlay spacer to advance (any click advances)
        page.update()

    def _end_tour():
        """Close the tour and persist the completed state (§4.4)."""
        state["tour_active"] = False
        state["tour_step"] = 0
        tour_overlay.visible = False
        tour_overlay.content = None

        # Persist tour_completado = true asynchronously
        try:
            repository.update_tour_completed(state["user_id"])
        except Exception:
            pass  # Best-effort persistence; don't block user

        page.update()

    # ── Route handler ─────────────────────────────────────────────

    def route_change(e):
        page.views.clear()
        route = page.route

        if route == "/auth" or not state["user_id"]:
            page.floating_action_button = None
            from views.auth_view import build_auth_view
            page.views.append(
                build_auth_view(page, repository, _on_auth_success)
            )
        elif route == "/onboarding":
            page.floating_action_button = None
            from views.profile_view import build_profile_view
            page.views.append(
                build_profile_view(
                    page, repository, state["user_id"], _on_profile_complete
                )
            )
        else:
            # Main app view with tabs + FAB
            _navigate_to_main_view()
            return  # _navigate_to_main_view handles page.update

        page.update()

    def _navigate_to_main_view():
        """Build the main view with content based on current tab."""
        role = state["role"] or "voluntario"
        tabs = ROLE_TABS.get(role, ROLE_TABS["voluntario"])
        idx = min(state["current_tab"], len(tabs) - 1)
        current_route = tabs[idx]["route"]

        content = _build_content_for_route(current_route)

        # Set up FAB S.O.S (S2_HU03)
        page.floating_action_button = _build_sos_fab()
        page.floating_action_button_location = (
            ft.FloatingActionButtonLocation.CENTER_FLOAT
        )

        # Reset the tour overlay reference for this view rebuild
        tour_overlay.visible = state["tour_active"]

        main_view = ft.View(
            route="/main",
            bgcolor=Colors.BACKGROUND_PRIMARY,
            appbar=_build_app_bar(),
            navigation_bar=_build_navigation_bar(),
            controls=[
                ft.Stack(
                    controls=[
                        # Main content layer
                        ft.Container(
                            content=content,
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=Spacing.MD),
                        ),
                        # Tour overlay layer (on top when active)
                        tour_overlay,
                    ],
                    expand=True,
                ),
            ],
            floating_action_button=_build_sos_fab(),
            floating_action_button_location=ft.FloatingActionButtonLocation.CENTER_FLOAT,
            padding=0,
        )
        page.views.clear()
        page.views.append(main_view)
        page.update()

    # ── Auth callbacks ────────────────────────────────────────────

    def _on_auth_success(user_id):
        """Called after successful login/register (§6.4)."""
        state["user_id"] = user_id

        # Try to get email from repository for profile display
        try:
            current_session = repository._client.auth.get_session() if hasattr(repository, '_client') else None
            if current_session and hasattr(current_session, 'user') and current_session.user:
                state["user_email"] = current_session.user.email or ""
        except Exception:
            pass

        # For MockRepository: find email from _users dict
        if hasattr(repository, '_users'):
            for email_key, user_data in repository._users.items():
                if user_data.get("id") == user_id:
                    state["user_email"] = email_key
                    break

        profile = repository.get_profile(user_id)

        if profile:
            state["role"] = profile.get("rol", "voluntario")
            state["cuadrilla_id"] = profile.get("cuadrilla_id")  # S3
            state["current_tab"] = 0

            # Check if tour needs to be shown (§4.4)
            if not profile.get("tour_completado", False):
                page.go("/main")
                _start_tour()
            else:
                page.go("/main")
        else:
            page.go("/onboarding")

    def _on_profile_complete():
        """Called after mandatory onboarding wizard (§6.5)."""
        profile = repository.get_profile(state["user_id"])
        state["role"] = profile.get("rol", "voluntario") if profile else "voluntario"
        state["current_tab"] = 0

        # After onboarding, always start the tour (§S2_HU01)
        page.go("/main")
        _start_tour()

    # ── Start ─────────────────────────────────────────────────────

    page.on_route_change = route_change
    page.go("/auth")


ft.app(target=main, assets_dir="assets")
