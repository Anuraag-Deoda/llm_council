"""
Council orchestrator that manages the 3-stage process.
"""
import asyncio
from datetime import datetime
from typing import List, AsyncGenerator, Optional
import json

from .llm_service import LLMService
from ..models import (
    ModelResponse,
    ReviewResponse,
    CouncilResponse,
    Stage,
    StreamChunk,
)
from ..config import settings


class CouncilOrchestrator:
    """Orchestrates the LLM Council's 3-stage deliberation process."""

    def __init__(self):
        self.llm_service = LLMService()

    async def run_council(
        self,
        user_query: str,
        conversation_id: str,
        selected_models: Optional[List[str]] = None,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Run the complete council process with streaming updates.

        Yields JSON-encoded StreamChunk objects.
        """
        # Determine which models to use
        if selected_models:
            models = selected_models
        else:
            # Use all available models
            all_models = self.llm_service.get_available_models()
            models = [m.id for m in all_models]

        # Stage 1: First Opinions
        yield self._encode_chunk(
            StreamChunk(
                type="stage_update",
                stage=Stage.FIRST_OPINIONS,
                content="Gathering initial responses from council members...",
            )
        )

        first_opinions = await self._stage1_first_opinions(
            user_query=user_query,
            models=models,
            stream=stream,
        )

        # Yield each first opinion as it completes
        for opinion in first_opinions:
            if opinion.error:
                yield self._encode_chunk(
                    StreamChunk(
                        type="error",
                        model_id=opinion.model_id,
                        content=f"Error from {opinion.model_id}: {opinion.error}",
                    )
                )
            else:
                yield self._encode_chunk(
                    StreamChunk(
                        type="model_response",
                        stage=Stage.FIRST_OPINIONS,
                        model_id=opinion.model_id,
                        content=opinion.response,
                    )
                )

        # Filter out failed responses
        valid_opinions = [o for o in first_opinions if not o.error]

        if not valid_opinions:
            yield self._encode_chunk(
                StreamChunk(
                    type="error",
                    content="All models failed to respond. Please try again.",
                )
            )
            return

        # Stage 2: Review
        yield self._encode_chunk(
            StreamChunk(
                type="stage_update",
                stage=Stage.REVIEW,
                content="Council members reviewing each other's responses...",
            )
        )

        reviews = await self._stage2_review(
            user_query=user_query,
            first_opinions=valid_opinions,
        )

        # Yield reviews
        for review in reviews:
            yield self._encode_chunk(
                StreamChunk(
                    type="review",
                    stage=Stage.REVIEW,
                    model_id=review.reviewer_model,
                    data={"rankings": review.rankings},
                )
            )

        # Stage 3: Final Response
        yield self._encode_chunk(
            StreamChunk(
                type="stage_update",
                stage=Stage.FINAL_RESPONSE,
                content=f"Chairman ({settings.chairman_model}) compiling final response...",
            )
        )

        # Stream the chairman's response
        async for chunk in self._stage3_final_response_streaming(
            user_query=user_query,
            first_opinions=valid_opinions,
            reviews=reviews,
        ):
            yield self._encode_chunk(
                StreamChunk(
                    type="final_response",
                    stage=Stage.FINAL_RESPONSE,
                    content=chunk,
                )
            )

        # Send completion signal
        yield self._encode_chunk(
            StreamChunk(
                type="complete",
                content="Council deliberation complete.",
            )
        )

    async def _stage1_first_opinions(
        self,
        user_query: str,
        models: List[str],
        stream: bool = True,
    ) -> List[ModelResponse]:
        """
        Stage 1: Collect first opinions from all models in parallel.
        """
        messages = [{"role": "user", "content": user_query}]

        async def get_model_response(model_id: str) -> ModelResponse:
            try:
                response = await self.llm_service.generate_response(
                    model=model_id,
                    messages=messages,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                )

                return ModelResponse(
                    model_id=model_id,
                    response=response,
                    timestamp=datetime.now().timestamp(),
                )
            except Exception as e:
                return ModelResponse(
                    model_id=model_id,
                    response="",
                    timestamp=datetime.now().timestamp(),
                    error=str(e),
                )

        # Run all requests in parallel
        tasks = [get_model_response(model) for model in models]
        responses = await asyncio.gather(*tasks)

        return responses

    async def _stage2_review(
        self,
        user_query: str,
        first_opinions: List[ModelResponse],
    ) -> List[ReviewResponse]:
        """
        Stage 2: Have each model review the others' responses.
        """

        async def get_review(model: ModelResponse) -> Optional[ReviewResponse]:
            try:
                review_data = await self.llm_service.generate_review(
                    reviewer_model=model.model_id,
                    user_query=user_query,
                    responses=first_opinions,
                    exclude_model=model.model_id,
                )

                return ReviewResponse(
                    reviewer_model=model.model_id,
                    rankings=review_data.get("rankings", []),
                    timestamp=datetime.now().timestamp(),
                )
            except Exception as e:
                print(f"Review error from {model.model_id}: {e}")
                return None

        # Run all reviews in parallel
        tasks = [get_review(model) for model in first_opinions]
        reviews = await asyncio.gather(*tasks)

        # Filter out None results
        return [r for r in reviews if r is not None]

    async def _stage3_final_response_streaming(
        self,
        user_query: str,
        first_opinions: List[ModelResponse],
        reviews: List[ReviewResponse],
    ) -> AsyncGenerator[str, None]:
        """
        Stage 3: Chairman synthesizes final response (streaming).
        """
        async for chunk in self.llm_service.openai_service.generate_streaming_chairman_response(
            user_query=user_query,
            model_responses=first_opinions,
            reviews=reviews,
        ):
            yield chunk

    def _encode_chunk(self, chunk: StreamChunk) -> str:
        """Encode a StreamChunk as a JSON string."""
        return json.dumps(chunk.model_dump()) + "\n"

    async def run_council_non_streaming(
        self,
        user_query: str,
        conversation_id: str,
        selected_models: Optional[List[str]] = None,
    ) -> CouncilResponse:
        """
        Run the complete council process without streaming (for testing).
        """
        # Determine which models to use
        if selected_models:
            models = selected_models
        else:
            all_models = self.llm_service.get_available_models()
            models = [m.id for m in all_models]

        # Stage 1
        first_opinions = await self._stage1_first_opinions(
            user_query=user_query,
            models=models,
            stream=False,
        )

        valid_opinions = [o for o in first_opinions if not o.error]

        if not valid_opinions:
            raise ValueError("All models failed to respond")

        # Stage 2
        reviews = await self._stage2_review(
            user_query=user_query,
            first_opinions=valid_opinions,
        )

        # Stage 3 (non-streaming)
        final_response = await self.llm_service.openai_service.generate_chairman_response(
            user_query=user_query,
            model_responses=valid_opinions,
            reviews=reviews,
        )

        return CouncilResponse(
            conversation_id=conversation_id,
            stage=Stage.FINAL_RESPONSE,
            user_query=user_query,
            first_opinions=first_opinions,
            reviews=reviews,
            final_response=final_response,
            chairman_model=settings.chairman_model,
            models_used=models,
            timestamp=datetime.now().timestamp(),
        )
