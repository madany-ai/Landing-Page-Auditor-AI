"""
High-level page loader.

Calls the fetcher, then extracts structured fields from the Scrapling page
object into a RawPage. No HTML is passed onwards — only text, headings,
buttons, links, forms, etc.
"""

from __future__ import annotations

import time
from loguru import logger

from schemas.page import RawPage
from scraper.fetch import fetch_page


# ── Helpers ──────────────────────────────────────────────────────────────────

import re
from w3lib.html import remove_tags

def _extract_text(html: str) -> str:
    """Safely strip HTML tags and normalize whitespace."""
    if not html:
        return ""
    text = remove_tags(html)
    return re.sub(r"\s+", " ", text).strip()


def _safe_getall(page, selector: str, limit: int = 150) -> list[str]:
    """Return all non-empty stripped strings matching *selector*."""
    try:
        base_sel = selector.replace("::text", "")
        results = []
        for el in page.css(base_sel):
            text = _extract_text(el.html_content)
            if text:
                results.append(text)
        return results[:limit]
    except Exception:
        return []


def _safe_get(page, selector: str) -> str:
    """Return first match for *selector*, or empty string."""
    try:
        base_sel = selector.replace("::text", "")
        el = page.css(base_sel)
        if el:
            return _extract_text(el[0].html_content)
        return ""
    except Exception:
        return ""


def _extract_buttons(page) -> list[str]:
    """Collect unique CTA / button labels."""
    raw: list[str] = []
    for sel in [
        "button::text",
        'input[type="submit"]',
        'a[class*="btn"]::text',
        'a[class*="button"]::text',
        'a[class*="cta"]::text',
        '[role="button"]::text',
    ]:
        raw.extend(_safe_getall(page, sel, limit=30))

    seen: set[str] = set()
    unique: list[str] = []
    for text in raw:
        key = text.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(text)
    return unique[:25]


def _extract_links(page) -> list[str]:
    """Return up to 50 href values."""
    try:
        links: list[str] = []
        for a in page.css("a")[:100]:
            href = a.attrib.get("href", "")
            if href and (href.startswith("http") or href.startswith("/")):
                links.append(href)
        return links[:50]
    except Exception:
        return []


def _extract_forms(page) -> list[dict]:
    """Return a list of form dicts, each with a 'fields' key."""
    try:
        forms: list[dict] = []
        for form in page.css("form"):
            fields: list[str] = []
            for inp in form.css("input, textarea, select"):
                label = (
                    inp.attrib.get("name")
                    or inp.attrib.get("placeholder")
                    or inp.attrib.get("type")
                    or ""
                )
                if label and label not in ("hidden", ""):
                    fields.append(label)
            forms.append({"fields": fields})
        return forms
    except Exception:
        return []


# ── Public API ────────────────────────────────────────────────────────────────

def load_page(url: str) -> RawPage:
    """
    Scrape *url* and return a :class:`RawPage`.

    Steps:
      1. Fetch the page (with stealth fallback)
      2. Extract title, meta, headings, paragraphs, list items, blockquotes,
         buttons, links, and forms
      3. Assemble body_text from those collections
    """
    start = time.perf_counter()
    page = fetch_page(url)

    # ── Core metadata ─────────────────────────────────────────────────────────
    title = _safe_get(page, "title::text")

    meta_description = ""
    try:
        meta_els = page.css('meta[name="description"]')
        if meta_els:
            meta_description = meta_els[0].attrib.get("content", "").strip()
    except Exception:
        pass

    # ── Text collections ──────────────────────────────────────────────────────
    headings: list[str] = []
    for tag in ("h1", "h2", "h3", "h4"):
        headings.extend(_safe_getall(page, f"{tag}::text"))

    paragraphs = _safe_getall(page, "p::text", limit=200)
    list_items = _safe_getall(page, "li::text", limit=200)
    blockquotes = _safe_getall(page, "blockquote::text", limit=30)

    # ── Interactive elements ──────────────────────────────────────────────────
    buttons = _extract_buttons(page)
    links = _extract_links(page)
    forms = _extract_forms(page)

    # ── Body text (capped at 15 000 chars) ───────────────────────────────────
    body_parts = headings + paragraphs + list_items
    body_text = "\n".join(p for p in body_parts if p)[:15_000]

    elapsed = time.perf_counter() - start
    logger.info(
        f"Page loaded in {elapsed:.2f}s | "
        f"title='{title}' | headings={len(headings)} | "
        f"paragraphs={len(paragraphs)} | list_items={len(list_items)} | "
        f"buttons={len(buttons)} | forms={len(forms)}"
    )

    return RawPage(
        url=url,
        title=title,
        meta_description=meta_description,
        headings=headings,
        paragraphs=paragraphs,
        list_items=list_items,
        blockquotes=blockquotes,
        body_text=body_text,
        buttons=buttons,
        links=links,
        forms=forms,
    )
