# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

"""Internal helper functions for vulnerability scan tools."""

import base64 as b64
import re
from typing import Any

from xsdata.models.datatype import XmlDateTime

import src.models.generated as models
import src.utils.utilities as utils


def _default_target_name(hosts: list[str]) -> str:
    """Generate a default target name based on host entries."""
    if len(hosts) == 1:
        return f"{hosts[0]}"
    if len(hosts) <= 3:
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
    """Recursively remove ``None`` values from dictionaries and lists."""
    if isinstance(obj, dict):
        return {k: _remove_none_values(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_remove_none_values(v) for v in obj if v is not None]
    return obj


def _truncate(text: str | None, max_chars: int) -> str | None:
    if text is None:
        return None
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _extract_report_content_item(
    report: models.Report | None,
    item_type: type[Any],
) -> Any | None:
    """Extract the first content item of a specified type from a report."""
    if report is None:
        return None
    for item in report.content:
        if isinstance(item, item_type):
            return item
    return None


def _extract_report_datetime(
    report: models.Report | None,
    item_type: type[Any] | None,
) -> str | None:
    if item_type is None:
        return None
    item = _extract_report_content_item(report, item_type)
    if item is None:
        return None
    value = getattr(item, "value", None)
    if isinstance(value, XmlDateTime):
        return str(value)
    if value is None:
        return None
    return str(value)


def _decode_report_text_blob(blob: str) -> str:
    """Decode a report text blob, handling plain text and Base64 payloads."""
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
    except Exception as exc:
        raise ValueError("Invalid Base64 string: decoding failed") from exc


def _extract_report_text(report: models.Report) -> str | None:
    """Extract and decode the main textual payload from a report."""
    text_chunks = [item for item in report.content if isinstance(item, str) and item.strip()]
    if not text_chunks:
        return None
    blob = max(text_chunks, key=lambda value: len(value.strip()))
    return _decode_report_text_blob(blob)


def _summarize_report_metadata(report: models.Report | None) -> dict[str, Any] | None:
    """Build a compact metadata summary for a report."""
    if report is None:
        return None

    task: models.Task | None = _extract_report_content_item(report, models.Task)
    creation_time = _extract_report_content_item(report, report.CreationTime)
    scan_start = str(report.ScanStart)
    scan_end = str(report.ScanEnd)

    return {
        "id": report.id,
        "created_at": str(creation_time.value) if creation_time else None,
        "scan_start": scan_start,
        "scan_end": scan_end,
        "task": {
            "id": task.id,
            "name": task.name,
        } if task else None,
    }


def _extract_delta_counts(report_text: str) -> dict[str, int]:
    """Extract counts of added, removed, and changed issues from delta text."""
    return {
        "added_issues": len(utils._ADDED_ISSUE_RE.findall(report_text)),
        "removed_issues": len(utils._REMOVED_ISSUE_RE.findall(report_text)),
        "changed_issues": len(utils._CHANGED_ISSUE_RE.findall(report_text)),
    }


def _build_txt_report_output(
    report: models.Report,
    report_text: str | None,
    *,
    include_full_text: bool = True,
    preview_chars: int = 6000,
) -> dict[str, Any] | None:
    if report_text is None:
        return None

    result: dict[str, Any] = {
        "report": _summarize_report_metadata(report),
    }

    if include_full_text:
        result["report_text"] = report_text
    else:
        result["report_text_preview"] = _truncate(report_text, preview_chars)
        result["report_text_truncated"] = len(report_text) > preview_chars

    return result
