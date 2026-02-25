# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GvmClientConfig(BaseSettings):
    """Application configuration (GVM/GMP credentials)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    USERNAME: str = "admin"
    PASSWORD: SecretStr = Field(..., description="Required Greenbone Password.")

    @field_validator("PASSWORD")
    @classmethod
    def _password_must_not_be_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            raise ValueError("PASSWORD must not be empty")
        return v
