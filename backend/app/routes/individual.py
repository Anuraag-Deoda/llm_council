"""
Individual model chat endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from ..services.llm_service import LLMService

router = APIRouter(prefix="/individual", tags=["individual"])

llm_service = LLMService()


class IndividualChatRequest(BaseModel):
    """Request for individual model chat."""
    model_id: str
    message: str
    conversation_history: Optional[list] = None  # List of {role, content}


class StreamChunk(BaseModel):
    """Streaming chunk for individual chat."""
    type: str  # "content", "complete", "error"
    content: Optional[str] = None


@router.post("/stream")
async def individual_chat_stream(request: IndividualChatRequest):
    """
    Stream a response from a single model.

    This is a simple 1-on-1 chat without council deliberation.
    """
    try:
        # Build messages array
        messages = request.conversation_history or []
        messages.append({"role": "user", "content": request.message})

        async def generate():
            try:
                # Stream response from the model
                async for chunk in llm_service.generate_streaming_response(
                    model=request.model_id,
                    messages=messages,
                ):
                    yield json.dumps({
                        "type": "content",
                        "content": chunk
                    }) + "\n"

                # Send completion signal
                yield json.dumps({
                    "type": "complete",
                    "content": None
                }) + "\n"

            except Exception as e:
                yield json.dumps({
                    "type": "error",
                    "content": str(e)
                }) + "\n"

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def individual_chat(request: IndividualChatRequest):
    """
    Get a complete response from a single model (non-streaming).
    """
    try:
        # Build messages array
        messages = request.conversation_history or []
        messages.append({"role": "user", "content": request.message})

        # Get response from the model
        response = await llm_service.generate_response(
            model=request.model_id,
            messages=messages,
        )

        return {
            "model_id": request.model_id,
            "response": response,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
