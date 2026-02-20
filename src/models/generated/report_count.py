from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef


@dataclass(kw_only=True)
class ReportCount:
    class Meta:
        name = "report_count"

    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "filtered",
                    "type": ForwardRef("ReportCount.Filtered"),
                },
                {
                    "name": "page",
                    "type": ForwardRef("ReportCount.Page"),
                },
                {
                    "name": "finished",
                    "type": ForwardRef("ReportCount.Finished"),
                },
                {
                    "type": ForwardRef("ReportCount.Value"),
                },
            ),
        },
    )

    @dataclass(kw_only=True)
    class Filtered:
        value: int = field(
            metadata={
                "required": True,
            }
        )

    @dataclass(kw_only=True)
    class Page:
        value: int = field(
            metadata={
                "required": True,
            }
        )

    @dataclass(kw_only=True)
    class Finished:
        value: int = field(
            metadata={
                "required": True,
            }
        )

    @dataclass(kw_only=True)
    class Value:
        value: int = field(
            metadata={
                "required": True,
            }
        )
