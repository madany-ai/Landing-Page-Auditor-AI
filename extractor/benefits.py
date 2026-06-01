"""Benefits section extractor."""

from __future__ import annotations
from schemas.page import RawPage

_BENEFIT_KEYWORDS = {
    "benefit", "why", "advantage", "value", "gain", "result",
    "achieve", "save", "earn", "grow", "improve", "transform",
    "get ", "boost", "increase", "reduce", "eliminate", "solve",
    # Arabic keywords
    "فائدة", "ميزة", "لماذا", "قيمة", "نتيجة",
    "حقق", "وفر", "اكسب", "اربح", "نمو", "حسّن",
    "تطوير", "زيادة", "تقليل", "تخلص", "حل"
}


def _is_benefit(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _BENEFIT_KEYWORDS)


def extract_benefits(raw_page: RawPage) -> list[str]:
    """
    Extract benefit statements from list items and short paragraphs.
    Returns up to 10 unique benefit strings.
    """
    candidates: list[str] = []

    # List items are the most common carrier of benefits
    for item in raw_page.list_items:
        if 15 < len(item) < 300 and _is_benefit(item):
            candidates.append(item)

    # Short paragraphs that look like benefit statements
    for p in raw_page.paragraphs:
        if 20 < len(p) < 200 and _is_benefit(p):
            candidates.append(p)

    # Deduplicate by prefix
    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        key = c[:60].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique[:10]
