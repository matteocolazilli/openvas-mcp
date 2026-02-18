# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

from src.core.mcp_server import OpenVASMCP
from src.utils.logging_config import setup_logging
from src.config import load_mcp_config

def main():
    """Initialize and run the OpenVAS MCP server."""

    setup_logging()
    
    mcp_config = load_mcp_config()

    exclude_tags = {"low_level"} if not mcp_config.LOW_LEVEL_TOOLS else set()
    
    mcp_server = OpenVASMCP("OpenVAS MCP Server", exclude_tags=exclude_tags)

    mcp_server.run(transport="stdio")

if __name__ == "__main__":
    main()
