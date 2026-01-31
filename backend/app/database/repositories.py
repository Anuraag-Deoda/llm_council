"""
Repository pattern for database operations
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from app.database.models import (
    Conversation, Message, ModelInfo, ConversationAnalytics,
    ModelAnalytics, CouncilConfiguration, RateLimitLog, CachedResponse,
    ChatType, MessageRole, ConversationStatus
)


class ConversationRepository:
    """Repository for conversation operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, conversation_data: Dict[str, Any]) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(**conversation_data)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    def get_by_user(
        self,
        user_id: str,
        chat_type: Optional[ChatType] = None,
        status: ConversationStatus = ConversationStatus.ACTIVE,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """Get conversations for a user"""
        query = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == status
        )

        if chat_type:
            query = query.filter(Conversation.type == chat_type)

        return query.order_by(
            desc(Conversation.last_message_at)
        ).limit(limit).offset(offset).all()

    def update(self, conversation_id: str, update_data: Dict[str, Any]) -> Optional[Conversation]:
        """Update conversation"""
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None

        for key, value in update_data.items():
            setattr(conversation, key, value)

        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def increment_message_count(self, conversation_id: str) -> None:
        """Increment message count for conversation"""
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.message_count += 1
            conversation.last_message_at = datetime.utcnow()
            self.db.commit()

    def add_tokens_and_cost(self, conversation_id: str, tokens: int, cost: float) -> None:
        """Add tokens and cost to conversation"""
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.total_tokens += tokens
            conversation.total_cost += cost
            self.db.commit()

    def delete(self, conversation_id: str) -> bool:
        """Soft delete conversation"""
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.status = ConversationStatus.DELETED
            self.db.commit()
            return True
        return False

    def hard_delete(self, conversation_id: str) -> bool:
        """Permanently delete conversation"""
        conversation = self.get_by_id(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False


class MessageRepository:
    """Repository for message operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, message_data: Dict[str, Any]) -> Message:
        """Create a new message"""
        message = Message(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_id(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        return self.db.query(Message).filter(Message.id == message_id).first()

    def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).limit(limit).offset(offset).all()

    def get_recent_context(
        self,
        conversation_id: str,
        max_messages: int = 10
    ) -> List[Message]:
        """Get recent messages for context"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(max_messages).all()[::-1]

    def update_metrics(
        self,
        message_id: str,
        latency_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None
    ) -> Optional[Message]:
        """Update message metrics"""
        message = self.get_by_id(message_id)
        if not message:
            return None

        if latency_ms is not None:
            message.latency_ms = latency_ms
        if tokens_used is not None:
            message.tokens_used = tokens_used
        if cost is not None:
            message.cost = cost

        self.db.commit()
        self.db.refresh(message)
        return message


class ModelRepository:
    """Repository for model operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, model_data: Dict[str, Any]) -> ModelInfo:
        """Create or update model"""
        existing = self.get_by_id(model_data.get('id'))
        if existing:
            return self.update(model_data['id'], model_data)

        model = ModelInfo(**model_data)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """Get model by ID"""
        return self.db.query(ModelInfo).filter(ModelInfo.id == model_id).first()

    def get_all_active(self) -> List[ModelInfo]:
        """Get all active models"""
        return self.db.query(ModelInfo).filter(
            ModelInfo.is_active == True
        ).all()

    def get_by_provider(self, provider: str, active_only: bool = True) -> List[ModelInfo]:
        """Get models by provider"""
        query = self.db.query(ModelInfo).filter(ModelInfo.provider == provider)
        if active_only:
            query = query.filter(ModelInfo.is_active == True)
        return query.all()

    def get_chairman(self) -> Optional[ModelInfo]:
        """Get chairman model"""
        return self.db.query(ModelInfo).filter(
            ModelInfo.is_chairman == True,
            ModelInfo.is_active == True
        ).first()

    def update(self, model_id: str, update_data: Dict[str, Any]) -> Optional[ModelInfo]:
        """Update model"""
        model = self.get_by_id(model_id)
        if not model:
            return None

        for key, value in update_data.items():
            if key != 'id':  # Don't update ID
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        return model

    def increment_requests(self, model_id: str, is_error: bool = False) -> None:
        """Increment request count"""
        model = self.get_by_id(model_id)
        if model:
            model.total_requests += 1
            if is_error:
                model.total_errors += 1
            self.db.commit()

    def update_avg_latency(self, model_id: str, latency_ms: float) -> None:
        """Update average latency using running average"""
        model = self.get_by_id(model_id)
        if model:
            total = model.total_requests
            current_avg = model.avg_latency_ms or 0
            new_avg = ((current_avg * (total - 1)) + latency_ms) / total
            model.avg_latency_ms = new_avg
            self.db.commit()


class AnalyticsRepository:
    """Repository for analytics operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_conversation_analytics(
        self,
        analytics_data: Dict[str, Any]
    ) -> ConversationAnalytics:
        """Create conversation analytics entry"""
        analytics = ConversationAnalytics(**analytics_data)
        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)
        return analytics

    def get_conversation_analytics(
        self,
        conversation_id: str
    ) -> List[ConversationAnalytics]:
        """Get analytics for a conversation"""
        return self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.conversation_id == conversation_id
        ).order_by(ConversationAnalytics.created_at).all()

    def create_model_analytics(
        self,
        model_id: str,
        timestamp: datetime,
        metrics: Dict[str, Any]
    ) -> ModelAnalytics:
        """Create or update model analytics for time bucket"""
        # Round timestamp to nearest hour
        hour_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)

        existing = self.db.query(ModelAnalytics).filter(
            ModelAnalytics.model_id == model_id,
            ModelAnalytics.timestamp == hour_timestamp
        ).first()

        if existing:
            for key, value in metrics.items():
                setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        analytics = ModelAnalytics(
            model_id=model_id,
            timestamp=hour_timestamp,
            **metrics
        )
        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)
        return analytics

    def get_model_analytics(
        self,
        model_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ModelAnalytics]:
        """Get model analytics for time range"""
        query = self.db.query(ModelAnalytics).filter(
            ModelAnalytics.model_id == model_id
        )

        if start_time:
            query = query.filter(ModelAnalytics.timestamp >= start_time)
        if end_time:
            query = query.filter(ModelAnalytics.timestamp <= end_time)

        return query.order_by(ModelAnalytics.timestamp).all()

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics"""
        total_conversations = self.db.query(func.count(Conversation.id)).scalar()
        total_messages = self.db.query(func.count(Message.id)).scalar()
        total_tokens = self.db.query(func.sum(Conversation.total_tokens)).scalar() or 0
        total_cost = self.db.query(func.sum(Conversation.total_cost)).scalar() or 0.0

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "total_cost": total_cost
        }


class ConfigurationRepository:
    """Repository for council configuration"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, config_data: Dict[str, Any]) -> CouncilConfiguration:
        """Create council configuration"""
        config = CouncilConfiguration(**config_data)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_by_id(self, config_id: int) -> Optional[CouncilConfiguration]:
        """Get configuration by ID"""
        return self.db.query(CouncilConfiguration).filter(
            CouncilConfiguration.id == config_id
        ).first()

    def get_by_name(self, name: str) -> Optional[CouncilConfiguration]:
        """Get configuration by name"""
        return self.db.query(CouncilConfiguration).filter(
            CouncilConfiguration.name == name
        ).first()

    def get_active(self) -> Optional[CouncilConfiguration]:
        """Get active configuration"""
        return self.db.query(CouncilConfiguration).filter(
            CouncilConfiguration.is_active == True
        ).first()

    def get_default(self) -> Optional[CouncilConfiguration]:
        """Get default configuration"""
        return self.db.query(CouncilConfiguration).filter(
            CouncilConfiguration.is_default == True
        ).first()

    def get_all(self) -> List[CouncilConfiguration]:
        """Get all configurations"""
        return self.db.query(CouncilConfiguration).order_by(
            desc(CouncilConfiguration.is_active),
            desc(CouncilConfiguration.created_at)
        ).all()

    def set_active(self, config_id: int) -> Optional[CouncilConfiguration]:
        """Set a configuration as active (and deactivate others)"""
        # Deactivate all
        self.db.query(CouncilConfiguration).update({"is_active": False})

        # Activate target
        config = self.get_by_id(config_id)
        if config:
            config.is_active = True
            self.db.commit()
            self.db.refresh(config)
            return config
        return None


