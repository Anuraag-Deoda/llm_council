"""
Configuration settings for the LLM Council application.
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # API Base URLs
    openai_base_url: str = "https://api.openai.com/v1"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Chairman Model
    chairman_model: str = "gpt-5.2"

    # OpenRouter Free Models
    openrouter_models: List[str] = [
        "arcee-ai/trinity-large-preview:free",
        "upstage/solar-pro-3:free",
        "liquid/lfm-2.5-1.2b-thinking:free",
        "tngtech/deepseek-r1t2-chimera:free",
        "z-ai/glm-4.5-air:free",
        "deepseek/deepseek-r1-0528:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
    ]

    # OpenAI Models
    openai_models: List[str] = [
        "gpt-5.2",
        "gpt-4o",
    ]

    # Application Settings
    cors_origins: Union[str, List[str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    max_tokens: int = 4000
    temperature: float = 0.7

    # Database
    database_path: str = "./data/conversations.json"

    # Timeouts
    request_timeout: int = 120  # seconds

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
