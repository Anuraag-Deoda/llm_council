"""
Database package initialization
"""
from .models import (
    Base,
    Conversation,
    Message,
    ModelInfo,
    ConversationAnalytics,
    ModelAnalytics,
    CouncilConfiguration,
    RateLimitLog,
    CachedResponse,
    ChatType,
    MessageRole,
    ConversationStatus,
)
from .rag_models import (
    DocumentSource,
    Document,
    DocumentChunk,
    ConflictRecord,
    RetrievalLog,
    SourceType,
    DocumentStatus,
    ConflictType,
    ConflictStatus,
)
from .auth_models import (
    User,
    MagicLinkToken,
)
from .session import (
    get_db,
    init_db,
    close_db,
    engine,
    SessionLocal,
)
from .storage import ConversationStorage

__all__ = [
    # Models
    "Base",
    "Conversation",
    "Message",
    "ModelInfo",
    "ConversationAnalytics",
    "ModelAnalytics",
    "CouncilConfiguration",
    "RateLimitLog",
    "CachedResponse",
    # Enums
    "ChatType",
    "MessageRole",
    "ConversationStatus",
    # RAG Models
    "DocumentSource",
    "Document",
    "DocumentChunk",
    "ConflictRecord",
    "RetrievalLog",
    # RAG Enums
    "SourceType",
    "DocumentStatus",
    "ConflictType",
    "ConflictStatus",
    # Auth Models
    "User",
    "MagicLinkToken",
    # Session
    "get_db",
    "init_db",
    "close_db",
    "engine",
    "SessionLocal",
    # Legacy
    "ConversationStorage",
]
