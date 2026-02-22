# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

import logging
from typing import Annotated, Any, Optional

from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from gvm.errors import GvmError, RequiredArgument
from pydantic import Field

from src.services.gvm_client import GvmClient
import src.constants as const


logger = logging.getLogger(__name__)

def register_gvm_primitive_tools(
        mcp: FastMCP, 
        gvm_client: GvmClient,
    ) -> None:
    """
    Registers primitive GVM tools with the FastMCP instance.
    
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
        tags=["gvm_primitive"]
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
                } if target.port_list else None,
            }
        return {"targets": result}
    
    
    @mcp.tool(
        name="get_target",
        title="Get a specific target",
        description="Retrieve a specific configured scan target.",
        tags=["gvm_primitive"]
    )
    async def get_target(
        target_id: Annotated[str,
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
                } if target.port_list else None,
            }
            return {"target": result}
        except GvmError as exc:
            raise ToolError(str(exc)) from exc
        
    @mcp.tool(
        name="create_target",
        title="Create a new target",
        description="Create a new scan target with specified hosts and optional port list.",
        tags=["gvm_primitive"]
    )
    async def create_target(
        name: Annotated[
            str,
            Field(
                description="A name for the new target.",
            ),
        ],
        hosts: Annotated[
            list[str],
            Field(
                description=
                """
                List of target hosts (IP addresses, CIDRs, or DNS names).
                
                Accepted formats: 
                - single IPs (e.g. '10.10.11.1'),
                - CIDR ranges (e.g. '192.168.1.1/24'),
                - FQDNs (e.g. 'example.com') 
                - IP ranges (e.g. '192.168.1.1-10', '192.168.1.1-192.168.1.255').""",
            ),
        ],
        port_range_list: Annotated[
            Optional[str],
            Field(
                description=
                """
                List of comma-separated port range specifications.

                Accepted formats:
                - single port (e.g. '7'), 
                - port range (e.g. '9-11'). 
                - These options can be mixed (e.g. '5', '7', '9-11', '13').
                
                An entry can be preceded by a protocol specifier ('T:' for TCP, 'U:' for UDP) (e.g. 'T:1-3', 'U:7').
                If no specifier is given, TCP is assumed.
                
                If not provided, the default 'All IANA assigned TCP ports' port list is used."""
            ),
        ],
        port_list_id: Annotated[
            Optional[str],
            Field(
                description=
                """
                Optional ID of an existing port list to use for the target. 
                If provided, this will override any port_ranges_list specification.

                If not provided, the default 'All IANA assigned TCP ports' port list is used.
                """,
            ),
        ],
    ) -> dict[str, Any]:   

        try:
            if port_list_id:
                response = gvm_client.create_target(name=name, hosts=hosts, port_list_id=port_list_id)
            elif port_range_list:
                response = gvm_client.create_target(name=name, hosts=hosts, port_range=port_range_list)
            else:
                port_list_id = const.ALL_IANA_ASSIGNED_TCP_PORT_LIST_ID
                response = gvm_client.create_target(name=name, hosts=hosts, port_list_id=port_list_id)

        except RequiredArgument as exc:
            raise ToolError(f"Missing required argument: {exc.argument}") from exc
        except GvmError as exc:
            raise ToolError(str(exc)) from exc

        target_id = response.id
        result = {
            "id": target_id,
            "name": name,
            "hosts": hosts,
            "port_list": {
                "id": port_list_id,
                "port_ranges": port_range_list,
            },
        }
        return {"target": result}

    @mcp.tool(
        name="get_tasks",
        title="Get currently existing tasks",
        description="Retrieve the list of currently existing tasks in GVM",
        tags=["gvm_primitive"]
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
                    "last_report_id": task.last_report.report.id if task.last_report and task.last_report.report else None,
                }
            return {"tasks": result}
        except GvmError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(
        name="get_port_lists",
        title="Get all port lists",
        description="Retrieve a list of all configured port lists.",
        tags=["gvm_primitive"]
    )
    async def get_port_lists() -> dict[str, Any]:

        try:
            response = gvm_client.get_port_lists(details=True)
            port_lists = response.port_list
            result = {}
            for port_list in port_lists:
                result[port_list.name] = {
                    "id": port_list.id,
                    "ports": port_list.port_ranges.port_range if port_list.port_ranges else None
                }
            return {"port_lists": result}
        except GvmError as exc:
            raise ToolError(str(exc)) from exc
        
    @mcp.tool(
        name="stop_scan",
        title="Stop scan",
        description="Stop a running scan task.",
    )
    async def stop_scan(
        task_id: Annotated[str, Field(description="The ID of the scan task.")],
    ) -> dict[str, Any]:

        try:
            gvm_client.stop_task(task_id=task_id)
        except RequiredArgument as exc:
            raise ToolError(f'Missing required argument: {exc.argument}') from exc
        except GvmError as exc:
            raise ToolError(f"Failed to stop task: {str(exc)}") from exc  

        return {
            "message": f"Task with ID {task_id} stopped successfully.",
        }
