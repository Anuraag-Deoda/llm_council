"""
Advanced analytics endpoints for insights and reporting
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from app.database import get_db
from app.database.models import (
    Conversation, Message, ModelInfo, ConversationAnalytics,
    ModelAnalytics, ChatType
)
from app.database.repositories import AnalyticsRepository, ModelRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# Response Models
# ============================================================================

class ConversationInsight(BaseModel):
    conversation_id: str
    total_interactions: int
    total_latency_ms: int
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    avg_consensus_score: float


class ModelPerformance(BaseModel):
    model_id: str
    model_name: str
    total_requests: int
    total_errors: int
    success_rate: float
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    avg_peer_review_rank: Optional[float]


class TrendData(BaseModel):
    timestamp: datetime
    value: float
    label: str


class LeaderboardEntry(BaseModel):
    rank: int
    model_id: str
    model_name: str
    metric_value: float
    metric_name: str


# ============================================================================
# Insights Endpoints
# ============================================================================

@router.get("/conversations/{conversation_id}", response_model=ConversationInsight)
def get_conversation_insights(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed insights for a conversation"""
    from app.core.analytics import analytics_service

    insights = analytics_service.get_conversation_insights(db, conversation_id)

    if not insights:
        return ConversationInsight(
            conversation_id=conversation_id,
            total_interactions=0,
            total_latency_ms=0,
            avg_latency_ms=0,
            total_tokens=0,
            total_cost=0,
            avg_consensus_score=0
        )

    return ConversationInsight(**insights)


