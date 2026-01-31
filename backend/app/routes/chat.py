"""
Chat endpoints for the LLM Council.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models import ChatRequest, CouncilResponse
from ..services.council_orchestrator import CouncilOrchestrator
from ..database import ConversationStorage
from ..config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
orchestrator = CouncilOrchestrator()
storage = ConversationStorage(settings.database_path)


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream a council response to a user query.

    Returns a streaming response with JSON-encoded chunks.
    """
    try:
        # Create or get conversation
        if request.conversation_id:
            conversation = storage.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            conversation_id = request.conversation_id
        else:
            conversation_id = storage.create_conversation()

        # Add user message to history
        storage.add_message(conversation_id, "user", request.message)

        # Stream the council response
        async def generate():
            final_response_parts = []

            async for chunk in orchestrator.run_council(
                user_query=request.message,
                conversation_id=conversation_id,
                selected_models=request.selected_models,
                stream=True,
            ):
                yield chunk

                # Collect final response parts
                import json
                try:
                    chunk_data = json.loads(chunk.strip())
                    if chunk_data.get("type") == "final_response":
                        content = chunk_data.get("content", "")
                        if content:
                            final_response_parts.append(content)
                except json.JSONDecodeError:
                    pass

            # After streaming completes, save the final response to history
            if final_response_parts:
                final_response = "".join(final_response_parts)
                storage.add_message(conversation_id, "assistant", final_response)

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "X-Conversation-ID": conversation_id,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CouncilResponse)
async def chat(request: ChatRequest):
    """
    Get a complete council response (non-streaming).

    Useful for testing or when streaming is not needed.
    """
    try:
        # Create or get conversation
        if request.conversation_id:
            conversation = storage.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            conversation_id = request.conversation_id
        else:
            conversation_id = storage.create_conversation()

        # Add user message to history
        storage.add_message(conversation_id, "user", request.message)

        # Run the council
        response = await orchestrator.run_council_non_streaming(
            user_query=request.message,
            conversation_id=conversation_id,
            selected_models=request.selected_models,
        )

        # Save council response
        storage.add_council_response(conversation_id, response)

        # Save assistant message
        if response.final_response:
            storage.add_message(conversation_id, "assistant", response.final_response)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get conversation history."""
    conversation = storage.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.get("/conversations")
async def list_conversations():
    """List all conversations."""
    return storage.list_conversations()


@router.delete("/history/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    success = storage.delete_conversation(conversation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "deleted"}
