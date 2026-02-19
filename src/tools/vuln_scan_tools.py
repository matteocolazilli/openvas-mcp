# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

"""Tool handlers for vulnerability scanning.
"""
import base64 as b64
import logging
import re
from typing import Annotated, Any, Optional

from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from gvm.errors import GvmError, RequiredArgument
from pydantic import Field
from xsdata.models.datatype import XmlDateTime

import src.models.generated as models
import src.constants as const
import src.utils.utilities as utils
from src.services.gvm_client import GvmClient


logger = logging.getLogger(__name__)


def _default_target_name(hosts: list[str]) -> str:
    """Generate a default target name based on host entries.

    Args:
        hosts (list[str]): List of host strings (IPs, CIDRs, DNS names, or
            ranges).

    Returns:
        str: Target name derived from the provided hosts.
    """
    if len(hosts) == 1:
        return f"{hosts[0]}"
    if len(hosts) <= 5:
        return ", ".join(sorted(hosts))
    return f"{len(hosts)} hosts"

def _summarize_task_status(task: models.Task) -> dict[str, Any]:
    target = task.target
    target_summary = None
    if target is not None:
        target_summary = {
            "id": target.id,
            "name": target.name,
            "hosts": target.hosts,
        }

    task_summary = {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "progress": task.progress,
        "result_count": task.result_count,
    }

    return _remove_none_values(
        {
            "task": task_summary,
            "target": target_summary,
        }
    )

