# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Matteo Colazilli

"""Internal helper functions for vulnerability scan tools."""

import base64 as b64
import re
from typing import Any

from xsdata.models.datatype import XmlDateTime

import src.models.generated as models

# Regex to check if a string could be Base64-encoded (only contains valid chars and whitespace)
_BASE64_CHARS_RE = re.compile(r"^[A-Za-z0-9+/=\s]+$")

# These regexes are used to extract summary counts of added/removed/changed issues from delta report text.
_ADDED_ISSUE_RE = re.compile(r"(?m)^\+\s+Added Issue\s*$")
_REMOVED_ISSUE_RE = re.compile(r"(?m)^-\s+Removed Issue\s*$")
_CHANGED_ISSUE_RE = re.compile(r"(?im)^(?:\*|~)\s+Changed Issue\s*$")


def _default_target_name(hosts: list[str]) -> str:
    """Generate a default target name from a list of hosts.

    Args:
        hosts (list[str]): Host entries (IP addresses, CIDRs, ranges, or DNS
            names).

    Returns:
        str: A generated target name suitable for display.
    """
    if len(hosts) == 1:
        return f"{hosts[0]}"
    if len(hosts) <= 3:
        return ", ".join(sorted(hosts))
    return f"{len(hosts)} hosts"


def _summarize_task_status(task: models.Task) -> dict[str, Any]:
    """Build a compact task status summary.

    Args:
        task (models.Task): Task model returned by the GVM API.

    Returns:
        dict[str, Any]: A dictionary containing task status/progress
        information and target details when available.
    """
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
    """Recursively remove ``None`` values from nested containers.

    Args:
        obj (Any): Dictionary, list, or scalar value to sanitize.

    Returns:
        Any: The same logical structure with ``None`` values removed from
        nested dictionaries and lists.
    """
    if isinstance(obj, dict):
        return {k: _remove_none_values(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_remove_none_values(v) for v in obj if v is not None]
    return obj


def _truncate(text: str | None, max_chars: int) -> str | None:
    """Truncate text to a maximum length.

    Args:
        text (str | None): Input text to truncate. ``None`` is returned
            unchanged.
        max_chars (int): Maximum output length in characters.

    Returns:
        str | None: The original text if no truncation is needed, otherwise a
        truncated string with a trailing ellipsis.
    """
    if text is None:
        return None
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _extract_report_content_item(
    report: models.Report | None,
    item_type: type[Any],
) -> Any | None:
    """Extract the first report content item matching a given type.

    Args:
        report (models.Report | None): Report model containing mixed content
            items.
        item_type (type[Any]): Content item type to search for.

    Returns:
        Any | None: The first matching content item, or ``None`` if the report
        is ``None`` or no matching item is present.
    """
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
    """Extract a datetime-like value from a typed report content item.

    Args:
        report (models.Report | None): Report model containing mixed content
            items.
        item_type (type[Any] | None): Content item type whose ``value``
            attribute should be read.

    Returns:
        str | None: The extracted value converted to ``str``, or ``None`` when
        the item type is not provided, the item is missing, or the item has no
        value.
    """
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
    """Decode a report text blob that may be Base64-encoded.

    The function returns plain text unchanged when the payload does not look
    like Base64.

    Args:
        blob (str): Raw report text payload.

    Returns:
        str: UTF-8 decoded report text.

    Raises:
        ValueError: If the payload looks like Base64 but has invalid padding or
            cannot be decoded.
    """
    stripped = blob.strip()
    if not stripped:
        return ""

    if not _BASE64_CHARS_RE.fullmatch(stripped):
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
    """Extract and decode the main textual payload from a report.

    Args:
        report (models.Report): Report model containing mixed content items.

    Returns:
        str | None: The decoded textual payload, or ``None`` if no text payload
        is present.
    """
    text_chunks = [
        item for item in report.content if isinstance(item, str) and item.strip()
    ]
    if not text_chunks:
        return None
    blob = max(text_chunks, key=lambda value: len(value.strip()))
    return _decode_report_text_blob(blob)


def _summarize_report_metadata(report: models.Report | None) -> dict[str, Any] | None:
    """Build a compact metadata summary for a report.

    Args:
        report (models.Report | None): Report model to summarize.

    Returns:
        dict[str, Any] | None: A metadata dictionary containing report
        timestamps and task identity, or ``None`` if no report is provided.
    """
    if report is None:
        return None

    task: models.Task | None = _extract_report_content_item(report, models.Task)
    creation_time = _extract_report_content_item(report, report.CreationTime)
    scan_start = _extract_report_datetime(report, report.ScanStart)
    scan_end = _extract_report_datetime(report, report.ScanEnd)

    return {
        "id": report.id,
        "created_at": str(creation_time.value) if creation_time else None,
        "scan_start": scan_start,
        "scan_end": scan_end,
        "task": {
            "id": task.id,
            "name": task.name,
        }
        if task
        else None,
    }


def _extract_delta_counts(report_text: str) -> dict[str, int]:
    """Extract issue-change counters from a delta report text.

    Args:
        report_text (str): Raw delta report text.

    Returns:
        dict[str, int]: A dictionary with counts for added, removed, and changed
        issues.
    """
    return {
        "added_issues": len(_ADDED_ISSUE_RE.findall(report_text)),
        "removed_issues": len(_REMOVED_ISSUE_RE.findall(report_text)),
        "changed_issues": len(_CHANGED_ISSUE_RE.findall(report_text)),
    }


def _build_txt_report_output(
    report: models.Report,
    report_text: str | None,
    *,
    include_full_text: bool = True,
    preview_chars: int = 6000,
) -> dict[str, Any] | None:
    """Build a normalized TXT report output payload.

    Args:
        report (models.Report): Report model used to extract metadata.
        report_text (str | None): Decoded TXT report content.
        include_full_text (bool): Whether to include the full report text
            instead of a preview.
        preview_chars (int): Maximum preview length when
            ``include_full_text`` is ``False``.

    Returns:
        dict[str, Any] | None: A dictionary containing report metadata and
        either the full report text or a preview, or ``None`` if
        ``report_text`` is missing.
    """
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
