"""
CLI entry point — Landing Page Auditor AI.

Usage:
    python main.py <URL> [--model MODEL]
    python main.py compare <URL> [--competitors 3]
    python main.py serve [--port 7860]
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
from config.logging import setup_logging
setup_logging()

# ── App ───────────────────────────────────────────────────────────────────────
app = typer.Typer(
    name="audit-page",
    help="Landing Page Auditor AI -- AI-powered CRO analysis",
    add_completion=False,
    pretty_exceptions_enable=False,
)

console = Console()


def _banner() -> None:
    console.print(
        Panel.fit(
            "[bold magenta]Landing Page Auditor AI[/bold magenta]\n"
            "[dim]AI-Powered Conversion Rate Optimization[/dim]",
            box=box.ROUNDED,
            border_style="magenta",
            padding=(0, 2),
        )
    )


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command(name="audit", help="Generate a Full Intelligence Report (Audit + Competitors).")
def audit_page(
    url: str = typer.Argument(..., help="Your landing page URL"),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model override"
    ),
    competitors: int = typer.Option(
        3, "--competitors", "-c", help="Number of competitors to discover"
    ),
    market: str = typer.Option(
        "Global", "--market", "-k", help="Target market (e.g. Egypt, Global)"
    ),
) -> None:
    """Discover competitors, audit them, and generate a Full Intelligence Report."""
    from competitors.comparator import run_competitor_pipeline
    from scoring.scoring_engine import get_score_grade

    _banner()
    console.print(f"\n[cyan]Intelligence Report for:[/cyan] {url}")
    console.print(f"[dim]Discovering up to {competitors} competitor(s) in market: {market}…[/dim]\n")

    total_steps = 3 + competitors
    with Progress(
        SpinnerColumn(spinner_name="line"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=28),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Initialising…", total=total_steps)

        def _progress_cb(msg: str, step: int, total: int) -> None:
            progress.update(task, description=f"[{step}/{total}] {msg}", completed=step, total=total)

        try:
            result = run_competitor_pipeline(
                url, model=model or None,
                market=market,
                num_competitors=competitors,
                progress_cb=_progress_cb,
            )
        except Exception as exc:
            console.print(f"\n[bold red]Analysis failed:[/bold red] {exc}")
            raise typer.Exit(1) from exc

    # Results
    target = result.target
    score_style = "green" if target.overall_score >= 70 else "yellow" if target.overall_score >= 50 else "red"

    console.print()
    console.print(Panel(
        f"[bold]Your Score:[/bold] [{score_style}]{target.overall_score}/100 ({target.grade})[/{score_style}]",
        title="[bold]Competitive Analysis[/bold]",
        box=box.ROUNDED,
        border_style="magenta",
    ))

    # Comparison table
    table = Table(title="Score Comparison", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Page", width=30)
    table.add_column("Score", justify="center", width=12)
    table.add_column("Grade", justify="center", width=8)

    c = "green" if target.overall_score >= 70 else "yellow" if target.overall_score >= 50 else "red"
    table.add_row(f">  {target.domain}", f"[{c}]{target.overall_score}/100[/{c}]", target.grade)

    for comp in result.competitors:
        if comp.overall_score > 0:
            c = "green" if comp.overall_score >= 70 else "yellow" if comp.overall_score >= 50 else "red"
            table.add_row(f"-  {comp.domain}", f"[{c}]{comp.overall_score}/100[/{c}]", comp.grade)
        else:
            table.add_row(f"-  {comp.domain}", "[red]Failed[/red]", "N/A")

    console.print(table)

    # Insights
    insights = result.insights
    if insights.quick_wins:
        console.print("\n[bold green]Quick Wins:[/bold green]")
        for win in insights.quick_wins:
            console.print(f"  * {win}")

    if insights.deep_insights:
        console.print("\n[bold cyan]Strategic Insights:[/bold cyan]")
        for ins in insights.deep_insights:
            console.print(f"\n  [bold]{ins.observation}[/bold]")
            console.print(f"  [dim]Evidence: {ins.evidence}[/dim]")
            console.print(f"  [yellow]Impact: {ins.impact}[/yellow]")
            console.print(f"  [green]Rec: {ins.recommendation}[/green]")

    if insights.action_plan:
        console.print("\n[bold magenta]Prioritized Action Plan:[/bold magenta]")
        for action in insights.action_plan:
            console.print(f"  {action.priority}. [bold]{action.title}[/bold] (Impact: {action.expected_impact}, Effort: {action.effort})")
            console.print(f"     [dim]{action.description}[/dim]")


@app.command(name="serve", help="Launch the Gradio web UI.")
def serve(
    port: int = typer.Option(7860, "--port", "-p", help="Server port"),
    share: bool = typer.Option(False, "--share", help="Create a public Gradio link"),
) -> None:
    """Start the Gradio web interface."""
    _banner()
    console.print(f"\n[cyan]Starting web UI on port {port}…[/cyan]\n")

    import subprocess
    import sys
    import os
    
    env = os.environ.copy()
    env["GRADIO_SERVER_PORT"] = str(port)
    if share:
        env["GRADIO_SHARE"] = "True"
        
    try:
        subprocess.run([sys.executable, "server.py"], env=env)
    except KeyboardInterrupt:
        pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Allow `python main.py <url>` as a shortcut for the audit command
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        sys.argv.insert(1, "audit")
    app()
