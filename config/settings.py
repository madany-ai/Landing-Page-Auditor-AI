"""Application settings loaded from .env via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenRouter / LLM
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    model: str = Field(default="deepseek/deepseek-chat", alias="MODEL")
    fallback_model: str = Field(default="openrouter/google/gemini-2.5-flash", alias="FALLBACK_MODEL")

    # LLM generation
    temperature: float = Field(default=0.2, alias="TEMPERATURE")
    max_tokens: int = Field(default=8000, alias="MAX_TOKENS")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
