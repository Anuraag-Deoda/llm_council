"""
OpenAI API service for GPT models.
"""
import asyncio
from typing import AsyncGenerator, Optional
import httpx
from ..config import settings


class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.timeout = settings.request_timeout

    def _is_gpt5_model(self, model: str) -> bool:
        """Check if the model is GPT-5.x which uses the responses endpoint."""
        return model.startswith("gpt-5")

    def _get_endpoint(self, model: str) -> str:
        """Get the appropriate endpoint for the model."""
        if self._is_gpt5_model(model):
            return f"{self.base_url}/responses"
        return f"{self.base_url}/chat/completions"

    async def generate_response(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate a non-streaming response from OpenAI."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # GPT-5 uses 'input' instead of 'messages'
            if self._is_gpt5_model(model):
                payload = {
                    "model": model,
                    "input": messages[0]["content"] if len(messages) == 1 else "\n\n".join([f"{m['role']}: {m['content']}" for m in messages]),
                    "text": {
                        "verbosity": "medium"
                    }
                }
            else:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

            endpoint = self._get_endpoint(model)
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

            # GPT-5 responses have different structure
            if self._is_gpt5_model(model):
                return data["text"]["content"]

            return data["choices"][0]["message"]["content"]

    async def generate_streaming_response(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from OpenAI."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # GPT-5 uses 'input' instead of 'messages'
            if self._is_gpt5_model(model):
                payload = {
                    "model": model,
                    "input": messages[0]["content"] if len(messages) == 1 else "\n\n".join([f"{m['role']}: {m['content']}" for m in messages]),
                    "text": {
                        "verbosity": "medium"
                    },
                    "stream": True,
                }
            else:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }

            endpoint = self._get_endpoint(model)

            async with client.stream(
                "POST",
                endpoint,
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            import json

                            data = json.loads(data_str)

                            # GPT-5 streaming format
                            if self._is_gpt5_model(model):
                                if "text" in data:
                                    # GPT-5 can return text as dict with delta or directly
                                    if isinstance(data["text"], dict) and "delta" in data["text"]:
                                        content = data["text"]["delta"]
                                        if content:
                                            yield content
                                    elif isinstance(data["text"], str):
                                        # Sometimes text is directly a string
                                        yield data["text"]
                            # GPT-4 and earlier format
                            elif (
                                "choices" in data
                                and len(data["choices"]) > 0
                                and "delta" in data["choices"][0]
                                and "content" in data["choices"][0]["delta"]
                            ):
                                content = data["choices"][0]["delta"]["content"]
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def generate_chairman_response(
        self,
        user_query: str,
        model_responses: list,
        reviews: Optional[list] = None,
    ) -> str:
        """
        Generate the final chairman response synthesizing all opinions.

        Args:
            user_query: The original user question
            model_responses: List of ModelResponse objects
            reviews: Optional list of ReviewResponse objects
        """
        # Build context for the chairman
        context = f"Original user query: {user_query}\n\n"
        context += "===== COUNCIL MEMBER RESPONSES =====\n\n"

        for i, response in enumerate(model_responses, 1):
            context += f"Response {i} (Model: {response.model_id}):\n"
            context += f"{response.response}\n\n"

        if reviews:
            context += "\n===== PEER REVIEWS AND RANKINGS =====\n\n"
            for review in reviews:
                context += f"Reviewer: {review.reviewer_model}\n"
                context += f"Rankings: {review.rankings}\n\n"

        chairman_prompt = f"""You are the Chairman of the LLM Council. Your role is to synthesize the responses from multiple AI models into a single, comprehensive, accurate answer.

{context}

Your task:
1. Analyze all the responses provided by the council members
2. Consider the peer reviews and rankings if provided
3. Identify common themes and agreements
4. Reconcile any disagreements or contradictions
5. Produce a final, authoritative answer that represents the best synthesis of all perspectives

Provide a clear, well-structured response that directly answers the user's query. Focus on accuracy, completeness, and clarity. Do not mention the internal council process - just provide the final answer as if it came from a single, highly knowledgeable source.
"""

        # For GPT-5, use single message; for GPT-4, use message array
        if self._is_gpt5_model(settings.chairman_model):
            messages = [{"role": "user", "content": chairman_prompt}]
        else:
            messages = [{"role": "user", "content": chairman_prompt}]

        return await self.generate_response(
            model=settings.chairman_model,
            messages=messages,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    async def generate_streaming_chairman_response(
        self,
        user_query: str,
        model_responses: list,
        reviews: Optional[list] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming chairman response.
        """
        # Build context (same as non-streaming)
        context = f"Original user query: {user_query}\n\n"
        context += "===== COUNCIL MEMBER RESPONSES =====\n\n"

        for i, response in enumerate(model_responses, 1):
            context += f"Response {i} (Model: {response.model_id}):\n"
            context += f"{response.response}\n\n"

        if reviews:
            context += "\n===== PEER REVIEWS AND RANKINGS =====\n\n"
            for review in reviews:
                context += f"Reviewer: {review.reviewer_model}\n"
                context += f"Rankings: {review.rankings}\n\n"

        chairman_prompt = f"""You are the Chairman of the LLM Council. Your role is to synthesize the responses from multiple AI models into a single, comprehensive, accurate answer.

{context}

Your task:
1. Analyze all the responses provided by the council members
2. Consider the peer reviews and rankings if provided
3. Identify common themes and agreements
4. Reconcile any disagreements or contradictions
5. Produce a final, authoritative answer that represents the best synthesis of all perspectives

Provide a clear, well-structured response that directly answers the user's query. Focus on accuracy, completeness, and clarity. Do not mention the internal council process - just provide the final answer as if it came from a single, highly knowledgeable source.
"""

        messages = [{"role": "user", "content": chairman_prompt}]

        async for chunk in self.generate_streaming_response(
            model=settings.chairman_model,
            messages=messages,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        ):
            yield chunk
