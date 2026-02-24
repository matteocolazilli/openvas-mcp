import asyncio
import logging
from typing import Optional

from fastmcp.server import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR
from pydantic import ValidationError

from src.config.gvm_client_config import load_gvm_config
from src.services.gvm_client import GvmClient
from src.tools.inspection_control_tools import register_inspection_control_tools
from src.tools.scan_workflow_tools import register_scan_workflow_tools

logger = logging.getLogger(__name__)


def _format_gvm_config_error(ex: ValidationError) -> str:
    for err in ex.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        err_type = err.get("type", "")
        msg = err.get("msg", "invalid value")

        if loc == "GMP_PASSWORD" and err_type == "missing":
            return "Failed to load GVM configuration: GMP_PASSWORD is required (set it in .env or environment variables)."
        if loc == "GMP_PASSWORD":
            return f"Failed to load GVM configuration: GMP_PASSWORD {msg}."

    return "Failed to load GVM configuration: invalid settings."


class _GreenboneInitMiddleware(Middleware):
    def __init__(self, server: "GreenboneMCP"):
        self.server = server

    async def on_initialize(self, context: MiddlewareContext, call_next):

        try:
            await self.server.ensure_ready()
        except ValidationError as ex:
            msg = _format_gvm_config_error(ex)
            logger.error(msg)
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=msg))
        except Exception as ex:
            msg = f"Failed to initialize Greenbone backend: {ex}"
            logger.exception(msg)
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=msg))
        
        # If initialization succeeds, continue processing the request
        return await call_next(context)


class GreenboneMCP(FastMCP):
    """
    MCP server for Greenbone/OpenVAS integration.
    """

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self._gvm_client: Optional[GvmClient] = None
        self._gvm_ready = False
        self._tools_registered = False
        self._init_lock = asyncio.Lock()

        self.add_middleware(_GreenboneInitMiddleware(self))


    async def ensure_ready(self) -> None:
        """Initialize config/client."""
        if self._gvm_ready:
            return

        async with self._init_lock:
            if self._gvm_ready:
                return

            gvm_config = load_gvm_config()

            self._gvm_client = GvmClient(
                username=gvm_config.GMP_USERNAME,
                password=gvm_config.GMP_PASSWORD.get_secret_value(),
            )

            if not self._tools_registered:
                register_inspection_control_tools(self, self._gvm_client)
                register_scan_workflow_tools(self, self._gvm_client)
                self._tools_registered = True

            self._gvm_ready = True
            logger.info("Greenbone backend initialized successfully.")
        

    @property
    def gvm(self) -> GvmClient:
        if self._gvm_client is None:
            raise RuntimeError("GVM client is not initialized yet")
        return self._gvm_client