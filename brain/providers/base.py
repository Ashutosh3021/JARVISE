"""
JARVIS Brain Layer - LLM Provider Abstraction

Unified interface for local (Ollama) and cloud (Groq, OpenRouter, Google AI) providers.
"""

from abc import ABC, abstractmethod
from typing import Generator
from loguru import logger


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    @abstractmethod
    def chat(self, messages: list[dict], model: str | None = None,
             temperature: float = 0.7) -> dict:
        """Send chat request, return dict with 'message' -> 'content'."""
        ...

    @abstractmethod
    def stream_chat(self, messages: list[dict], model: str | None = None,
                    temperature: float = 0.7) -> Generator[str, None, None]:
        """Stream chat response, yield content chunks."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is reachable."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        ...
