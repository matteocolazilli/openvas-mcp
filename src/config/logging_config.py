# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DEFAULT_DATEFMT = "%d-%m-%Y %H:%M:%S"


class LoggingConfig(BaseSettings):
    """Defines the logging configuration using Pydantic.

    It automatically reads from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields from the environment
    )

    # Configuration fields with types and default values
    LOG_LEVEL: str = "INFO"


def load_logging_config() -> LoggingConfig:
    """Loads, validates, and returns the Logging configuration."""
    try:
        config = LoggingConfig()
        logger.info(f"Logging Configuration loaded: log_level={config.LOG_LEVEL} ")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        # Re-raise the exception to prevent the application from starting
        # with a bad configuration.
        raise


def setup_logging(
    level: str | int | None = None,
) -> None:
    """Configure root logging once, with console + file handlers."""

    logging_config = load_logging_config()

    resolved_level = level or logging_config.LOG_LEVEL
    if isinstance(resolved_level, str):
        resolved_level = logging._nameToLevel.get(resolved_level.upper(), logging.INFO)

    root_logger = logging.getLogger()

    formatter = logging.Formatter(_DEFAULT_FORMAT, datefmt=_DEFAULT_DATEFMT)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(stream=sys.stderr),
    ]
    for handler in handlers:
        handler.setFormatter(formatter)

    root_logger.setLevel(resolved_level)
    for handler in handlers:
        root_logger.addHandler(handler)
