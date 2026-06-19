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

def safe_llm_call(client, messages: list[dict], response_model, model: str | None = None, **kwargs):
    """
    Executes a structured LLM call, automatically falling back if the primary model fails.
    """
    primary_model = get_model_name(model)
    fallback_model = get_model_name(settings.fallback_model)
    
    try:
        return client.chat.completions.create(
            model=primary_model,
            messages=messages,
            response_model=response_model,
            **kwargs
        )
    except Exception as exc:
        err_str = str(exc)
        if "free-models-per-day" in err_str or "Rate limit exceeded" in err_str:
            clean_err = "OpenRouter free-tier rate limit exceeded"
        elif "<failed_attempts>" in err_str:
            clean_err = "LLM API Error (Multiple retries failed)"
        else:
            clean_err = err_str.split("\n")[0][:100]
            
        logger.warning(f"Primary model {primary_model} failed ({clean_err}). Falling back to {fallback_model}...")
        try:
            return client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                response_model=response_model,
                **kwargs
            )
        except Exception as fallback_exc:
            logger.error(f"Fallback model {fallback_model} also failed: {fallback_exc}")
            raise
