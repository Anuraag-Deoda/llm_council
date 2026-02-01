"""
Admin endpoints for managing the LLM Council system
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.database.repositories import ModelRepository, ConfigurationRepository, AnalyticsRepository

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ModelResponse(BaseModel):
    id: str
    name: str
    provider: str
    is_active: bool
    is_chairman: bool
    max_tokens: Optional[int]
    temperature: float
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    capabilities: List[str]
    total_requests: int
    total_errors: int
    avg_latency_ms: float

    class Config:
        from_attributes = True


class CouncilConfigResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    is_default: bool
    voting_system: str
    min_models: int
    max_models: Optional[int]
    chairman_model_id: Optional[str]
    enable_peer_review: bool
    peer_review_anonymous: bool

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    id: str
    name: str
    provider: str
    is_active: bool = True
    is_chairman: bool = False
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    capabilities: List[str] = []


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_chairman: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None
    capabilities: Optional[List[str]] = None


class CouncilConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    voting_system: str = "ranked_choice"
    min_models: int = 3
    max_models: Optional[int] = None
    chairman_model_id: Optional[str] = None
    enable_peer_review: bool = True
    peer_review_anonymous: bool = True


class CouncilConfigUpdate(BaseModel):
    description: Optional[str] = None
    voting_system: Optional[str] = None
    min_models: Optional[int] = None
    max_models: Optional[int] = None
    chairman_model_id: Optional[str] = None
    enable_peer_review: Optional[bool] = None
    peer_review_anonymous: Optional[bool] = None
    is_active: Optional[bool] = None


class SystemStats(BaseModel):
    total_models: int
    active_models: int
    total_conversations: int
    total_messages: int
    total_tokens: int
    total_cost: float
    active_configurations: int


# ============================================================================
# Model Management Endpoints
# ============================================================================

@router.get("/models", response_model=List[ModelResponse])
def list_models(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all models in the system"""
    from app.database.models import ModelInfo
    repo = ModelRepository(db)

    if active_only:
        models = repo.get_all_active()
    else:
        models = db.query(ModelInfo).all()

    return models


@router.post("/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create_model(
    model_data: ModelCreate,
    db: Session = Depends(get_db)
):
    """Create a new model"""
    repo = ModelRepository(db)

    # Check if model already exists
    existing = repo.get_by_id(model_data.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model {model_data.id} already exists"
        )

    model = repo.create(model_data.model_dump())
    return model


@router.get("/models/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific model"""
    repo = ModelRepository(db)
    model = repo.get_by_id(model_id)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )

    return model


@router.patch("/models/{model_id}", response_model=ModelResponse)
def update_model(
    model_id: str,
    model_update: ModelUpdate,
    db: Session = Depends(get_db)
):
    """Update a model"""
    repo = ModelRepository(db)

    # Filter out None values
    update_data = {k: v for k, v in model_update.model_dump().items() if v is not None}

    model = repo.update(model_id, update_data)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )

    return model


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Deactivate a model (soft delete)"""
    repo = ModelRepository(db)

    model = repo.update(model_id, {"is_active": False})

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )


# ============================================================================
# Council Configuration Endpoints
# ============================================================================

@router.get("/configs", response_model=List[CouncilConfigResponse])
def list_configurations(db: Session = Depends(get_db)):
    """List all council configurations"""
    repo = ConfigurationRepository(db)
    return repo.get_all()


@router.post("/configs", response_model=CouncilConfigResponse, status_code=status.HTTP_201_CREATED)
def create_configuration(
    config_data: CouncilConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new council configuration"""
    repo = ConfigurationRepository(db)

    # Check if config with same name exists
    existing = repo.get_by_name(config_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Configuration '{config_data.name}' already exists"
        )

    config = repo.create(config_data.model_dump())
    return config


@router.get("/configs/{config_id}", response_model=CouncilConfigResponse)
def get_configuration(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific configuration"""
    repo = ConfigurationRepository(db)
    config = repo.get_by_id(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    return config


@router.patch("/configs/{config_id}", response_model=CouncilConfigResponse)
def update_configuration(
    config_id: int,
    config_update: CouncilConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update a council configuration"""
    repo = ConfigurationRepository(db)

    config = repo.get_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    # Update configuration
    update_data = {k: v for k, v in config_update.model_dump().items() if v is not None}

    for key, value in update_data.items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)

    return config


@router.post("/configs/{config_id}/activate", response_model=CouncilConfigResponse)
def activate_configuration(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Set a configuration as active"""
    repo = ConfigurationRepository(db)

    config = repo.set_active(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    return config


# ============================================================================
# System Statistics Endpoints
# ============================================================================

@router.get("/stats", response_model=SystemStats)
def get_system_stats(db: Session = Depends(get_db)):
    """Get overall system statistics"""
    model_repo = ModelRepository(db)
    analytics_repo = AnalyticsRepository(db)
    config_repo = ConfigurationRepository(db)

    # Get model counts
    all_models = db.query(ModelInfo).all()
    active_models = [m for m in all_models if m.is_active]

    # Get global stats
    global_stats = analytics_repo.get_global_stats()

    # Get active configs
    active_configs = db.query(CouncilConfiguration).filter(
        CouncilConfiguration.is_active == True
    ).count()

    return SystemStats(
        total_models=len(all_models),
        active_models=len(active_models),
        total_conversations=global_stats.get("total_conversations", 0),
        total_messages=global_stats.get("total_messages", 0),
        total_tokens=global_stats.get("total_tokens", 0),
        total_cost=global_stats.get("total_cost", 0.0),
        active_configurations=active_configs
    )


@router.get("/stats/models/{model_id}")
def get_model_stats(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific model"""
    from app.core.analytics import analytics_service

    insights = analytics_service.get_model_insights(db, model_id)

    if not insights:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No statistics found for model {model_id}"
        )

    return insights


@router.post("/maintenance/cleanup-cache")
def trigger_cache_cleanup(db: Session = Depends(get_db)):
    """Manually trigger cache cleanup"""
    from app.database.repositories import CacheRepository

    cache_repo = CacheRepository(db)
    deleted_count = cache_repo.delete_expired()

    return {
        "status": "success",
        "deleted_entries": deleted_count
    }


@router.post("/maintenance/sync-models")
def sync_models_from_config(db: Session = Depends(get_db)):
    """Sync models from configuration to database"""
    from app.config import settings

    model_repo = ModelRepository(db)
    created_count = 0
    updated_count = 0

    # Sync OpenAI models
    for model_id in settings.openai_models:
        existing = model_repo.get_by_id(model_id)

        model_data = {
            "id": model_id,
            "name": model_id.upper(),
            "provider": "openai",
            "is_active": True,
            "is_chairman": model_id == settings.chairman_model
        }

        if existing:
            model_repo.update(model_id, model_data)
            updated_count += 1
        else:
            model_repo.create(model_data)
            created_count += 1

    # Sync OpenRouter models
    for model_id in settings.openrouter_models:
        existing = model_repo.get_by_id(model_id)

        model_data = {
            "id": model_id,
            "name": model_id.split("/")[-1],
            "provider": "openrouter",
            "is_active": True,
            "is_chairman": False
        }

        if existing:
            model_repo.update(model_id, model_data)
            updated_count += 1
        else:
            model_repo.create(model_data)
            created_count += 1

    return {
        "status": "success",
        "created": created_count,
        "updated": updated_count
    }
