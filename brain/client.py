"""
JARVIS Brain Layer - LLM Client Module

Provides Ollama integration with streaming support and health checking.
"""

import json
import time
from typing import Generator, AsyncGenerator

import requests
from loguru import logger

from core.config import Config


class OllamaConnectionError(Exception):
    """Raised when unable to connect to Ollama server."""
    pass


class OllamaClient:
    """Ollama LLM client with streaming support."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.host = self.config.ollama_host
        self.default_model = self.config.ollama_model
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def health_check(self, retries: int = 3, backoff: float = 1.0) -> bool:
        """Check if Ollama server is running."""
        for attempt in range(retries):
            try:
                response = self._session.get(f"{self.host}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info("Ollama server health check passed")
                    return True
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ollama health check attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(backoff * (2 ** attempt))
        
        logger.error("Ollama server health check failed")
        return False

    def list_models(self) -> list[dict]:
        """List available Ollama models."""
        try:
            response = self._session.get(f"{self.host}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [{"name": m["name"], "size": m.get("size", 0)} for m in data.get("models", [])]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> dict:
        """Send chat request to Ollama (non-streaming)."""
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        
        try:
            response = self._session.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Chat request failed: {e}")
            raise OllamaConnectionError(f"Failed to chat with Ollama: {e}")

    def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Send chat request to Ollama with streaming response."""
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        try:
            response = self._session.post(
                f"{self.host}/api/chat",
                json=payload,
                stream=True,
                timeout=120,
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = line.decode("utf-8")
                        if data.startswith("{"):
                            chunk = json.loads(data)
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                if content:
                                    yield content
                    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                        continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Streaming chat request failed: {e}")
            raise OllamaConnectionError(f"Failed to stream chat with Ollama: {e}")

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> dict:
        """Generate completion (non-streaming)."""
        payload = {
            "model": model or self.default_model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
        }

        try:
            response = self._session.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Generate request failed: {e}")
            raise OllamaConnectionError(f"Failed to generate with Ollama: {e}")

    def stream_generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Generate completion with streaming response."""
        payload = {
            "model": model or self.default_model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True,
        }

        try:
            response = self._session.post(
                f"{self.host}/api/generate",
                json=payload,
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = line.decode("utf-8")
                        if data.startswith("{"):
                            chunk = json.loads(data)
                            if "response" in chunk:
                                content = chunk["response"]
                                if content:
                                    yield content
                    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                        continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Streaming generate request failed: {e}")
            raise OllamaConnectionError(f"Failed to stream generate with Ollama: {e}")


__all__ = ["OllamaClient", "OllamaConnectionError"]
