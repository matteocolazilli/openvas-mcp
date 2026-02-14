# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class GvmAdapterConfig(BaseSettings):
    """Defines the application configuration using Pydantic.

    It automatically reads from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields from the environment
    )

    GMP_USERNAME: str = "admin"
    GMP_PASSWORD: str = "admin"


def load_gvm_config() -> GvmAdapterConfig:
    """Loads, validates, and returns the GVM configuration."""
    try:
        config = GvmAdapterConfig()
        logger.info(
            f"Gvm Configuration loaded: "
            f"GMP_USERNAME={config.GMP_USERNAME}, "
            f"GMP_PASSWORD={'*' * len(config.GMP_PASSWORD)}"  # Mask the password in logs
        )
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        # Re-raise the exception to prevent the application from starting
        # with a bad configuration.
        raise

class MCPConfig(BaseSettings):
    """Defines the MCP server configuration using Pydantic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields from the environment
    )

    LOW_LEVEL_TOOLS: bool = False


def load_mcp_config() -> MCPConfig:
    """Loads, validates, and returns the MCP server configuration."""
    try:
        config = MCPConfig()
        logger.info(f"MCP Configuration loaded: LOW_LEVEL_TOOLS={config.LOW_LEVEL_TOOLS}")
        return config
    except Exception as e:
        logger.error(f"Error loading MCP configuration: {e}")
        raise