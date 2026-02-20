# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class GvmClientConfig(BaseSettings):
    """Application configuration (GVM/GMP credentials)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GMP_USERNAME: str = "admin"
    GMP_PASSWORD: SecretStr = Field(..., description="Required GMP password.")

    @field_validator("GMP_PASSWORD")
    @classmethod
    def _password_must_not_be_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            raise ValueError("GMP_PASSWORD must not be empty")
        return v


def load_gvm_config() -> GvmClientConfig:
    """
    Load and validate the GVM configuration.

    - On success: returns config and logs a masked password.
    - On failure: raises pydantic.ValidationError.
    """
    config = GvmClientConfig()

    pwd_len = len(config.GMP_PASSWORD.get_secret_value())
    logger.info(
        "Gvm Client Configuration loaded: GMP_USERNAME=%s, GMP_PASSWORD=%s",
        config.GMP_USERNAME,
        "*" * pwd_len,
    )
    return config
