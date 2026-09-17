"""
JARVIS Brain Layer - LLM Provider Abstraction

Providers:
- Ollama: local inference
- Groq: cloud inference (fast, free tier)
- OpenRouter: cloud inference (multi-model)
- Google AI Studio: cloud inference (Gemini)
"""

from brain.providers.base import LLMProvider
from brain.providers.ollama import OllamaProvider
from brain.providers.cloud import CloudProvider, create_cloud_provider

__all__ = ["LLMProvider", "OllamaProvider", "CloudProvider", "create_cloud_provider"]
