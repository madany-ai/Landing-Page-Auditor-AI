"""
Full audit pipeline orchestrator.

Both the CLI (main.py) and the GUI (gui/app.py) import and call
``run_audit_pipeline()``. Neither entry point duplicates pipeline logic.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

from loguru import logger

from scraper.page_loader import load_page
from extractor.extractor import extract_content
from llm.analyzer import analyze
from scoring.scoring_engine import calculate_score
from reports.markdown_report import generate_markdown_report
from reports.html_report import generate_html_report
from reports.pdf_report import generate_pdf_report
from schemas.page import RawPage, LandingPageContent
from schemas.analysis import AuditResult


# Type alias: progress_cb(message, current_step, total_steps)
ProgressCallback = Callable[[str, int, int], None]


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_output_dir(url: str) -> Path:
    """Create and return an output directory based on domain + timestamp."""
    parsed = urlparse(url)
    domain = (
        parsed.netloc
        .replace("www.", "")
        .replace(".", "_")
        .replace(":", "_")
    ) or "unknown"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / f"{domain}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# ── Public API ────────────────────────────────────────────────────────────────

def run_audit_pipeline(
    url: str,
    model: Optional[str] = None,
    progress_cb: Optional[ProgressCallback] = None,
    skip_reports: bool = False,
) -> dict:
    """
    Execute the complete landing-page audit pipeline.

    Steps:
        1. Fetch page          (scraper layer)
        2. Extract content     (extractor layer)
        3. LLM analysis        (llm layer)
        4. Calculate score     (scoring layer)
        5. Generate reports    (reports layer)

    Args:
        url:         Landing page URL to audit.
        model:       Optional LLM model override.
        progress_cb: Optional callback(msg, step, total) for live progress.
        skip_reports: If True, do not generate the standalone PDF/HTML/MD reports.

    Returns:
        dict with keys: raw_page, content, result, overall_score,
                        md_path, html_path, output_dir
    """
    total = 5 if not skip_reports else 4

    def notify(msg: str, step: int) -> None:
        logger.info(f"[{step}/{total}] {msg}")
        if progress_cb:
            progress_cb(msg, step, total)

    # ── Step 1 ────────────────────────────────────────────────────────────────
    notify("Fetching page…", 1)
    raw_page: RawPage = load_page(url)

    # ── Step 2 ────────────────────────────────────────────────────────────────
    notify("Extracting content…", 2)
    content: LandingPageContent = extract_content(raw_page)

    # ── Step 3 ────────────────────────────────────────────────────────────────
    notify("Running AI analysis…", 3)
    result: AuditResult = analyze(content, url=url, model=model)

    # ── Step 4 ────────────────────────────────────────────────────────────────
    notify("Calculating score…", 4)
    overall_score = calculate_score(result)
    result.overall_score = overall_score

    # ── Step 5 ────────────────────────────────────────────────────────────────
    md_path, html_path, pdf_path = None, None, None
    output_dir = get_output_dir(url)

    if not skip_reports:
        notify("Generating reports…", 5)
        md_path = generate_markdown_report(result, url, output_dir)
        html_path = generate_html_report(result, url, output_dir)
        pdf_path = generate_pdf_report(md_path)
        logger.success(f"Audit complete — score: {overall_score}/100 → {output_dir}")
    else:
        logger.success(f"Audit analysis complete — score: {overall_score}/100")

    return {
        "raw_page": raw_page,
        "content": content,
        "result": result,
        "overall_score": overall_score,
        "md_path": md_path,
        "html_path": html_path,
        "pdf_path": pdf_path,
        "output_dir": output_dir,
    }
