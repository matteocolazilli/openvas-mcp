# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

"""Tool handlers for vulnerability scanning."""

from typing import Annotated, Any, Optional

from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from gvm.errors import GvmError, RequiredArgument
from pydantic import Field

import src.tools.utils.constants as const
from src.services.gvm_client import GvmClient
from src.tools.utils.helpers import (
    _build_txt_report_output,
    _default_target_name,
    _extract_delta_counts,
    _extract_report_text,
    _remove_none_values,
    _summarize_task_status,
)

# Main tool registration function


def register_vm_workflow_tools(
    mcp: FastMCP,
    gvm_client: GvmClient,
) -> None:
    """Register vulnerability scanning tools on the MCP server.

    Args:
        mcp (FastMCP): FastMCP server instance where tools are registered.
        gvm_client (GvmClient): GVM client used by tool handlers to call
            OpenVAS/GMP APIs.

    Returns:
        None: This function registers tools as side effects.
    """

    @mcp.tool(
        name="start_scan",
        title="Start scan",
        description="""
        Create the minimal target/task resources and start a focused vulnerability scan.

        The scan will use the default "Full and fast" scan configuration, 
        and "All IANA assigned TCP ports" port list (if not overridden).
        Returns a dictionary containing the target ID, task ID, and report ID.

        Note: This tool does not wait for scan completion; use "scan_status" tool to poll for status.
        """,
    )
    async def start_scan(
        hosts: Annotated[
            list[str],
            Field(
                description="""
                List of target hosts (IP addresses, CIDRs, or DNS names).
                
                Accepted formats: 
                - single IPs (e.g. '10.10.11.1'),
                - CIDR ranges (e.g. '192.168.1.1/24'),
                - FQDNs (e.g. 'example.com') 
                - IP ranges (e.g. '192.168.1.1-10', '192.168.1.1-192.168.1.255').
                """,
            ),
        ],
        port_ranges_list: Annotated[
            Optional[str],
            Field(
                description="""
                List of comma-separated port range specifications.

                Accepted formats:
                - single port (e.g. '7'), 
                - port range (e.g. '9-11'). 
                - These options can be mixed (e.g. '5', '7', '9-11', '13').
                
                An entry can be preceded by a protocol specifier ('T:' for TCP, 'U:' for UDP) (e.g. 'T:1-3', 'U:7').
                If no specifier is given, TCP is assumed.
                
                If not provided, the default 'All IANA assigned TCP ports' port list is used.
                """
            ),
        ],
        port_list_id: Annotated[
            Optional[str],
            Field(
                description="""
                Optional ID of an existing port list to use for the target.
                
                If not provided, the default 'All IANA assigned TCP ports' port list is used.
                """
            ),
        ],
        target_name: Annotated[
            Optional[str],
            Field(
                description="""
                Optional name for the new target.
                
                If not provided, a name will be generated based on the hosts.
                """,
            ),
        ],
    ) -> dict[str, Any]:

        target_name = target_name or _default_target_name(hosts)

        if port_list_id:
            port_ranges_list = None
        elif not port_list_id and not port_ranges_list:
            port_list_id = const.ALL_IANA_ASSIGNED_TCP_PORT_LIST_ID


        create_target_kwargs: dict[str, Any] = {
            "name": target_name,
            "hosts": hosts,
            "port_range": port_ranges_list,
            "port_list_id": port_list_id
        }

        try:
            target_response = gvm_client.create_target(**create_target_kwargs)
        except GvmError as exc:
            raise ToolError(f"Failed to create target: {str(exc)}") from exc

        task_name = f"Scan {target_name} - Greenbone MCP"
        target_id = target_response.id

        try:
            task_response = gvm_client.create_task(
                name=task_name,
                config_id=const.FULL_AND_FAST_SCAN_CONFIG_ID,
                target_id=target_id,
                scanner_id=const.OPENVAS_SCANNER_ID,
            )
        except GvmError as exc:
            raise ToolError(f"Failed to create task: {str(exc)}") from exc

        task_id = task_response.id

        try:
            start_task_response = gvm_client.start_task(task_id=task_id)
        except GvmError as exc:
            raise ToolError(f"Failed to start task: {str(exc)}") from exc

        report_id = start_task_response.report_id

        return {
            "target": {
                "id": target_id,
                "name": target_name,
            },
            "task": {
                "id": task_id,
                "name": task_name,
                "scan_config_id": const.FULL_AND_FAST_SCAN_CONFIG_ID,
                "scanner_id": const.OPENVAS_SCANNER_ID,
            },
            "report": {"report_id": report_id},
        }

    @mcp.tool(
        name="scan_status",
        title="Scan status",
        description="Retrieve the current status and progress of a scan task.",
    )
    async def scan_status(
        task_id: Annotated[str, Field(description="The ID of the scan task.")],
    ) -> dict[str, Any]:

        try:
            task_response = gvm_client.get_task(task_id=task_id)
        except RequiredArgument as exc:
            raise ToolError(f"Missing required argument: {exc.argument}") from exc
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve task: {str(exc)}") from exc

        task = task_response.task[0]

        summary = _summarize_task_status(task)

        return _remove_none_values(summary)

    @mcp.tool(
        name="fetch_latest_report",
        title="Fetch latest report",
        description="Retrieve the most recent report for a scan task, optionally including full results.",
    )
    async def fetch_latest_report(
        task_id: Annotated[str, Field(description="The ID of the scan task.")],
    ) -> dict[str, Any]:

        try:
            get_task_response = gvm_client.get_task(task_id=task_id)
        except RequiredArgument as exc:
            raise ToolError(f"Missing required argument: {exc.argument}") from exc
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve task: {str(exc)}") from exc

        tasks = get_task_response.task
        if not tasks:
            raise ToolError(f"No task found for task ID {task_id}.")
        task = tasks[0]

        report_id = None
        if task.last_report and task.last_report.report:
            report_id = task.last_report.report.id
        elif task.current_report and task.current_report.report:
            report_id = task.current_report.report.id

        if not report_id:
            raise ToolError(f"No reports are available yet for task {task_id}.")

        try:
            get_report_response = gvm_client.get_report(
                report_id=report_id,
                filter_string="levels=chml",  # Filters by Critical, High, Medium, and Low severity issues
                report_format_id=const.DEFAULT_REPORT_FORMAT_ID,
            )
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve report: {str(exc)}") from exc

        report = get_report_response.report[0] if get_report_response.report else None

        if not report:
            raise ToolError(f"No reports are available yet for task {task_id}.")

        report_txt = _extract_report_text(report)

        output = _build_txt_report_output(
            report,
            report_txt
        )

        return _remove_none_values(output)

    @mcp.tool(
        name="restart_scan",
        title="Restart scan",
        description="""Restart a new scan associated with an existing task.

        Useful to perform a scan on an already created task and its associated target without needing to create a new task.
        Returns a dictionary containing the target ID, task ID, and new report ID for the rescan task.""",
    )
    async def restart_scan(
        task_id: Annotated[
            str, Field(description="The ID of the task to be restarted.")
        ],
    ) -> dict[str, Any]:
        
        try:
            get_tasks_response = gvm_client.get_task(task_id=task_id)
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve task: {str(exc)}") from exc

        task = get_tasks_response.task[0] if get_tasks_response.task else None
    
        if not task:
            raise ToolError(f"No tasks found for task ID {task_id}.")
        
        try:
            start_task_response = gvm_client.start_task(task_id=task_id)
        except GvmError as exc:
            raise ToolError(f"Failed to start task: {str(exc)}") from exc

        new_report_id = start_task_response.report_id

        task_id = task.id
        task_name = task.name if task.name else None
        
        target_id = task.target.id if task.target and task.target.id else None
        target_name = task.target.name if task.target and task.target.name else None

        return _remove_none_values({
            "target": {
                "id": target_id,
                "name": target_name,
            },
            "task": {
                "id": task_id,
                "name": task_name,
                "scan_config_id": const.FULL_AND_FAST_SCAN_CONFIG_ID,
                "scanner_id": const.OPENVAS_SCANNER_ID,
            },
            "report": {"report_id": new_report_id},
        })

    @mcp.tool(
        name="delta_report",
        title="Delta Report",
        description="""
        Compare the most recent report of a task with the previous one and return the differences.
        Useful for tracking changes over time when rescanning the same target.
        Returns a dictionary summarizing new, resolved, and persistent vulnerabilities.
        """,
    )
    async def delta_report(
        task_id: Annotated[
            str,
            Field(
                description="The ID of the task for which to generate the delta report."
            ),
        ],
        full_details: Annotated[
            bool,
            Field(description="Whether to include full details of the delta report."),
        ] = False,
    ) -> dict[str, Any]:

        try:
            get_reports_response = gvm_client.get_reports(
                filter_string=f"~{task_id} sort-reverse=date", details=True
            )
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve reports: {str(exc)}") from exc

        reports = get_reports_response.report

        if not reports:
            raise ToolError(f"No reports found for task ID {task_id}.")

        if len(reports) < 2:
            raise ToolError(
                f"Not enough reports available for task ID {task_id} to compute delta."
            )

        last_report_id = reports[0].id
        previous_report_id = reports[1].id
        if last_report_id == previous_report_id:
            raise ToolError(
                f"Current report and last report are identical for task ID {task_id}."
            )

        try:
            delta_response = gvm_client.get_report(
                report_id=last_report_id,
                delta_report_id=previous_report_id,
                filter_string="levels=chml",
                report_format_id=const.DEFAULT_REPORT_FORMAT_ID,
            )
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve delta report: {str(exc)}") from exc

        reports = delta_response.report if delta_response else []
        report = next(
            (candidate for candidate in reports if candidate.id == last_report_id), None
        )
        if report is None and reports:
            report = reports[0]
        if not report:
            raise ToolError(f"Delta report is empty for task ID {task_id}.")

        report_text = _extract_report_text(report)
        result = {}

        result["delta_report"] = {
            "task_id": task_id,
            "base_report_id": last_report_id,
            "delta_report_id": previous_report_id,
            "delta_report_txt": report_text,
        }

        return _remove_none_values(result)
