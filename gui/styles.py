"""
Colour palette and font definitions for the Tkinter GUI.

All widgets import from here — no hard-coded colours elsewhere.
"""


class Colors:
    # Backgrounds
    BG        = "#0f1117"
    SURFACE   = "#1a1d27"
    SURFACE_2 = "#252836"

    # Accents
    ACCENT       = "#7c3aed"
    ACCENT_HOVER = "#6d28d9"
    ACCENT_LIGHT = "#8b5cf6"

    # Status
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR   = "#ef4444"
    INFO    = "#3b82f6"

    # Text
    TEXT       = "#e2e8f0"
    TEXT_DIM   = "#94a3b8"
    TEXT_MUTED = "#64748b"

    # Structural
    BORDER = "#2d3748"

    # Score colours (reused by gauge and bars)
    SCORE_GOOD = "#10b981"
    SCORE_MED  = "#f59e0b"
    SCORE_BAD  = "#ef4444"


class Fonts:
    TITLE       = ("Segoe UI", 16, "bold")
    HEADING     = ("Segoe UI", 13, "bold")
    SUBHEADING  = ("Segoe UI", 11, "bold")
    BODY        = ("Segoe UI", 10)
    BODY_BOLD   = ("Segoe UI", 10, "bold")
    SMALL       = ("Segoe UI", 9)
    MONO        = ("Consolas", 10)
    SCORE_BIG   = ("Segoe UI", 44, "bold")
    SCORE_LABEL = ("Segoe UI", 11)
