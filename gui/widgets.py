"""
Reusable Tkinter widgets for the Landing Page Auditor GUI.

ScoreGauge   — circular progress ring with central score number
CategoryBar  — labelled progress bar row for one CRO category
LogConsole   — dark scrollable text console for audit log output
"""

from __future__ import annotations
import tkinter as tk
import arabic_reshaper
from bidi.algorithm import get_display
from gui.styles import Colors, Fonts


# ── ScoreGauge ────────────────────────────────────────────────────────────────

class ScoreGauge(tk.Canvas):
    """
    Circular progress ring that visualises the 0–100 CRO score.

    Drawing strategy:
      • Gray full-circle outline   → background ring
      • Coloured arc (clockwise from 12 o'clock) → score fill
      • Large number + label       → drawn in the centre
    """

    def __init__(self, parent: tk.Widget, size: int = 200, **kwargs):
        super().__init__(
            parent,
            width=size, height=size,
            bg=Colors.SURFACE,
            highlightthickness=0,
            **kwargs,
        )
        self._size = size
        self.set_score(0)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_score(self, score: float) -> None:
        """Redraw the gauge for *score* (0–100)."""
        self.delete("all")
        self._draw(score)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _score_color(score: float) -> str:
        if score >= 70:
            return Colors.SCORE_GOOD
        if score >= 50:
            return Colors.SCORE_MED
        return Colors.SCORE_BAD

    def _draw(self, score: float) -> None:
        s = self._size
        pad = 22
        cx = cy = s // 2
        x0, y0, x1, y1 = pad, pad, s - pad, s - pad

        # Background ring
        self.create_oval(x0, y0, x1, y1, outline=Colors.BORDER, width=14, fill="")

        # Score arc — start=90° (12 o'clock), negative extent = clockwise
        if score > 0:
            color = self._score_color(score)
            extent = -(score / 100) * 359.9   # full circle at 100%
            self.create_arc(
                x0, y0, x1, y1,
                start=90, extent=extent,
                style="arc", outline=color, width=14,
            )

        # Centre text
        color = self._score_color(score) if score > 0 else Colors.TEXT_MUTED
        self.create_text(
            cx, cy - 10,
            text=f"{int(score)}" if score > 0 else "—",
            font=Fonts.SCORE_BIG,
            fill=color,
        )
        self.create_text(
            cx, cy + 30,
            text="out of 100",
            font=Fonts.SMALL,
            fill=Colors.TEXT_DIM,
        )


# ── CategoryBar ───────────────────────────────────────────────────────────────

class CategoryBar(tk.Frame):
    """
    One row in the category-scores panel.

    Layout: [Label 14ch] [Canvas progress bar] [Score 5ch]
    The canvas redraws itself whenever it is resized.
    """

    def __init__(
        self,
        parent: tk.Widget,
        name: str,
        score: float = 0.0,
        **kwargs,
    ):
        super().__init__(parent, bg=Colors.SURFACE, **kwargs)
        self._score = score
        self._color = self._score_color(score)
        self._build(name, score)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _score_color(score: float) -> str:
        if score >= 7:
            return Colors.SCORE_GOOD
        if score >= 5:
            return Colors.SCORE_MED
        return Colors.SCORE_BAD

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self, name: str, score: float) -> None:
        self.columnconfigure(1, weight=1)

        # Name label (fixed width)
        tk.Label(
            self,
            text=name[:15],
            font=Fonts.SMALL,
            fg=Colors.TEXT_DIM,
            bg=Colors.SURFACE,
            anchor="w",
            width=13,
        ).grid(row=0, column=0, sticky="w", padx=(0, 4))

        # Canvas bar (expands)
        self._canvas = tk.Canvas(
            self,
            height=7,
            bg=Colors.SURFACE,
            highlightthickness=0,
        )
        self._canvas.grid(row=0, column=1, sticky="ew", padx=2, pady=4)
        self._canvas.bind("<Configure>", self._redraw)

        # Score label
        tk.Label(
            self,
            text=f"{score:.1f}",
            font=Fonts.BODY_BOLD,
            fg=self._color,
            bg=Colors.SURFACE,
            width=4,
            anchor="e",
        ).grid(row=0, column=2, padx=(4, 0))

    def _redraw(self, event: tk.Event | None = None) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w <= 1:
            return
        self._canvas.delete("all")
        # Background track
        self._canvas.create_rectangle(0, 1, w, h - 1, fill=Colors.BORDER, outline="")
        # Fill
        fill_w = int((self._score / 10) * w)
        if fill_w > 0:
            self._canvas.create_rectangle(0, 1, fill_w, h - 1, fill=self._color, outline="")


# ── LogConsole ────────────────────────────────────────────────────────────────

class LogConsole(tk.Frame):
    """
    Scrollable, read-only text widget styled for dark console output.

    Supports coloured tags: 'step', 'success', 'error', 'warning', 'dim'.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=Colors.SURFACE_2, **kwargs)
        self._build()

    def _build(self) -> None:
        # Title bar
        title_bar = tk.Frame(self, bg=Colors.SURFACE_2)
        title_bar.pack(fill="x")

        tk.Label(
            title_bar,
            text="📋  Audit Log",
            font=Fonts.SUBHEADING,
            fg=Colors.TEXT,
            bg=Colors.SURFACE_2,
            anchor="w",
            padx=12, pady=8,
        ).pack(side="left")

        # Divider
        tk.Frame(self, bg=Colors.BORDER, height=1).pack(fill="x")

        # Text + scrollbar
        text_frame = tk.Frame(self, bg=Colors.SURFACE_2)
        text_frame.pack(fill="both", expand=True)

        sb = tk.Scrollbar(text_frame, bg=Colors.SURFACE_2, troughcolor=Colors.SURFACE_2)
        sb.pack(side="right", fill="y")

        self._text = tk.Text(
            text_frame,
            font=Fonts.MONO,
            bg=Colors.SURFACE_2,
            fg=Colors.TEXT,
            insertbackground=Colors.ACCENT,
            selectbackground=Colors.ACCENT,
            yscrollcommand=sb.set,
            state="disabled",
            wrap="word",
            padx=12, pady=8,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        self._text.pack(side="left", fill="both", expand=True)
        sb.config(command=self._text.yview)

        # Colour tags
        self._text.tag_config("step",    foreground=Colors.ACCENT_LIGHT)
        self._text.tag_config("success", foreground=Colors.SUCCESS)
        self._text.tag_config("error",   foreground=Colors.ERROR)
        self._text.tag_config("warning", foreground=Colors.WARNING)
        self._text.tag_config("dim",     foreground=Colors.TEXT_MUTED)
        self._text.tag_config("info",    foreground=Colors.INFO)
        
        # Alignment tags
        self._text.tag_config("rtl",     justify="right")

    # ── Public API ────────────────────────────────────────────────────────────

    def log(self, message: str, tag: str = "") -> None:
        """Append *message* to the console, optionally with a colour *tag*."""
        # Fix Arabic rendering in Tkinter Text widget
        reshaped = arabic_reshaper.reshape(message)
        bidi_text = get_display(reshaped)

        self._text.config(state="normal")
        if tag:
            tags = tuple(tag.split())
            self._text.insert("end", bidi_text + "\n", tags)
        else:
            self._text.insert("end", bidi_text + "\n")
        self._text.see("end")
        self._text.config(state="disabled")

    def clear(self) -> None:
        """Clear all text from the console."""
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        self._text.config(state="disabled")
