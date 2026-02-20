from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.filters import Filters
from src.models.generated.info import Report
from src.models.generated.report_count import ReportCount
from src.models.generated.reports import Reports
from src.models.generated.sort import Sort


@dataclass(kw_only=True)
class GetReportsResponse:
    class Meta:
        name = "get_reports_response"

    status: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    status_text: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    report: list[Report] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
    filters: Filters = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    sort: Sort = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    reports: Reports = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    report_count: ReportCount = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
