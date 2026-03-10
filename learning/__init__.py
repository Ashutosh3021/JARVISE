"""
JARVIS Learning Module

Provides intelligent learning capabilities:
- Retry failed tools with alternatives
- Remember user preferences
- Cache successful tool results for faster access
"""

from learning.retry_engine import RetryEngine, RetryResult, AlternativeStrategy
from learning.preference_memory import PreferenceMemory, Preference
from learning.tool_cache import ToolCache, get_tool_cache, CacheEntry

# Constants
MAX_RETRIES = 3
CACHE_TTL = 3600  # 1 hour in seconds

__all__ = [
    # Core classes
    "RetryEngine",
    "RetryResult",
    "AlternativeStrategy",
    "PreferenceMemory",
    "Preference",
    "ToolCache",
    "CacheEntry",
    # Utilities
    "get_tool_cache",
    # Constants
    "MAX_RETRIES",
    "CACHE_TTL",
]
