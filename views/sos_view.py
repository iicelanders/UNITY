"""
SOS View — Emergency alert history and enhanced emergency reporting.

Sprint 2: The SOS send button has been refactored to a global FAB in main.py
(S2_HU03). This module provides the user's alert history display and
a reusable coordinate generation utility.

Sprint 3 (S3_HU03): Added ``build_sos_report_view`` — interactive map with
clickable pin, emergency type dropdown, dual-transactional send with
partial-failure handling per SRS §2.4, and input validation via sos_service.

Geolocation simulation bounds (§4.2 — Concepción):
  Latitude:  -36.8000 to -36.8500
  Longitude: -73.0000 to -73.0800
"""

import random

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography
from core.sos_service import (
    TIPOS_EMERGENCIA,
    crear_alerta_con_notificacion,
    interpolar_coordenadas,
)


def generate_simulated_coordinates():
    """Generate random coordinates within Concepción bounds (§4.2).

    Returns:
        tuple: (latitud, longitud) as floats.
    """
    lat = random.uniform(-36.8000, -36.8500)
    lon = random.uniform(-73.0000, -73.0800)
    return lat, lon


def build_sos_view(page, repository, user_id):
    """Return a Column with the SOS alert history (embedded in the main View)."""

    alerts_list = ft.ListView(expand=True, spacing=Spacing.SM, padding=Spacing.MD)

    def _load_user_alerts():
        alerts_list.controls.clear()
        alerts = repository.get_user_alerts(user_id)
        if not alerts:
            alerts_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No tienes alertas registradas",
                        color=Colors.TEXT_TERTIARY,
                        size=Typography.BODY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=Spacing.XL,
                )
            )
        else:
            for alert in reversed(alerts):
                status_color = Colors.SUCCESS if alert["resuelta"] else Colors.WARNING
                status_text = "Resuelta" if alert["resuelta"] else "Activa"
                alerts_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.LOCATION_ON,
                                    color=status_color,
                                    size=20,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"Lat: {alert['latitud']:.4f}, "
                                            f"Lon: {alert['longitud']:.4f}",
                                            size=Typography.BODY,
                                            color=Colors.TEXT_PRIMARY,
                                        ),
                                        ft.Text(
                                            alert["fecha_alerta"][:19].replace("T", " "),
                                            size=Typography.CAPTION,
                                            color=Colors.TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        status_text,
                                        size=Typography.CAPTION,
                                        color=status_color,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    bgcolor=Colors.BACKGROUND_TERTIARY,
                                    border_radius=BorderRadius.FULL,
                                    padding=ft.padding.symmetric(
                                        horizontal=Spacing.SM, vertical=Spacing.XS
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        bgcolor=Colors.BACKGROUND_SECONDARY,
                        border_radius=BorderRadius.MD,
                        padding=ft.padding.all(Spacing.MD),
                    )
                )
        page.update()

    # ── Layout ────────────────────────────────────────────────────

    _load_user_alerts()

    return ft.Column(
        controls=[
            ft.Container(height=Spacing.LG),
            ft.Text(
                "Historial de Emergencias",
                size=Typography.TITLE,
                weight=ft.FontWeight.W_600,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Text(
                "Usa el botón S.O.S flotante para enviar alertas",
                size=Typography.BODY,
                color=Colors.TEXT_SECONDARY,
            ),
            ft.Container(height=Spacing.MD),
            ft.Divider(color=Colors.DIVIDER, height=1),
            ft.Container(height=Spacing.MD),
            ft.Text(
                "Tus alertas",
                size=Typography.SUBTITLE,
                weight=ft.FontWeight.W_500,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Container(
                content=alerts_list,
                expand=True,
            ),
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


# ══════════════════════════════════════════════════════════════════
#  S3_HU03 — Enhanced Emergency Report View
# ══════════════════════════════════════════════════════════════════

# ── Private UI Helpers (componentization per >20-line rule) ──────

_MAP_WIDTH = 400
_MAP_HEIGHT = 400
_GRID_LINE_COUNT = 6


def _build_pin_marker(pos_x, pos_y):
    """Return a positioned pin icon for the map overlay.

    Args:
        pos_x: Horizontal offset in pixels (from left).
        pos_y: Vertical offset in pixels (from top).

    Returns:
        ft.Container wrapping the pin icon, positioned at (pos_x, pos_y).
    """
    pin_size = 32
    return ft.Container(
        content=ft.Icon(
            ft.icons.LOCATION_ON,
            color=Colors.DANGER,
            size=pin_size,
        ),
        left=pos_x - pin_size / 2,
        top=pos_y - pin_size,
        animate_position=ft.animation.Animation(
            duration=200,
            curve=ft.AnimationCurve.EASE_OUT,
        ),
    )


def _build_map_container(on_tap_handler, pin_marker, coordinates_text):
    """Construct the interactive map area with grid overlay and movable pin.

    Args:
        on_tap_handler: Callback invoked with TapEvent when user clicks the map.
        pin_marker: ft.Container returned by ``_build_pin_marker``.
        coordinates_text: ft.Text widget displaying current lat/lon.

    Returns:
        ft.Column containing the map title, map area and coordinates display.
    """
    # Grid lines to simulate a map background
    grid_controls = []

    # Vertical lines
    for i in range(1, _GRID_LINE_COUNT):
        offset_x = (_MAP_WIDTH / _GRID_LINE_COUNT) * i
        grid_controls.append(
            ft.Container(
                width=1,
                height=_MAP_HEIGHT,
                bgcolor=Colors.DIVIDER,
                left=offset_x,
                top=0,
            )
        )

    # Horizontal lines
    for i in range(1, _GRID_LINE_COUNT):
        offset_y = (_MAP_HEIGHT / _GRID_LINE_COUNT) * i
        grid_controls.append(
            ft.Container(
                width=_MAP_WIDTH,
                height=1,
                bgcolor=Colors.DIVIDER,
                left=0,
                top=offset_y,
            )
        )

    map_stack = ft.Stack(
        controls=[
            # Map background image
            ft.Image(
                src="/mapa_concepcion.png",
                width=_MAP_WIDTH,
                height=_MAP_HEIGHT,
                fit=ft.ImageFit.COVER,
            ),
            # Grid layer
            *grid_controls,
            # Clickable gesture layer (must span full area)
            ft.GestureDetector(
                content=ft.Container(
                    width=_MAP_WIDTH,
                    height=_MAP_HEIGHT,
                    bgcolor=ft.colors.TRANSPARENT,
                ),
                on_tap_down=on_tap_handler,
            ),
            # Pin layer
            pin_marker,
        ],
        width=_MAP_WIDTH,
        height=_MAP_HEIGHT,
    )

    map_container = ft.Container(
        content=map_stack,
        width=_MAP_WIDTH,
        height=_MAP_HEIGHT,
        bgcolor=Colors.BACKGROUND_TERTIARY,
        border_radius=BorderRadius.MD,
        border=ft.border.all(1, Colors.BORDER),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    return ft.Column(
        controls=[
            ft.Text(
                "Ubicación de la Emergencia",
                size=Typography.SUBTITLE,
                weight=ft.FontWeight.W_500,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Container(height=Spacing.SM),
            map_container,
            ft.Container(height=Spacing.XS),
            coordinates_text,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )


# ── Main Report View ─────────────────────────────────────────────

def build_sos_report_view(page, repository, user_id, cuadrilla_id):
    """Return a Column with the enhanced SOS emergency report form.

    Includes:
      - Emergency type dropdown
      - Interactive map with clickable pin for location selection
      - Send button with dual-transactional insert and partial failure handling
      - Alert history list

    The view is "dumb" — all validation, interpolation and persistence
    are delegated to ``core.sos_service``.

    Args:
        page: ft.Page reference for SnackBar and update calls.
        repository: DataRepository implementation.
        user_id: UUID string of the current user.
        cuadrilla_id: UUID string of the user's cuadrilla (may be None).

    Returns:
        ft.Column ready to be embedded in a ft.View.
    """

    # ── Mutable state (immutable-by-default; these are the only exceptions) ──
    selected_lat = None
    selected_lon = None

    # ── UI Widgets ────────────────────────────────────────────────

    tipo_emergencia_dropdown = ft.Dropdown(
        label="Tipo de Emergencia",
        prefix_icon=ft.icons.WARNING_AMBER_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
        width=_MAP_WIDTH,
        options=[ft.dropdown.Option(tipo) for tipo in TIPOS_EMERGENCIA],
    )

    error_text = ft.Text(
        value="",
        color=Colors.DANGER,
        size=Typography.BODY,
        visible=False,
    )

    coordinates_text = ft.Text(
        "Toca el mapa para seleccionar ubicación",
        size=Typography.CAPTION,
        color=Colors.TEXT_TERTIARY,
        text_align=ft.TextAlign.CENTER,
    )

    pin_marker = _build_pin_marker(_MAP_WIDTH / 2, _MAP_HEIGHT / 2)
    pin_marker.visible = False  # Hidden until first click

    # ── Event Handlers ────────────────────────────────────────────

    def _on_map_tap(e):
        """Handle tap on the map area: interpolate coords and move pin."""
        nonlocal selected_lat, selected_lon

        click_x = e.local_x
        click_y = e.local_y

        # Delegate interpolation to service layer
        selected_lat, selected_lon = interpolar_coordenadas(
            click_x, click_y, _MAP_WIDTH, _MAP_HEIGHT
        )

        # Update pin position
        pin_size = 32
        pin_marker.left = click_x - pin_size / 2
        pin_marker.top = click_y - pin_size
        pin_marker.visible = True

        # Update coordinate display
        coordinates_text.value = (
            f"Lat: {selected_lat:.4f}, Lon: {selected_lon:.4f}"
        )
        coordinates_text.color = Colors.TEXT_SECONDARY

        # Clear any previous validation error
        error_text.visible = False

        page.update()

    def _show_snackbar(message, icon, icon_color):
        """Display a styled SnackBar (consistent with project pattern)."""
        page.snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=icon_color, size=20),
                    ft.Text(
                        f"  {message}",
                        color=Colors.TEXT_PRIMARY,
                    ),
                ],
            ),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            duration=3000,
        )
        page.snack_bar.open = True

    def _on_send_report(e):
        """Validate and send the emergency report via sos_service."""
        nonlocal selected_lat, selected_lon
        tipo = tipo_emergencia_dropdown.value

        result = crear_alerta_con_notificacion(
            repository=repository,
            user_id=user_id,
            latitud=selected_lat,
            longitud=selected_lon,
            tipo_emergencia=tipo,
            cuadrilla_id=cuadrilla_id,
        )

        if not result.success:
            error_text.value = result.error
            error_text.visible = True
            page.update()
            return

        if result.alerta_creada_sin_chat:
            _show_snackbar(
                result.error,
                ft.icons.WARNING_AMBER,
                Colors.WARNING,
            )
        else:
            _show_snackbar(
                "Reporte de emergencia enviado exitosamente",
                ft.icons.CHECK_CIRCLE,
                Colors.SUCCESS,
            )

        # Reset form state
        tipo_emergencia_dropdown.value = None
        pin_marker.visible = False
        selected_lat = None
        selected_lon = None
        coordinates_text.value = "Toca el mapa para seleccionar ubicación"
        coordinates_text.color = Colors.TEXT_TERTIARY
        error_text.visible = False

        _load_alert_history()
        page.update()

    # ── Map Section ───────────────────────────────────────────────

    map_section = _build_map_container(_on_map_tap, pin_marker, coordinates_text)

    # ── Send Button ───────────────────────────────────────────────

    send_button = ft.ElevatedButton(
        text="Enviar Reporte de Emergencia",
        icon=ft.icons.CRISIS_ALERT,
        bgcolor=Colors.DANGER,
        color=Colors.TEXT_ON_ACCENT,
        width=_MAP_WIDTH,
        height=48,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
        ),
        on_click=_on_send_report,
    )

    # ── Alert History ─────────────────────────────────────────────

    alerts_list = ft.ListView(
        expand=True, spacing=Spacing.SM, padding=Spacing.MD
    )

    def _load_alert_history():
        """Populate the alert history list from the repository."""
        alerts_list.controls.clear()
        alerts = repository.get_user_alerts(user_id)

        if not alerts:
            alerts_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No tienes alertas registradas",
                        color=Colors.TEXT_TERTIARY,
                        size=Typography.BODY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=Spacing.XL,
                )
            )
            return

        for alert in reversed(alerts):
            status_color = Colors.SUCCESS if alert["resuelta"] else Colors.WARNING
            status_text = "Resuelta" if alert["resuelta"] else "Activa"
            tipo_label = alert.get("tipo_emergencia", "")

            alerts_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.icons.LOCATION_ON,
                                color=status_color,
                                size=20,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        tipo_label if tipo_label else "Alerta SOS",
                                        size=Typography.BODY,
                                        weight=ft.FontWeight.W_600,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        f"Lat: {alert['latitud']:.4f}, "
                                        f"Lon: {alert['longitud']:.4f}",
                                        size=Typography.CAPTION,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        alert["fecha_alerta"][:19].replace("T", " "),
                                        size=Typography.CAPTION,
                                        color=Colors.TEXT_TERTIARY,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    status_text,
                                    size=Typography.CAPTION,
                                    color=status_color,
                                    weight=ft.FontWeight.W_600,
                                ),
                                bgcolor=Colors.BACKGROUND_TERTIARY,
                                border_radius=BorderRadius.FULL,
                                padding=ft.padding.symmetric(
                                    horizontal=Spacing.SM, vertical=Spacing.XS
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    bgcolor=Colors.BACKGROUND_SECONDARY,
                    border_radius=BorderRadius.MD,
                    padding=ft.padding.all(Spacing.MD),
                )
            )

    # Initial load
    _load_alert_history()

    # ── Layout Assembly ───────────────────────────────────────────

    return ft.Column(
        controls=[
            # Section header
            ft.Container(height=Spacing.LG),
            ft.Text(
                "Reporte de Emergencia",
                size=Typography.TITLE,
                weight=ft.FontWeight.W_600,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Text(
                "Selecciona el tipo y ubicación de la emergencia",
                size=Typography.BODY,
                color=Colors.TEXT_SECONDARY,
            ),
            ft.Container(height=Spacing.MD),

            # Emergency type dropdown
            tipo_emergencia_dropdown,
            ft.Container(height=Spacing.MD),

            # Map section (title + grid + pin + coordinates)
            map_section,
            ft.Container(height=Spacing.MD),

            # Send button
            send_button,

            # Validation error display
            error_text,
            ft.Container(height=Spacing.MD),

            # Divider between report form and history
            ft.Divider(color=Colors.DIVIDER, height=1),
            ft.Container(height=Spacing.MD),

            # Alert history
            ft.Text(
                "Historial de Alertas",
                size=Typography.SUBTITLE,
                weight=ft.FontWeight.W_500,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Container(
                content=alerts_list,
                expand=True,
            ),

            # Bottom spacer
            ft.Container(height=Spacing.XXL),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
