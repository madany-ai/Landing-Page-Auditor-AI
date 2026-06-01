"""
Main Tkinter application window for Landing Page Auditor AI.

Layout (horizontal):
  ┌─────────────┬──────────────────────┬───────────────────┐
  │ Left Panel  │   Log Console        │  Results Panel    │
  │ (inputs +   │   (live audit log)   │  (gauge + bars)   │
  │  buttons)   │                      │                   │
  └─────────────┴──────────────────────┴───────────────────┘

The audit pipeline runs in a background thread; results are
posted back to the main thread via a Queue polled every 100 ms.
"""

from __future__ import annotations

import os
import queue
import threading
import webbrowser
from pathlib import Path
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk

from gui.styles import Colors, Fonts
from gui.widgets import ScoreGauge, CategoryBar, LogConsole


# ── Model presets ─────────────────────────────────────────────────────────────
_MODELS = [
    "openrouter/owl-alpha",
]

_CATEGORY_KEYS = [
    ("Clarity",            "clarity"),
    ("Value Proposition",  "value_proposition"),
    ("Offer Strength",     "offer"),
    ("CTA Quality",        "cta"),
    ("Trust Signals",      "trust"),
    ("Friction",           "friction"),
    ("Objection Handling", "objections"),
    ("ICP Alignment",      "icp"),
]


