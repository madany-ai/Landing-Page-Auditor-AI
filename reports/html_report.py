"""HTML report generator."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from schemas.analysis import AuditResult
from scoring.scoring_engine import get_score_grade, get_score_label, get_score_color_hex


_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _build_categories(result: AuditResult) -> list[tuple]:
    """Return (display_name, CategoryAnalysis, weight_int) tuples."""
    return [
        ("Clarity",             result.clarity,           20),
        ("Value Proposition",   result.value_proposition, 15),
        ("Offer Strength",      result.offer,             15),
        ("Trust Signals",       result.trust,             15),
        ("CTA Quality",         result.cta,               10),
        ("ICP Alignment",       result.icp,               10),
        ("Objection Handling",  result.objections,        10),
        ("Friction",            result.friction,           5),
    ]


def _category_color(score: float) -> str:
    if score >= 7:
        return "#10b981"
    if score >= 5:
        return "#f59e0b"
    return "#ef4444"


def generate_html_report(
    result: AuditResult,
    url: str,
    output_dir: Path,
    comparison_result = None,
) -> Path:
    """Render the HTML report and write it to *output_dir/report.html*."""
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)
    # Allow math in templates
    env.globals["round"] = round
    template = env.get_template("report.html.j2")

    score = result.overall_score or 0.0
    # SVG arc: semicircle radius=90, arc length ≈ π*90 ≈ 282.74
    arc_length = 282.74
    score_dash = round((score / 100) * arc_length, 1)

    context = {
        "url": url,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
        "categories": _build_categories(result),
        "score_color": get_score_color_hex(score),
        "score_grade": get_score_grade(score),
        "score_label": get_score_label(score),
        "score_dash": score_dash,
        "arc_length": arc_length,
        "category_color": _category_color,
        "comparison": comparison_result,
    }

    rendered = template.render(**context)
    report_path = output_dir / "report.html"
    report_path.write_text(rendered, encoding="utf-8")
    logger.info(f"HTML report → {report_path}")
    return report_path
