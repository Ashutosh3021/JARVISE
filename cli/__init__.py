"""
JARVIS CLI Package

Command-line interface for JARVIS AI Assistant
"""

__version__ = "1.0.0"
__author__ = "JARVIS Team"

from cli.client import JarvisClient
from cli.shell import JarvisShell
from cli.display import display_chat, display_memory, display_stats, display_error

__all__ = [
    "JarvisClient",
    "JarvisShell", 
    "display_chat",
    "display_memory", 
    "display_stats",
    "display_error",
]
