# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging
from typing import Annotated, Any

from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from gvm.errors import GvmError, RequiredArgument
from pydantic import Field

from src.services.gvm_client import GvmClient

logger = logging.getLogger(__name__)


def register_inspection_control_tools(
    mcp: FastMCP,
    gvm_client: GvmClient,
) -> None:
    """
    Registers inspection/control tools with the FastMCP instance.

    Args:
        mcp (FastMCP): The FastMCP instance to register the tools with.
        gvm_client (GvmClient): The GvmClient instance to interact with GVM.

    Returns:
        None: This function does not return anything. It registers tools with the FastMCP instance.
    """

    @mcp.tool(
        name="get_targets",
        title="Get all targets",
        description="Retrieve a list of all configured scan targets.",
        tags=["inspection_control"],
    )
    async def get_targets() -> dict[str, Any]:

        try:
            response = gvm_client.get_targets()
        except Exception as exc:
            logger.error("Error in get_targets: %s", exc)
            raise ToolError(str(exc)) from exc

        targets = response.target
        result = {}
        for target in targets:
            result[target.name] = {
                "id": target.id,
                "hosts": target.hosts,
                "port_list": {
                    "id": target.port_list.id,
                    "name": target.port_list.name,
                }
                if target.port_list
                else None,
            }
        return {"targets": result}

    @mcp.tool(
        name="get_target",
        title="Get a specific target",
        description="Retrieve a specific configured scan target.",
        tags=["inspection_control"],
    )
    async def get_target(
        target_id: Annotated[
            str,
            Field(
                description="The UUID of the target to be retrieved.",
            ),
        ],
    ) -> dict[str, Any]:

        try:
            response = gvm_client.get_target(target_id=target_id)
            target = response.target[0]
            result = {
                "id": target.id,
                "name": target.name,
                "hosts": target.hosts,
                "port_list": {
                    "id": target.port_list.id,
                    "name": target.port_list.name,
                }
                if target.port_list
                else None,
            }
            return {"target": result}
        except GvmError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        name="get_tasks",
        title="Get currently existing tasks",
        description="Retrieve the list of currently existing tasks in GVM",
        tags=["inspection_control"],
    )
    async def get_tasks() -> dict[str, Any]:

        try:
            response = gvm_client.get_tasks(details=True)
            tasks = response.task
            result = {}
            for task in tasks:
                result[task.name] = {
                    "id": task.id,
                    "status": task.status,
                    "progress": task.progress,
                    "owner": task.owner,
                    "target_id": task.target.id,
                    "scanner_id": task.scanner.id,
                    "scan_config_id": task.config.id,
                    "creation_time": task.creation_time,
                    "modification_time": task.modification_time,
                    "last_report_id": task.last_report.report.id
                    if task.last_report and task.last_report.report
                    else None,
                }
            return {"tasks": result}
        except GvmError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        name="get_port_lists",
        title="Get all port lists",
        description="Retrieve a list of all configured port lists.",
        tags=["inspection_control"],
    )
    async def get_port_lists() -> dict[str, Any]:

        try:
            response = gvm_client.get_port_lists(details=True)
            port_lists = response.port_list
            result = {}
            for port_list in port_lists:
                result[port_list.name] = {
                    "id": port_list.id,
                    "ports": port_list.port_ranges.port_range
                    if port_list.port_ranges
                    else None,
                }
            return {"port_lists": result}
        except GvmError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        name="start_task",
        title="Start a scan task",
        description="Start a scan task with a given task ID.",
    )
    async def start_task(
        task_id: Annotated[
            str, Field(description="The ID of the scan task to be started.")
        ],
    ) -> dict[str, Any]:

        try:
            response = gvm_client.start_task(task_id=task_id)
        except RequiredArgument as exc:
            raise ToolError(f"Missing required argument: {exc.argument}") from exc
        except GvmError as exc:
            raise ToolError(f"Failed to start task: {str(exc)}") from exc

        return {
            "message": f"Task with ID {task_id} started successfully.",
            "report_id": response.report_id if hasattr(response, "report_id") else None,
        }

    @mcp.tool(
        name="stop_task",
        title="Stop scan task",
        description="Stop a running scan task.",
    )
    async def stop_task(
        task_id: Annotated[str, Field(description="The ID of the scan task.")],
    ) -> dict[str, Any]:

        try:
            gvm_client.stop_task(task_id=task_id)
        except RequiredArgument as exc:
            raise ToolError(f"Missing required argument: {exc.argument}") from exc
        except GvmError as exc:
            raise ToolError(f"Failed to stop task: {str(exc)}") from exc

        return {
            "message": f"Task with ID {task_id} stopped successfully.",
        }
