"""
Pytest configuration and fixtures for JARVIS tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_hardware():
    """Mock hardware info for testing."""
    from dataclasses import dataclass
    
    @dataclass
    class MockHardwareInfo:
        cpu_physical_cores: int = 6
        cpu_logical_cores: int = 12
        cpu_freq_mhz: float = 2400.0
        vram_total_mb: int = 0
        gpu_name: str = "Unknown"
        has_nvidia: bool = False
        has_amd: bool = True
    
    return MockHardwareInfo()


@pytest.fixture
def mock_config():
    """Mock config for testing."""
    from core.config import Profile
    
    class MockConfig:
        profile = Profile.CPU
        whisper_model = "tiny"
        ollama_model = "qwen2.5-coder:7b"
        ollama_host = "http://localhost:11434"
        chroma_persist_directory = "./data/chromadb"
        memory_file = "./data/MEMORY.md"
        ui_host = "0.0.0.0"
        ui_port = 8000
        log_level = "INFO"
        log_file = "./data/jarvis.log"
        vram_mb = 0
        
        def select_profile(self):
            return Profile.CPU
    
    return MockConfig()


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    return {
        "message": {
            "content": "This is a test response from the agent."
        }
    }


@pytest.fixture
def mock_vector_store():
    """Mock vector store for memory tests."""
    store = MagicMock()
    store.save_conversation = MagicMock(return_value="test_id_123")
    store.get_context = MagicMock(return_value=[])
    store.get_stats = MagicMock(return_value={"total_entries": 0})
    return store


@pytest.fixture
def mock_memory_file():
    """Mock memory file controller."""
    controller = MagicMock()
    controller.get_section = MagicMock(return_value="")
    controller.save_fact = MagicMock()
    controller.get_preference = MagicMock(return_value=None)
    return controller
