"""
Chat View — Squad chat coordination (S3_HU02).

Dumb view: all business logic lives in core.chat_service.
Renders message bubbles, handles polling, and manages connection state.
"""

import asyncio

import flet as ft

from core.design_tokens import Colors, Spacing, BorderRadius, Typography
from core.chat_service import (
    puede_acceder_chat,
    obtener_mensajes_nuevos,
    enviar_mensaje,
    gestionar_estado_conexion,
    ESTADO_RECONECTANDO,
)

# Polling interval in seconds.
_POLL_INTERVAL_SECONDS = 3


# ── Private component builders ────────────────────────────────────


def _build_empty_state():
    # type: () -> ft.Column
    """Centered empty state for users without a cuadrilla."""
    return ft.Column(
        controls=[
            ft.Icon(
                ft.icons.FORUM_OUTLINED,
                color=Colors.TEXT_TERTIARY,
                size=64,
            ),
            ft.Text(
                "No tienes una cuadrilla asignada",
                size=Typography.SUBTITLE,
                color=Colors.TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=Spacing.MD,
        expand=True,
    )


def _build_message_bubble(message, is_own, is_alert):
    # type: (dict, bool, bool) -> ft.Row
    """Single chat bubble wrapped in a directional Row.

    Own messages align right; others align left.
    Max width is ~75% of mobile screen (≈310px on a 414px viewport).
    """
    bubble_controls = []

    # Sender name — only for other users' messages
    if not is_own:
        bubble_controls.append(
            ft.Text(
                message.get("nombre_usuario", ""),
                size=Typography.CAPTION,
                color=Colors.TEXT_SECONDARY,
                weight=ft.FontWeight.W_600,
            )
        )

    # Message body — word-wrap enabled
    bubble_controls.append(
        ft.Text(
            message.get("texto_mensaje", ""),
            size=Typography.BODY,
            color=Colors.TEXT_PRIMARY,
            no_wrap=False,
        )
    )

    # Timestamp
    raw_ts = message.get("timestamp", "")
    display_ts = raw_ts[:16].replace("T", " ") if raw_ts else ""
    bubble_controls.append(
        ft.Text(
            display_ts,
            size=Typography.CAPTION,
            color=Colors.TEXT_TERTIARY,
        )
    )

    # Background and alert border
    bg_color = Colors.CHAT_BUBBLE_SELF if is_own else Colors.CHAT_BUBBLE_OTHER
    alert_border = (
        ft.border.only(left=ft.BorderSide(3, Colors.CHAT_ALERT_BORDER))
        if is_alert
        else None
    )

    # Inner row: optional alert icon + text column
    inner_controls = []
    if is_alert:
        inner_controls.append(
            ft.Icon(ft.icons.ERROR_OUTLINE, color=Colors.DANGER, size=18)
        )
    inner_controls.append(
        ft.Column(controls=bubble_controls, spacing=Spacing.XS, tight=True)
    )

    # The bubble container — constrained to ~75% width
    bubble = ft.Container(
        content=ft.Row(
            controls=inner_controls,
            spacing=Spacing.SM,
        ),
        bgcolor=bg_color,
        border=alert_border,
        border_radius=BorderRadius.MD,
        padding=ft.padding.symmetric(
            horizontal=Spacing.MD, vertical=Spacing.SM
        ),
        width=310,
    )

    # Directional wrapper: aligns bubble to the correct side
    return ft.Row(
        controls=[bubble],
        alignment=(
            ft.MainAxisAlignment.END if is_own
            else ft.MainAxisAlignment.START
        ),
    )


def _build_input_row(text_field, send_button):
    # type: (ft.TextField, ft.IconButton) -> ft.Container
    """Fixed input row at the bottom of the chat."""
    return ft.Container(
        content=ft.Row(
            controls=[text_field, send_button],
            spacing=Spacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=Colors.BACKGROUND_SECONDARY,
        border_radius=BorderRadius.LG,
        padding=ft.padding.symmetric(
            horizontal=Spacing.MD, vertical=Spacing.SM
        ),
    )


# ── Public view builder ──────────────────────────────────────────


def build_chat_view(page, repository, user_id, cuadrilla_id):
    # type: (ft.Page, object, str, str) -> ft.Column
    """Build the squad chat Column.

    Args:
        page: Flet page instance.
        repository: DataRepository implementation.
        user_id: UUID of the current user.
        cuadrilla_id: UUID of the user's cuadrilla (may be None/empty).

    Returns:
        ft.Column ready to be embedded in a parent view.
    """

    # ── Early Return: no cuadrilla ──────────────────────────────
    if not puede_acceder_chat(cuadrilla_id):
        disabled_field = ft.TextField(
            hint_text="Escribe un mensaje...",
            disabled=True,
            expand=True,
            border_color=Colors.BORDER,
            bgcolor=Colors.BACKGROUND_SECONDARY,
            color=Colors.TEXT_TERTIARY,
            text_size=Typography.BODY,
            border_radius=BorderRadius.SM,
        )
        disabled_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            icon_color=Colors.TEXT_TERTIARY,
            disabled=True,
        )
        return ft.Column(
            controls=[
                _build_empty_state(),
                _build_input_row(disabled_field, disabled_button),
            ],
            expand=True,
        )

    # ── Mutable closure state ───────────────────────────────────
    ultimo_timestamp = {"value": ""}
    ciclos_fallidos = {"value": 0}
    polling_active = {"value": True}

    # ── Chat messages ListView ──────────────────────────────────
    chat_messages = ft.ListView(
        expand=True,
        spacing=Spacing.SM,
        auto_scroll=True,
        padding=ft.padding.symmetric(
            horizontal=Spacing.SM, vertical=Spacing.SM
        ),
    )

    # ── Connection banner ───────────────────────────────────────
    connection_banner = ft.Container(
        content=ft.Row(
            controls=[
                ft.ProgressRing(
                    width=16,
                    height=16,
                    stroke_width=2,
                    color=Colors.WARNING,
                ),
                ft.Text(
                    "Buscando conexión...",
                    size=Typography.CAPTION,
                    color=Colors.WARNING,
                ),
            ],
            spacing=Spacing.SM,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=Colors.BACKGROUND_TERTIARY,
        border_radius=BorderRadius.SM,
        padding=ft.padding.symmetric(
            horizontal=Spacing.MD, vertical=Spacing.SM
        ),
        visible=False,
    )

    # ── Helpers: message rendering ──────────────────────────────

    def _append_messages(messages):
        # type: (list) -> None
        """Append a batch of NEW messages to the ListView."""
        for msg in messages:
            is_own = msg.get("usuario_id") == user_id
            is_alert = bool(msg.get("es_alerta"))
            chat_messages.controls.append(
                _build_message_bubble(msg, is_own, is_alert)
            )
        # Advance the cursor so the next poll only fetches newer messages.
        if messages:
            last_ts = messages[-1].get("timestamp", "")
            if last_ts:
                ultimo_timestamp["value"] = last_ts

    # ── Send handler ────────────────────────────────────────────

    def _handle_send(event):
        # type: (ft.ControlEvent) -> None
        text = message_field.value or ""
        result = enviar_mensaje(repository, cuadrilla_id, user_id, text)

        if result.success:
            message_field.value = ""
            if result.data:
                _append_messages([result.data])
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(result.error, color=Colors.TEXT_PRIMARY),
                bgcolor=Colors.DANGER_DARK,
                duration=3000,
            )
            page.snack_bar.open = True

        page.update()

    # ── Input controls ──────────────────────────────────────────

    message_field = ft.TextField(
        hint_text="Escribe un mensaje...",
        expand=True,
        border_color=Colors.BORDER,
        bgcolor=Colors.BACKGROUND_PRIMARY,
        color=Colors.TEXT_PRIMARY,
        text_size=Typography.BODY,
        border_radius=BorderRadius.SM,
        on_submit=_handle_send,
        content_padding=ft.padding.symmetric(
            horizontal=Spacing.MD, vertical=Spacing.SM
        ),
    )

    send_button = ft.IconButton(
        icon=ft.icons.SEND_ROUNDED,
        icon_color=Colors.ACCENT_PRIMARY,
        tooltip="Enviar mensaje",
        on_click=_handle_send,
    )

    input_row = _build_input_row(message_field, send_button)

    # ── Async polling ───────────────────────────────────────────

    async def _poll_messages():
        """Fetch new messages every _POLL_INTERVAL_SECONDS."""
        while polling_active["value"]:
            result = obtener_mensajes_nuevos(
                repository, cuadrilla_id, ultimo_timestamp["value"]
            )

            if result.success:
                ciclos_fallidos["value"] = 0
                if connection_banner.visible:
                    connection_banner.visible = False

                new_messages = result.data or []
                if new_messages:
                    _append_messages(new_messages)
                    page.update()
            else:
                ciclos_fallidos["value"] += 1
                estado = gestionar_estado_conexion(ciclos_fallidos["value"])
                should_show = estado == ESTADO_RECONECTANDO

                if connection_banner.visible != should_show:
                    connection_banner.visible = should_show
                    page.update()

            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

    # ── Initial load + start polling ────────────────────────────

    initial_result = obtener_mensajes_nuevos(
        repository, cuadrilla_id, ultimo_timestamp["value"]
    )
    if initial_result.success and initial_result.data:
        _append_messages(initial_result.data)

    page.run_task(_poll_messages)

    # ── Layout assembly ─────────────────────────────────────────

    def on_dispose():
        """Stop the polling loop when the view is removed."""
        polling_active["value"] = False

    view = ft.Column(
        controls=[
            connection_banner,
            chat_messages,
            input_row,
        ],
        expand=True,
    )

    # Expose cleanup hook so the parent can call it on navigation.
    view.on_dispose = on_dispose  # type: ignore[attr-defined]

    return view
