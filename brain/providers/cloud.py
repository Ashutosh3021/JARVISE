"""
Cloud LLM providers — Groq, OpenRouter, Google AI Studio.

All three use OpenAI-compatible chat completions API.
"""

import json
from typing import Generator
import requests
from loguru import logger

from brain.providers.base import LLMProvider


class CloudProvider(LLMProvider):
    """Generic OpenAI-compatible cloud provider."""

    PROVIDERS = {
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "env_key": "GROQ_API_KEY",
            "default_model": "qwen/qwen3.8-27b",
            "name": "Groq",
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "env_key": "OPENROUTER_API_KEY",
            "default_model": "meta-llama/llama-3.2-3b-instruct:free",
            "name": "OpenRouter",
        },
        "google": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "env_key": "GOOGLE_AI_API_KEY",
            "default_model": "gemini-2.0-flash",
            "name": "Google AI Studio",
        },
    }

    def __init__(self, provider: str, api_key: str, model: str | None = None):
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Choose from: {list(self.PROVIDERS.keys())}")

        info = self.PROVIDERS[provider]
        self._provider = provider
        self._name = info["name"]
        self._base_url = info["base_url"]
        self._api_key = api_key
        self._model = model or info["default_model"]
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def chat(self, messages, model=None, temperature=0.7):
        payload = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
        }
        try:
            response = self._session.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            # Normalize to Ollama-like format
            choice = data["choices"][0]
            return {
                "message": {
                    "content": choice["message"]["content"],
                }
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"{self._name} chat request failed: {e}")
            raise

    def stream_chat(self, messages, model=None, temperature=0.7):
        payload = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        try:
            response = self._session.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

            line_buffer = ""
            for raw_chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if not raw_chunk:
                    continue
                line_buffer += raw_chunk
                while "\n" in line_buffer:
                    line, line_buffer = line_buffer.split("\n", 1)
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # strip "data: "
                    if data_str == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException as e:
            logger.error(f"{self._name} stream request failed: {e}")
            raise

    def health_check(self):
        try:
            # Lightweight models list call
            response = self._session.get(f"{self._base_url}/models", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    @property
    def provider_name(self):
        return self._provider

    @property
    def default_model(self):
        return self._model


def create_cloud_provider(provider: str, api_key: str, model: str | None = None) -> CloudProvider:
    """Factory to create a cloud provider instance."""
    return CloudProvider(provider, api_key, model)
