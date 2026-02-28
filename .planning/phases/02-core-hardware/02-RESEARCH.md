# Phase 2: Core Hardware Detection & Config - Research

**Researched:** 2026-02-28
**Domain:** Python hardware detection, configuration management, logging on Windows
**Confidence:** HIGH

## Summary

Phase 2 implements hardware detection, configuration loading, and centralized logging for JARVIS. The primary challenge is Windows-specific GPU/VRAM detection, which requires handling NVIDIA (via nvidia-ml-py), AMD (via pynvml-amd-windows or registry), and integrated GPUs. Configuration should use pydantic-settings for type-safe validation of .env files. Logging will use Python's built-in logging with TimedRotatingFileHandler, or loguru (already in requirements.txt).

**Primary recommendation:** Use psutil for CPU/system info, nvidia-ml-py for NVIDIA GPUs, gpu-list for cross-vendor VRAM detection, pydantic-settings for config, and loguru for logging.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HW-01 | Hardware detection module (CPU/GPU, VRAM measurement) | psutil (CPU), nvidia-ml-py/gpu-list (GPU/VRAM), win32 (WMI fallback) |
| HW-02 | Configuration profile selection (CPU/Low GPU/Mid GPU/High GPU) | VRAM thresholds mapped to config profiles |
| HW-03 | .env configuration loader with validation | pydantic-settings with env_file support |
| HW-04 | Centralized logging system (console + file) | loguru (already in requirements.txt) or stdlib logging |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| psutil | >=5.9.0 | CPU, memory, system info | Cross-platform standard for system metrics |
| nvidia-ml-py | >=13.0.0 | NVIDIA GPU/VRAM detection via NVML | Official NVIDIA bindings, Windows support |
| pydantic-settings | >=2.0.0 | Type-safe config from .env | Pydantic ecosystem standard, built-in .env support |
| loguru | >=0.7.0 | Logging (already in requirements.txt) | Cleaner API than stdlib, built-in rotation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| gpu-list | >=0.1.0 | Cross-vendor GPU/VRAM on Windows | Fallback for non-NVIDIA GPUs (AMD, Intel) |
| pynvml-amd-windows | >=1.0.0 | AMD GPU detection on Windows | If using pynvml-style API with AMD |
| win32com.client | via pywin32 | WMI queries for GPU info | Last resort fallback |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pydantic-settings | python-dotenv only | python-dotenv lacks validation; pydantic-settings is comprehensive |
| loguru | stdlib logging + TimedRotatingFileHandler | Loguru is cleaner and already in requirements.txt |
| nvidia-ml-py | GPUtil | GPUtil is older, less maintained; nvidia-ml-py is official |
| gpu-list | WMI queries directly | gpu-list is simpler, uses Windows registry |

## Architecture Patterns

### Recommended Project Structure
```
src/
├── core/
│   ├── __init__.py
│   ├── hardware.py      # HW-01: Hardware detection
│   ├── config.py        # HW-03: Configuration loader
│   └── logger.py       # HW-04: Logging setup
├── config/
│   ├── profiles.py     # HW-02: Profile definitions
│   └── __init__.py
data/
└── logs/               # Log output directory
```

### Pattern 1: Hardware Detection with Fallbacks
```python
# Source: psutil docs + nvidia-ml-py documentation
import psutil
from typing import Optional

def get_cpu_info() -> dict:
    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
    }

def get_vram_mb() -> int:
    # Try NVIDIA first
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return info.total // (1024 * 1024)
    except:
        pass
    
    # Fallback: gpu-list or registry
    try:
        from gpu_list import get_gpus
        gpus = get_gpus()
        if gpus:
            return gpus[0].memory_total
    except:
        pass
    
    return 0  # CPU-only
```

### Pattern 2: Config Profile Selection
```python
# Source: pydantic-settings docs
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

class Profile(str, Enum):
    CPU = "cpu"
    LOW_GPU = "low_gpu"
    MID_GPU = "mid_gpu"
    HIGH_GPU = "high_gpu"

class HardwareConfig(BaseSettings):
    vram_mb: int = 0
    profile: Profile = Profile.CPU
    
    def select_profile(self) -> Profile:
        if self.vram_mb >= 8000:
            return Profile.HIGH_GPU
        elif self.vram_mb >= 4000:
            return Profile.MID_GPU
        elif self.vram_mb >= 2000:
            return Profile.LOW_GPU
        return Profile.CPU
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
```

