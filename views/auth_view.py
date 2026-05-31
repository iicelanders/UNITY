"""
Auth View — Login / Register screen (entry point).

Implements SRS §6.4: after successful auth, checks if profile exists.
If yes → navigate to main app. If no → force onboarding in profile_view.
"""

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography


def build_auth_view(page: ft.Page, repository, on_auth_success):
    """Return a View for the /auth route."""

    is_login_mode = {"value": True}  # mutable ref for closure

    # ── Form fields ───────────────────────────────────────────────

    email_field = ft.TextField(
        label="Correo electrónico",
        prefix_icon=ft.icons.EMAIL_OUTLINED,
        keyboard_type=ft.KeyboardType.EMAIL,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
    )

    password_field = ft.TextField(
        label="Contraseña",
        prefix_icon=ft.icons.LOCK_OUTLINED,
        password=True,
        can_reveal_password=True,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_color=Colors.BORDER,
        focused_border_color=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=Colors.TEXT_SECONDARY),
        border_radius=BorderRadius.MD,
        text_size=Typography.BODY_LARGE,
    )

    error_text = ft.Text(
        value="",
        color=Colors.DANGER,
        size=Typography.BODY,
        visible=False,
    )

    loading_ring = ft.ProgressRing(
        color=Colors.ACCENT_PRIMARY,
        visible=False,
        width=20,
        height=20,
    )

    # ── Handlers ──────────────────────────────────────────────────

    def handle_submit(e):
        email = (email_field.value or "").strip()
        password = password_field.value or ""

        if not email or not password:
            _show_error("Por favor, completa todos los campos")
            return

        if len(password) < 6:
            _show_error("La contraseña debe tener al menos 6 caracteres")
            return

        error_text.visible = False
        loading_ring.visible = True
        submit_button.disabled = True
        page.update()

        if is_login_mode["value"]:
            result = repository.sign_in(email, password)
        else:
            result = repository.sign_up(email, password)

        loading_ring.visible = False
        submit_button.disabled = False

        if result.success:
            on_auth_success(result.user_id)
        else:
            _show_error(result.error)

        page.update()

    def _show_error(message: str):
        error_text.value = message
        error_text.visible = True
        page.update()

    def toggle_mode(e):
        is_login_mode["value"] = not is_login_mode["value"]
        is_login = is_login_mode["value"]

        submit_button.text = "Iniciar Sesión" if is_login else "Registrarse"
        toggle_link.text = "Regístrate" if is_login else "Inicia Sesión"
        toggle_label.value = (
            "¿No tienes cuenta?" if is_login else "¿Ya tienes cuenta?"
        )
        title_text.value = (
            "Bienvenido de vuelta" if is_login else "Crear cuenta"
        )
        subtitle_text.value = (
            "Inicia sesión para continuar"
            if is_login
            else "Únete a la comunidad UNITY"
        )
        error_text.visible = False
        page.update()

    # ── UI Components ─────────────────────────────────────────────

    logo_icon = ft.Icon(
        name=ft.icons.PEOPLE_ALT_ROUNDED,
        color=Colors.ACCENT_PRIMARY,
        size=48,
    )

    logo_text = ft.Text(
        value="UNITY",
        size=Typography.DISPLAY,
        weight=ft.FontWeight.BOLD,
        color=Colors.ACCENT_PRIMARY,
    )

    logo_subtitle = ft.Text(
        value="Voluntariado Universitario",
        size=Typography.BODY,
        color=Colors.TEXT_SECONDARY,
    )

    title_text = ft.Text(
        value="Bienvenido de vuelta",
        size=Typography.HEADING,
        weight=ft.FontWeight.W_600,
        color=Colors.TEXT_PRIMARY,
    )

    subtitle_text = ft.Text(
        value="Inicia sesión para continuar",
        size=Typography.BODY,
        color=Colors.TEXT_SECONDARY,
    )

    submit_button = ft.ElevatedButton(
        text="Iniciar Sesión",
        on_click=handle_submit,
        bgcolor=Colors.ACCENT_PRIMARY,
        color=Colors.TEXT_ON_ACCENT,
        width=320,
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BorderRadius.MD),
        ),
    )

    toggle_label = ft.Text(
        value="¿No tienes cuenta?",
        size=Typography.BODY,
        color=Colors.TEXT_SECONDARY,
    )

    toggle_link = ft.TextButton(
        text="Regístrate",
        on_click=toggle_mode,
        style=ft.ButtonStyle(color=Colors.ACCENT_PRIMARY),
    )

    # Contextual hint based on data source
    is_mock = hasattr(repository, '_users')  # MockRepository has _users dict

    if is_mock:
        hint_content = ft.Column(
            controls=[
                ft.Text(
                    "Cuentas de demo (modo offline):",
                    size=Typography.CAPTION,
                    color=Colors.TEXT_TERTIARY,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    "voluntario@unity.cl  /  123456",
                    size=Typography.CAPTION,
                    color=Colors.TEXT_TERTIARY,
                ),
                ft.Text(
                    "lider@unity.cl  /  123456",
                    size=Typography.CAPTION,
                    color=Colors.TEXT_TERTIARY,
                ),
                ft.Text(
                    "comando@unity.cl  /  123456",
                    size=Typography.CAPTION,
                    color=Colors.TEXT_TERTIARY,
                ),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    else:
        hint_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.icons.CLOUD_DONE_OUTLINED,
                            color=Colors.SUCCESS,
                            size=16,
                        ),
                        ft.Text(
                            "Conectado a Supabase",
                            size=Typography.CAPTION,
                            color=Colors.SUCCESS,
                            weight=ft.FontWeight.W_600,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=Spacing.XS,
                ),
                ft.Text(
                    "Registra una cuenta nueva o inicia sesión",
                    size=Typography.CAPTION,
                    color=Colors.TEXT_TERTIARY,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    demo_hint = ft.Container(
        content=hint_content,
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_radius=BorderRadius.MD,
        padding=ft.padding.all(Spacing.MD),
        margin=ft.margin.only(top=Spacing.LG),
    )

    # ── Layout ────────────────────────────────────────────────────

    content = ft.Column(
        controls=[
            ft.Container(height=Spacing.XXL),
            ft.Column(
                controls=[logo_icon, logo_text, logo_subtitle],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Spacing.XS,
            ),
            ft.Container(height=Spacing.XL),
            title_text,
            subtitle_text,
            ft.Container(height=Spacing.LG),
            email_field,
            ft.Container(height=Spacing.SM),
            password_field,
            ft.Container(height=Spacing.SM),
            error_text,
            ft.Container(height=Spacing.MD),
            ft.Row(
                controls=[submit_button, loading_ring],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=Spacing.SM,
            ),
            ft.Container(height=Spacing.MD),
            ft.Row(
                controls=[toggle_label, toggle_link],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            ),
            demo_hint,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
    )

    return ft.View(
        route="/auth",
        bgcolor=Colors.BACKGROUND_PRIMARY,
        padding=ft.padding.symmetric(horizontal=Spacing.LG),
        controls=[content],
    )
