from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class ReportFormat:
    class Meta:
        name = "report_format"

    id: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
