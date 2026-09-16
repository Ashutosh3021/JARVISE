"""
JARVIS CLI Package
"""

__version__ = "1.0.0"

from cli.client import JarvisClient
from cli.shell import simple_shell
from cli.display import display_chat, display_memory, display_stats, display_error

__all__ = [
    "JarvisClient",
    "simple_shell",
    "display_chat",
    "display_memory",
    "display_stats",
    "display_error",
]
