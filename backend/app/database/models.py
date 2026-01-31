"""
Database models for LLM Council
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    JSON, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ChatType(str, enum.Enum):
    """Chat type enumeration"""
    COUNCIL = "council"
    INDIVIDUAL = "individual"


class MessageRole(str, enum.Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(Base):
    """Conversation/Chat sessions"""
    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=True)  # For multi-user support
    type = Column(SQLEnum(ChatType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, index=True)

    # Metadata
    model_id = Column(String(100), nullable=True)  # For individual chats
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Statistics
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    analytics = relationship("ConversationAnalytics", back_populates="conversation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_conv_user_type', 'user_id', 'type'),
        Index('idx_conv_status_updated', 'status', 'updated_at'),
    )


class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"

    id = Column(String(100), primary_key=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message content
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    model_id = Column(String(100), nullable=True)
    model_name = Column(String(255), nullable=True)

    # Metadata
    metadata = Column(JSON, default=dict)

    # Performance metrics
    latency_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('idx_msg_conv_created', 'conversation_id', 'created_at'),
        Index('idx_msg_model', 'model_id', 'created_at'),
    )


class ModelInfo(Base):
    """Model registry and configuration"""
    __tablename__ = "models"

    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False, index=True)

    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    is_chairman = Column(Boolean, default=False)
    max_tokens = Column(Integer, nullable=True)
    temperature = Column(Float, default=0.7)

    # Pricing
    cost_per_1k_input_tokens = Column(Float, default=0.0)
    cost_per_1k_output_tokens = Column(Float, default=0.0)

    # Metadata
    metadata = Column(JSON, default=dict)
    capabilities = Column(JSON, default=list)  # e.g., ["streaming", "function_calling"]

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Statistics
    total_requests = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)

    # Relationships
    analytics = relationship("ModelAnalytics", back_populates="model")

    __table_args__ = (
        Index('idx_model_provider_active', 'provider', 'is_active'),
    )


class ConversationAnalytics(Base):
    """Analytics per conversation"""
    __tablename__ = "conversation_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Stage metrics
    stage = Column(String(50), nullable=True)  # first_opinions, review, final_response
    stage_duration_ms = Column(Integer, nullable=True)

    # Model participation
    models_used = Column(JSON, default=list)
    model_count = Column(Integer, default=0)

    # Performance
    total_latency_ms = Column(Integer, nullable=False)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Quality metrics
    peer_review_scores = Column(JSON, default=dict)  # {model_id: {rank: int, score: float}}
    consensus_score = Column(Float, nullable=True)  # Measure of agreement

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="analytics")

    __table_args__ = (
        Index('idx_analytics_conv_created', 'conversation_id', 'created_at'),
    )


class ModelAnalytics(Base):
    """Time-series analytics per model"""
    __tablename__ = "model_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(100), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time bucket (hourly aggregation)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Request metrics
    request_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)

    # Performance metrics
    avg_latency_ms = Column(Float, default=0.0)
    p50_latency_ms = Column(Float, nullable=True)
    p95_latency_ms = Column(Float, nullable=True)
    p99_latency_ms = Column(Float, nullable=True)

    # Usage metrics
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Quality metrics
    avg_peer_review_rank = Column(Float, nullable=True)
    times_ranked_first = Column(Integer, default=0)

    # Relationships
    model = relationship("ModelInfo", back_populates="analytics")

    __table_args__ = (
        Index('idx_model_analytics_time', 'model_id', 'timestamp'),
    )


class CouncilConfiguration(Base):
    """Configurable council behavior"""
    __tablename__ = "council_configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Active configuration
    is_active = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)

    # Council settings
    voting_system = Column(String(50), default="ranked_choice")  # ranked_choice, weighted, consensus
    min_models = Column(Integer, default=3)
    max_models = Column(Integer, nullable=True)

    # Chairman settings
    chairman_model_id = Column(String(100), nullable=True)
    chairman_prompt_template = Column(Text, nullable=True)

    # Stage settings
    enable_peer_review = Column(Boolean, default=True)
    peer_review_anonymous = Column(Boolean, default=True)
    require_reasoning = Column(Boolean, default=True)

    # Prompt templates
    stage1_prompt_template = Column(Text, nullable=True)
    stage2_prompt_template = Column(Text, nullable=True)
    stage3_prompt_template = Column(Text, nullable=True)

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_council_config_active', 'is_active', 'is_default'),
    )


class RateLimitLog(Base):
    """Rate limiting logs"""
    __tablename__ = "rate_limit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(255), nullable=False, index=True)  # IP or user_id
    endpoint = Column(String(255), nullable=False, index=True)

    # Request details
    request_count = Column(Integer, default=1)
    blocked_count = Column(Integer, default=0)

    # Time window
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    metadata = Column(JSON, default=dict)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_ratelimit_id_time', 'identifier', 'created_at'),
        Index('idx_ratelimit_window', 'window_start', 'window_end'),
    )


class CachedResponse(Base):
    """Cache for model responses"""
    __tablename__ = "cached_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), nullable=False, unique=True, index=True)

    # Request details
    model_id = Column(String(100), nullable=False, index=True)
    prompt_hash = Column(String(64), nullable=False, index=True)

    # Response
    response_data = Column(JSON, nullable=False)

    # Metadata
    hit_count = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)

    # TTL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('idx_cache_model_hash', 'model_id', 'prompt_hash'),
        Index('idx_cache_expires', 'expires_at'),
    )
