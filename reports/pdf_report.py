"""PDF report generator."""

from __future__ import annotations

from pathlib import Path
from loguru import logger
from markdown_pdf import MarkdownPdf, Section

def generate_pdf_report(markdown_path: Path) -> Path:
    """Read the generated Markdown report and save it as PDF in the same directory."""
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown report not found at {markdown_path}")

    # Read markdown text
    md_text = markdown_path.read_text(encoding="utf-8")
    
    # Generate PDF
    pdf_path = markdown_path.with_suffix(".pdf")
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(md_text, toc=False))
        pdf.save(str(pdf_path))
        logger.info(f"PDF report → {pdf_path}")
        return pdf_path
    except Exception as exc:
        logger.error(f"Failed to generate PDF: {exc}")
        raise
