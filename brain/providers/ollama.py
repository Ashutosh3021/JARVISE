"""
Ollama local provider — wraps existing OllamaClient.
"""

from typing import Generator
from loguru import logger

from brain.providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Local Ollama provider."""

    def __init__(self, host: str = "http://localhost:11434",
                 model: str = "llama3.2:latest"):
        from brain.client import OllamaClient, Config
        self._host = host
        self._model = model
        config = Config(ollama_host=host, ollama_model=model)
        self._client = OllamaClient(config)

    def chat(self, messages, model=None, temperature=0.7):
        return self._client.chat(messages, model=model or self._model, temperature=temperature)

    def stream_chat(self, messages, model=None, temperature=0.7):
        return self._client.stream_chat(messages, model=model or self._model, temperature=temperature)

    def health_check(self):
        return self._client.health_check()

    @property
    def provider_name(self):
        return "ollama"

    @property
    def default_model(self):
        return self._model

    def list_models(self):
        return self._client.list_models()

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        import requests
        try:
            logger.info(f"Pulling model: {model_name}...")
            response = requests.post(
                f"{self._host}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=600,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    status = data.get("status", "")
                    if status:
                        logger.info(f"Pull: {status}")
            logger.info(f"Model {model_name} pulled successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    def get_best_model(self, vram_mb: int = 0) -> str:
        """Pick the best model the system can run locally."""
        models = self.list_models()
        if not models:
            return self._model

        # Size-based ranking (prefer smaller models for lower VRAM)
        # Rough VRAM estimates in MB
        SIZE_MAP = {
            "qwen2.5-coder:7b": 5000,
            "mistral:7b": 5000,
            "llama3.2:latest": 2500,
            "llama3.2:1b": 1500,
            "qwen2.5:3b": 2500,
            "phi3:mini": 2000,
            "gemma2:2b": 1800,
        }

        available_names = {m["name"] for m in models}
        # Filter by what's actually pulled
        candidates = []
        for name, size_mb in SIZE_MAP.items():
            # Check if any pulled model matches (handle name variations)
            for pulled in available_names:
                if name.split(":")[0] in pulled:
                    candidates.append((pulled, size_mb))
                    break

        if not candidates:
            # Just pick the first available
            return models[0]["name"]

        # Sort by size, prefer models that fit in VRAM
        if vram_mb > 0:
            fitting = [(n, s) for n, s in candidates if s <= vram_mb]
            if fitting:
                # Pick largest that fits
                fitting.sort(key=lambda x: x[1], reverse=True)
                return fitting[0][0]

        # Fallback: pick smallest
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
