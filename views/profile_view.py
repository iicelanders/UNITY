"""
Profile View — Wizard de Registro y Visualización de Perfil (S2_HU01).

Sprint 2 implementation:
  - 3-step wizard for new user onboarding (§S2_HU01)
  - Read-only profile display for returning users (§4.1)
  - Bidirectional navigation with data preservation (QA_01)
  - Role editing restricted to 'comando' users only (§4.1)
"""

from __future__ import annotations

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography

SKILL_OPTIONS = [
    "Primeros auxilios",
    "Logística",
    "Construcción",
    "Comunicaciones",
    "Cocina",
    "Transporte",
    "Electricidad",
    "Búsqueda y rescate",
]

AVAILABILITY_OPTIONS = [
    "Mañana (8:00-12:00)",
    "Tarde (12:00-18:00)",
    "Completo (8:00-18:00)",
    "Noche (18:00-22:00)",
    "Fines de semana",
]


def build_profile_view(page, repository, user_id, on_profile_complete):
    """Return a View for the /onboarding route (3-step wizard)."""

    selected_skills = []
    current_step = {"value": 0}  # Mutable dict for closure access

    # ── Form fields (shared across steps) ─────────────────────────

    name_field = ft.TextField(
        label="Nombre completo",
        prefix_icon=ft.icons.PERSON_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
    )

    availability_dropdown = ft.Dropdown(
        label="Disponibilidad horaria",
        prefix_icon=ft.icons.SCHEDULE_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
        options=[ft.dropdown.Option(opt) for opt in AVAILABILITY_OPTIONS],
    )

    error_text = ft.Text(
        value="", color=Colors.DANGER, size=Typography.BODY, visible=False
    )

    # ── Skills chips ──────────────────────────────────────────────

    def build_skill_chips():
        chips = []
        for skill in SKILL_OPTIONS:
            is_selected = skill in selected_skills
            chips.append(
                ft.Container(
                    content=ft.Text(
                        skill,
                        size=Typography.CAPTION,
                        color=Colors.TEXT_ON_ACCENT
                        if is_selected
                        else Colors.TEXT_SECONDARY,
                    ),
                    bgcolor=Colors.ACCENT_PRIMARY
                    if is_selected
                    else Colors.BACKGROUND_TERTIARY,
                    border_radius=BorderRadius.FULL,
                    padding=ft.padding.symmetric(
                        horizontal=Spacing.MD, vertical=Spacing.SM
                    ),
                    on_click=lambda e, s=skill: toggle_skill(s),
                    animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
                )
            )
        return chips

    def toggle_skill(skill):
        if skill in selected_skills:
            selected_skills.remove(skill)
        else:
            selected_skills.append(skill)
        skills_wrap.controls = build_skill_chips()
        page.update()

    skills_wrap = ft.Row(
        controls=build_skill_chips(),
        wrap=True,
        spacing=Spacing.SM,
        run_spacing=Spacing.SM,
    )

    # ── Step indicator (dots) ─────────────────────────────────────

    def _build_step_indicator():
        dots = []
        step_labels = ["Identificación", "Habilidades", "Disponibilidad"]
        for i in range(3):
            is_active = i == current_step["value"]
            is_completed = i < current_step["value"]
            dot_color = (
                Colors.ACCENT_PRIMARY if is_active
                else Colors.SUCCESS if is_completed
                else Colors.BACKGROUND_TERTIARY
            )
            dots.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            width=36 if is_active else 12,
                            height=12,
                            bgcolor=dot_color,
                            border_radius=BorderRadius.FULL,
                            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
                        ),
                        ft.Text(
                            step_labels[i],
                            size=Typography.CAPTION - 2,
                            color=Colors.TEXT_PRIMARY if is_active else Colors.TEXT_TERTIARY,
                            weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Spacing.XS,
                )
            )
        return ft.Row(
            controls=dots,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=Spacing.LG,
        )

    # ── Validation helpers ────────────────────────────────────────

    def _validate_step_1():
        """Returns True if step 1 is valid, shows error otherwise."""
        name = (name_field.value or "").strip()
        if not name:
            _show_error("Ingresa tu nombre completo")
            return False
        # Check for numeric characters
        if any(char.isdigit() for char in name):
            _show_error("El nombre no debe contener números")
            return False
        return True

    def _validate_step_2():
        """Returns True if step 2 is valid."""
        if not selected_skills:
            _show_error("Selecciona al menos una habilidad")
            return False
        return True

    def _validate_step_3():
        """Returns True if step 3 is valid."""
        if not availability_dropdown.value:
            _show_error("Selecciona tu disponibilidad")
            return False
        return True

    def _show_error(message):
        error_text.value = message
        error_text.visible = True
        page.update()

    def _clear_error():
        error_text.visible = False

    # ── Navigation handlers ───────────────────────────────────────

    def _go_next(e):
        _clear_error()
        step = current_step["value"]

        if step == 0 and not _validate_step_1():
            return
        if step == 1 and not _validate_step_2():
            return

        if step < 2:
            current_step["value"] = step + 1
            _rebuild_wizard()

    def _go_back(e):
        _clear_error()
        if current_step["value"] > 0:
            current_step["value"] -= 1
            _rebuild_wizard()

    def _handle_submit(e):
        _clear_error()
        if not _validate_step_3():
            return

        name = (name_field.value or "").strip()
        availability = availability_dropdown.value

        repository.create_profile(
            user_id=user_id,
            nombre_completo=name,
            habilidades=selected_skills.copy(),
            disponibilidad=availability,
        )
        on_profile_complete()

    # ── Step content builders ─────────────────────────────────────

    def _build_step_1():
        """Paso 1: Identificación Personal."""
        return ft.Column(
            controls=[
                ft.Container(height=Spacing.LG),
                ft.Icon(
                    name=ft.icons.PERSON_ADD_ALT_1_ROUNDED,
                    color=Colors.ACCENT_PRIMARY,
                    size=48,
                ),
                ft.Container(height=Spacing.SM),
                ft.Text(
                    "¿Cómo te llamas?",
                    size=Typography.TITLE,
                    weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Ingresa tu nombre completo para el registro",
                    size=Typography.BODY,
                    color=Colors.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=Spacing.LG),
                name_field,
                ft.Container(height=Spacing.SM),
                error_text,
                ft.Container(height=Spacing.LG),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Siguiente",
                            icon=ft.icons.ARROW_FORWARD,
                            on_click=_go_next,
                            bgcolor=Colors.ACCENT_PRIMARY,
                            color=Colors.TEXT_ON_ACCENT,
                            width=200,
                            height=48,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(
                                    radius=BorderRadius.MD
                                ),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_step_2():
        """Paso 2: Capacidades Técnicas."""
        # Refresh chip visuals in case user goes back and forth
        skills_wrap.controls = build_skill_chips()
        return ft.Column(
            controls=[
                ft.Container(height=Spacing.LG),
                ft.Icon(
                    name=ft.icons.ENGINEERING_ROUNDED,
                    color=Colors.ACCENT_PRIMARY,
                    size=48,
                ),
                ft.Container(height=Spacing.SM),
                ft.Text(
                    "Tus habilidades",
                    size=Typography.TITLE,
                    weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Selecciona las que apliquen a tu experiencia",
                    size=Typography.BODY,
                    color=Colors.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=Spacing.LG),
                skills_wrap,
                ft.Container(height=Spacing.SM),
                error_text,
                ft.Container(height=Spacing.LG),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            text="Atrás",
                            icon=ft.icons.ARROW_BACK,
                            on_click=_go_back,
                            style=ft.ButtonStyle(
                                color=Colors.TEXT_SECONDARY,
                                shape=ft.RoundedRectangleBorder(
                                    radius=BorderRadius.MD
                                ),
                                side=ft.BorderSide(1, Colors.BORDER),
                            ),
                            width=140,
                            height=48,
                        ),
                        ft.ElevatedButton(
                            text="Siguiente",
                            icon=ft.icons.ARROW_FORWARD,
                            on_click=_go_next,
                            bgcolor=Colors.ACCENT_PRIMARY,
                            color=Colors.TEXT_ON_ACCENT,
                            width=140,
                            height=48,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(
                                    radius=BorderRadius.MD
                                ),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=Spacing.MD,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_step_3():
        """Paso 3: Asignación de Tiempo."""
        return ft.Column(
            controls=[
                ft.Container(height=Spacing.LG),
                ft.Icon(
                    name=ft.icons.SCHEDULE_ROUNDED,
                    color=Colors.ACCENT_PRIMARY,
                    size=48,
                ),
                ft.Container(height=Spacing.SM),
                ft.Text(
                    "Tu disponibilidad",
                    size=Typography.TITLE,
                    weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "¿Cuándo puedes participar como voluntario?",
                    size=Typography.BODY,
                    color=Colors.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=Spacing.LG),
                availability_dropdown,
                ft.Container(height=Spacing.SM),
                error_text,
                ft.Container(height=Spacing.XL),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            text="Atrás",
                            icon=ft.icons.ARROW_BACK,
                            on_click=_go_back,
                            style=ft.ButtonStyle(
                                color=Colors.TEXT_SECONDARY,
                                shape=ft.RoundedRectangleBorder(
                                    radius=BorderRadius.MD
                                ),
                                side=ft.BorderSide(1, Colors.BORDER),
                            ),
                            width=140,
                            height=48,
                        ),
                        ft.ElevatedButton(
                            text="Completar perfil",
                            icon=ft.icons.CHECK_CIRCLE_OUTLINED,
                            on_click=_handle_submit,
                            bgcolor=Colors.SUCCESS,
                            color=Colors.TEXT_ON_ACCENT,
                            width=180,
                            height=48,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(
                                    radius=BorderRadius.MD
                                ),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=Spacing.MD,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ── Wizard container ──────────────────────────────────────────

    wizard_content = ft.Column(
        controls=[],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def _rebuild_wizard():
        """Rebuild the wizard content for the current step."""
        step = current_step["value"]
        step_builders = [_build_step_1, _build_step_2, _build_step_3]
        step_view = step_builders[step]()

        wizard_content.controls = [
            ft.Container(height=Spacing.MD),
            _build_step_indicator(),
            step_view,
            ft.Container(height=Spacing.LG),
        ]
        page.update()

    # Initial build
    _rebuild_wizard()

    return ft.View(
        route="/onboarding",
        bgcolor=Colors.BACKGROUND_PRIMARY,
        padding=ft.padding.symmetric(horizontal=Spacing.LG),
        controls=[wizard_content],
        appbar=ft.AppBar(
            title=ft.Text("Nuevo perfil", color=Colors.TEXT_PRIMARY),
            bgcolor=Colors.BACKGROUND_SECONDARY,
            center_title=True,
        ),
    )


# ═══════════════════════════════════════════════════════════════════
# Profile Display — Read-only view for returning users (§4.1)
# ═══════════════════════════════════════════════════════════════════

def build_profile_display_view(page, repository, user_id, user_email, viewer_role):
    """Build a profile display with editable availability and read-only identity fields.

    Args:
        page: Flet page reference.
        repository: Data repository.
        user_id: ID of the profile being viewed.
        user_email: Email address of the user (for display).
        viewer_role: Role of the currently logged-in user (for role-edit permissions).
    """
    profile = repository.get_profile(user_id)
    if not profile:
        return ft.Text("Perfil no encontrado", color=Colors.DANGER)

    role_labels = {
        "voluntario": "Voluntario",
        "lider_cuadrilla": "Líder de Cuadrilla",
        "comando": "Comando",
    }

    # ── Read-only fields ──────────────────────────────────────────

    name_display = ft.TextField(
        label="Nombre completo",
        value=profile["nombre_completo"],
        prefix_icon=ft.icons.PERSON_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
        read_only=True,
        disabled=True,
    )

    email_display = ft.TextField(
        label="Correo electrónico",
        value=user_email or "—",
        prefix_icon=ft.icons.EMAIL_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
        read_only=True,
        disabled=True,
    )

    # ── Role display (static, read-only in Identity card) ─────────

    role_display = ft.TextField(
        label="Rol",
        value=role_labels.get(profile.get("rol", ""), profile.get("rol", "")),
        prefix_icon=ft.icons.SHIELD_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
        read_only=True,
        disabled=True,
    )

    # ── Skills checkboxes (editable in Config card) ─────────────────

    current_user_skills = profile.get("habilidades", [])

    skill_checkboxes = {
        skill: ft.Checkbox(
            label=skill,
            value=skill in current_user_skills,
            check_color=Colors.TEXT_ON_ACCENT,
            active_color=Colors.ACCENT_PRIMARY,
        )
        for skill in SKILL_OPTIONS
    }

    editable_skills_wrap = ft.Column(
        controls=list(skill_checkboxes.values()),
        spacing=Spacing.XS,
    )

    # ── Editable availability ─────────────────────────────────────

    avail_dropdown = ft.Dropdown(
        label="Disponibilidad horaria",
        value=profile.get("disponibilidad", ""),
        prefix_icon=ft.icons.SCHEDULE_OUTLINED,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
        options=[ft.dropdown.Option(opt) for opt in AVAILABILITY_OPTIONS],
    )

    save_status = ft.Text(
        value="", size=Typography.BODY, visible=False
    )

    def _get_selected_skills():
        """Read current checkbox states to build the skills list."""
        return [
            skill for skill, checkbox in skill_checkboxes.items()
            if checkbox.value
        ]

    def _save_changes(e):
        update_data = {
            "disponibilidad": avail_dropdown.value,
            "habilidades": _get_selected_skills(),
        }
        try:
            repository.update_profile(user_id, update_data)
            save_status.value = "✓ Cambios guardados"
            save_status.color = Colors.SUCCESS
            save_status.visible = True
        except Exception:
            save_status.value = "Error al guardar"
            save_status.color = Colors.DANGER
            save_status.visible = True
        page.update()

    save_button = ft.ElevatedButton(
        text="Guardar cambios",
        icon=ft.icons.SAVE_OUTLINED,
        on_click=_save_changes,
        bgcolor=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_ON_ACCENT,
        width=220,
        height=45,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
        ),
    )

    # ── Layout ────────────────────────────────────────────────────

    return ft.Column(
        controls=[
            ft.Container(height=Spacing.XL),
            ft.Container(
                content=ft.Icon(
                    ft.icons.ACCOUNT_CIRCLE,
                    color=Colors.ACCENT_PRIMARY,
                    size=80,
                ),
                alignment=ft.alignment.center,
            ),
            ft.Container(height=Spacing.SM),
            ft.Text(
                profile["nombre_completo"],
                size=Typography.TITLE,
                weight=ft.FontWeight.W_600,
                color=Colors.TEXT_PRIMARY,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(
                content=ft.Text(
                    role_labels.get(profile.get("rol", ""), profile.get("rol", "")),
                    size=Typography.CAPTION,
                    color=Colors.ACCENT_PRIMARY,
                    weight=ft.FontWeight.W_600,
                ),
                bgcolor=Colors.BACKGROUND_TERTIARY,
                border_radius=BorderRadius.FULL,
                padding=ft.padding.symmetric(
                    horizontal=Spacing.MD, vertical=Spacing.XS
                ),
            ),
            ft.Container(height=Spacing.LG),
            # Identity section (read-only) — includes Role
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Identidad  🔒",
                            size=Typography.SUBTITLE,
                            weight=ft.FontWeight.W_500,
                            color=Colors.TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Estos campos no son editables",
                            size=Typography.CAPTION,
                            color=Colors.TEXT_TERTIARY,
                        ),
                        ft.Container(height=Spacing.SM),
                        name_display,
                        ft.Container(height=Spacing.SM),
                        email_display,
                        ft.Container(height=Spacing.SM),
                        role_display,
                    ],
                ),
                bgcolor=Colors.BACKGROUND_SECONDARY,
                border_radius=BorderRadius.LG,
                padding=ft.padding.all(Spacing.LG),
                margin=ft.margin.symmetric(horizontal=Spacing.MD),
            ),
            ft.Container(height=Spacing.MD),
            # Editable section — Skills + Availability
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Configuración  ✏️",
                            size=Typography.SUBTITLE,
                            weight=ft.FontWeight.W_500,
                            color=Colors.TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Puedes modificar estos campos",
                            size=Typography.CAPTION,
                            color=Colors.TEXT_TERTIARY,
                        ),
                        ft.Container(height=Spacing.SM),
                        ft.Text(
                            "Habilidades",
                            size=Typography.BODY_LARGE,
                            weight=ft.FontWeight.W_500,
                            color=Colors.TEXT_PRIMARY,
                        ),
                        ft.Container(height=Spacing.XS),
                        editable_skills_wrap,
                        ft.Container(height=Spacing.MD),
                        avail_dropdown,
                        ft.Container(height=Spacing.SM),
                        save_status,
                        ft.Container(height=Spacing.MD),
                        ft.Row(
                            controls=[save_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                ),
                bgcolor=Colors.BACKGROUND_SECONDARY,
                border_radius=BorderRadius.LG,
                padding=ft.padding.all(Spacing.LG),
                margin=ft.margin.symmetric(horizontal=Spacing.MD),
            ),
            ft.Container(height=Spacing.XXL),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
