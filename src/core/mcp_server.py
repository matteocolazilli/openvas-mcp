# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging

from fastmcp.server import FastMCP
from gvm.connections import UnixSocketConnection

from src.config import load_gvm_config
from src.services.gvm_adapter import GvmAdapter
from src.tools.vuln_scan_tools import register_vuln_scan_tools
from src.tools.low_level_tools import register_low_level_tools

logger = logging.getLogger(__name__)

class OpenVASMCP(FastMCP):
    """
    MCP server for Greenbone/OpenVAS integration.
    """

    def __init__(self, name: str,*args, **kwargs):
        super().__init__(name, *args, **kwargs)
        gvm_config = load_gvm_config()

        connection = UnixSocketConnection()

        self.gvm_adapter = GvmAdapter(
            connection=connection,
            username=gvm_config.GMP_USERNAME,
            password=gvm_config.GMP_PASSWORD,
        )

        register_low_level_tools(self, self.gvm_adapter)
        register_vuln_scan_tools(self, self.gvm_adapter)


    @property
    def gvm(self) -> GvmAdapter:
        """Access the GVM adapter instance."""
        return self.gvm_adapter
