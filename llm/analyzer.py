"""
LLM analysis runner.

Sends structured page content to the LLM and returns a validated AuditResult.
Retries up to 3 times with exponential back-off (tenacity).
"""

from __future__ import annotations

import time
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, RetryCallState

from schemas.page import LandingPageContent
from schemas.analysis import AuditResult
from llm.client import get_client, get_model_name
from llm.prompts import SYSTEM_PROMPT, build_user_prompt
from config.settings import settings


# ── Retry helpers ─────────────────────────────────────────────────────────────

def _before_sleep(retry_state: RetryCallState) -> None:
    attempt = retry_state.attempt_number
    wait = getattr(retry_state.next_action, "sleep", "?")
    logger.warning(
        f"LLM call failed (attempt {attempt}/3). "
        f"Retrying in ~{wait}s… "
        f"Error: {retry_state.outcome.exception()}"
    )


# ── Core LLM call (with retry) ────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    before_sleep=_before_sleep,
    reraise=True,
)
def _call_llm(messages: list[dict], model: str) -> AuditResult:
    """Make one instructor-validated LLM call and return an AuditResult."""
    client = get_client()
    from llm.client import safe_llm_call
    return safe_llm_call(
        client=client,
        messages=messages,
        response_model=AuditResult,
        model=model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def analyze(
    content: LandingPageContent,
    url: str = "",
    model: str | None = None,
) -> AuditResult:
    """
    Send *content* to the LLM and return a structured :class:`AuditResult`.

    Args:
        content: Structured page content from the extractor layer.
        url:     Original URL (included in the user prompt for context).
        model:   Optional model override; uses settings.model if None.

    Returns:
        Validated AuditResult with per-category scores, findings, and
        recommendations. overall_score is NOT set here — that is the
        scoring engine's responsibility.
    """
    model_name = get_model_name(model)
    logger.info(f"Running LLM analysis → model: {model_name}")
    start = time.perf_counter()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(content, url)},
    ]

    result: AuditResult = _call_llm(messages, model_name)

    elapsed = time.perf_counter() - start
    logger.info(f"LLM analysis complete in {elapsed:.2f}s")

    return result
