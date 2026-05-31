"""
SOS View — Emergency alert history display.

Sprint 2: The SOS send button has been refactored to a global FAB in main.py
(S2_HU03). This module now provides the user's alert history display and
a reusable coordinate generation utility.

Geolocation simulation bounds (§4.2 — Concepción):
  Latitude:  -36.8000 to -36.8500
  Longitude: -73.0000 to -73.0800
"""

import random

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography


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
