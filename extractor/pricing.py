"""Pricing section extractor."""

from __future__ import annotations
import re
from schemas.page import RawPage

_PRICE_RE = re.compile(
    r"(\$|€|£|USD|EUR|GBP|ر\.س|درهم|ج\.م|ريال|د\.ك|د\.إ)\s*\d[\d,\.]*"
    r"|\d[\d,\.]*\s*(\$|€|£|USD|EUR|GBP|ر\.س|درهم|ج\.م|ريال|د\.ك|د\.إ)"
    r"|free trial|free plan|pricing|per month|per year|\/mo|\/yr|\/user"
    r"|مجانا|شهريا|سنويا|خطة|أسعار|سعر",
    re.IGNORECASE,
)

_TIER_KEYWORDS = {
    "free", "starter", "basic", "pro", "plus", "professional",
    "business", "enterprise", "team", "growth", "scale",
    "مجاني", "أساسي", "احترافي", "متقدم", "شركات", "أعمال"
}


def extract_pricing(raw_page: RawPage) -> list[dict]:
    """
    Extract pricing plan information.

    Looks for:
    - Heading tiers (Free, Pro, Enterprise, etc.)
    - Paragraphs and list items containing price patterns
    """
    pricing: list[dict] = []

    # Tier headings
    for heading in raw_page.headings:
        if any(kw in heading.lower() for kw in _TIER_KEYWORDS) and len(heading) < 60:
            pricing.append({"plan": heading, "price": "see page"})

    # Paragraphs / list items with price signals
    for text in raw_page.paragraphs + raw_page.list_items:
        if _PRICE_RE.search(text) and len(text) < 250:
            pricing.append({"detail": text.strip()})

    # If no pricing detected at all
    if not pricing and not _PRICE_RE.search(raw_page.body_text):
        return [{"note": "No pricing information detected on page"}]

    # Deduplicate by first 60 chars
    seen: set[str] = set()
    unique: list[dict] = []
    for item in pricing:
        key = str(item)[:60]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:10]
