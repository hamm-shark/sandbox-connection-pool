"""Configure application logging."""

import logging
import logging.config
from typing import Any


def configure_logging(log_level: str) -> None:
    """Configure centralized logging for the application."""

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(levelname)-8s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "src": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",  # Suppress verbose SQLAlchemy engine logs
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(config)
