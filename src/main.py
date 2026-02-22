# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

from src.core.mcp_server import GreenboneMCP
from src.config.logging_config import setup_logging


def main():
    """Create and run the Greenbone MCP server."""

    setup_logging()
    mcp_server = GreenboneMCP("Greenbone MCP Server")

    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
