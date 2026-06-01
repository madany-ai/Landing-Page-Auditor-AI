"""
CLI entry point — Landing Page Auditor AI.

Usage:
    python main.py <URL> [--model MODEL]
    python main.py gui
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import box
from rich.table import Table

# ── Bootstrap ────────────────────────────────────────────────────────────────
# Setup logging before anything else so all module imports are covered.
from config.logging import setup_logging
setup_logging()

# ── App ───────────────────────────────────────────────────────────────────────
app = typer.Typer(
    name="audit-page",
    help="🚀 Landing Page Auditor AI — AI-powered CRO analysis",
    add_completion=False,
    pretty_exceptions_enable=False,
)

console = Console()


def _banner() -> None:
    console.print(
        Panel.fit(
            "[bold magenta]🚀  Landing Page Auditor AI[/bold magenta]\n"
            "[dim]AI-Powered Conversion Rate Optimization[/dim]",
            box=box.ROUNDED,
            border_style="magenta",
            padding=(0, 2),
        )
    )


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command(name="audit", help="Audit a landing page.")
def audit_page(
    url: str = typer.Argument(..., help="Landing page URL to audit"),
    model: Optional[str] = typer.Option(
        None, "--model", "-m",
        help="LLM model override (e.g. google/gemini-flash-1.5)"
    ),
) -> None:
    """Run the full CRO audit pipeline on *url* and print a summary."""
    from pipeline import run_audit_pipeline
    from scoring.scoring_engine import get_score_grade, get_score_label, get_score_color_hex

    _banner()
    console.print(f"\n[cyan]Auditing:[/cyan] {url}\n")

    # ── Progress display ──────────────────────────────────────────────────────
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=28),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Initialising…", total=5)

        def _progress_cb(msg: str, step: int, total: int) -> None:
            progress.update(task, description=f"[{step}/{total}] {msg}", completed=step)

        try:
            data = run_audit_pipeline(url, model=model or None, progress_cb=_progress_cb)
        except Exception as exc:
            console.print(f"\n[bold red]❌  Audit failed:[/bold red] {exc}")
            raise typer.Exit(1) from exc

    # ── Results summary ───────────────────────────────────────────────────────
    result = data["result"]
    score  = data["overall_score"]
    grade  = get_score_grade(score)
    label  = get_score_label(score)

    score_style = "green" if score >= 70 else "yellow" if score >= 50 else "red"

    console.print()
    console.print(
        Panel(
            f"[bold {score_style}]Score: {score}/100  —  {grade} ({label})[/bold {score_style}]\n\n"
            f"[dim]{result.executive_summary}[/dim]",
            title="[bold]📊 Audit Complete[/bold]",
            box=box.ROUNDED,
            border_style=score_style,
        )
    )

    # Category table
    table = Table(title="Category Scores", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Category",  style="bold", width=22)
    table.add_column("Score",     justify="center", width=9)
    table.add_column("Weight",    justify="center", width=8)
    table.add_column("Rating",    width=14)

    rows = [
        ("Clarity",            result.clarity.score,           "20%"),
        ("Value Proposition",  result.value_proposition.score, "15%"),
        ("Offer Strength",     result.offer.score,             "15%"),
        ("Trust Signals",      result.trust.score,             "15%"),
        ("CTA Quality",        result.cta.score,               "10%"),
        ("ICP Alignment",      result.icp.score,               "10%"),
        ("Objection Handling", result.objections.score,        "10%"),
        ("Friction",           result.friction.score,           "5%"),
    ]
    for name, s, w in rows:
        c = "green" if s >= 7 else "yellow" if s >= 5 else "red"
        bar = "█" * int(s) + "░" * (10 - int(s))
        table.add_row(name, f"[{c}]{s}/10[/{c}]", w, f"[{c}]{bar}[/{c}]")

    console.print(table)

    # Revenue leaks
    console.print("\n[bold red]🚨 Top Revenue Leaks:[/bold red]")
    for i, leak in enumerate(result.top_revenue_leaks, 1):
        console.print(f"  [red]{i}.[/red] {leak}")

    # Report paths
    console.print(f"\n[bold green]✅ Reports saved:[/bold green]")
    console.print(f"  📄 Markdown : [cyan]{data['md_path']}[/cyan]")
    console.print(f"  🌐 HTML     : [cyan]{data['html_path']}[/cyan]")
    console.print(f"  📕 PDF      : [cyan]{data['pdf_path']}[/cyan]")


@app.command(name="gui", help="Launch the Tkinter GUI.")
def launch_gui() -> None:
    """Open the graphical interface."""
    from config.logging import setup_logging
    setup_logging()
    from gui.app import AuditorApp
    gui_app = AuditorApp()
    gui_app.mainloop()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Allow `python main.py <url>` as a shortcut for the audit command
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        sys.argv.insert(1, "audit")
    app()