### Pattern 3: Logging Setup with Loguru
```python
# Source: loguru documentation
from loguru import logger
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = "./data/jarvis.log"):
    logger.remove()
    
    # Console output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # File output with rotation
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="midnight",  # New file each day
        retention="7 days",   # Keep 7 days of logs
        compression="zip",    # Compress old logs
    )
    
    return logger
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| VRAM detection on Windows | Custom WMI queries | nvidia-ml-py + gpu-list | Complex to handle all GPU vendors; libraries already solve this |
| Config validation | Manual os.getenv() parsing | pydantic-settings | Type safety, validation, env_file support built-in |
| Log rotation | Custom file handling | loguru or TimedRotatingFileHandler | Edge cases (concurrent writes, compression) already handled |
| Hardware capability detection | Hardcoded checks | psutil + vendor libraries | psutil normalizes cross-platform differences |

**Key insight:** Hardware detection on Windows is surprisingly complex due to multiple GPU vendors (NVIDIA, AMD, Intel) and varying driver implementations. Using established libraries avoids months of debugging vendor-specific edge cases.

## Common Pitfalls

### Pitfall 1: NVML Not Available
**What goes wrong:** nvidia-ml-py fails with NVML not found on non-NVIDIA systems
**Why it happens:** NVML is NVIDIA-specific; AMD/Intel systems don't have it
**How to avoid:** Wrap in try/except, fallback to gpu-list for non-NVIDIA
**Warning signs:** `nvml.NVMLError_NotFound` exception

### Pitfall 2: Multiple GPUs
**What goes wrong:** Code assumes single GPU, takes first GPU's VRAM
**Why it happens:** Some systems have multiple GPUs (integrated + dedicated)
**How to avoid:** Select primary GPU (dedicated over integrated), document which is used
**Warning signs:** Unexpected CPU-only profile on systems with dGPU

### Pitfall 3: Config Not Found
**What goes wrong:** Application fails if .env file missing
**Why it happens:** pydantic-settings requires .env by default
**How to avoid:** Use `env_file=".env"` with defaults; graceful degradation
**Warning signs:** `ValidationError` at startup

### Pitfall 4: Log File Permissions
**What goes wrong:** Can't write to log file, app crashes
**Why it happens:** Running from read-only location or no write permission
**How to avoid:** Create log directory with parents=True, handle permission errors
**Warning signs:** `PermissionError` when creating log file

## Code Examples

### Complete Hardware Detection Module
```python
# src/core/hardware.py
import psutil
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class HardwareInfo:
    cpu_physical_cores: int
    cpu_logical_cores: int
    cpu_freq_mhz: float
    vram_total_mb: int
    gpu_name: str
    has_nvidia: bool
    has_amd: bool

def detect_hardware() -> HardwareInfo:
    cpu_physical = psutil.cpu_count(logical=False) or 0
    cpu_logical = psutil.cpu_count(logical=True) or 0
    cpu_freq = psutil.cpu_freq()
    cpu_freq_mhz = cpu_freq.current if cpu_freq else 0.0
    
    vram_mb = 0
    gpu_name = "Unknown"
    has_nvidia = False
    has_amd = False
    
    # Try NVIDIA
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
    except:
        pass
    
    # Try gpu-list (supports AMD, Intel, generic)
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
                    pass  # Integrated
        except:
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
```

### Complete Config with Profile Selection
```python
# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
from pathlib import Path

class Profile(str, Enum):
    CPU = "cpu"
    LOW_GPU = "low_gpu"
    MID_GPU = "mid_gpu"
    HIGH_GPU = "high_gpu"

class Config(BaseSettings):
    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    
    # Voice
    wake_word: str = "jarvis"
    whisper_model: str = "base"
    kokoro_voice: str = "af_sarah"
    tts_speed: float = 1.0
    
    # Memory
    chroma_persist_directory: str = "./data/chromadb"
    memory_file: str = "./data/MEMORY.md"
    
    # UI
    ui_host: str = "0.0.0.0"
    ui_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./data/jarvis.log"
    
    # Runtime (set by hardware detection)
    vram_mb: int = 0
    profile: Profile = Profile.CPU
    
    def select_profile(self) -> Profile:
        if self.vram_mb >= 8000:
            return Profile.HIGH_GPU
        elif self.vram_mb >= 4000:
            return Profile.MID_GPU
        elif self.vram_mb >= 2000:
            return Profile.LOW_GPU
        return Profile.CPU
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

