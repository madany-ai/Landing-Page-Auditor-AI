"""Testimonials / reviews extractor."""

from __future__ import annotations
import re
from schemas.page import RawPage

# Quoted text patterns (straight and curly quotes)
_QUOTE_PATTERNS = [
    re.compile(r'"([^"]{25,400})"'),
    re.compile(r'\u201c([^\u201d]{25,400})\u201d'),
    re.compile(r"'([^']{25,400})'"),
]

_TESTIMONIAL_KEYWORDS = {
    "love", "amazing", "fantastic", "excellent", "great",
    "highly recommend", "best", "helped", "changed", "transformed",
    "rating", "stars", "reviewed", "verified", "customer", "client",
    "★", "⭐", "5/5", "4/5", "10/10",
    # Arabic keywords
    "رائع", "ممتاز", "عظيم", "أنصح به", "تقييم", "عملاء",
    "أفضل", "ساعدنا", "غير", "مذهل", "نجمة"
}


def extract_testimonials(raw_page: RawPage) -> list[str]:
    """
    Extract testimonial text from:
    1. Blockquote elements
    2. Quoted patterns in paragraphs
    3. List items with social-proof signals
    """
    collected: list[str] = list(raw_page.blockquotes[:8])

    full_text = "\n".join(raw_page.paragraphs)

    for pattern in _QUOTE_PATTERNS:
        for match in pattern.findall(full_text):
            if any(kw in match.lower() for kw in _TESTIMONIAL_KEYWORDS):
                collected.append(match.strip())

    # Short list items with social-proof signals
    for item in raw_page.list_items:
        if 20 < len(item) < 300 and any(kw in item.lower() for kw in _TESTIMONIAL_KEYWORDS):
            collected.append(item)

    # Deduplicate
    seen: set[str] = set()
    unique: list[str] = []
    for t in collected:
        key = t[:60].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(t)

    return unique[:8]
