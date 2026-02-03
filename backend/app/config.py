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

    # JWT Settings
    jwt_secret_key: str = Field(default="change-this-in-production-use-a-long-random-string", description="Secret key for JWT encoding")
    jwt_algorithm: str = Field(default="HS256", description="JWT encoding algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")

    # Email Settings (Gmail SMTP)
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(default="", description="SMTP username (Gmail address)")
    smtp_password: str = Field(default="", description="SMTP password (Gmail app password)")
    smtp_from_email: str = Field(default="", description="From email address")
    magic_link_expire_minutes: int = Field(default=15, description="Magic link expiration in minutes")
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend URL for email links")

    # RAG Core Settings
    enable_rag: bool = Field(default=True, description="Enable RAG functionality")
    rag_embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model")
    rag_embedding_dimensions: int = Field(default=1536, description="Embedding vector dimensions")
    rag_chunk_size: int = Field(default=512, description="Target chunk size in tokens")
    rag_chunk_overlap: int = Field(default=50, description="Overlap between chunks in tokens")
    rag_top_k: int = Field(default=10, description="Number of chunks to retrieve")
    rag_similarity_threshold: float = Field(default=0.5, description="Minimum similarity score")

    # RAG Conflict Detection
    rag_conflict_threshold: float = Field(default=0.6, description="Minimum confidence to report conflict")
    rag_conflict_check_top_n: int = Field(default=5, description="Number of top chunks to check for conflicts")
    rag_conflict_model: str = Field(default="gpt-4o", description="Model for conflict detection")

    # RAG Trust Weights (scoring algorithm)
    rag_weight_similarity: float = Field(default=0.4, description="Weight for similarity score")
    rag_weight_source_trust: float = Field(default=0.3, description="Weight for source trust score")
    rag_weight_recency: float = Field(default=0.2, description="Weight for recency score")
    rag_weight_author_authority: float = Field(default=0.1, description="Weight for author authority score")

    # RAG Default Source Trust Scores
    rag_trust_weight_document: float = Field(default=0.8, description="Default trust for uploaded documents")
    rag_trust_weight_notion: float = Field(default=0.7, description="Default trust for Notion sources")
    rag_trust_weight_github: float = Field(default=0.6, description="Default trust for GitHub sources")
    rag_trust_weight_slack: float = Field(default=0.5, description="Default trust for Slack sources")

    # RAG File Upload
    rag_max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    rag_allowed_file_types: List[str] = Field(
        default=["pdf", "docx", "doc", "txt", "md", "markdown"],
        description="Allowed file types for upload"
    )
    rag_upload_dir: str = Field(default="./data/rag_uploads", description="Directory for uploaded files")

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

    @field_validator('rag_allowed_file_types', mode='before')
    @classmethod
    def parse_file_types(cls, v):
        """Parse allowed file types from comma-separated string or list."""
        if isinstance(v, str):
            return [ft.strip().lower() for ft in v.split(',') if ft.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