def load_config() -> Config:
    config = Config()
    config.profile = config.select_profile()
    return config
```

### Complete Logging Setup
```python
# src/core/logger.py
from loguru import logger
import sys
from pathlib import Path

def setup_logging(log_level: str, log_file: str) -> None:
    logger.remove()
    
    # Console (stderr by default)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # File with rotation
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="midnight",
        retention="7 days",
        compression="zip",
    )
```

### Integration in Main
```python
# src/core/__init__.py or main.py
from .hardware import detect_hardware, HardwareInfo
from .config import load_config, Config, Profile
from .logger import setup_logging
from loguru import logger

def initialize_phase2() -> tuple[HardwareInfo, Config]:
    # Hardware detection
    hw_info = detect_hardware()
    
    # Load config with VRAM
    config = load_config()
    config.vram_mb = hw_info.vram_total_mb
    config.profile = config.select_profile()
    
    # Setup logging
    setup_logging(config.log_level, config.log_file)
    
    # Report detected hardware
    logger.info(f"Detected hardware: CPU={hw_info.cpu_logical_cores} cores, GPU={hw_info.gpu_name}, VRAM={hw_info.vram_total_mb}MB")
    logger.info(f"Selected profile: {config.profile.value}")
    
    return hw_info, config
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WMI queries | nvidia-ml-py + gpu-list | 2023+ | Much faster, vendor-neutral |
| Manual config parsing | pydantic-settings | 2022+ (Pydantic v2) | Type safety, validation |
| Custom log rotation | loguru | 2019+ | Built-in, cleaner API |
| Hardcoded profiles | VRAM thresholds | Current | Auto-detects capabilities |

**Deprecated/outdated:**
- `pywin32` WMI queries: Replaced by vendor-specific libraries (nvidia-ml-py, gpu-list)
- `python-dotenv` alone: Replaced by pydantic-settings for production apps
- Custom logging handlers: loguru is simpler and already in requirements.txt

## Open Questions

1. **Multiple GPU handling**
   - What we know: gpu-list can return multiple GPUs
   - What's unclear: How to select primary GPU for LLM inference
   - Recommendation: Use NVIDIA if present, else dedicated AMD, else integrated

2. **VRAM thresholds for profiles**
   - What we know: LLM models have minimum VRAM requirements
   - What's unclear: Exact thresholds for optimal performance
   - Recommendation: Use conservative estimates (2GB/4GB/8GB) that work for most models

3. **Fallback on headless server**
   - What we know: Some servers have no GPU
   - What's unclear: How to handle VRAM detection failure gracefully
   - Recommendation: Default to CPU profile with warning log

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0.0 |
| Config file | pytest.ini or pyproject.toml |
| Quick run command | `pytest tests/test_hardware.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|---------------|
| HW-01 | Detect CPU/GPU/VRAM | unit | `pytest tests/test_hardware.py::test_detect_hardware -x` | ❌ Wave 0 |
| HW-02 | Profile selection by VRAM | unit | `pytest tests/test_config.py::test_profile_selection -x` | ❌ Wave 0 |
| HW-03 | Load .env config | unit | `pytest tests/test_config.py::test_config_loading -x` | ❌ Wave 0 |
| HW-04 | Console + file logging | unit | `pytest tests/test_logger.py::test_logging_setup -x` | ❌ Wave 0 |

### Wave 0 Gaps
- `tests/test_hardware.py` — covers HW-01
- `tests/test_config.py` — covers HW-02, HW-03
- `tests/test_logger.py` — covers HW-04
- `tests/conftest.py` — shared fixtures (hardware mock, config mock)

## Sources

### Primary (HIGH confidence)
- psutil documentation - https://psutil.readthedocs.io/
- nvidia-ml-py (pynvml) - https://pypi.org/project/nvidia-ml-py/
- pydantic-settings - https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- loguru documentation - https://loguru.readthedocs.io/

### Secondary (MEDIUM confidence)
- gpu-list PyPI - https://pypi.org/project/gpu-list/
- pynvml-amd-windows - https://pypi.org/project/pynvml-amd-windows/
- Windows WMI via pywin32 - https://timgolden.me.uk/python/wmi/tutorial.html

### Tertiary (LOW confidence)
- Stack Overflow WMI queries - needs verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Well-established libraries with Windows support
- Architecture: HIGH - Standard patterns from official docs
- Pitfalls: MEDIUM - Some Windows edge cases may require validation

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (30 days for stable libraries)
