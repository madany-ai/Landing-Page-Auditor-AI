"""
Content extraction orchestrator.

Converts a RawPage into a LandingPageContent by running each section
extractor in sequence. No HTML is forwarded — only structured text.
"""

from __future__ import annotations

import time
from loguru import logger

from schemas.page import RawPage, LandingPageContent
from extractor.hero import extract_hero
from extractor.benefits import extract_benefits
from extractor.testimonials import extract_testimonials
from extractor.pricing import extract_pricing
from extractor.faq import extract_faq
from extractor.cta import extract_cta_buttons


# ── Inline extractors for smaller sections ────────────────────────────────────

_FEATURE_KEYWORDS = {
    "feature", "capability", "integration", "support", "include",
    "work with", "compatible", "platform", "tool", "function",
    "dashboard", "report", "analytic", "automati", "connect",
    # Arabic keywords
    "ميزة", "ميزات", "قدرة", "تكامل", "دعم", "يشمل", "يتضمن",
    "متوافق", "منصة", "أداة", "وظيفة", "لوحة", "تقرير", "تحليل",
    "ربط", "خصائص"
}

_SOCIAL_PROOF_KEYWORDS = {
    "customers", "users", "companies", "trusted by", "client",
    "rated", "reviews", "stars", "5/5", "★", "10,000", "100,000",
    "million", "businesses",
    # Arabic keywords
    "عملاء", "مستخدمين", "شركات", "موثوق", "تقييم",
    "مراجعات", "نجوم", "ألف", "مليون", "أعمال"
}

_TRUST_KEYWORDS = {
    "secure", "ssl", "certified", "guarantee", "verified",
    "award", "featured in", "as seen in", "money back",
    "satisfaction", "iso", "gdpr", "privacy", "encrypted",
    "badge", "accredited", "compliant",
    # Arabic keywords
    "آمن", "معتمد", "ضمان", "موثق", "جائزة", "مميز في",
    "استرداد", "رضا", "خصوصية", "مشفر", "اعتماد", "موافق"
}

_GUARANTEE_KEYWORDS = {
    "guarantee", "money back", "risk free", "no risk",
    "satisfaction", "30-day", "60-day", "90-day",
    "refund", "cancel anytime", "no commitment",
    # Arabic keywords
    "ضمان", "استرداد الأموال", "بدون مخاطر", "لا توجد مخاطرة",
    "رضا", "يوم", "استرجاع", "إلغاء في أي وقت", "بدون التزام"
}


def _dedup(items: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item[:60].lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _extract_features(raw_page: RawPage) -> list[str]:
    candidates: list[str] = []
    for item in raw_page.list_items:
        if 10 < len(item) < 200 and any(kw in item.lower() for kw in _FEATURE_KEYWORDS):
            candidates.append(item)
    for p in raw_page.paragraphs:
        if 15 < len(p) < 200 and any(kw in p.lower() for kw in _FEATURE_KEYWORDS):
            candidates.append(p)
    return _dedup(candidates, 10)


def _extract_social_proof(raw_page: RawPage) -> list[str]:
    candidates: list[str] = []
    for text in raw_page.headings + raw_page.paragraphs:
        if len(text) < 200 and any(kw in text.lower() for kw in _SOCIAL_PROOF_KEYWORDS):
            candidates.append(text)
    return _dedup(candidates, 6)


def _extract_trust_signals(raw_page: RawPage) -> list[str]:
    candidates: list[str] = []
    for text in raw_page.paragraphs + raw_page.list_items:
        if len(text) < 200 and any(kw in text.lower() for kw in _TRUST_KEYWORDS):
            candidates.append(text)
    return _dedup(candidates, 8)


def _extract_guarantees(raw_page: RawPage) -> list[str]:
    candidates: list[str] = []
    all_text = raw_page.headings + raw_page.paragraphs + raw_page.list_items
    for text in all_text:
        if any(kw in text.lower() for kw in _GUARANTEE_KEYWORDS):
            candidates.append(text)
    return _dedup(candidates, 5)


# ── Public API ────────────────────────────────────────────────────────────────

def extract_content(raw_page: RawPage) -> LandingPageContent:
    """
    Convert *raw_page* into a :class:`LandingPageContent` ready for LLM analysis.

    Runs all section extractors and assembles the structured output.
    """
    start = time.perf_counter()
    logger.info("Extracting page content sections…")

    content = LandingPageContent(
        title=raw_page.title,
        meta_description=raw_page.meta_description,
        hero_section=extract_hero(raw_page),
        benefits=extract_benefits(raw_page),
        features=_extract_features(raw_page),
        testimonials=extract_testimonials(raw_page),
        social_proof=_extract_social_proof(raw_page),
        pricing=extract_pricing(raw_page),
        faq=extract_faq(raw_page),
        cta_buttons=extract_cta_buttons(raw_page),
        forms=raw_page.forms,
        trust_signals=_extract_trust_signals(raw_page),
        guarantees=_extract_guarantees(raw_page),
        raw_text_summary=raw_page.body_text[:2000],
    )

    elapsed = time.perf_counter() - start
    logger.info(
        f"Extraction complete in {elapsed:.2f}s | "
        f"benefits={len(content.benefits)} | features={len(content.features)} | "
        f"testimonials={len(content.testimonials)} | cta={len(content.cta_buttons)}"
    )
    return content
