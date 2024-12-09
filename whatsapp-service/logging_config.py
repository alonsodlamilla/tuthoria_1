import logging
from logging.config import dictConfig

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "INFO",
        },
        "file": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/whatsapp_service.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "INFO",
        },
    },
    "root": {"level": "INFO", "handlers": ["console", "file"]},
}


def setup_logging():
    """Configure logging for the application."""
    import os

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    dictConfig(logging_config)
