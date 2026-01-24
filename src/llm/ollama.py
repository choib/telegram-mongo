import httpx
import json
import logging
from typing import AsyncIterator, Dict, Any, List
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)


from src.llm.base import BaseLLMClient

class OllamaClient(BaseLLMClient):
    """Client for interacting with Ollama API with connection pooling and caching."""
    
    # Connection pool by host - class-level to share across instances
    _client_pool = {}
    _pool_lock = None
    
    def __init__(self, host: str, model: str, timeout: int = 60, cache_size: int = 1000):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server host URL
            model: Default model to use
            timeout: Request timeout in seconds
            cache_size: Maximum number of cached responses
        """
        self.host = host
        self.model = model
        self.timeout = timeout
        self.cache_size = cache_size
        
        # Initialize cache
        self._response_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize pool lock if not exists
        if OllamaClient._pool_lock is None:
            import asyncio
            OllamaClient._pool_lock = asyncio.Lock()
    
    async def _get_client(self):
        """
        Get or create HTTP client for connection pooling, ensuring it's valid for the current loop.
        """
        import asyncio
        import httpx
        
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        async with OllamaClient._pool_lock:
            client_data = OllamaClient._client_pool.get(self.host)
            client = client_data[0] if client_data else None
            client_loop = client_data[1] if client_data else None
            
            # Recreate client if:
            # 1. It doesn't exist
            # 2. It's explicitly closed
            # 3. The loop it was created on is different from the current loop
            if client is None or client.is_closed or client_loop != current_loop:
                if client:
                    try:
                        # Don't await aclose if the loop is already closed/different
                        if client_loop == current_loop:
                            await client.aclose()
                    except:
                        pass
                
                logger.info(f"Creating new httpx client for {self.host} (Loop changed: {client_loop != current_loop})")
                new_client = httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=httpx.Limits(
                        max_connections=100,
                        max_keepalive_connections=50
                    )
                )
                OllamaClient._client_pool[self.host] = (new_client, current_loop)
                return new_client
            
            return client
    
    def _get_cache_key(self, prompt: str) -> str:
        """
        Generate cache key from prompt with normalization.
        
        Args:
            prompt: The prompt to hash
            
        Returns:
            Cache key string
        """
        # Normalize prompt by removing extra whitespace and standardizing
        # This helps with cache hits for semantically identical queries
        normalized_prompt = " ".join(prompt.strip().split())
        
        # Use SHA256 hash of normalized prompt for cache key
        return hashlib.sha256(normalized_prompt.encode('utf-8')).hexdigest()
    
    def _get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache hit/miss counts
        """
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_size': len(self._response_cache)
        }
    
    async def generate(self, prompt: Any, temperature: float = 0.7) -> str:
        """
        Generate a response (compatible with BaseLLMClient).
        Supports both string prompt and dict with messages.
        """
        if isinstance(prompt, dict) and "messages" in prompt:
            # Convert LangChain formatted messages to Ollama format if needed
            # For now, just pass through if it's already in a list-like format
            return await self.chat(prompt["messages"])
        return await self.request(str(prompt))

    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Alias for chat_stream for consistency with bot.py."""
        async for chunk in self.chat_stream(prompt):
            yield chunk

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Mock embed for Ollama (can be expanded later with /api/embeddings)."""
        return [[] for _ in texts]

    async def request(self, prompt: str) -> str:
        """
        Send a request to Ollama generate endpoint.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Generated response
            
        Raises:
            httpx.HTTPError: If request fails
        """
        # Check cache first
        cache_key = self._get_cache_key(prompt)
        if cache_key in self._response_cache:
            self._cache_hits += 1
            logger.debug(f"Cache hit for prompt (key: {cache_key[:16]}...)")
            return self._response_cache[cache_key]
        
        self._cache_misses += 1
        client = await self._get_client()
        
        logger.info(f"Ollama Request: POST /api/generate (Model: {self.model})")
        try:
            response = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            out = ""
            chunk_count = 0
            async for chunk in response.aiter_bytes():
                if chunk:
                    try:
                        data = json.loads(chunk)
                        chunk_content = data.get("response", "")
                        out += chunk_content
                        chunk_count += 1
                    except json.JSONDecodeError:
                        pass
            
            logger.info(f"Ollama Request Complete: Received {chunk_count} chunks, {len(out)} chars")
            # Cache the response
            if len(self._response_cache) < self.cache_size:
                self._response_cache[cache_key] = out
            
            return out
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, Any]]) -> str:
        """
        Send a chat request to Ollama.
        
        Args:
            messages: Chat messages in Ollama format
            
        Returns:
            Chat response
            
        Raises:
            httpx.HTTPError: If request fails
        """
        logger.debug(f"Ollama chat input messages type: {type(messages)}")
        
        # Create cache key from messages
        messages_json = json.dumps(messages, sort_keys=True)
        cache_key = self._get_cache_key(messages_json)
        
        # Check cache first
        if cache_key in self._response_cache:
            self._cache_hits += 1
            logger.debug(f"Cache hit for chat (key: {cache_key[:16]}...)")
            return self._response_cache[cache_key]
        
        self._cache_misses += 1
        client = await self._get_client()
        
        logger.info(f"Ollama Chat: POST /api/chat (Model: {self.model})")
        try:
            request_data = {
                "model": self.model,
                "messages": messages,
            }
            
            response = await client.post(
                f"{self.host}/api/chat",
                json=request_data,
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            
            out = ""
            line_count = 0
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk_content = data.get("message", {}).get("content", "")
                        out += chunk_content
                        line_count += 1
                    except json.JSONDecodeError:
                        pass
            
            logger.info(f"Ollama Chat Complete: Received {line_count} lines, {len(out)} chars")
            # Cache the response
            if len(self._response_cache) < self.cache_size:
                self._response_cache[cache_key] = out
            
            return out
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    async def chat_stream(self, prompt: str) -> AsyncIterator[str]:
        """
        Stream chat response from Ollama.
        
        Args:
            prompt: The prompt to send
            
        Yields:
            Response chunks
            
        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        
        logger.info(f"Ollama Stream: POST /api/generate (Model: {self.model})")
        async with client.stream(
            "POST",
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
            },
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            chunk_count = 0
            async for chunk in response.aiter_bytes():
                if chunk:
                    try:
                        data = json.loads(chunk)
                        chunk_content = data.get("response", "")
                        yield chunk_content
                        chunk_count += 1
                    except json.JSONDecodeError:
                        pass
            logger.info(f"Ollama Stream Complete: Sent {chunk_count} chunks")


# Legacy functions for backward compatibility
async def ollama_request(prompt: str, host: str, model: str) -> str:
    """Legacy function for backward compatibility."""
    client = OllamaClient(host=host, model=model)
    return await client.request(prompt)


async def ollama_chat(messages: Dict[str, Any], host: str, model: str) -> str:
    """Legacy function for backward compatibility."""
    client = OllamaClient(host=host, model=model)
    return await client.chat(messages)


async def ollama_chat_stream(prompt: str, host: str, model: str) -> AsyncIterator[str]:
    """Legacy function for backward compatibility."""
    client = OllamaClient(host=host, model=model)
    async for chunk in client.chat_stream(prompt):
        yield chunk
