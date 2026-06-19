"""Generator for comparison reports (HTML and PDF)."""

from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from loguru import logger
from schemas.comparison import ComparisonResult


def generate_comparison_html(
    result: ComparisonResult,
    output_dir: Path,
) -> Path:
    """Generate the HTML comparison report."""
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("comparison.html.j2")

    html_content = template.render(
        target=result.target,
        competitors=result.competitors,
        insights=result.insights,
    )

    html_path = output_dir / "comparison_report.html"
    html_path.write_text(html_content, encoding="utf-8")
    return html_path


def generate_comparison_pdf(
    html_path: Path,
    output_dir: Path,
) -> Path:
    """Generate a PDF comparison report from the HTML file."""
    # We can reuse the pdf generation logic, but it needs an MD path currently.
    # The current PDF implementation (markdown-pdf) requires markdown.
    # Since we didn't build a markdown version of the comparison yet, 
    # we'll just skip PDF for comparison for now to keep it simple, 
    # or return None.
    logger.info("PDF generation for comparison is not yet implemented. Skipping.")
    return Path("")
