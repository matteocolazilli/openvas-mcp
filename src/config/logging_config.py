# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

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

def _resolve_log_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    return logging.getLevelNamesMapping().get(level.upper(), logging.INFO)


def setup_logging(
    level: str | int | None = None,
) -> None:
    """Configure root logging for stderr output."""

    logging_config = LoggingConfig()
    resolved_level = _resolve_log_level(level or logging_config.LOG_LEVEL)

    logging.basicConfig(
        level=resolved_level,
        format=_DEFAULT_FORMAT,
        datefmt=_DEFAULT_DATEFMT,
        handlers=[logging.StreamHandler(stream=sys.stderr)],
        force=True,
    )
