import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any, List, AsyncIterator
from urllib.parse import urljoin

from src.llm.base import BaseLLMClient
from config import config

logger = logging.getLogger(__name__)

class GeminiClient(BaseLLMClient):
    """
    Client for Google Gemini API (Gemini 1.5 Flash / Gemini 3 Flash).
    This client implements the same interface as BaseLLMClient:
        - async generate(prompt: str, temperature: float = 0.7) -> str
        - async embed(texts: List[str]) -> List[List[float]]
    Only generation is implemented for now; embedding can be added later.
    """

    def __init__(self):
        # Load configuration from the central config module
        self.api_key: str = config.GEMINI_API_KEY
        self.model: str = config.GEMINI_MODEL or "gemini-2.5-flash-lite"
        
        # Use v1beta for better compatibility with newer/preview models in 2026
        self.base_url: str = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        logger.info(f"Initialized GeminiClient with model: {self.model}")
        self.headers: Dict[str, str] = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _post_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper to POST JSON to the Gemini API with retry logic.
        Retries on network errors and on 5xx responses.
        """
        import tenacity

        @tenacity.retry(
            reraise=True,
            stop=tenacity.stop_after_attempt(5),
            wait=tenacity.wait_exponential(multiplier=2, min=4, max=20),
            retry=tenacity.retry_if_exception_type((aiohttp.ClientError, aiohttp.ClientResponseError)),
        )
        async def _do_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, headers=self.headers) as resp:
                    logger.debug(f"Gemini API response status: {resp.status}")
                    
                    # Handle Rate Limits (429) specifically
                    if resp.status == 429:
                        logger.warning("Gemini API Rate Limit hit (429). Retrying with backoff...")
                        raise aiohttp.ClientResponseError(
                            request_info=resp.request_info,
                            history=resp.history,
                            status=resp.status,
                            message="Too Many Requests"
                        )
                        
                    # Raise for 5xx errors to trigger retry
                    if 500 <= resp.status < 600:
                        raise aiohttp.ClientResponseError(
                            request_info=resp.request_info,
                            history=resp.history,
                            status=resp.status,
                            message=f"Server error {resp.status}"
                        )
                    resp.raise_for_status()
                    return await resp.json()

        result = await _do_request()
        logger.debug(f"Gemini API raw response keys: {list(result.keys())}")
        return result

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate a text response from Gemini.

        Args:
            prompt: The user prompt.
            temperature: Controls randomness (0‑1). Not directly used by Gemini API
                         but kept for compatibility with Ollama interface.

        Returns:
            Generated text.
        """
        # Gemini does not accept temperature; we ignore it but keep signature compatibility
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generation_config": {
                "temperature": temperature,
                "top_p": 1,
                "max_output_tokens": 8192,
            },
        }

        try:
            result = await self._post_json(payload)
            # The response structure is nested; extract the generated text.
            # Example: {"candidates": [{"outputTokenCount": ..., "content": "..."}]}
            candidates = result.get("candidates")
            if not candidates:
                raise RuntimeError("No candidates returned from Gemini API")

            generated_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            logger.debug(f"Gemini generation produced {len(generated_text)} chars")
            return generated_text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    async def chat(self, messages: List[Dict[str, Any]]) -> str:
        """
        Send a chat request to Gemini.
        For simplicity, we concatenate messages into a single prompt for now,
        respecting the roles where possible.
        """
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant" or role == "ai":
                prompt += f"Assistant: {content}\n"
        
        # Add a final indicator for the AI to respond
        if not prompt.strip().endswith("Assistant:"):
            prompt += "Assistant: "
            
        return await self.generate(prompt)

    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """
        Stream chat response from Gemini.
        Note: The current implementation doesn't actually stream (Gemini API supports it
        but we'd need another endpoint). For interface compatibility, we yield the whole result as one chunk.
        """
        result = await self.generate(prompt)
        yield result

    async def chat_stream(self, prompt: str) -> AsyncIterator[str]:
        """Alias for generate_stream for consistency with agents.py."""
        async for chunk in self.generate_stream(prompt):
            yield chunk

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Gemini does not expose a dedicated embedding endpoint in the public API.
        For now we return an empty list to preserve interface compatibility.
        Future work can integrate the Vertex AI embedding endpoints.
        """
        logger.warning("Gemini embed is not implemented; returning empty list.")
        return [[] for _ in texts]