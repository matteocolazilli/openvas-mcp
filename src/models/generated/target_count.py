from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef


@dataclass(kw_only=True)
class TargetCount:
    class Meta:
        name = "target_count"

    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "filtered",
                    "type": ForwardRef("TargetCount.Filtered"),
                },
                {
                    "name": "page",
                    "type": ForwardRef("TargetCount.Page"),
                },
                {
                    "type": ForwardRef("TargetCount.Value"),
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
    class Value:
        value: int = field(
            metadata={
                "required": True,
            }
        )
