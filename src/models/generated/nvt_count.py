from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef


@dataclass(kw_only=True)
class NvtCount:
    class Meta:
        name = "nvt_count"

    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "growing",
                    "type": ForwardRef("NvtCount.Growing"),
                },
                {
                    "type": ForwardRef("NvtCount.Value"),
                },
            ),
        },
    )

    @dataclass(kw_only=True)
    class Growing:
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
