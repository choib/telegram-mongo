from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator

class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        ...

    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]]) -> str:
        ...

    @abstractmethod
    async def chat_stream(self, prompt: str) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        ...