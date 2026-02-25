import logging
from typing import Optional

from fastmcp.server import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR
from pydantic import ValidationError

from src.config.gvm_client_config import GvmClientConfig
from src.services.gvm_client import GvmClient
from src.tools.inspection_control_tools import register_inspection_control_tools
from src.tools.vm_workflow_tools import register_vm_workflow_tools

from gvm.errors import GvmResponseError

logger = logging.getLogger(__name__)


def _format_gvm_config_error(ex: ValidationError) -> str:
    for err in ex.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        err_type = err.get("type", "")
        msg = err.get("msg", "invalid value")

        if loc == "PASSWORD" and err_type == "missing":
            return "Failed to load GVM configuration: PASSWORD is required (set it in .env or environment variables)."
        if loc == "PASSWORD":
            return f"Failed to load GVM configuration: PASSWORD {msg}."

    return "Failed to load GVM configuration: invalid settings."


class GreenboneInitMiddleware(Middleware):
    def __init__(self, server: "GreenboneMCP"):
        self.server = server

    async def on_initialize(self, context: MiddlewareContext, call_next):

        try:
            self.server.init()
        except McpError:
            raise  # Re-raise McpError to signal initialization failure
        except ValidationError as ex:
            msg = _format_gvm_config_error(ex)
            logger.error(msg)
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=msg))
        except Exception as ex:
            msg = f"Failed to initialize Greenbone backend: {ex}"
            logger.exception(msg)
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=msg))
        
        # If initialization succeeds, continue processing the request
        await call_next(context)


class GreenboneMCP(FastMCP):
    """
    MCP server for Greenbone/OpenVAS integration.
    """

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self._gvm_client: Optional[GvmClient] = None
        self._gvm_ready = False
        self._tools_registered = False

        self.add_middleware(GreenboneInitMiddleware(self))


    def init(self) -> None:
        """Initialize config/client."""
        if self._gvm_ready:
            return

        gvm_client_config = GvmClientConfig()

        username = gvm_client_config.USERNAME
        password = gvm_client_config.PASSWORD.get_secret_value()

        self._gvm_client = GvmClient(
            username=username,
            password=password,
        )
        
        try:
            self._gvm_client.authenticate()
        except GvmResponseError as ex:
            self._gvm_client = None  # Ensure client is not set if authentication fails
            if "Authentication failed" in str(ex):
                raise McpError(ErrorData(code=INTERNAL_ERROR, message="Failed to authenticate with GVM: wrong credentials."))
            else:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to authenticate with GVM: {ex}"))
            
        if not self._tools_registered:
            register_inspection_control_tools(self, self._gvm_client)
            register_vm_workflow_tools(self, self._gvm_client)
            self._tools_registered = True

        self._gvm_ready = True
        logger.info("Greenbone backend initialized successfully.")
        

    @property
    def gvm(self) -> GvmClient:
        if self._gvm_client is None:
            raise RuntimeError("GVM client is not initialized yet")
        return self._gvm_client