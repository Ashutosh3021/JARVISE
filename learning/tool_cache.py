"""
JARVIS Learning Module - Tool Cache

Caches successful tool results for faster future access.
"""

import json
import time
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class CacheEntry:
    """A cached tool result."""
    tool_name: str
    args_hash: str
    result: str
    timestamp: datetime
    success: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tool_name": self.tool_name,
            "args_hash": self.args_hash,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create CacheEntry from dictionary."""
        return cls(
            tool_name=data["tool_name"],
            args_hash=data["args_hash"],
            result=data["result"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            success=data.get("success", True),
        )


class ToolCache:
    """Cache for storing and retrieving tool results."""
    
    def __init__(self, cache_dir: str = "./data/tool_cache.json", ttl: int = 3600):
        """Initialize tool cache.
        
        Args:
            cache_dir: Path to JSON file for cache persistence
            ttl: Time-to-live for cache entries in seconds (default: 3600 = 1 hour)
        """
        self.cache_path = Path(cache_dir)
        self.ttl = ttl
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
        }
        
        # Ensure data directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        self._load()
    
    def _load(self) -> None:
        """Load cache from storage file."""
        if not self.cache_path.exists():
            logger.debug("No cache file found, starting fresh")
            return
        
        try:
            with open(self.cache_path, "r") as f:
                data = json.load(f)
            
            for key, entry_data in data.items():
                try:
                    entry = CacheEntry.from_dict(entry_data)
                    # Only load non-expired entries
                    if not self._is_expired(entry):
                        self._cache[key] = entry
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid cache entry: {e}")
            
            logger.info(f"Loaded {len(self._cache)} cache entries")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
    
    def _save(self) -> None:
        """Save cache to storage file."""
        try:
            data = {
                key: entry.to_dict()
                for key, entry in self._cache.items()
            }
            
            with open(self.cache_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._cache)} cache entries")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired.
        
        Args:
            entry: Cache entry to check
            
        Returns:
            True if expired, False otherwise
        """
        age = time.time() - entry.timestamp.timestamp()
        return age > self.ttl
    
    def _hash_args(self, args: dict) -> str:
        """Create a consistent hash for tool arguments.
        
        Args:
            args: Arguments dictionary
            
        Returns:
            SHA256 hash of the arguments
        """
        # Sort keys for consistent hashing
        args_str = json.dumps(args, sort_keys=True)
        return hashlib.sha256(args_str.encode()).hexdigest()[:16]
    
    def _make_key(self, tool_name: str, args: dict) -> str:
        """Create a cache key from tool name and arguments.
        
        Args:
            tool_name: Name of the tool
            args: Arguments dictionary
            
        Returns:
            Cache key string
        """
        args_hash = self._hash_args(args)
        return f"{tool_name}:{args_hash}"
    
    def get(self, tool_name: str, args: dict) -> str | None:
        """Get a cached result.
        
        Args:
            tool_name: Name of the tool
            args: Arguments used
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(tool_name, args)
        
        if key not in self._cache:
            self._stats["misses"] += 1
            logger.debug(f"Cache miss: {tool_name}")
            return None
        
        entry = self._cache[key]
        
        # Check expiration
        if self._is_expired(entry):
            del self._cache[key]
            self._stats["misses"] += 1
            logger.debug(f"Cache expired: {tool_name}")
            return None
        
        self._stats["hits"] += 1
        logger.debug(f"Cache hit: {tool_name}")
        return entry.result
    
    def set(
        self, 
        tool_name: str, 
        args: dict, 
        result: str, 
        success: bool = True
    ) -> None:
        """Store a result in cache.
        
        Args:
            tool_name: Name of the tool
            args: Arguments used
            result: Result to cache
            success: Whether the execution was successful
        """
        # Only cache successful results by default
        if not success:
            logger.debug(f"Not caching failed result: {tool_name}")
            return
        
        key = self._make_key(tool_name, args)
        
        self._cache[key] = CacheEntry(
            tool_name=tool_name,
            args_hash=self._hash_args(args),
            result=result,
            timestamp=datetime.now(),
            success=success
        )
        
        self._stats["sets"] += 1
        logger.debug(f"Cached result: {tool_name}")
        
        # Save periodically (every 10 sets)
        if self._stats["sets"] % 10 == 0:
            self._save()
    
    def invalidate(self, tool_name: str, args: dict | None = None) -> int:
        """Remove cached entries.
        
        Args:
            tool_name: Name of the tool to invalidate
            args: Optional specific args to invalidate (None = all for tool)
            
        Returns:
            Number of entries removed
        """
        if args is not None:
            # Remove specific entry
            key = self._make_key(tool_name, args)
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Invalidated cache: {tool_name}")
                self._save()
                return 1
            return 0
        
        # Remove all entries for this tool
        keys_to_remove = [
            key for key, entry in self._cache.items()
            if entry.tool_name == tool_name
        ]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.debug(f"Invalidated {len(keys_to_remove)} cache entries for {tool_name}")
            self._save()
        
        return len(keys_to_remove)
    
    def clear_expired(self) -> int:
        """Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        keys_to_remove = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.info(f"Cleared {len(keys_to_remove)} expired cache entries")
            self._save()
        
        return len(keys_to_remove)
    
    def clear_all(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._save()
        logger.info("Cleared all cache entries")
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "hit_rate": round(hit_rate, 2),
            "cache_size": len(self._cache),
            "ttl_seconds": self.ttl,
        }
    
    def get_all_entries(self) -> list[dict]:
        """Get all cache entries as list of dicts.
        
        Returns:
            List of cache entry dicts
        """
        return [
            {
                **entry.to_dict(),
                "age_seconds": time.time() - entry.timestamp.timestamp(),
                "expired": self._is_expired(entry),
            }
            for entry in self._cache.values()
        ]


# Global cache instance
_global_cache: ToolCache | None = None


def get_tool_cache() -> ToolCache:
    """Get the global tool cache instance.
    
    Returns:
        Global ToolCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ToolCache()
    return _global_cache


__all__ = ["ToolCache", "CacheEntry", "get_tool_cache"]
