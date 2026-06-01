"""
LiteLLM + Instructor client factory.

instructor wraps the LiteLLM completion function to enforce structured
JSON output via Pydantic models — no manual JSON parsing required.
"""

from __future__ import annotations

import os
import instructor
import litellm
from loguru import logger

from config.settings import settings

# ── Silence noisy litellm debug output ───────────────────────────────────────
litellm.suppress_debug_info = True
os.environ["LITELLM_LOG"] = "ERROR"

# ── Inject OpenRouter credentials into the environment ───────────────────────
if settings.openrouter_api_key:
    os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
else:
    logger.warning("OPENROUTER_API_KEY is not set — LLM calls will fail.")


def get_client():
    """Return an instructor-wrapped litellm completion client."""
    return instructor.from_litellm(litellm.completion, mode=instructor.Mode.JSON)


def get_model_name(model: str | None = None) -> str:
    """
    Return the fully-qualified model name for OpenRouter.

    LiteLLM expects the format ``openrouter/<provider>/<model>``.
    If the caller already includes the prefix it is returned unchanged.
    """
    m = (model or settings.model).strip()
    if not m.startswith("openrouter/"):
        return f"openrouter/{m}"
    return m
