import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Industry-grade configuration management.
    Validates environment variables at runtime.
    """

    # Project Metadata
    PROJECT_NAME: str = "Nexus-Talent AI"
    ENV: str = "production"

    # LLM Configuration
    GEMINI_API_KEY: str
    OLLAMA_URL: str = "http://localhost:11434"

    # Infrastructure URLs
    REDIS_URL: str = "redis://localhost:6379"
    WEAVIATE_URL: str = "http://localhost:8080"

    # Observability
    SIGNOZ_ENDPOINT: str = "http://localhost:4317"

    # Security
    SECRET_KEY: str = "temporary_secret_change_in_production"

    # Load from .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Global settings instance
settings = Settings()
