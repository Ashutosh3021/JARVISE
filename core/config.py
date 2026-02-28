"""
JARVIS Configuration Module

Provides configuration loading from .env files with automatic hardware profile selection
based on available VRAM.
"""

from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Profile(str, Enum):
    """Hardware profile based on available VRAM."""
    CPU = "cpu"
    LOW_GPU = "low_gpu"
    MID_GPU = "mid_gpu"
    HIGH_GPU = "high_gpu"


class Config(BaseSettings):
    """JARVIS configuration with .env support and automatic profile selection."""

    # Ollama Configuration
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama API host URL"
    )
    ollama_model: str = Field(
        default="llama3.2:latest",
        description="Default Ollama model to use"
    )

    # Voice Configuration
    wake_word: str = Field(
        default="jarvis",
        description="Wake word to trigger voice assistant"
    )
    whisper_model: str = Field(
        default="base",
        description="Whisper model for speech-to-text"
    )
    kokoro_voice: str = Field(
        default="af_sarah",
        description="Kokoro voice for text-to-speech"
    )
    tts_speed: float = Field(
        default=1.0,
        description="TTS playback speed multiplier"
    )

    # Memory Configuration
    chroma_persist_directory: str = Field(
        default="./data/chromadb",
        description="ChromaDB persistence directory"
    )
    memory_file: str = Field(
        default="./data/MEMORY.md",
        description="Human-editable memory file path"
    )

    # UI Configuration
    ui_host: str = Field(
        default="0.0.0.0",
        description="UI server host"
    )
    ui_port: int = Field(
        default=8000,
        description="UI server port"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: str = Field(
        default="./data/jarvis.log",
        description="Log file path"
    )

    # Runtime Configuration (set by hardware detection)
    vram_mb: int = Field(
        default=0,
        description="Detected VRAM in MB (set at runtime)"
    )
    profile: Profile = Field(
        default=Profile.CPU,
        description="Selected hardware profile (set at runtime)"
    )

    # Profile thresholds (in MB)
    LOW_GPU_THRESHOLD: int = Field(default=2048, description="Minimum VRAM for LOW_GPU profile")
    MID_GPU_THRESHOLD: int = Field(default=4096, description="Minimum VRAM for MID_GPU profile")
    HIGH_GPU_THRESHOLD: int = Field(default=8192, description="Minimum VRAM for HIGH_GPU profile")

    def select_profile(self) -> Profile:
        """
        Select appropriate hardware profile based on available VRAM.
        
        Thresholds:
        - CPU: < 2GB VRAM
        - LOW_GPU: 2-4GB VRAM  
        - MID_GPU: 4-8GB VRAM
        - HIGH_GPU: > 8GB VRAM
        """
        if self.vram_mb >= self.HIGH_GPU_THRESHOLD:
            return Profile.HIGH_GPU
        elif self.vram_mb >= self.MID_GPU_THRESHOLD:
            return Profile.MID_GPU
        elif self.vram_mb >= self.LOW_GPU_THRESHOLD:
            return Profile.LOW_GPU
        return Profile.CPU

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


def load_config(vram_mb: int | None = None) -> Config:
    """
    Load configuration from .env file and optionally set VRAM.
    
    Args:
        vram_mb: Optional VRAM in MB. If not provided, profile defaults to CPU.
        
    Returns:
        Config instance with profile automatically selected based on VRAM.
    """
    config = Config()
    
    # Set VRAM if provided and select profile
    if vram_mb is not None:
        config.vram_mb = vram_mb
    
    # Auto-select profile based on VRAM
    config.profile = config.select_profile()
    
    return config


# Export public API
__all__ = ["Config", "Profile", "load_config"]
