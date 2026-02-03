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
    model_config = {"protected_namespaces": ()}

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
    # RAG options
    use_rag: bool = False  # Enable RAG for this request
    rag_source_ids: Optional[List[int]] = None  # Filter RAG to specific sources


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    model_config = {"protected_namespaces": ()}

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


# ============================================================================
# RAG Models
# ============================================================================

class SourceType(str, Enum):
    """Document source types."""
    DOCUMENT = "document"
    SLACK = "slack"
    NOTION = "notion"
    GITHUB = "github"
    WEB = "web"


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConflictType(str, Enum):
    """Types of detected conflicts."""
    FACTUAL = "factual"
    TEMPORAL = "temporal"
    OPINION = "opinion"
    NUMERICAL = "numerical"
    PROCEDURAL = "procedural"


class ConflictStatusEnum(str, Enum):
    """Conflict resolution status."""
    DETECTED = "detected"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class DocumentSourceCreate(BaseModel):
    """Request to create a document source."""
    name: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType = SourceType.DOCUMENT
    description: Optional[str] = None
    base_trust_score: float = Field(default=0.7, ge=0.0, le=1.0)
    connection_config: Optional[Dict[str, Any]] = None


class DocumentSourceResponse(BaseModel):
    """Document source response."""
    id: int
    name: str
    source_type: SourceType
    description: Optional[str]
    base_trust_score: float
    is_active: bool
    document_count: int
    last_sync_at: Optional[str]
    last_sync_status: Optional[str]
    created_at: str


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    document_id: int
    title: str
    status: DocumentStatus
    file_type: Optional[str]
    task_id: Optional[str] = None
    message: str


class DocumentResponse(BaseModel):
    """Document details response."""
    id: int
    source_id: int
    source_name: str
    title: str
    file_type: Optional[str]
    status: DocumentStatus
    chunk_count: int
    token_count: int
    author: Optional[str]
    error_message: Optional[str]
    created_at: str
    indexed_at: Optional[str]


class DocumentListResponse(BaseModel):
    """List of documents response."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class RAGQueryRequest(BaseModel):
    """Request for RAG query."""
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)
    source_ids: Optional[List[int]] = None
    include_conflict_detection: bool = True


class ChunkScore(BaseModel):
    """Score breakdown for a chunk."""
    final: float
    similarity: float
    source_trust: float
    recency: float
    author_authority: float


class RetrievedChunk(BaseModel):
    """A retrieved document chunk."""
    chunk_id: int
    document_id: int
    document_title: str
    source_name: str
    source_type: str
    content: str
    section_title: Optional[str]
    scores: ChunkScore


class DetectedConflictResponse(BaseModel):
    """A detected conflict between sources."""
    type: ConflictType
    confidence: float
    source_a: str
    source_b: str
    explanation: str
    recommendation: str


class RAGQueryResponse(BaseModel):
    """Response from RAG query."""
    query: str
    context: str
    chunks: List[RetrievedChunk]
    conflicts: List[DetectedConflictResponse]
    conflict_report: str
    timing: Dict[str, int]


class ConflictResponse(BaseModel):
    """Conflict record response."""
    id: int
    chunk_a_id: int
    chunk_b_id: int
    conflict_type: ConflictType
    confidence: float
    explanation: Optional[str]
    recommendation: Optional[str]
    status: ConflictStatusEnum
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    detected_at: str
    resolved_at: Optional[str]


class ConflictResolveRequest(BaseModel):
    """Request to resolve a conflict."""
    status: ConflictStatusEnum = Field(..., description="New status for the conflict")
    resolution_notes: Optional[str] = None
    preferred_chunk_id: Optional[int] = None
    resolved_by: Optional[str] = None
