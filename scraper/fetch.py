"""
Low-level page fetcher.

Strategy:
  1. Try Scrapling's fast Fetcher (HTTP, TLS impersonation)
  2. If blocked or empty body detected → fall back to StealthyFetcher (headless browser)
  3. If both fail → raise RuntimeError
"""

from __future__ import annotations

import time
from loguru import logger


_BLOCK_SIGNALS = [
    "access denied",
    "403 forbidden",
    "cloudflare",
    "please verify you are a human",
    "captcha",
    "bot detection",
    "rate limit exceeded",
    "you have been blocked",
]


def _looks_blocked(page) -> bool:
    """Heuristically check whether the fetched page is a block / CAPTCHA page."""
    try:
        texts = page.css("body *::text").getall()
        body = " ".join(texts).lower()
        if len(body) < 200:
            return True
        return any(sig in body for sig in _BLOCK_SIGNALS)
    except Exception:
        return False


def fetch_page(url: str):
    """
    Fetch *url* and return a Scrapling page object.

    Falls back to StealthyFetcher when the normal Fetcher is blocked.
    """
    from scrapling.fetchers import Fetcher, StealthyFetcher

    logger.info(f"Fetching: {url}")
    start = time.perf_counter()

    # ── Attempt 1: Fast Fetcher ──────────────────────────────────────────────
    try:
        page = Fetcher.get(url, stealthy_headers=True)
        if _looks_blocked(page):
            logger.warning("Page looks blocked — switching to StealthyFetcher.")
            raise ValueError("Blocked response detected")
        elapsed = time.perf_counter() - start
        logger.info(f"Fetcher succeeded in {elapsed:.2f}s")
        return page
    except Exception as exc:
        logger.warning(f"Normal fetch failed ({exc}). Trying StealthyFetcher…")

    # ── Attempt 2: Stealth headless browser ──────────────────────────────────
    try:
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
        elapsed = time.perf_counter() - start
        logger.info(f"StealthyFetcher succeeded in {elapsed:.2f}s")
        return page
    except Exception as exc:
        logger.error(f"StealthyFetcher also failed: {exc}")
        raise RuntimeError(
            f"Unable to fetch '{url}'. "
            "Ensure scrapling browsers are installed (`scrapling install`). "
            f"Original error: {exc}"
        ) from exc
