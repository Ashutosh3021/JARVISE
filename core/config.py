"""
JARVIS Configuration Module

Provides configuration loading from .env files with automatic hardware profile selection
based on available VRAM.
"""

from enum import Enum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


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

    @field_validator("ollama_host")
    @classmethod
    def validate_ollama_host(cls, v: str) -> str:
        """Validate Ollama host URL format."""
        if not v:
            raise ConfigValidationError("ollama_host cannot be empty")
        if not v.startswith(("http://", "https://")):
            raise ConfigValidationError("ollama_host must start with http:// or https://")
        return v

    @field_validator("ollama_model")
    @classmethod
    def validate_ollama_model(cls, v: str) -> str:
        """Validate Ollama model name format."""
        if not v:
            raise ConfigValidationError("ollama_model cannot be empty")
        # Model names should be lowercase with optional :tag suffix
        # Allow dots, hyphens, underscores, and colons (e.g., llama3.2:latest, qwen2.5-coder:7b)
        if not v.replace(":", "").replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise ConfigValidationError(f"Invalid Ollama model name: {v}")
        return v

    @field_validator("whisper_model")
    @classmethod
    def validate_whisper_model(cls, v: str) -> str:
        """Validate Whisper model name."""
        valid_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        if v not in valid_models:
            raise ConfigValidationError(
                f"Invalid whisper_model: {v}. Valid options: {', '.join(valid_models)}"
            )
        return v

    @field_validator("tts_speed")
    @classmethod
    def validate_tts_speed(cls, v: float) -> float:
        """Validate TTS speed is within reasonable bounds."""
        if not 0.5 <= v <= 2.0:
            raise ConfigValidationError("tts_speed must be between 0.5 and 2.0")
        return v

    @field_validator("ui_port")
    @classmethod
    def validate_ui_port(cls, v: int) -> int:
        """Validate UI port is in valid range."""
        if not 1024 <= v <= 65535:
            raise ConfigValidationError("ui_port must be between 1024 and 65535")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ConfigValidationError(
                f"Invalid log_level: {v}. Valid options: {', '.join(valid_levels)}"
            )
        return v_upper

    @field_validator("vram_mb")
    @classmethod
    def validate_vram_mb(cls, v: int) -> int:
        """Validate VRAM value is non-negative."""
        if v < 0:
            raise ConfigValidationError("vram_mb cannot be negative")
        return v

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
        
    Raises:
        ConfigValidationError: If configuration values are invalid.
        FileNotFoundError: If .env file is specified but not found.
    """
    # Try to load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        try:
            config = Config()
        except Exception as e:
            raise ConfigValidationError(f"Failed to load configuration: {e}")
    else:
        config = Config()
    
    # Set VRAM if provided and select profile
    if vram_mb is not None:
        config.vram_mb = vram_mb
    
    # Auto-select profile based on VRAM
    config.profile = config.select_profile()
    
    return config


def validate_config(config: Config) -> list[str]:
    """
    Validate configuration and return list of warnings.
    
    Args:
        config: Configuration to validate.
        
    Returns:
        List of warning messages (empty if all checks pass).
    """
    warnings = []
    
    # Check Ollama connection (if possible)
    try:
        import requests
        response = requests.get(f"{config.ollama_host}/api/tags", timeout=5)
        if response.status_code != 200:
            warnings.append(f"Ollama at {config.ollama_host} returned status {response.status_code}")
    except ImportError:
        warnings.append("requests library not installed - cannot verify Ollama connection")
    except Exception as e:
        warnings.append(f"Cannot connect to Ollama at {config.ollama_host}: {e}")
    
    # Check data directory exists
    data_dir = Path(config.chroma_persist_directory).parent
    if not data_dir.exists():
        warnings.append(f"Data directory {data_dir} does not exist")
    
    # Check log file directory exists
    log_dir = Path(config.log_file).parent
    if not log_dir.exists():
        warnings.append(f"Log directory {log_dir} does not exist")
    
    return warnings


# Export public API
__all__ = ["Config", "Profile", "load_config", "validate_config", "ConfigValidationError"]
