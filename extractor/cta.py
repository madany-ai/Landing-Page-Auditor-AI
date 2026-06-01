"""CTA buttons extractor."""

from __future__ import annotations
from schemas.page import RawPage

_CTA_KEYWORDS = {
    "get started", "sign up", "start free", "try", "buy", "order",
    "download", "register", "join", "book", "schedule", "contact",
    "request", "demo", "free trial", "get", "start", "subscribe",
    "access", "claim", "grab", "learn more", "see how", "watch",
    "explore", "discover", "yes", "activate", "unlock", "begin",
    # Arabic keywords
    "ابدأ", "سجل", "اشترك", "جرب", "شراء", "اطلب",
    "حمل", "انضم", "احجز", "تواصل", "طلب", "تجربة مجانية",
    "احصل", "اكتشف", "تعرف على المزيد", "شاهد", "تفعيل"
}


def _is_cta(text: str) -> bool:
    lower = text.lower().strip()
    return any(kw in lower for kw in _CTA_KEYWORDS)


def extract_cta_buttons(raw_page: RawPage) -> list[str]:
    """
    Return unique CTA button labels from the page.

    All buttons are included; CTA-like ones are listed first.
    """
    cta_first: list[str] = []
    other: list[str] = []

    for btn in raw_page.buttons:
        if btn and len(btn) > 1:
            if _is_cta(btn):
                cta_first.append(btn)
            else:
                other.append(btn)

    combined = cta_first + other

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in combined:
        key = c.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique[:15]
