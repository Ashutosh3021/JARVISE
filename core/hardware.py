"""Hardware detection module for JARVIS.

Detects CPU cores, GPU name, and VRAM at startup.
"""

from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class HardwareInfo:
    """Hardware information detected at startup."""
    cpu_physical_cores: int
    cpu_logical_cores: int
    cpu_freq_mhz: float
    vram_total_mb: int
    gpu_name: str
    has_nvidia: bool
    has_amd: bool


def detect_hardware() -> HardwareInfo:
    """Detect hardware capabilities of the system.
    
    Uses psutil for CPU info and tries nvidia-ml-py first for NVIDIA GPUs,
    falling back to gpu-list for AMD/Intel GPU detection.
    
    Returns:
        HardwareInfo with detected hardware capabilities.
    """
    # CPU detection
    cpu_physical = psutil.cpu_count(logical=False) or 0
    cpu_logical = psutil.cpu_count(logical=True) or 0
    
    cpu_freq = psutil.cpu_freq()
    cpu_freq_mhz = cpu_freq.current if cpu_freq else 0.0
    
    # GPU detection - initialize defaults
    vram_mb = 0
    gpu_name = "Unknown"
    has_nvidia = False
    has_amd = False
    
    # Try NVIDIA first via nvidia-ml-py (pynvml)
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        gpu_name = name
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram_mb = info.total // (1024 * 1024)
        has_nvidia = True
    except Exception:
        pass
    
    # Fallback to gpu-list for AMD/Intel/non-NVIDIA GPUs
    if vram_mb == 0:
        try:
            from gpu_list import get_gpus
            gpus = get_gpus()
            if gpus:
                gpu_name = gpus[0].name
                vram_mb = gpus[0].memory_total
                # Check vendor
                if "AMD" in gpu_name or "Radeon" in gpu_name:
                    has_amd = True
                elif "Intel" in gpu_name:
                    pass  # Integrated GPU
        except Exception:
            pass
    
    return HardwareInfo(
        cpu_physical_cores=cpu_physical,
        cpu_logical_cores=cpu_logical,
        cpu_freq_mhz=cpu_freq_mhz,
        vram_total_mb=vram_mb,
        gpu_name=gpu_name,
        has_nvidia=has_nvidia,
        has_amd=has_amd,
    )
