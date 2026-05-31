"""
Equipment View — Tool inventory and material assignment (HU03 / S2_HU02).

Implements SRS §6.8: sequential insert in entregas_material then
update cantidad_disponible in inventario_herramientas.

Sprint 2 additions:
  - AlertDialog "ticket" receipt replaces SnackBar (§S2_HU02)
  - Network error handling with AlertDialog (§5.2)
  - Form state preservation on error (§5.3)
"""

from datetime import datetime

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography


def build_equipment_view(page, repository, user_id):
    """Return a Column with the equipment management interface."""

    inventory_list = ft.ListView(expand=True, spacing=Spacing.SM, padding=Spacing.SM)
    assignment_list = ft.ListView(expand=True, spacing=Spacing.SM, padding=Spacing.SM)

    # ── Inventory Tab ─────────────────────────────────────────────

    def _load_inventory():
        inventory_list.controls.clear()
        tools = repository.get_inventory()
        if not tools:
            inventory_list.controls.append(
                ft.Text(
                    "Sin herramientas en inventario",
                    color=Colors.TEXT_TERTIARY,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        else:
            for tool in tools:
                total = tool["cantidad_total"]
                available = tool["cantidad_disponible"]
                ratio = available / total if total > 0 else 0
                bar_color = (
                    Colors.DANGER if ratio < 0.3
                    else Colors.WARNING if ratio < 0.6
                    else Colors.SUCCESS
                )
                inventory_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.icons.BUILD_OUTLINED,
                                            color=Colors.ACCENT_PRIMARY,
                                            size=20,
                                        ),
                                        ft.Text(
                                            tool["nombre_herramienta"],
                                            size=Typography.BODY_LARGE,
                                            weight=ft.FontWeight.W_500,
                                            color=Colors.TEXT_PRIMARY,
                                            expand=True,
                                        ),
                                        ft.Text(
                                            f"{available}/{total}",
                                            size=Typography.BODY,
                                            color=bar_color,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                    ],
                                ),
                                ft.ProgressBar(
                                    value=ratio,
                                    color=bar_color,
                                    bgcolor=Colors.BACKGROUND_TERTIARY,
                                    bar_height=6,
                                    border_radius=BorderRadius.SM,
                                ),
                            ],
                            spacing=Spacing.SM,
                        ),
                        bgcolor=Colors.BACKGROUND_SECONDARY,
                        border_radius=BorderRadius.MD,
                        padding=ft.padding.all(Spacing.MD),
                    )
                )
        page.update()

    # ── Assignment Form ───────────────────────────────────────────

    tool_dropdown = ft.Dropdown(
        label="Herramienta",
        prefix_icon=ft.icons.HANDYMAN_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
    )

    volunteer_dropdown = ft.Dropdown(
        label="Asignar a",
        prefix_icon=ft.icons.PERSON_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
    )

    quantity_field = ft.TextField(
        label="Cantidad",
        prefix_icon=ft.icons.NUMBERS,
        keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
    )

    assign_error = ft.Text(
        value="", color=Colors.DANGER, size=Typography.BODY, visible=False
    )

    def _populate_dropdowns():
        tools = repository.get_inventory()
        tool_dropdown.options = [
            ft.dropdown.Option(
                key=t["id"],
                text=f"{t['nombre_herramienta']} (disp: {t['cantidad_disponible']})",
            )
            for t in tools
            if t["cantidad_disponible"] > 0
        ]
        volunteers = repository.get_all_volunteers()
        volunteer_dropdown.options = [
            ft.dropdown.Option(key=v["id"], text=v["nombre_completo"])
            for v in volunteers
        ]
        page.update()

    # ── Helper: find display names from dropdown options ──────────

    def _get_tool_display_name(tool_id):
        """Resolve tool_id to its herramienta name from dropdown options."""
        for opt in (tool_dropdown.options or []):
            if opt.key == tool_id:
                # Strip the "(disp: X)" suffix to get clean name
                text = opt.text or ""
                paren_idx = text.rfind(" (disp:")
                return text[:paren_idx] if paren_idx > 0 else text
        return "Herramienta"

    def _get_volunteer_display_name(vol_id):
        """Resolve vol_id to volunteer name from dropdown options."""
        for opt in (volunteer_dropdown.options or []):
            if opt.key == vol_id:
                return opt.text or "Voluntario"
        return "Voluntario"

    # ── Ticket AlertDialog (S2_HU02) ─────────────────────────────

    def _show_ticket_dialog(tool_name, cantidad, volunteer_name):
        """Show a premium receipt-style AlertDialog after successful assignment."""
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        def close_dialog(e):
            dialog.open = False
            page.update()

        ticket_content = ft.Container(
            content=ft.Column(
                controls=[
                    # Ticket header with check icon
                    ft.Container(
                        content=ft.Icon(
                            ft.icons.CHECK_CIRCLE_ROUNDED,
                            color=Colors.SUCCESS,
                            size=48,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Text(
                        "Asignación Exitosa",
                        size=Typography.TITLE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_PRIMARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=Spacing.MD),
                    ft.Divider(color=Colors.DIVIDER, height=1),
                    ft.Container(height=Spacing.MD),
                    # Ticket details
                    _ticket_row(ft.icons.BUILD_OUTLINED, "Material", tool_name),
                    ft.Container(height=Spacing.SM),
                    _ticket_row(ft.icons.INVENTORY_2_OUTLINED, "Cantidad", str(cantidad)),
                    ft.Container(height=Spacing.SM),
                    _ticket_row(ft.icons.PERSON_OUTLINED, "Voluntario", volunteer_name),
                    ft.Container(height=Spacing.SM),
                    _ticket_row(ft.icons.CALENDAR_TODAY, "Fecha", fecha),
                    ft.Container(height=Spacing.MD),
                    ft.Divider(color=Colors.DIVIDER, height=1),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            border_radius=BorderRadius.LG,
            padding=ft.padding.all(Spacing.LG),
            width=320,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.RECEIPT_LONG, color=Colors.ACCENT_PRIMARY, size=24),
                    ft.Text(
                        "  Comprobante de Entrega",
                        size=Typography.SUBTITLE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.ACCENT_PRIMARY,
                    ),
                ],
            ),
            content=ticket_content,
            actions=[
                ft.ElevatedButton(
                    text="Cerrar",
                    icon=ft.icons.CLOSE,
                    on_click=close_dialog,
                    bgcolor=Colors.ACCENT_PRIMARY,
                    color=Colors.TEXT_ON_ACCENT,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor=Colors.BACKGROUND_PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.LG),
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    def _ticket_row(icon_name, label, value):
        """Build a single row for the ticket receipt."""
        return ft.Row(
            controls=[
                ft.Icon(icon_name, color=Colors.ACCENT_PRIMARY, size=18),
                ft.Text(
                    f"{label}:",
                    size=Typography.BODY,
                    color=Colors.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500,
                    width=90,
                ),
                ft.Text(
                    value,
                    size=Typography.BODY_LARGE,
                    color=Colors.TEXT_PRIMARY,
                    weight=ft.FontWeight.W_600,
                    expand=True,
                ),
            ],
            spacing=Spacing.SM,
        )

    # ── Network Error AlertDialog (§5.2) ─────────────────────────

    def _show_network_error_dialog():
        """Show a high-priority error dialog for network/server failures."""
        def close_error(e):
            error_dialog.open = False
            page.update()

        error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.WIFI_OFF_ROUNDED, color=Colors.DANGER, size=28),
                    ft.Text(
                        "  Falla de Conexión con el Servidor",
                        size=Typography.SUBTITLE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.DANGER,
                    ),
                ],
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Los cambios no pudieron ser sincronizados "
                            "con la base de datos.",
                            size=Typography.BODY_LARGE,
                            color=Colors.TEXT_PRIMARY,
                        ),
                        ft.Container(height=Spacing.SM),
                        ft.Text(
                            "Verifica tu conexión a internet e intenta "
                            "de nuevo. Tu formulario se ha conservado.",
                            size=Typography.BODY,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                ),
                width=300,
                padding=ft.padding.symmetric(vertical=Spacing.SM),
            ),
            actions=[
                ft.ElevatedButton(
                    text="Entendido",
                    icon=ft.icons.CHECK,
                    on_click=close_error,
                    bgcolor=Colors.DANGER,
                    color=Colors.TEXT_ON_ACCENT,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor=Colors.BACKGROUND_PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.LG),
        )

        page.dialog = error_dialog
        error_dialog.open = True
        page.update()

    # ── Assignment handler ────────────────────────────────────────

    def handle_assign(e):
        tool_id = tool_dropdown.value
        vol_id = volunteer_dropdown.value
        qty_str = (quantity_field.value or "").strip()

        if not tool_id or not vol_id or not qty_str:
            assign_error.value = "Completa todos los campos"
            assign_error.visible = True
            page.update()
            return

        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            assign_error.value = "Ingresa una cantidad válida"
            assign_error.visible = True
            page.update()
            return

        # Resolve display names BEFORE the call (for the ticket)
        tool_name = _get_tool_display_name(tool_id)
        volunteer_name = _get_volunteer_display_name(vol_id)

        try:
            repository.assign_material(
                herramienta_id=tool_id,
                usuario_asignado=vol_id,
                cantidad=qty,
            )
            # ── SUCCESS: clear form and show ticket (§5.3) ────────
            assign_error.visible = False
            tool_dropdown.value = None
            volunteer_dropdown.value = None
            quantity_field.value = ""

            _load_inventory()
            _load_assignments()
            _populate_dropdowns()

            _show_ticket_dialog(tool_name, qty, volunteer_name)

        except ValueError as exc:
            # Business logic error (stock insuficiente) — show inline
            # §5.3: form state is PRESERVED (no reset)
            assign_error.value = str(exc)
            assign_error.visible = True
            page.update()

        except (ConnectionError, Exception):
            # Network / server error — show modal dialog
            # §5.3: form state is PRESERVED (no reset)
            assign_error.visible = False
            _show_network_error_dialog()

    assign_button = ft.ElevatedButton(
        text="Asignar material",
        icon=ft.icons.ASSIGNMENT_TURNED_IN,
        on_click=handle_assign,
        bgcolor=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_ON_ACCENT,
        width=280,
        height=45,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
        ),
    )

    # ── Assignments list ──────────────────────────────────────────

    def _load_assignments():
        assignment_list.controls.clear()
        assignments = repository.get_assignments()
        if not assignments:
            assignment_list.controls.append(
                ft.Text(
                    "Sin entregas registradas",
                    color=Colors.TEXT_TERTIARY,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        else:
            for a in reversed(assignments):
                assignment_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.INVENTORY_2_OUTLINED,
                                    color=Colors.ACCENT_PRIMARY,
                                    size=20,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"{a.get('nombre_herramienta') or 'Herramienta eliminada'} × {a['cantidad']}",
                                            size=Typography.BODY,
                                            color=Colors.TEXT_PRIMARY,
                                            weight=ft.FontWeight.W_500,
                                        ),
                                        ft.Text(
                                            f"→ {a.get('nombre_usuario') or 'Usuario eliminado'}",
                                            size=Typography.CAPTION,
                                            color=Colors.TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Text(
                                    a["fecha_entrega"][:10],
                                    size=Typography.CAPTION,
                                    color=Colors.TEXT_TERTIARY,
                                ),
                            ],
                        ),
                        bgcolor=Colors.BACKGROUND_SECONDARY,
                        border_radius=BorderRadius.MD,
                        padding=ft.padding.all(Spacing.MD),
                    )
                )
        page.update()

    # ── Tabs ──────────────────────────────────────────────────────

    _load_inventory()
    _load_assignments()
    _populate_dropdowns()

    tabs = ft.Tabs(
        selected_index=0,
        indicator_color=Colors.ACCENT_PRIMARY,
        label_color=Colors.ACCENT_PRIMARY,
        unselected_label_color=Colors.TEXT_SECONDARY,
        divider_color=Colors.DIVIDER,
        expand=True,
        tabs=[
            ft.Tab(
                text="Inventario",
                icon=ft.icons.INVENTORY_OUTLINED,
                content=ft.Container(
                    content=inventory_list,
                    padding=ft.padding.only(top=Spacing.SM),
                    expand=True,
                ),
            ),
            ft.Tab(
                text="Asignar",
                icon=ft.icons.ASSIGNMENT_OUTLINED,
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(height=Spacing.MD),
                            tool_dropdown,
                            ft.Container(height=Spacing.SM),
                            volunteer_dropdown,
                            ft.Container(height=Spacing.SM),
                            quantity_field,
                            ft.Container(height=Spacing.SM),
                            assign_error,
                            ft.Container(height=Spacing.MD),
                            ft.Row(
                                controls=[assign_button],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            # Extra bottom padding to clear NavigationBar
                            ft.Container(height=Spacing.XXL),
                        ],
                        scroll=ft.ScrollMode.ADAPTIVE,
                    ),
                    padding=ft.padding.symmetric(horizontal=Spacing.SM),
                    expand=True,
                ),
            ),
            ft.Tab(
                text="Entregas",
                icon=ft.icons.LOCAL_SHIPPING_OUTLINED,
                content=ft.Container(
                    content=assignment_list,
                    padding=ft.padding.only(top=Spacing.SM),
                    expand=True,
                ),
            ),
        ],
    )

    return ft.Column(controls=[tabs], expand=True)
