"""
Structured logging configuration.
Replaces all print() calls across the application.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger for the app
    root_logger = logging.getLogger("app")
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(handler)
    root_logger.propagate = False

    # Silence noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger scoped under 'app' namespace."""
    return logging.getLogger(f"app.{name}")
