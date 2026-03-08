"""
Unit tests for config module.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Tests for configuration module."""
    
    def test_load_config_defaults(self):
        """Test loading config with default values."""
        from core.config import load_config, Profile
        
        config = load_config(0)  # CPU mode
        
        assert config.profile == Profile.CPU
        assert config.vram_mb == 0
    
    def test_profile_selection_cpu(self):
        """Test profile selection for CPU (0 VRAM)."""
        from core.config import load_config, Profile
        
        config = load_config(0)
        
        assert config.profile == Profile.CPU
    
    def test_profile_selection_low_gpu(self):
        """Test profile selection for low GPU (2GB VRAM)."""
        from core.config import load_config, Profile
        
        config = load_config(2048)  # 2GB
        
        assert config.profile == Profile.LOW_GPU
    
    def test_profile_selection_mid_gpu(self):
        """Test profile selection for mid GPU (6GB VRAM)."""
        from core.config import load_config, Profile
        
        config = load_config(6144)  # 6GB
        
        assert config.profile == Profile.MID_GPU
    
    def test_profile_selection_high_gpu(self):
        """Test profile selection for high GPU (12GB VRAM)."""
        from core.config import load_config, Profile
        
        config = load_config(12288)  # 12GB
        
        assert config.profile == Profile.HIGH_GPU
    
    def test_profile_threshold_boundaries(self):
        """Test profile selection at threshold boundaries."""
        from core.config import load_config, Profile
        
        # Test boundary: 2048MB = LOW_GPU
        config = load_config(2047)
        assert config.profile == Profile.CPU
        
        config = load_config(2048)
        assert config.profile == Profile.LOW_GPU
        
        # Test boundary: 4096MB = MID_GPU
        config = load_config(4095)
        assert config.profile == Profile.LOW_GPU
        
        config = load_config(4096)
        assert config.profile == Profile.MID_GPU
        
        # Test boundary: 8192MB = HIGH_GPU
        config = load_config(8191)
        assert config.profile == Profile.MID_GPU
        
        config = load_config(8192)
        assert config.profile == Profile.HIGH_GPU
    
    def test_config_has_required_attributes(self):
        """Test that config has all required attributes."""
        from core.config import load_config
        
        config = load_config(0)
        
        # Check required attributes
        assert hasattr(config, 'ollama_host')
        assert hasattr(config, 'ollama_model')
        assert hasattr(config, 'whisper_model')
        assert hasattr(config, 'kokoro_voice')
        assert hasattr(config, 'profile')
        assert hasattr(config, 'vram_mb')
    
    def test_profile_enum(self):
        """Test that Profile enum works correctly."""
        from core.config import Profile
        
        assert Profile.CPU.value == "cpu"
        assert Profile.LOW_GPU.value == "low_gpu"
        assert Profile.MID_GPU.value == "mid_gpu"
        assert Profile.HIGH_GPU.value == "high_gpu"