def _remove_none_values(obj: Any) -> Any:
    """Recursively remove ``None`` values from dictionaries and lists.

    Args:
        obj (Any): Input object to sanitize.

    Returns:
        Any: Sanitized object with ``None`` values removed from nested
            containers.
    """
    if isinstance(obj, dict):
        return {k: _remove_none_values(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_remove_none_values(v) for v in obj if v is not None]
    return obj

def _xml_datetime_to_iso(value: XmlDateTime | None) -> str | None:
    """Serialize an ``XmlDateTime`` value to a stable ISO-8601 string.

    Args:
        value (XmlDateTime | None): XML datetime value to serialize.

    Returns:
        str | None: ISO-8601 string representation, or ``None`` if the input is
            ``None``.
    """
    if value is None:
        return None
    # XmlDateTime is tuple-like; JSON encoding would turn it into a list.
    # Use string form to keep tool output clean and stable.
    return str(value)

def _truncate(text: str | None, max_chars: int) -> str | None:
    if text is None:
        return None
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."

def _extract_report_content_item(report: models.Report | None, item_type: type[Any]) -> Any | None:
    if report is None:
        return None
    for item in report.content:
        if isinstance(item, item_type):
            return item
    return None

def _extract_report_datetime(report: models.Report | None, item_type: type[Any] | None) -> str | None:
    if item_type is None:
        return None
    item = _extract_report_content_item(report, item_type)
    if item is None:
        return None
    value = getattr(item, "value", None)
    if isinstance(value, XmlDateTime):
        return _xml_datetime_to_iso(value)
    if value is None:
        return None
    return str(value)

def _decode_report_text_blob(blob: str) -> str:
    """Decode a report text blob, handling plain text and Base64 payloads.

    Args:
        blob (str): Report text blob, potentially Base64-encoded.

    Returns:
        str: Decoded UTF-8 report text.

    Raises:
        ValueError: If the blob looks like Base64 but has invalid padding or cannot
            be decoded.
    """
    stripped = blob.strip()
    if not stripped:
        return ""

    if not utils._BASE64_CHARS_RE.fullmatch(stripped):
        return stripped
    
    normalized = re.sub(r"\s+", "", stripped)
    if not normalized:
        return ""

    remainder = len(normalized) % 4

    if remainder == 1:
        raise ValueError("Invalid Base64 string: incorrect padding")
    if remainder:
        normalized += "=" * (4 - remainder)

    try:
        decoded = b64.b64decode(normalized, validate=False)
        return decoded.decode("utf-8", errors="replace")
    except Exception:
        raise ValueError("Invalid Base64 string: decoding failed")

def _extract_report_text(report: models.Report) -> str | None:
    """Extract and decode the main textual payload from a report.

    Args:
        report (models.Report): Report object containing mixed content items.

    Returns:
        str | None: Decoded report text, or ``None`` when no text payload is
            present.
    """
    text_chunks = [item for item in report.content if isinstance(item, str) and item.strip()]
    if not text_chunks:
        return None
    blob = max(text_chunks, key=lambda value: len(value.strip()))
    return _decode_report_text_blob(blob)

def _summarize_report_metadata(report: models.Report | None) -> dict[str, Any] | None:
    """Build a compact metadata summary for a report.

    Args:
        report (models.Report | None): Report instance to summarize.

    Returns:
        dict[str, Any] | None: Metadata dictionary with report, task, owner, and
            format information, or ``None`` when no report is provided.
    """
    if report is None:
        return None

    owner = _extract_report_content_item(report, models.Owner)
    task = _extract_report_content_item(report, models.Task)
    report_format = _extract_report_content_item(report, models.ReportFormat)

    return _remove_none_values(
        {
            "id": report.id,
            "format_id": report.format_id,
            "content_type": report.content_type,
            "extension": report.extension,
            "owner": owner.name if owner else None,
            "created_at": _extract_report_datetime(report, getattr(models.Report, "CreationTime", None)),
            "modified_at": _extract_report_datetime(report, getattr(models.Report, "ModificationTime", None)),
            "task": {
                "id": task.id if task else None,
                "name": task.name if task else None,
                },
            "report_format": {
                "id": report_format.id if report_format else None,
                "name": report_format.name if report_format else None,
            },
        }
    )

def _extract_delta_counts(report_text: str) -> dict[str, int]:
    return {
        "added_issues": len(utils._ADDED_ISSUE_RE.findall(report_text)),
        "removed_issues": len(utils._REMOVED_ISSUE_RE.findall(report_text)),
        "changed_issues": len(utils._CHANGED_ISSUE_RE.findall(report_text)),
    }

def _build_txt_report_output(
    report: models.Report,
    report_text: str | None,
    *,
    include_full_text: bool,
    include_delta_summary: bool = False,
    preview_chars: int = 6000,
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "report": _summarize_report_metadata(report),
        "report_text_total_chars": len(report_text) if report_text is not None else None,
    }

    if report_text is not None:
        if include_full_text:
            output["report_text"] = report_text
        else:
            output["report_text_preview"] = _truncate(report_text, preview_chars)

        if include_delta_summary:
            output["delta_summary"] = _extract_delta_counts(report_text)

    return _remove_none_values(output)

# Main tool registration function

def register_vuln_scan_tools(
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
        description=
        """
        Create the minimal target/task resources and start a focused vulnerability scan.
        The scan will use the OpenVAS scanner, "Full and fast" scan configuration, 
        and "All IANA assigned TCP ports" port list (if not overridden).
        Returns a dictionary containing the target ID, task ID, and report ID.

        Use this tool when the user wants to quickly scan specific hosts with minimal setup.

        Note: This tool does not wait for scan completion; use "scan_status" tool to poll for status.
        """
    )
    async def start_scan(
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
                - IP ranges (e.g. '192.168.1.1-10', '192.168.1.1-192.168.1.255').
                """,
            ),
        ],
        port_ranges_list: Annotated[
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
                
                If not provided, the default 'All IANA assigned TCP ports' port list is used.
                """
            ),
        ],
        target_name: Annotated[
            Optional[str],
            Field(
                description=
                """
                Optional name for the new target.
                
                If not provided, a name will be generated based on the hosts.
                """,
            ),
        ],
    ) -> dict[str, Any]:


        target_name = target_name or _default_target_name(hosts)

        create_target_kwargs: dict[str, Any] = {
                "name": target_name,
                "hosts": hosts,
                "port_range": port_ranges_list if port_ranges_list else None,
                "port_list_id": None if port_ranges_list else const.ALL_IANA_ASSIGNED_TCP_PORT_LIST_ID,
            }

        try:
            target_response = gvm_client.create_target(**create_target_kwargs)
        except GvmError as exc:
            raise ToolError(f"Failed to create target: {str(exc)}") from exc
        
        task_name = f"Scan {target_name} - OpenVAS MCP"
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
            launch_response = gvm_client.start_task(task_id=task_id)
        except GvmError as exc:
            raise ToolError(f"Failed to start task: {str(exc)}") from exc

        report_id = launch_response.report_id

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
            "report": {
                "report_id": report_id
            }
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
            raise ToolError(f'Missing required argument: {exc.argument}') from exc
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
        include_details: Annotated[bool, Field(description="Whether to include full results in the report.")] = True,
    ) -> dict[str, Any]:

        try:
            get_task_response = gvm_client.get_task(task_id=task_id)
            tasks = get_task_response.task
            if not tasks:
                raise ToolError(f"No task found for task ID {task_id}.")
            task = tasks[0]
        except RequiredArgument as exc:
            raise ToolError(f'Missing required argument: {exc.argument}') from exc
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve task: {str(exc)}") from exc
        
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
                # Filters by Critical, High, Medium, and Low severity issues
                filter_string="levels=chml",
                report_format_id=const.DEFAULT_REPORT_FORMAT_ID,
            )
        
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve task: {str(exc)}") from exc

        reports = get_report_response.report if get_report_response else []
        report = next((candidate for candidate in reports if candidate.id == report_id), None)
        if report is None and reports:
            report = reports[0]
        if not report:
            raise ToolError(f"No reports are available yet for task {task_id}.")
    
        report_text = _extract_report_text(report)

        output = _build_txt_report_output(
            report,
            report_text,
            include_full_text=include_details,
        )

        return _remove_none_values(output)


    @mcp.tool(
        name="rescan_target",
        title="Rescan target",
        description="""Initiate a new scan on an existing target by relaunching the latest related task.
        Useful for quickly rescanning the same target without needing to create a new task or target.
        Returns a dictionary containing the target ID, task ID, and new report ID for the rescan task."""
    )
    async def rescan_target(
        target_id: Annotated[str, Field(description="The ID of the target to be rescanned.")],
    ) -> dict[str, Any]:

        try:
            get_tasks_response = gvm_client.get_tasks()
        except RequiredArgument as exc:
            raise ToolError(f'Missing required argument: {exc.argument}') from exc
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve task: {str(exc)}") from exc
        
        tasks = get_tasks_response.task
        task = next((t for t in tasks if t.target.id == target_id), None)
        if not task:
            raise ToolError(f"No tasks found for target ID {target_id}.")
        
        task_id = task.id
        target_id = task.target.id
        target_name = task.target.name  

        try:
            start_task_response = gvm_client.start_task(task_id=task_id)
        except GvmError as exc:
            raise ToolError(f"Failed to start task: {str(exc)}") from exc

        new_report_id = start_task_response.report_id

        return {
            "target": {
                "id": target_id,
                "name": target_name,
            },
            "task": {
                "id": task_id,
                "name": task.name,
                "scan_config_id": task.config.id,
                "scanner_id": task.scanner.id,
            },
            "report": {
                "report_id": new_report_id
            }
        }
    

    @mcp.tool(
        name="delta_report",
        title="Delta Report",
        description=
        """
        Compare the most recent report of a task with the previous one and return the differences.
        Useful for tracking changes over time when rescanning the same target.
        Returns a dictionary summarizing new, resolved, and persistent vulnerabilities.
        """
    )
    async def delta_report(
        task_id: Annotated[str, Field(description="The ID of the task for which to generate the delta report.")],
    ) -> dict[str, Any]:
    
        try:
            get_reports_response = gvm_client.get_reports(filter_string=f"~{task_id} sort-reverse=date", details=True)
        except GvmError as exc:
            raise ToolError(f"Failed to retrieve reports: {str(exc)}") from exc
        
        reports = get_reports_response.report

        if not reports:
            raise ToolError(f"No reports found for task ID {task_id}.")

        if len(reports) < 2:
            raise ToolError(f"Not enough reports available for task ID {task_id} to compute delta.")

        last_report_id = reports[0].id
        previous_report_id = reports[1].id
        if last_report_id == previous_report_id:
            raise ToolError(f"Current report and last report are identical for task ID {task_id}.")

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
        report = next((candidate for candidate in reports if candidate.id == last_report_id), None)
        if report is None and reports:
            report = reports[0]
        if not report:
            raise ToolError(f"Delta report is empty for task ID {task_id}.")

        report_text = _extract_report_text(report)
        output = _build_txt_report_output(
            report,
            report_text,
            include_full_text=True,
            include_delta_summary=True,
        )
        
        output["comparison"] = {
            "base_report_id": last_report_id,
            "delta_report_id": previous_report_id,
        }

        return _remove_none_values(output)
