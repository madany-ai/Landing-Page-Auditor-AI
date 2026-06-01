"""Markdown report generator."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from schemas.analysis import AuditResult


_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _build_categories(result: AuditResult) -> list[tuple]:
    """Return (display_name, CategoryAnalysis, weight_pct) tuples."""
    return [
        ("Clarity",             result.clarity,           "20%"),
        ("Value Proposition",   result.value_proposition, "15%"),
        ("Offer Strength",      result.offer,             "15%"),
        ("Trust Signals",       result.trust,             "15%"),
        ("CTA Quality",         result.cta,               "10%"),
        ("ICP Alignment",       result.icp,               "10%"),
        ("Objection Handling",  result.objections,        "10%"),
        ("Friction",            result.friction,           "5%"),
    ]


def generate_markdown_report(
    result: AuditResult,
    url: str,
    output_dir: Path,
) -> Path:
    """Render the Markdown report and write it to *output_dir/report.md*."""
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)
    template = env.get_template("report.md.j2")

    context = {
        "url": url,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
        "categories": _build_categories(result),
    }

    rendered = template.render(**context)
    report_path = output_dir / "report.md"
    report_path.write_text(rendered, encoding="utf-8")
    logger.info(f"Markdown report → {report_path}")
    return report_path
