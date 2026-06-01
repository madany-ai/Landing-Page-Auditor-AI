"""Pydantic models for raw scraped page data and structured extracted content."""

from __future__ import annotations
from pydantic import BaseModel, Field


class RawPage(BaseModel):
    """Raw data scraped directly from the page. Never sent to LLM as-is."""

    url: str
    title: str = ""
    meta_description: str = ""

    # Structured text collections (used by extractors)
    headings: list[str] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    list_items: list[str] = Field(default_factory=list)
    blockquotes: list[str] = Field(default_factory=list)

    # Interactive elements
    buttons: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    forms: list[dict] = Field(default_factory=list)

    # Full body text (first 15 000 chars, for keyword extraction)
    body_text: str = ""


class LandingPageContent(BaseModel):
    """
    Structured content extracted from a landing page.
    This is what gets sent to the LLM — never raw HTML.
    """

    title: str = ""
    meta_description: str = ""

    hero_section: dict = Field(default_factory=dict)
    benefits: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    testimonials: list[str] = Field(default_factory=list)
    social_proof: list[str] = Field(default_factory=list)
    pricing: list[dict] = Field(default_factory=list)
    faq: list[dict] = Field(default_factory=list)
    cta_buttons: list[str] = Field(default_factory=list)
    forms: list[dict] = Field(default_factory=list)
    trust_signals: list[str] = Field(default_factory=list)
    guarantees: list[str] = Field(default_factory=list)

    # Short text summary of page body (first ~2 000 chars)
    raw_text_summary: str = ""
