"""
Design Tokens — UNITY App

Semantic constants for the entire UI. No magic numbers allowed.
Inspired by the JOIN app dark-mode aesthetic from Diseño_ux.png.

Usage: Import and reference tokens instead of hardcoding values.
  from core.design_tokens import Colors, Spacing, BorderRadius, Typography
"""


class Colors:
    """Semantic color palette — dark mode with terracota accents."""

    # Backgrounds
    BACKGROUND_PRIMARY = "#1C1C1E"
    BACKGROUND_SECONDARY = "#2C2C2E"
    BACKGROUND_TERTIARY = "#3A3A3C"
    BACKGROUND_ELEVATED = "#48484A"

    # Accent
    ACCENT_PRIMARY = "#C67C4E"        # Terracota / copper
    ACCENT_PRIMARY_LIGHT = "#D4956B"
    ACCENT_SECONDARY = "#5E5CE6"      # Purple

    # Semantic
    DANGER = "#FF453A"
    DANGER_DARK = "#CC362E"
    SUCCESS = "#30D158"
    WARNING = "#FFD60A"
    WARNING_DARK = "#E68A00"          # Deep amber — high contrast with white text
    INFO = "#64D2FF"

    # Text
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#ABABAB"
    TEXT_TERTIARY = "#636366"
    TEXT_ON_ACCENT = "#FFFFFF"

    # Borders and dividers
    DIVIDER = "#38383A"
    BORDER = "#48484A"

    # Chat (S3_HU02)
    CHAT_BUBBLE_SELF = "#2C3E50"
    CHAT_BUBBLE_OTHER = "#2C2C2E"
    CHAT_ALERT_BORDER = "#FF453A"

    # Calendar / Turnos (S3_HU01)
    TURNO_LIBRE = "#3A3A3C"
    TURNO_ASIGNADO = "#C67C4E"
    TURNO_CONFLICTO = "#FF453A"


class Spacing:
    """Consistent spacing scale (in pixels)."""

    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48


class BorderRadius:
    """Border radius tokens."""

    SM = 8
    MD = 12
    LG = 16
    XL = 24
    FULL = 100


class Typography:
    """Font size scale."""

    CAPTION = 12
    BODY = 14
    BODY_LARGE = 16
    SUBTITLE = 18
    TITLE = 22
    HEADING = 28
    DISPLAY = 34
