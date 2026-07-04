"""
Turnos View — Weekly schedule calendar (S3_HU01).

Dumb view: all business logic and validation lives in turnos_service.py.
Renders a 7×6 grid (Lun–Dom × 08:00–20:00) with role-based interactions.
"""

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography
from core.turnos_service import puede_editar_turnos, crear_turno_validado, eliminar_turno


# ── Constants ────────────────────────────────────────────────────

_DAY_NAMES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
_TIME_SLOTS = [
    (8, 10),
    (10, 12),
    (12, 14),
    (14, 16),
    (16, 18),
    (18, 20),
]


# ── Public entry point ───────────────────────────────────────────

def build_turnos_view(page, repository, user_id, cuadrilla_id, user_rol):
    """Return a scrollable Column with the weekly schedule grid.

    Args:
        page: ft.Page instance for dialogs and snack bars.
        repository: DataRepository implementation.
        user_id: Current authenticated user UUID.
        cuadrilla_id: UUID of the user's cuadrilla, or None.
        user_rol: Role string (e.g. 'lider_cuadrilla', 'voluntario').
    """
    # ── Early return: no cuadrilla ───────────────────────────────
    if cuadrilla_id is None:
        return _build_empty_state("No tienes una cuadrilla asignada")

    is_editable = puede_editar_turnos(user_rol)

    # ── Mutable state containers ─────────────────────────────────
    grid_container = ft.Container(expand=True)
    loading_indicator = ft.ProgressRing(
        color=Colors.ACCENT_PRIMARY,
        width=40,
        height=40,
    )
    loading_wrapper = ft.Container(
        content=loading_indicator,
        alignment=ft.alignment.center,
        padding=Spacing.XL,
    )

    # ── Data helpers ─────────────────────────────────────────────

    def _get_cuadrilla_members():
        """Return volunteers filtered to this cuadrilla."""
        all_volunteers = repository.get_all_volunteers()
        return [
            v for v in all_volunteers
            if v.get("cuadrilla_id") == cuadrilla_id
        ]

    def _build_turno_lookup(turnos):
        """Build a dict keyed by (dia_semana, start_hour) for O(1) lookup.

        Only maps the canonical 2-hour slots defined in _TIME_SLOTS.
        """
        lookup = {}  # type: dict
        for turno in turnos:
            dia = turno.get("dia_semana")
            start_hour = _extract_hour(turno.get("inicio_hora", ""))
            if dia is not None and start_hour is not None:
                lookup[(dia, start_hour)] = turno
        return lookup

    # ── Grid refresh ─────────────────────────────────────────────

    def _refresh_grid(show_loading=False):
        """Reload turnos from repository and rebuild the grid."""
        if show_loading:
            grid_container.content = loading_wrapper
            page.update()

        try:
            turnos = repository.get_turnos_by_cuadrilla(cuadrilla_id)
        except Exception:
            _show_snack_bar(
                "Error de red al cargar los turnos.",
                icon=ft.icons.ERROR_OUTLINE,
                color=Colors.DANGER,
            )
            turnos = []

        lookup = _build_turno_lookup(turnos)
        grid_container.content = _build_grid(lookup, is_editable)
        page.update()

    # ── Grid construction ────────────────────────────────────────

    def _build_grid(lookup, editable):
        """Return the full 7×6 grid wrapped in a responsive Column."""
        # Header row
        header_row = ft.Row(
            controls=[
                # Empty corner cell to align with time labels
                ft.Container(width=48),
            ] + [_build_day_header(name) for name in _DAY_NAMES],
            spacing=Spacing.XS,
        )

        # Time slot rows
        rows = [header_row]
        for start_hour, end_hour in _TIME_SLOTS:
            time_label = _build_time_label(start_hour, end_hour)
            cells = []
            for dia_index in range(7):
                turno = lookup.get((dia_index, start_hour))
                cell = _build_time_slot_cell(
                    turno=turno,
                    dia=dia_index,
                    hora=start_hour,
                    is_editable=editable,
                    on_click=_on_slot_click,
                    on_delete=_on_slot_delete,
                )
                cells.append(cell)

            rows.append(
                ft.Row(
                    controls=[time_label] + cells,
                    spacing=Spacing.XS,
                )
            )

        return ft.Column(
            controls=rows,
            spacing=Spacing.XS,
        )

    # ── Click handlers ───────────────────────────────────────────

    def _on_slot_click(dia, hora):
        """Handle click on an empty slot — open create dialog."""
        if not is_editable:
            return
        _open_create_dialog(dia, hora)

    def _on_slot_delete(turno):
        """Handle delete icon press — open confirmation dialog."""
        if not is_editable:
            return
        _open_delete_dialog(turno)

    # ── Create dialog ────────────────────────────────────────────

    def _open_create_dialog(dia, hora):
        """Show dialog with user dropdown and time info for turno creation."""
        members = _get_cuadrilla_members()
        if not members:
            _show_snack_bar(
                "No hay voluntarios en esta cuadrilla.",
                icon=ft.icons.INFO_OUTLINE,
                color=Colors.WARNING,
            )
            return

        selected_user_id = {"value": members[0]["id"]}
        start_hour, end_hour = hora, hora + 2

        user_dropdown = ft.Dropdown(
            label="Voluntario",
            width=280,
            value=members[0]["id"],
            options=[
                ft.dropdown.Option(
                    key=m["id"],
                    text=m.get("nombre_completo", m["id"][:8]),
                )
                for m in members
            ],
            on_change=lambda e: _update_selected(e, selected_user_id),
            bgcolor=Colors.BACKGROUND_TERTIARY,
            color=Colors.TEXT_PRIMARY,
            label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
            border_color=Colors.BORDER,
            focused_border_color=Colors.ACCENT_PRIMARY,
        )

        time_display = ft.Text(
            "{day}  {start}:00 – {end}:00".format(
                day=_DAY_NAMES[dia],
                start=str(start_hour).zfill(2),
                end=str(end_hour).zfill(2),
            ),
            size=Typography.BODY_LARGE,
            color=Colors.TEXT_PRIMARY,
            weight=ft.FontWeight.W_500,
        )

        def _on_confirm(e):
            _close_dialog()
            _create_turno(
                usuario_id=selected_user_id["value"],
                dia_semana=dia,
                start_hour=start_hour,
                end_hour=end_hour,
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CALENDAR_MONTH, color=Colors.ACCENT_PRIMARY, size=24),
                ft.Text(
                    "Asignar turno",
                    size=Typography.SUBTITLE,
                    color=Colors.TEXT_PRIMARY,
                    weight=ft.FontWeight.W_600,
                ),
            ], spacing=Spacing.SM),
            content=ft.Column(
                controls=[
                    time_display,
                    ft.Container(height=Spacing.SM),
                    user_dropdown,
                ],
                tight=True,
                spacing=Spacing.MD,
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    on_click=lambda e: _close_dialog(),
                    style=ft.ButtonStyle(
                        color=Colors.TEXT_SECONDARY,
                        side=ft.BorderSide(1, Colors.BORDER),
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
                    ),
                ),
                ft.ElevatedButton(
                    "Asignar",
                    on_click=_on_confirm,
                    bgcolor=Colors.ACCENT_PRIMARY,
                    color=Colors.TEXT_ON_ACCENT,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
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

    # ── Delete dialog ────────────────────────────────────────────

    def _open_delete_dialog(turno):
        """Show confirmation dialog before deleting a turno."""
        turno_id = turno.get("id", "")
        user_name = turno.get("nombre_usuario", "este voluntario")
        dia_name = _DAY_NAMES[turno.get("dia_semana", 0)]
        start_h = _extract_hour(turno.get("inicio_hora", ""))
        display_time = "{h}:00".format(h=str(start_h).zfill(2)) if start_h is not None else ""

        def _on_confirm(e):
            _close_dialog()
            _delete_turno(turno_id)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.DELETE_OUTLINE, color=Colors.DANGER, size=24),
                ft.Text(
                    "Eliminar turno",
                    size=Typography.SUBTITLE,
                    color=Colors.TEXT_PRIMARY,
                    weight=ft.FontWeight.W_600,
                ),
            ], spacing=Spacing.SM),
            content=ft.Text(
                "¿Eliminar el turno de {user} el {day} a las {time}?".format(
                    user=user_name,
                    day=dia_name,
                    time=display_time,
                ),
                size=Typography.BODY,
                color=Colors.TEXT_SECONDARY,
            ),
            actions=[
                ft.OutlinedButton(
                    "Cancelar",
                    on_click=lambda e: _close_dialog(),
                    style=ft.ButtonStyle(
                        color=Colors.TEXT_SECONDARY,
                        side=ft.BorderSide(1, Colors.BORDER),
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
                    ),
                ),
                ft.ElevatedButton(
                    "Eliminar",
                    on_click=_on_confirm,
                    bgcolor=Colors.DANGER,
                    color=Colors.TEXT_ON_ACCENT,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=BorderRadius.SM),
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

    # ── Service calls ────────────────────────────────────────────

    def _create_turno(usuario_id, dia_semana, start_hour, end_hour):
        """Delegate to turnos_service and handle result."""
        # Build ISO timestamps (date part is irrelevant for weekly grid;
        # we use a fixed reference date per-day for consistency).
        inicio_hora = "2000-01-01T{h}:00:00".format(h=str(start_hour).zfill(2))
        fin_hora = "2000-01-01T{h}:00:00".format(h=str(end_hour).zfill(2))

        result = crear_turno_validado(
            repository=repository,
            usuario_id=usuario_id,
            cuadrilla_id=cuadrilla_id,
            inicio_hora=inicio_hora,
            fin_hora=fin_hora,
            dia_semana=dia_semana,
        )

        if result.success:
            _show_snack_bar(
                "Turno asignado correctamente.",
                icon=ft.icons.CHECK_CIRCLE,
                color=Colors.SUCCESS,
            )
            _refresh_grid()
        else:
            _show_snack_bar(
                result.error,
                icon=ft.icons.ERROR_OUTLINE,
                color=Colors.DANGER,
            )

    def _delete_turno(turno_id):
        """Delegate to turnos_service and handle result."""
        result = eliminar_turno(repository, turno_id)

        if result.success:
            _show_snack_bar(
                "Turno eliminado.",
                icon=ft.icons.CHECK_CIRCLE,
                color=Colors.SUCCESS,
            )
            _refresh_grid()
        else:
            _show_snack_bar(
                result.error,
                icon=ft.icons.ERROR_OUTLINE,
                color=Colors.DANGER,
            )

    # ── Dialog / SnackBar helpers ────────────────────────────────

    def _close_dialog():
        if page.dialog:
            page.dialog.open = False
        page.update()

    def _show_snack_bar(message, icon=ft.icons.CHECK_CIRCLE, color=Colors.SUCCESS):
        page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(icon, color=color, size=20),
                ft.Text("  " + message, color=Colors.TEXT_PRIMARY),
            ]),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            duration=3000,
        )
        page.snack_bar.open = True
        page.update()

    def _update_selected(e, ref):
        ref["value"] = e.control.value

    # ── Refresh button ───────────────────────────────────────────

    refresh_button = ft.IconButton(
        icon=ft.icons.REFRESH,
        icon_color=Colors.ACCENT_PRIMARY,
        tooltip="Actualizar calendario",
        on_click=lambda e: _refresh_grid(show_loading=True),
    )

    # ── Initial load ─────────────────────────────────────────────

    grid_container.content = loading_wrapper
    _refresh_grid(show_loading=True)

    # ── Layout ───────────────────────────────────────────────────

    return ft.Column(
        controls=[
            ft.Container(height=Spacing.MD),
            ft.Row(
                controls=[
                    ft.Text(
                        "Calendario de Turnos",
                        size=Typography.TITLE,
                        weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_PRIMARY,
                        expand=True,
                    ),
                    refresh_button,
                ],
            ),
            ft.Container(height=Spacing.SM),
            _build_legend_row(),
            ft.Container(height=Spacing.MD),
            grid_container,
            # Extra bottom padding to clear NavigationBar on mobile
            ft.Container(height=Spacing.XXL),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


# ── Extracted components ─────────────────────────────────────────

def _build_day_header(day_name):
    """Single day column header (Lun, Mar, …)."""
    return ft.Container(
        content=ft.Text(
            day_name,
            size=Typography.CAPTION,
            weight=ft.FontWeight.W_600,
            color=Colors.ACCENT_PRIMARY,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_radius=BorderRadius.SM,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(
            vertical=Spacing.SM,
            horizontal=Spacing.XS,
        ),
        expand=True,
    )


def _build_time_label(start_hour, end_hour):
    """Left-column time range label."""
    return ft.Container(
        content=ft.Text(
            "{s}–{e}".format(
                s=str(start_hour).zfill(2),
                e=str(end_hour).zfill(2),
            ),
            size=Typography.CAPTION,
            color=Colors.TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        ),
        width=48,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(vertical=Spacing.SM),
    )


def _build_time_slot_cell(turno, dia, hora, is_editable, on_click, on_delete):
    """Single grid cell representing a 2-hour block.

    States:
        - Empty (turno is None): TURNO_LIBRE, clickable if editable
        - Assigned (turno exists): TURNO_ASIGNADO with user name + delete icon
    """
    if turno is None:
        return _build_empty_cell(dia, hora, is_editable, on_click)
    return _build_assigned_cell(turno, is_editable, on_delete)


def _build_empty_cell(dia, hora, is_editable, on_click):
    """Render an available (empty) time slot."""
    return ft.Container(
        content=ft.Text(
            "Libre",
            size=Typography.CAPTION,
            color=Colors.TEXT_TERTIARY,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor=Colors.TURNO_LIBRE,
        border_radius=BorderRadius.SM,
        alignment=ft.alignment.center,
        padding=ft.padding.all(Spacing.SM),
        expand=True,
        on_click=(lambda e, d=dia, h=hora: on_click(d, h)) if is_editable else None,
        ink=is_editable,
        tooltip="Asignar turno" if is_editable else None,
    )


def _build_assigned_cell(turno, is_editable, on_delete):
    """Render a cell with an assigned turno."""
    user_name = turno.get("nombre_usuario", "—")

    name_text = ft.Text(
        user_name,
        size=10,
        color=Colors.TEXT_ON_ACCENT,
        text_align=ft.TextAlign.CENTER,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    if is_editable:
        content = ft.Column(
            controls=[
                name_text,
                ft.IconButton(
                    icon=ft.icons.DELETE_OUTLINE,
                    icon_size=14,
                    icon_color=Colors.TEXT_ON_ACCENT,
                    tooltip="Eliminar turno",
                    on_click=lambda e, t=turno: on_delete(t),
                    style=ft.ButtonStyle(
                        padding=ft.padding.all(0),
                    ),
                    width=24,
                    height=24,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )
    else:
        content = name_text

    return ft.Container(
        content=content,
        bgcolor=Colors.TURNO_ASIGNADO,
        border_radius=BorderRadius.SM,
        alignment=ft.alignment.center,
        padding=ft.padding.all(Spacing.XS),
        expand=True,
        tooltip=user_name,
    )


def _build_legend_row():
    """Color legend explaining the cell states."""
    return ft.Row(
        controls=[
            _build_legend_chip("Libre", Colors.TURNO_LIBRE),
            _build_legend_chip("Asignado", Colors.TURNO_ASIGNADO),
            _build_legend_chip("Conflicto", Colors.TURNO_CONFLICTO),
        ],
        spacing=Spacing.MD,
    )


def _build_legend_chip(label, color):
    """Single legend entry with color dot + text."""
    return ft.Row(
        controls=[
            ft.Container(
                width=12,
                height=12,
                bgcolor=color,
                border_radius=BorderRadius.FULL,
            ),
            ft.Text(
                label,
                size=Typography.CAPTION,
                color=Colors.TEXT_SECONDARY,
            ),
        ],
        spacing=Spacing.XS,
    )


def _build_empty_state(message):
    """Return a centred empty-state Column."""
    return ft.Column(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.icons.CALENDAR_TODAY,
                            color=Colors.TEXT_TERTIARY,
                            size=48,
                        ),
                        ft.Text(
                            message,
                            size=Typography.BODY_LARGE,
                            color=Colors.TEXT_TERTIARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Spacing.MD,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=Spacing.XL,
            ),
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


# ── Private utilities ────────────────────────────────────────────

def _extract_hour(timestamp_str):
    """Extract the hour (int) from an ISO timestamp or HH:MM string.

    Returns None if the string cannot be parsed.
    """
    if not timestamp_str:
        return None
    # Handle "HH:MM" or "HH:MM:SS" directly
    if "T" not in timestamp_str and ":" in timestamp_str:
        try:
            return int(timestamp_str.split(":")[0])
        except (ValueError, IndexError):
            return None
    # Handle ISO "...THH:MM:SS..."
    if "T" in timestamp_str:
        try:
            time_part = timestamp_str.split("T")[1]
            return int(time_part.split(":")[0])
        except (ValueError, IndexError):
            return None
    return None
