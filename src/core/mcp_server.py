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
            gvm_client_config = GvmClientConfig()

            self.server._gvm_client = GvmClient(
                username=gvm_client_config.USERNAME,
                password=gvm_client_config.PASSWORD.get_secret_value(),
            )
            
            self.server._gvm_client.authenticate()

        except ValidationError as ex:
            self.server._gvm_client = None
            msg = _format_gvm_config_error(ex)
            logger.error(msg)
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=msg))
        except GvmResponseError as ex:
            self.server._gvm_client = None
            if "Authentication failed" in str(ex):
                raise McpError(ErrorData(code=INTERNAL_ERROR, message="Failed to authenticate with GVM: wrong credentials."))
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to authenticate with GVM: {ex}"))
        except Exception as ex:
            self.server._gvm_client = None  
            logger.exception("Failed to initialize Greenbone backend: %s", ex)
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to initialize Greenbone backend: {ex}"))

        register_inspection_control_tools(self.server, self.server._gvm_client)
        register_vm_workflow_tools(self.server, self.server._gvm_client)

        logger.info("Greenbone backend initialized successfully.")
        await call_next(context)


class GreenboneMCP(FastMCP):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self._gvm_client: Optional[GvmClient] = None
        self.add_middleware(GreenboneInitMiddleware(self))

    @property
    def gvm(self) -> GvmClient:
        if self._gvm_client is None:
            raise RuntimeError("GVM client is not initialized yet")
        return self._gvm_client
