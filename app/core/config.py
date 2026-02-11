"""
Centralized configuration module using pydantic-settings.
Single source of truth for all application settings.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = "GymAI - Gestor Inteligente de Rutinas"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # --- Groq AI ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "llama-3.2-11b-vision-preview"

    # --- Database ---
    DATABASE_URL: str = ""
    FORCE_SQLITE: bool = False

    # --- Server ---
    HOST: str = "localhost"
    PORT: int = 8000
    CORS_ORIGINS: str = "*"

    # --- Image Analysis ---
    MAX_IMAGE_SIZE_MB: int = 10

    @property
    def max_image_size_bytes(self) -> int:
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    @property
    def ai_configured(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def is_vercel(self) -> bool:
        return bool(os.environ.get("VERCEL_ENV"))

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton)."""
    return Settings()
