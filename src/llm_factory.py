"""Factory for selecting LLM clients based on configuration."""

from typing import Type

from src.llm.base import BaseLLMClient

from src.llm.ollama import OllamaClient
from src.llm.gemini import GeminiClient

def get_llm_client() -> Type[BaseLLMClient]:
    """
    Return an instantiated LLM client based on the configuration.
    
    The decision is made by reading ``LLM_PROVIDER`` from the config.
    Supported values:
        - "ollama": Use the local Ollama client (default)
        - "gemini": Use the Gemini cloud client
    
    Raises:
        ValueError: If an unsupported provider is configured.
    """
    from config import config

    provider = (config.LLM_PROVIDER or "ollama").lower()
    if provider == "gemini":
        return GeminiClient()
    else:
        # Default to Ollama if not explicitly set or unknown
        return OllamaClient(
            host=config.OLLAMA_HOST,
            model=config.OLLAMA_MODEL
        )