"""
System Stats REST Routes

Provides REST endpoints for system statistics:
- GET /api/stats/current - Get current CPU, memory, and VRAM stats
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


def get_vram_stats() -> Optional[dict[str, float]]:
    """Get VRAM statistics if available.
    
    Returns:
        VRAM stats dict or None if unavailable
    """
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()
        
        total_gb = mem_info.total / (1024**3)
        used_gb = mem_info.used / (1024**3)
        percent = (mem_info.used / mem_info.total) * 100
        
        return {
            "percent": round(percent, 1),
            "used_gb": round(used_gb, 2),
            "total_gb": round(total_gb, 2)
        }
    except ImportError:
        # nvidia-ml-py not installed
        return None
    except Exception as e:
        logger.warning(f"Could not get VRAM stats: {e}")
        return None


@router.get("/stats/current")
async def get_current_stats() -> dict[str, Any]:
    """
    Get current system statistics.
    
    Returns:
        Dict with cpu, memory, and optional vram stats
    """
    try:
        from tools.system_monitor import SystemMonitorTool
        
        monitor = SystemMonitorTool()
        
        # Get CPU stats
        cpu = {"percent": 0.0}
        try:
            cpu_stats = monitor.get_cpu_usage()
            cpu = {"percent": round(cpu_stats.percent, 1)}
        except Exception as e:
            logger.warning(f"Could not get CPU stats: {e}")
        
        # Get memory stats
        memory = {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0}
        try:
            mem_stats = monitor.get_memory_usage()
            memory = {
                "percent": round(mem_stats.percent, 1),
                "used_gb": round(mem_stats.used_gb, 2),
                "total_gb": round(mem_stats.total_gb, 2)
            }
        except Exception as e:
            logger.warning(f"Could not get memory stats: {e}")
        
        # Get VRAM stats (optional)
        vram = get_vram_stats()
        
        return {
            "cpu": cpu,
            "memory": memory,
            "vram": vram
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
