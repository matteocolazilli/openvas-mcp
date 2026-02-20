from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef


@dataclass(kw_only=True)
class PortListCount:
    class Meta:
        name = "port_list_count"

    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "filtered",
                    "type": ForwardRef("PortListCount.Filtered"),
                },
                {
                    "name": "page",
                    "type": ForwardRef("PortListCount.Page"),
                },
                {
                    "type": ForwardRef("PortListCount.Value"),
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