class CacheRepository:
    """Repository for cache operations"""

    def __init__(self, db: Session):
        self.db = db

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if not expired"""
        cached = self.db.query(CachedResponse).filter(
            CachedResponse.cache_key == cache_key,
            CachedResponse.expires_at > datetime.utcnow()
        ).first()

        if cached:
            cached.hit_count += 1
            self.db.commit()
            return cached.response_data

        return None

    def set(
        self,
        cache_key: str,
        model_id: str,
        prompt_hash: str,
        response_data: Dict[str, Any],
        ttl_seconds: int = 3600
    ) -> CachedResponse:
        """Set cache entry"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        existing = self.db.query(CachedResponse).filter(
            CachedResponse.cache_key == cache_key
        ).first()

        if existing:
            existing.response_data = response_data
            existing.expires_at = expires_at
            existing.hit_count = 0
            self.db.commit()
            self.db.refresh(existing)
            return existing

        cached = CachedResponse(
            cache_key=cache_key,
            model_id=model_id,
            prompt_hash=prompt_hash,
            response_data=response_data,
            expires_at=expires_at
        )
        self.db.add(cached)
        self.db.commit()
        self.db.refresh(cached)
        return cached

    def delete_expired(self) -> int:
        """Delete expired cache entries"""
        result = self.db.query(CachedResponse).filter(
            CachedResponse.expires_at <= datetime.utcnow()
        ).delete()
        self.db.commit()
        return result