class AuditorApp(tk.Tk):
    """Root window for Landing Page Auditor AI."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Landing Page Auditor AI")
        self.geometry("1160x730")
        self.minsize(1000, 650)
        self.configure(bg=Colors.BG)

        # State
        self._running = False
        self._html_path: Path | None = None
        self._md_path:   Path | None = None
        self._pdf_path:  Path | None = None
        self._queue: queue.Queue = queue.Queue()
        self._bar_widgets: dict[str, CategoryBar] = {}

        self._apply_ttk_style()
        self._build_ui()
        self._poll_queue()   # start queue polling loop

    # ══════════════════════════════════════════════════════════════════════════
    # Style
    # ══════════════════════════════════════════════════════════════════════════

    def _apply_ttk_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                        fieldbackground=Colors.SURFACE_2,
                        background=Colors.SURFACE_2,
                        foreground=Colors.TEXT,
                        selectbackground=Colors.SURFACE_2,
                        selectforeground=Colors.TEXT,
                        arrowcolor=Colors.ACCENT_LIGHT,
                        borderwidth=1,
                        relief="flat")
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", Colors.SURFACE_2)],
                  selectbackground=[("readonly", Colors.SURFACE_2)])

    # ══════════════════════════════════════════════════════════════════════════
    # UI Construction
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        self._build_header()
        self._build_main()

    # ── Header bar ────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=Colors.SURFACE, height=56)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Accent stripe
        tk.Frame(header, bg=Colors.ACCENT, height=3).pack(fill="x", side="top")

        row = tk.Frame(header, bg=Colors.SURFACE)
        row.pack(fill="both", expand=True, padx=18)

        tk.Label(row, text="🚀 Landing Page Auditor AI",
                 font=Fonts.TITLE, fg=Colors.TEXT, bg=Colors.SURFACE
                 ).pack(side="left", pady=0)

        tk.Label(row, text="  AI-Powered CRO Analysis",
                 font=Fonts.BODY, fg=Colors.TEXT_DIM, bg=Colors.SURFACE
                 ).pack(side="left")

    # ── Three-column layout ───────────────────────────────────────────────────

    def _build_main(self) -> None:
        main = tk.Frame(self, bg=Colors.BG)
        main.pack(fill="both", expand=True, padx=14, pady=14)

        self._left   = self._build_left_panel(main)
        self._center = self._build_center_panel(main)
        self._right  = self._build_right_panel(main)

    # ── Left panel ────────────────────────────────────────────────────────────

    def _build_left_panel(self, parent: tk.Widget) -> tk.Frame:
        panel = tk.Frame(parent, bg=Colors.SURFACE, width=275)
        panel.pack(side="left", fill="y", padx=(0, 12))
        panel.pack_propagate(False)

        inner = tk.Frame(panel, bg=Colors.SURFACE)
        inner.pack(fill="both", expand=True, padx=14, pady=16)

        # ── Title
        tk.Label(inner, text="Audit Settings",
                 font=Fonts.HEADING, fg=Colors.TEXT, bg=Colors.SURFACE
                 ).pack(anchor="w")
        self._divider(inner)

        # ── URL entry
        tk.Label(inner, text="Landing Page URL",
                 font=Fonts.SMALL, fg=Colors.TEXT_DIM, bg=Colors.SURFACE
                 ).pack(anchor="w", pady=(0, 4))

        url_frame = tk.Frame(inner, bg=Colors.SURFACE_2, bd=0)
        url_frame.pack(fill="x", pady=(0, 12))

        self._url_entry = tk.Entry(
            url_frame, font=Fonts.BODY,
            bg=Colors.SURFACE_2, fg=Colors.TEXT,
            insertbackground=Colors.ACCENT_LIGHT,
            relief="flat", bd=8, highlightthickness=0,
        )
        self._url_entry.pack(fill="x")
        self._url_entry.insert(0, "https://")
        self._url_entry.bind("<Return>", lambda _: self._start_audit())

        # ── Model dropdown
        tk.Label(inner, text="LLM Model",
                 font=Fonts.SMALL, fg=Colors.TEXT_DIM, bg=Colors.SURFACE
                 ).pack(anchor="w", pady=(0, 4))

        self._model_var = tk.StringVar(value=_MODELS[0])
        combo = ttk.Combobox(
            inner, textvariable=self._model_var,
            values=_MODELS, font=Fonts.BODY,
            style="Dark.TCombobox", state="normal",
        )
        combo.pack(fill="x", pady=(0, 20))

        # ── Run button
        self._run_btn = tk.Button(
            inner,
            text="🚀  Run Audit",
            font=("Segoe UI", 12, "bold"),
            bg=Colors.ACCENT, fg="white",
            activebackground=Colors.ACCENT_HOVER, activeforeground="white",
            relief="flat", cursor="hand2", pady=11,
            command=self._start_audit,
        )
        self._run_btn.pack(fill="x", pady=(0, 14))

        # ── Status
        self._divider(inner)
        self._status_lbl = tk.Label(
            inner, text="Ready to audit.",
            font=Fonts.SMALL, fg=Colors.TEXT_DIM, bg=Colors.SURFACE,
            wraplength=230, justify="left",
        )
        self._status_lbl.pack(anchor="w", pady=(8, 0))

        # Spacer
        tk.Frame(inner, bg=Colors.SURFACE).pack(fill="both", expand=True)

        # ── Report buttons (disabled until audit finishes)
        self._divider(inner)

        self._html_btn = tk.Button(
            inner, text="🌐  Open HTML Report",
            font=Fonts.SMALL, bg=Colors.SURFACE_2, fg=Colors.TEXT_MUTED,
            activebackground=Colors.SURFACE_2, activeforeground=Colors.TEXT,
            relief="flat", cursor="hand2", pady=9, state="disabled",
            command=self._open_html,
        )
        self._html_btn.pack(fill="x", pady=(8, 5))

        self._md_btn = tk.Button(
            inner, text="📄  Open Markdown Report",
            font=Fonts.SMALL, bg=Colors.SURFACE_2, fg=Colors.TEXT_MUTED,
            activebackground=Colors.SURFACE_2, activeforeground=Colors.TEXT,
            relief="flat", cursor="hand2", pady=9, state="disabled",
            command=self._open_md,
        )
        self._md_btn.pack(fill="x", pady=(0, 5))

        self._pdf_btn = tk.Button(
            inner, text="📕  Open PDF Report",
            font=Fonts.SMALL, bg=Colors.SURFACE_2, fg=Colors.TEXT_MUTED,
            activebackground=Colors.SURFACE_2, activeforeground=Colors.TEXT,
            relief="flat", cursor="hand2", pady=9, state="disabled",
            command=self._open_pdf,
        )
        self._pdf_btn.pack(fill="x")

        return panel

    # ── Center panel ──────────────────────────────────────────────────────────

    def _build_center_panel(self, parent: tk.Widget) -> LogConsole:
        log = LogConsole(parent)
        log.pack(side="left", fill="both", expand=True, padx=(0, 12))
        return log

    # ── Right panel ───────────────────────────────────────────────────────────

    def _build_right_panel(self, parent: tk.Widget) -> tk.Frame:
        panel = tk.Frame(parent, bg=Colors.SURFACE, width=295)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        inner = tk.Frame(panel, bg=Colors.SURFACE)
        inner.pack(fill="both", expand=True, padx=14, pady=16)

        # Title
        tk.Label(inner, text="Results",
                 font=Fonts.HEADING, fg=Colors.TEXT, bg=Colors.SURFACE
                 ).pack(anchor="w")
        self._divider(inner)

        # Gauge
        self._gauge = ScoreGauge(inner, size=190)
        self._gauge.pack(pady=(4, 2))

        # Score label
        self._score_lbl = tk.Label(
            inner, text="— Awaiting Audit —",
            font=Fonts.SCORE_LABEL, fg=Colors.TEXT_DIM, bg=Colors.SURFACE,
        )
        self._score_lbl.pack()

        self._divider(inner)

        # Category bars
        tk.Label(inner, text="Category Scores",
                 font=("Segoe UI", 9, "bold"), fg=Colors.TEXT_DIM,
                 bg=Colors.SURFACE,
                 ).pack(anchor="w", pady=(0, 5))

        self._bars_frame = tk.Frame(inner, bg=Colors.SURFACE)
        self._bars_frame.pack(fill="x")

        for display_name, _ in _CATEGORY_KEYS:
            bar = CategoryBar(self._bars_frame, display_name, score=0)
            bar.pack(fill="x", pady=2)
            self._bar_widgets[display_name] = bar

        return panel

    # ══════════════════════════════════════════════════════════════════════════
    # Audit lifecycle
    # ══════════════════════════════════════════════════════════════════════════

    def _start_audit(self) -> None:
        if self._running:
            return

        url = self._url_entry.get().strip()
        if not url or url in ("https://", "http://", ""):
            messagebox.showerror("Missing URL", "Please enter a valid landing page URL.")
            return

        model = self._model_var.get().strip() or None

        # Reset UI
        self._running = True
        self._run_btn.config(state="disabled", text="⏳  Running…")
        self._html_btn.config(state="disabled", fg=Colors.TEXT_MUTED)
        self._md_btn.config(state="disabled",   fg=Colors.TEXT_MUTED)
        self._status_lbl.config(text="Audit in progress…", fg=Colors.TEXT_DIM)
        self._center.clear()
        self._gauge.set_score(0)
        self._score_lbl.config(text="Analysing…", fg=Colors.TEXT_DIM)

        self._center.log(f"Starting audit: {url}", "info")
        self._center.log(f"Model: {model or 'default'}", "dim")
        self._center.log("─" * 50, "dim")

        threading.Thread(
            target=self._audit_thread,
            args=(url, model),
            daemon=True,
        ).start()

    def _audit_thread(self, url: str, model: str | None) -> None:
        """Background thread: runs pipeline and posts results to queue."""
        try:
            from pipeline import run_audit_pipeline

            def cb(msg: str, step: int, total: int) -> None:
                self._queue.put(("log",    f"[{step}/{total}] {msg}", "step"))
                self._queue.put(("status", f"Step {step}/{total}: {msg}"))

            data = run_audit_pipeline(url, model=model, progress_cb=cb)
            self._queue.put(("done", data))

        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    # ── Queue polling ─────────────────────────────────────────────────────────

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self._queue.get_nowait()
                kind = item[0]

                if kind == "log":
                    _, msg, tag = item
                    self._center.log(msg, tag)

                elif kind == "status":
                    _, msg = item
                    self._status_lbl.config(text=msg, fg=Colors.TEXT_DIM)

                elif kind == "done":
                    _, data = item
                    self._on_complete(data)

                elif kind == "error":
                    _, err = item
                    self._on_error(err)

        except queue.Empty:
            pass

        self.after(100, self._poll_queue)

    # ── Completion / error handlers ───────────────────────────────────────────

    def _on_complete(self, data: dict) -> None:
        from scoring.scoring_engine import get_score_grade, get_score_label

        result = data["result"]
        score  = data["overall_score"]
        grade  = get_score_grade(score)
        label  = get_score_label(score)

        self._html_path = data.get("html_path")
        self._md_path   = data.get("md_path")
        self._pdf_path  = data.get("pdf_path")

        # Gauge
        self._gauge.set_score(score)

        # Score label
        color = Colors.SCORE_GOOD if score >= 70 else Colors.SCORE_MED if score >= 50 else Colors.SCORE_BAD
        self._score_lbl.config(text=f"{score}/100  —  {grade}  ({label})", fg=color)

        # Rebuild category bars
        for widget in self._bars_frame.winfo_children():
            widget.destroy()
        self._bar_widgets.clear()

        for display_name, attr in _CATEGORY_KEYS:
            cat = getattr(result, attr)
            bar = CategoryBar(self._bars_frame, display_name, score=cat.score)
            bar.pack(fill="x", pady=2)
            self._bar_widgets[display_name] = bar

        # Log summary
        self._center.log("\n" + "═" * 50, "dim rtl")
        self._center.log(f"✅ Audit complete!  Score: {score}/100  ({grade} — {label})", "success rtl")
        self._center.log("═" * 50, "dim rtl")
        self._center.log("\n🚨 Top Revenue Leaks:", "step rtl")
        for i, leak in enumerate(result.top_revenue_leaks, 1):
            self._center.log(f"   {i}. {leak}", "rtl")
        if self._html_path:
            self._center.log(f"\n📄 HTML report: {self._html_path}", "dim rtl")

        # Enable report buttons
        if self._html_path:
            self._html_btn.config(state="normal", fg=Colors.ACCENT_LIGHT)
        if self._md_path:
            self._md_btn.config(state="normal", fg=Colors.TEXT)
        if self._pdf_path:
            self._pdf_btn.config(state="normal", fg=Colors.SCORE_BAD)

        self._running = False
        self._run_btn.config(state="normal", text="🚀  Run Audit")
        self._status_lbl.config(
            text=f"✅ Done! Score: {score}/100", fg=Colors.SUCCESS
        )

    def _on_error(self, error_msg: str) -> None:
        self._center.log(f"\n❌ Error: {error_msg}", "error")
        self._running = False
        self._run_btn.config(state="normal", text="🚀  Run Audit")
        self._status_lbl.config(text="❌ Error — see log.", fg=Colors.ERROR)
        messagebox.showerror("Audit Failed", f"The audit encountered an error:\n\n{error_msg}")

    # ══════════════════════════════════════════════════════════════════════════
    # Report openers
    # ══════════════════════════════════════════════════════════════════════════

    def _open_html(self) -> None:
        if self._html_path and Path(self._html_path).exists():
            webbrowser.open(Path(self._html_path).resolve().as_uri())

    def _open_md(self) -> None:
        if self._md_path and Path(self._md_path).exists():
            try:
                os.startfile(str(self._md_path))   # Windows
            except AttributeError:
                webbrowser.open(str(self._md_path))

    def _open_pdf(self) -> None:
        if self._pdf_path and Path(self._pdf_path).exists():
            try:
                os.startfile(str(self._pdf_path))   # Windows
            except AttributeError:
                webbrowser.open(str(self._pdf_path))

    # ══════════════════════════════════════════════════════════════════════════
    # Utilities
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _divider(parent: tk.Widget) -> None:
        tk.Frame(parent, bg=Colors.BORDER, height=1).pack(fill="x", pady=10)
