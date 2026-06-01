"""FAQ section extractor."""

from __future__ import annotations
import re
from schemas.page import RawPage

_FAQ_TRIGGERS = {
    "faq", "frequently asked", "common question", "have questions", "got questions",
    "أسئلة", "شائعة", "سؤال", "استفسارات"
}
_QA_PATTERN = re.compile(
    r"(?:Q|س)[:\.]\s*(.+?)\s*(?:A|ج)[:\.]\s*(.+?)(?=(?:Q|س)[:\.]|$)",
    re.IGNORECASE | re.DOTALL,
)


def extract_faq(raw_page: RawPage) -> list[dict]:
    """
    Extract FAQ items from:
    1. Question-mark headings
    2. Explicit Q: A: patterns in body text
    """
    body_lower = raw_page.body_text.lower()

    # Only proceed if there are FAQ indicators
    has_faq = any(trigger in body_lower for trigger in _FAQ_TRIGGERS)
    has_questions = any("?" in h for h in raw_page.headings)

    if not has_faq and not has_questions:
        return []

    faq: list[dict] = []

    # Headings that are questions
    for heading in raw_page.headings:
        if "?" in heading and len(heading) > 10:
            faq.append({"question": heading.strip(), "answer": ""})

    # Explicit Q: A: format in body text
    for match in _QA_PATTERN.finditer(raw_page.body_text[:6000]):
        q = match.group(1).strip()
        a = match.group(2).strip()[:300]
        if len(q) > 10:
            faq.append({"question": q, "answer": a})

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for item in faq:
        key = item["question"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:10]
