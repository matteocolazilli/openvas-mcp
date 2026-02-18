# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging

from fastmcp.server import FastMCP
from pydantic import ValidationError

from src.config import load_gvm_config
from src.services.gvm_client import GvmClient
from src.tools.vuln_scan_tools import register_vuln_scan_tools
from src.tools.low_level_tools import register_low_level_tools

logger = logging.getLogger(__name__)


def _format_gvm_config_error(ex: ValidationError) -> str:
    """
    Convert a Pydantic ValidationError into a single user-friendly message.
    """
    for err in ex.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        err_type = err.get("type", "")
        msg = err.get("msg", "invalid value")

        if loc == "GMP_PASSWORD" and err_type == "missing":
            return "Failed to load GVM configuration: GMP_PASSWORD is required (set it in .env or environment variables)."
        if loc == "GMP_PASSWORD":
            return f"Failed to load GVM configuration: GMP_PASSWORD {msg}."

    return "Failed to load GVM configuration: invalid settings."


class OpenVASMCP(FastMCP):
    """
    MCP server for Greenbone/OpenVAS integration.
    """

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        try:
            gvm_config = load_gvm_config()
        except ValidationError as ex:
            logger.error(_format_gvm_config_error(ex))
            raise SystemExit(1)

        self.gvm_client = GvmClient(
            username=gvm_config.GMP_USERNAME,
            password=gvm_config.GMP_PASSWORD.get_secret_value(),
        )

        register_low_level_tools(self, self.gvm_client)
        register_vuln_scan_tools(self, self.gvm_client)

    @property
    def gvm(self) -> GvmClient:
        """Access the GVM client instance."""
        return self.gvm_client