@router.get("/models/{model_id}/performance", response_model=ModelPerformance)
def get_model_performance(
    model_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific model"""
    from app.core.analytics import analytics_service

    insights = analytics_service.get_model_insights(
        db, model_id, start_date, end_date
    )

    if not insights or insights.get("no_data"):
        # Return default data
        model_repo = ModelRepository(db)
        model = model_repo.get_by_id(model_id)

        return ModelPerformance(
            model_id=model_id,
            model_name=model.name if model else model_id,
            total_requests=0,
            total_errors=0,
            success_rate=0.0,
            avg_latency_ms=0.0,
            total_tokens=0,
            total_cost=0.0,
            avg_peer_review_rank=None
        )

    return ModelPerformance(**insights)


@router.get("/trends/usage")
def get_usage_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get usage trends over time"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get conversation counts by day
    daily_counts = db.query(
        func.date(Conversation.created_at).label('date'),
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.created_at >= start_date,
        Conversation.created_at <= end_date
    ).group_by(
        func.date(Conversation.created_at)
    ).order_by('date').all()

    trends = [
        TrendData(
            timestamp=datetime.combine(date, datetime.min.time()),
            value=float(count),
            label="Conversations"
        )
        for date, count in daily_counts
    ]

    return {"trends": trends}


@router.get("/trends/cost")
def get_cost_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get cost trends over time"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get daily costs
    daily_costs = db.query(
        func.date(Conversation.created_at).label('date'),
        func.sum(Conversation.total_cost).label('cost')
    ).filter(
        Conversation.created_at >= start_date,
        Conversation.created_at <= end_date
    ).group_by(
        func.date(Conversation.created_at)
    ).order_by('date').all()

    trends = [
        TrendData(
            timestamp=datetime.combine(date, datetime.min.time()),
            value=float(cost or 0),
            label="Cost (USD)"
        )
        for date, cost in daily_costs
    ]

    return {"trends": trends}


@router.get("/trends/tokens")
def get_token_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get token usage trends over time"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get daily token usage
    daily_tokens = db.query(
        func.date(Conversation.created_at).label('date'),
        func.sum(Conversation.total_tokens).label('tokens')
    ).filter(
        Conversation.created_at >= start_date,
        Conversation.created_at <= end_date
    ).group_by(
        func.date(Conversation.created_at)
    ).order_by('date').all()

    trends = [
        TrendData(
            timestamp=datetime.combine(date, datetime.min.time()),
            value=float(tokens or 0),
            label="Tokens"
        )
        for date, tokens in daily_tokens
    ]

    return {"trends": trends}


# ============================================================================
# Leaderboards
# ============================================================================

@router.get("/leaderboard/latency")
def get_latency_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get model leaderboard by average latency (lower is better)"""
    models = db.query(ModelInfo).filter(
        ModelInfo.is_active == True,
        ModelInfo.avg_latency_ms > 0
    ).order_by(
        ModelInfo.avg_latency_ms
    ).limit(limit).all()

    leaderboard = [
        LeaderboardEntry(
            rank=idx + 1,
            model_id=model.id,
            model_name=model.name,
            metric_value=model.avg_latency_ms,
            metric_name="Avg Latency (ms)"
        )
        for idx, model in enumerate(models)
    ]

    return {"leaderboard": leaderboard}


@router.get("/leaderboard/success-rate")
def get_success_rate_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get model leaderboard by success rate (higher is better)"""
    models = db.query(ModelInfo).filter(
        ModelInfo.is_active == True,
        ModelInfo.total_requests > 0
    ).all()

    # Calculate success rates
    model_rates = []
    for model in models:
        success_rate = (
            (model.total_requests - model.total_errors) / model.total_requests * 100
        )
        model_rates.append({
            "model": model,
            "success_rate": success_rate
        })

    # Sort by success rate (descending)
    model_rates.sort(key=lambda x: x["success_rate"], reverse=True)

    leaderboard = [
        LeaderboardEntry(
            rank=idx + 1,
            model_id=item["model"].id,
            model_name=item["model"].name,
            metric_value=item["success_rate"],
            metric_name="Success Rate (%)"
        )
        for idx, item in enumerate(model_rates[:limit])
    ]

    return {"leaderboard": leaderboard}


@router.get("/leaderboard/peer-review")
def get_peer_review_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get model leaderboard by peer review rankings"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get average peer review ranks
    model_ranks = db.query(
        ModelAnalytics.model_id,
        func.avg(ModelAnalytics.avg_peer_review_rank).label('avg_rank')
    ).filter(
        ModelAnalytics.timestamp >= start_date,
        ModelAnalytics.timestamp <= end_date,
        ModelAnalytics.avg_peer_review_rank.isnot(None)
    ).group_by(
        ModelAnalytics.model_id
    ).order_by(
        'avg_rank'
    ).limit(limit).all()

    model_repo = ModelRepository(db)

    leaderboard = []
    for idx, (model_id, avg_rank) in enumerate(model_ranks):
        model = model_repo.get_by_id(model_id)

        leaderboard.append(LeaderboardEntry(
            rank=idx + 1,
            model_id=model_id,
            model_name=model.name if model else model_id,
            metric_value=avg_rank,
            metric_name="Avg Peer Review Rank"
        ))

    return {"leaderboard": leaderboard}


# ============================================================================
# Comparisons
# ============================================================================

@router.get("/compare/models")
def compare_models(
    model_ids: List[str] = Query(...),
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Compare multiple models side by side"""
    from app.core.analytics import analytics_service

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    comparisons = []

    for model_id in model_ids:
        insights = analytics_service.get_model_insights(
            db, model_id, start_date, end_date
        )

        if insights and not insights.get("no_data"):
            comparisons.append(insights)

    return {"models": comparisons}


@router.get("/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Get high-level analytics summary"""
    analytics_repo = AnalyticsRepository(db)
    global_stats = analytics_repo.get_global_stats()

    # Get conversation type breakdown
    council_count = db.query(func.count(Conversation.id)).filter(
        Conversation.type == ChatType.COUNCIL
    ).scalar()

    individual_count = db.query(func.count(Conversation.id)).filter(
        Conversation.type == ChatType.INDIVIDUAL
    ).scalar()

    # Get recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_conversations = db.query(func.count(Conversation.id)).filter(
        Conversation.created_at >= yesterday
    ).scalar()

    recent_messages = db.query(func.count(Message.id)).filter(
        Message.created_at >= yesterday
    ).scalar()

    return {
        "global_stats": global_stats,
        "conversation_breakdown": {
            "council": council_count,
            "individual": individual_count
        },
        "recent_activity": {
            "conversations_24h": recent_conversations,
            "messages_24h": recent_messages
        }
    }
