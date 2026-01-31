"""
Unified LLM service that abstracts OpenAI and OpenRouter.
"""
from typing import AsyncGenerator, List
from .openai_service import OpenAIService
from .openrouter_service import OpenRouterService
from ..config import settings
from ..models import ModelInfo


class LLMService:
    """Unified service for all LLM interactions."""

    def __init__(self):
        self.openai_service = OpenAIService()
        self.openrouter_service = OpenRouterService()

    def get_available_models(self) -> List[ModelInfo]:
        """Get list of all available models."""
        models = []

        # Add OpenRouter models
        for model_id in settings.openrouter_models:
            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_id.split("/")[-1].split(":")[0],  # Extract name
                    provider="openrouter",
                    is_chairman=False,
                )
            )

        # Add OpenAI models
        for model_id in settings.openai_models:
            is_chairman = model_id == settings.chairman_model
            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider="openai",
                    is_chairman=is_chairman,
                )
            )

        return models

    def _get_service(self, model_id: str):
        """Get the appropriate service for a model."""
        if model_id in settings.openai_models:
            return self.openai_service
        elif model_id in settings.openrouter_models:
            return self.openrouter_service
        else:
            raise ValueError(f"Unknown model: {model_id}")

    async def generate_response(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate a response from any model."""
        service = self._get_service(model)
        return await service.generate_response(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_streaming_response(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from any model."""
        service = self._get_service(model)
        async for chunk in service.generate_streaming_response(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    async def generate_review(
        self,
        reviewer_model: str,
        user_query: str,
        responses: list,
        exclude_model: str,
    ) -> dict:
        """
        Have a model review and rank other models' responses.

        Args:
            reviewer_model: The model doing the reviewing
            user_query: Original user query
            responses: List of ModelResponse objects
            exclude_model: The reviewer's own response to exclude
        """
        # Anonymize responses (exclude reviewer's own response)
        anonymized = []
        model_map = {}  # Maps letter to model_id

        letter_idx = 0
        for response in responses:
            if response.model_id == exclude_model:
                continue

            letter = chr(65 + letter_idx)  # A, B, C, etc.
            model_map[letter] = response.model_id
            anonymized.append(
                {
                    "id": letter,
                    "response": response.response,
                }
            )
            letter_idx += 1

        if not anonymized:
            return {"rankings": [], "model_map": model_map}

        # Build review prompt
        review_prompt = f"""You are reviewing responses from other AI models to the following user query:

USER QUERY: {user_query}

Below are the responses from other models (anonymized as A, B, C, etc.):

"""

        for item in anonymized:
            review_prompt += f"\n===== Response {item['id']} =====\n"
            review_prompt += f"{item['response']}\n"

        review_prompt += """

Your task is to:
1. Evaluate each response for accuracy, completeness, clarity, and usefulness
2. Rank them from best to worst
3. Provide brief reasoning for your rankings

Respond in the following JSON format:
{
  "rankings": [
    {
      "response_id": "A",
      "rank": 1,
      "reasoning": "Brief explanation of why this is ranked first"
    },
    {
      "response_id": "B",
      "rank": 2,
      "reasoning": "Brief explanation of why this is ranked second"
    }
  ]
}

Be objective and critical. Focus on factual accuracy and helpfulness.
"""

        messages = [{"role": "user", "content": review_prompt}]

        # Get review from the model
        review_text = await self.generate_response(
            model=reviewer_model,
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent reviews
            max_tokens=2000,
        )

        # Parse the JSON response
        import json
        import re

        # Try to extract JSON from the response
        json_match = re.search(r"\{.*\}", review_text, re.DOTALL)
        if json_match:
            try:
                review_data = json.loads(json_match.group())

                # Map anonymous IDs back to model IDs
                rankings = []
                for ranking in review_data.get("rankings", []):
                    response_id = ranking.get("response_id")
                    if response_id in model_map:
                        rankings.append(
                            {
                                "model_id": model_map[response_id],
                                "rank": ranking.get("rank"),
                                "reasoning": ranking.get("reasoning"),
                            }
                        )

                return {"rankings": rankings, "model_map": model_map}
            except json.JSONDecodeError:
                pass

        # Fallback if parsing fails
        return {"rankings": [], "model_map": model_map}
