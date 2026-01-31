"""
Models endpoints for listing available models.
"""
from fastapi import APIRouter
from typing import List
from ..models import ModelInfo
from ..services.llm_service import LLMService

router = APIRouter(prefix="/models", tags=["models"])

llm_service = LLMService()


@router.get("/", response_model=List[ModelInfo])
async def get_models():
    """
    Get list of all available models.

    Returns models from both OpenAI and OpenRouter.
    """
    return llm_service.get_available_models()


@router.get("/chairman")
async def get_chairman():
    """Get the current chairman model."""
    from ..config import settings

    return {
        "chairman_model": settings.chairman_model,
        "provider": "openai",
    }
