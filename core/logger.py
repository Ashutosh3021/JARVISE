# JARVIS Logging Module
# Centralized logging with console and file output using loguru

from loguru import logger
import sys
from pathlib import Path


def setup_logging(log_level: str, log_file: str) -> None:
    """
    Configure centralized logging with console and file output.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file (e.g., "./data/logs/jarvis.log")
    """
    # Remove default handler
    logger.remove()
    
    # Console handler with colored format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation, retention, and compression
    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",  # Log everything to file for debugging
        rotation="00:00",      # Rotate at midnight (new file each day)
        retention="7 days",    # Keep logs for 7 days
        compression="zip",     # Compress old logs to zip
    )
