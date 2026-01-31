"""
OpenRouter API service for accessing free models.
"""
import asyncio
from typing import AsyncGenerator
import httpx
from ..config import settings


class OpenRouterService:
    """Service for interacting with OpenRouter API."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.timeout = settings.request_timeout

    async def generate_response(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate a non-streaming response from OpenRouter."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",  # Optional, for rankings
                "X-Title": "LLM Council",  # Optional, shows in rankings
            }

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

    async def generate_streaming_response(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from OpenRouter."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "LLM Council",
            }

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }

            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
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
                            if (
                                "choices" in data
                                and len(data["choices"]) > 0
                                and "delta" in data["choices"][0]
                                and "content" in data["choices"][0]["delta"]
                            ):
                                content = data["choices"][0]["delta"]["content"]
                                yield content
                        except json.JSONDecodeError:
                            continue
