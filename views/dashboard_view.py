"""
Dashboard View — Command center metrics (HU04).

Read-only view with KPI cards and active alert management.
Implements SRS §6.6: 'Marcar Resuelta' button for each active alert.
"""

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography


def build_dashboard_view(page: ft.Page, repository, user_id):
    """Return a Column with the dashboard interface."""

    alerts_list = ft.ListView(spacing=Spacing.SM, padding=Spacing.SM)

    # ── KPI Cards ─────────────────────────────────────────────────

    def _build_kpi_card(title: str, value: str, icon_name, color: str):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon_name, color=color, size=28),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Text(
                        value,
                        size=Typography.HEADING,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        title,
                        size=Typography.CAPTION,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
                spacing=Spacing.XS,
            ),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            border_radius=BorderRadius.LG,
            padding=ft.padding.all(Spacing.MD),
            expand=True,
        )

    volunteers_card = _build_kpi_card(
        "Voluntarios",
        str(repository.get_total_volunteers()),
        ft.icons.PEOPLE_ALT_ROUNDED,
        Colors.ACCENT_PRIMARY,
    )

    alerts_card = _build_kpi_card(
        "Alertas activas",
        str(repository.get_active_alerts_count()),
        ft.icons.WARNING_AMBER_ROUNDED,
        Colors.DANGER,
    )

    critical = repository.get_critical_tools()
    critical_card = _build_kpi_card(
        "Herram. críticas",
        str(len(critical)),
        ft.icons.BUILD_CIRCLE_OUTLINED,
        Colors.WARNING,
    )

    kpi_row = ft.Row(
        controls=[volunteers_card, alerts_card, critical_card],
        spacing=Spacing.SM,
    )

    # ── Critical tools detail ─────────────────────────────────────

    def _build_critical_section():
        items = repository.get_critical_tools()
        if not items:
            return ft.Container(
                content=ft.Text(
                    "Sin herramientas en nivel crítico",
                    color=Colors.TEXT_TERTIARY,
                    size=Typography.BODY,
                ),
                padding=Spacing.MD,
            )
        chips = []
        for tool in items:
            chips.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.WARNING, color=Colors.WARNING, size=16),
                            ft.Text(
                                f"{tool['nombre_herramienta']}: "
                                f"{tool['cantidad_disponible']}/{tool['cantidad_total']}",
                                size=Typography.BODY,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    bgcolor=Colors.BACKGROUND_TERTIARY,
                    border_radius=BorderRadius.SM,
                    padding=ft.padding.symmetric(
                        horizontal=Spacing.MD, vertical=Spacing.SM
                    ),
                )
            )
        return ft.Row(controls=chips, wrap=True, spacing=Spacing.SM, run_spacing=Spacing.SM)

    # ── Active alerts with resolve button ─────────────────────────

    def _load_alerts():
        alerts_list.controls.clear()
        active = repository.get_active_alerts()
        if not active:
            alerts_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No hay alertas activas",
                        color=Colors.TEXT_TERTIARY,
                        size=Typography.BODY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=Spacing.XL,
                )
            )
        else:
            for alert in active:
                alerts_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.LOCATION_ON,
                                    color=Colors.DANGER,
                                    size=20,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            alert.get("nombre_usuario") or "Usuario eliminado",
                                            size=Typography.BODY,
                                            color=Colors.TEXT_PRIMARY,
                                            weight=ft.FontWeight.W_500,
                                        ),
                                        ft.Text(
                                            f"({alert['latitud']:.4f}, "
                                            f"{alert['longitud']:.4f})",
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
                                ft.ElevatedButton(
                                    text="Resolver",
                                    icon=ft.icons.CHECK,
                                    on_click=lambda e, aid=alert["id"]: _resolve(aid),
                                    bgcolor=Colors.SUCCESS,
                                    color=Colors.TEXT_PRIMARY,
                                    height=36,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(
                                            radius=BorderRadius.SM
                                        ),
                                        padding=ft.padding.symmetric(horizontal=Spacing.MD),
                                    ),
                                ),
                            ],
                        ),
                        bgcolor=Colors.BACKGROUND_SECONDARY,
                        border_radius=BorderRadius.MD,
                        padding=ft.padding.all(Spacing.MD),
                    )
                )
        page.update()

    def _resolve(alert_id: str):
        repository.resolve_alert(alert_id)

        page.snack_bar = ft.SnackBar(
            content=ft.Text("Alerta marcada como resuelta", color=Colors.TEXT_PRIMARY),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            duration=2000,
        )
        page.snack_bar.open = True

        _refresh_all()

    def _refresh_all():
        # Update KPI values
        volunteers_card.content.controls[1].value = str(
            repository.get_total_volunteers()
        )
        alerts_card.content.controls[1].value = str(
            repository.get_active_alerts_count()
        )
        new_critical = repository.get_critical_tools()
        critical_card.content.controls[1].value = str(len(new_critical))

        _load_alerts()
        page.update()

    # ── Refresh button ────────────────────────────────────────────

    refresh_button = ft.IconButton(
        icon=ft.icons.REFRESH,
        icon_color=Colors.ACCENT_PRIMARY,
        tooltip="Actualizar datos",
        on_click=lambda e: _refresh_all(),
    )

    # ── Layout ────────────────────────────────────────────────────

    _load_alerts()

    return ft.Column(
        controls=[
            ft.Container(height=Spacing.MD),
            ft.Row(
                controls=[
                    ft.Text(
                        "Centro de Comando",
                        size=Typography.TITLE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_PRIMARY,
                        expand=True,
                    ),
                    refresh_button,
                ],
            ),
            ft.Container(height=Spacing.MD),
            kpi_row,
            ft.Container(height=Spacing.MD),
            ft.Text(
                "Suministros críticos",
                size=Typography.SUBTITLE,
                weight=ft.FontWeight.W_500,
                color=Colors.TEXT_PRIMARY,
            ),
            _build_critical_section(),
            ft.Container(height=Spacing.MD),
            ft.Divider(color=Colors.DIVIDER, height=1),
            ft.Container(height=Spacing.SM),
            ft.Text(
                "Alertas SOS activas",
                size=Typography.SUBTITLE,
                weight=ft.FontWeight.W_500,
                color=Colors.TEXT_PRIMARY,
            ),
            ft.Container(content=alerts_list, expand=True),
            # Extra bottom padding to clear NavigationBar on mobile
            ft.Container(height=Spacing.XXL),
        ],
        expand=True,
        scroll=ft.ScrollMode.ADAPTIVE,
    )
