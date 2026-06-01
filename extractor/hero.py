"""Hero section extractor."""

from __future__ import annotations
from schemas.page import RawPage


def extract_hero(raw_page: RawPage) -> dict:
    """
    Extract the hero section: headline, sub-headline, supporting text.

    Strategy:
    - Headline    → first H1 (or first H2 if no H1 found)
    - Sub-headline → second heading
    - Supporting  → first substantive paragraph (>30 chars), or meta description
    """
    headings = raw_page.headings

    headline = headings[0] if headings else ""
    subheadline = headings[1] if len(headings) > 1 else ""

    supporting_text = ""
    for p in raw_page.paragraphs[:8]:
        if len(p) > 30:
            supporting_text = p
            break

    if not supporting_text:
        supporting_text = raw_page.meta_description

    return {
        "headline": headline,
        "subheadline": subheadline,
        "supporting_text": supporting_text,
    }
