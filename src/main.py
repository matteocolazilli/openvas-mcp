# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

from src.core.mcp_server import OpenVASMCP
from src.utils.logging_config import setup_logging


def main():
    """Initialize and run the OpenVAS MCP server."""

    setup_logging()
    mcp_server = OpenVASMCP("OpenVAS MCP Server")

    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
