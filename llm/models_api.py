"""
Fetches available models dynamically from OpenRouter API.
Provides caching so we don't hit the API on every page load.
"""

from __future__ import annotations

import httpx
from functools import lru_cache
from loguru import logger

# Fallback models in case the API is down
DEFAULT_MODELS = [
    "deepseek/deepseek-chat",
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4",
    "meta-llama/llama-4-maverick",
]

@lru_cache(maxsize=1)
def get_openrouter_models() -> list[str]:
    """Fetch the list of model IDs from OpenRouter."""
    logger.info("Fetching dynamic model list from OpenRouter API...")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get("https://openrouter.ai/api/v1/models")
            response.raise_for_status()
            
            data = response.json().get("data", [])
            models = sorted([m["id"] for m in data if "id" in m])
            
            if models:
                logger.info(f"Loaded {len(models)} models from OpenRouter.")
                # Put a few popular ones at the top, then the rest sorted alphabetically
                popular = [m for m in DEFAULT_MODELS if m in models]
                others = [m for m in models if m not in popular]
                return popular + others
                
    except Exception as exc:
        logger.error(f"Failed to fetch OpenRouter models: {exc}. Using defaults.")
    
    return DEFAULT_MODELS
