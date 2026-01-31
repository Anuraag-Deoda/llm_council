"""
Configuration settings for the LLM Council application.
"""
from typing import List, Union, Optional
from pydantic import field_validator, Field
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

    # Database Settings
    database_url: str = Field(
        default="postgresql://llm_council:council_password@db:5432/llm_council_db",
        description="Database connection URL (use psycopg2 driver for sync)"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    database_path: str = "./data/conversations.json"  # Legacy fallback

    # Redis Settings
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URL"
    )
    redis_max_connections: int = Field(default=50, description="Max Redis connections")
    redis_socket_timeout: int = Field(default=5, description="Redis socket timeout in seconds")

    # Cache Settings
    enable_cache: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=10000, description="Max cache entries")

    # Rate Limiting Settings
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Max requests per window")
    rate_limit_window_seconds: int = Field(default=3600, description="Rate limit window in seconds")
    rate_limit_burst: int = Field(default=20, description="Burst allowance")

    # Celery Settings
    celery_broker_url: str = Field(
        default="redis://redis:6379/1",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://redis:6379/2",
        description="Celery result backend URL"
    )

    # Monitoring Settings
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")

    # Analytics Settings
    enable_analytics: bool = Field(default=True, description="Enable analytics tracking")
    analytics_batch_size: int = Field(default=100, description="Batch size for analytics")
    analytics_flush_interval: int = Field(default=60, description="Flush interval in seconds")

    # WebSocket Settings
    websocket_max_connections: int = Field(default=1000, description="Max WebSocket connections")
    websocket_ping_interval: int = Field(default=30, description="WebSocket ping interval")
    websocket_ping_timeout: int = Field(default=10, description="WebSocket ping timeout")

    # Council Configuration
    default_voting_system: str = Field(default="ranked_choice", description="Default voting system")
    min_council_models: int = Field(default=3, description="Minimum models in council")
    max_council_models: Optional[int] = Field(default=None, description="Maximum models in council")
    enable_peer_review: bool = Field(default=True, description="Enable peer review stage")
    peer_review_anonymous: bool = Field(default=True, description="Anonymous peer reviews")

    # Timeouts
    request_timeout: int = 120  # seconds
    llm_timeout: int = Field(default=90, description="LLM API timeout in seconds")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Security
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    require_api_key: bool = Field(default=False, description="Require API key for requests")
    allowed_api_keys: List[str] = Field(default=[], description="List of valid API keys")

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @field_validator('allowed_api_keys', mode='before')
    @classmethod
    def parse_api_keys(cls, v):
        """Parse API keys from comma-separated string or list."""
        if isinstance(v, str):
            return [key.strip() for key in v.split(',') if key.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
