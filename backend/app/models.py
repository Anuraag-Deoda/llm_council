"""
Pydantic models for request/response validation.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class Stage(str, Enum):
    """Council discussion stages."""
    FIRST_OPINIONS = "first_opinions"
    REVIEW = "review"
    FINAL_RESPONSE = "final_response"


class ModelResponse(BaseModel):
    """Individual model's response."""
    model_id: str
    response: str
    timestamp: float
    error: Optional[str] = None


class ReviewResponse(BaseModel):
    """Model's review of other responses."""
    reviewer_model: str
    rankings: List[Dict[str, Any]]  # List of {model_id, rank, reasoning}
    timestamp: float


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float


class CouncilResponse(BaseModel):
    """Complete council response with all stages."""
    conversation_id: str
    stage: Stage
    user_query: str

    # Stage 1: First opinions
    first_opinions: List[ModelResponse] = []

    # Stage 2: Reviews
    reviews: List[ReviewResponse] = []

    # Stage 3: Final response
    final_response: Optional[str] = None
    chairman_model: Optional[str] = None

    # Metadata
    models_used: List[str] = []
    timestamp: float


class ChatRequest(BaseModel):
    """User chat request."""
    message: str
    conversation_id: Optional[str] = None
    selected_models: Optional[List[str]] = None  # Optional model selection


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    type: str  # "stage_update", "model_response", "review", "final_response", "error"
    stage: Optional[Stage] = None
    model_id: Optional[str] = None
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ModelInfo(BaseModel):
    """Information about an available model."""
    id: str
    name: str
    provider: str  # "openai" or "openrouter"
    is_chairman: bool = False


class ConversationHistory(BaseModel):
    """Conversation history."""
    conversation_id: str
    messages: List[ChatMessage]
    council_responses: List[CouncilResponse] = []
    created_at: float
    updated_at: float
