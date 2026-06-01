"""Loguru logging configuration."""

import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logging() -> None:
    """Configure Loguru sinks for console and file output."""
    # Ensure output directory exists
    Path("output").mkdir(exist_ok=True)

    # Remove default sink
    logger.remove()

    # Console sink — human-readable, coloured
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    # File sink — verbose, rotating
    logger.add(
        "output/auditor.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
        backtrace=True,
        diagnose=True,
        encoding="utf-8",
    )
