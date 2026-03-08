"""
Unit tests for hardware detection module.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHardwareDetection:
    """Tests for hardware detection module."""
    
    def test_detect_hardware_returns_info(self):
        """Test that hardware detection returns HardwareInfo."""
        from core.hardware import detect_hardware
        
        hw = detect_hardware()
        
        # Verify basic attributes exist
        assert hasattr(hw, 'cpu_physical_cores')
        assert hasattr(hw, 'cpu_logical_cores')
        assert hasattr(hw, 'vram_total_mb')
        assert hasattr(hw, 'gpu_name')
        assert hasattr(hw, 'has_nvidia')
        assert hasattr(hw, 'has_amd')
    
    def test_cpu_cores_detected(self):
        """Test that CPU cores are detected."""
        from core.hardware import detect_hardware
        
        hw = detect_hardware()
        
        # CPU cores should be positive integers
        assert hw.cpu_physical_cores > 0
        assert hw.cpu_logical_cores > 0
        assert hw.cpu_logical_cores >= hw.cpu_physical_cores
    
    def test_vram_detected(self):
        """Test that VRAM is detected."""
        from core.hardware import detect_hardware
        
        hw = detect_hardware()
        
        # VRAM should be non-negative
        assert hw.vram_total_mb >= 0
    
    def test_gpu_name_reported(self):
        """Test that GPU name is reported."""
        from core.hardware import detect_hardware
        
        hw = detect_hardware()
        
        # GPU name should be a string
        assert isinstance(hw.gpu_name, str)
    
    def test_nvidia_amd_flags(self):
        """Test that NVIDIA/AMD flags are boolean."""
        from core.hardware import detect_hardware
        
        hw = detect_hardware()
        
        assert isinstance(hw.has_nvidia, bool)
        assert isinstance(hw.has_amd, bool)


class TestHardwareInfo:
    """Tests for HardwareInfo dataclass."""
    
    def test_hardware_info_creation(self):
        """Test creating HardwareInfo manually."""
        from core.hardware import HardwareInfo
        
        hw = HardwareInfo(
            cpu_physical_cores=6,
            cpu_logical_cores=12,
            cpu_freq_mhz=2400.0,
            vram_total_mb=8192,
            gpu_name="NVIDIA RTX 3080",
            has_nvidia=True,
            has_amd=False
        )
        
        assert hw.cpu_physical_cores == 6
        assert hw.vram_total_mb == 8192
        assert hw.has_nvidia is True
        assert hw.has_amd is False
