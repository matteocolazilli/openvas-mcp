from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef


@dataclass(kw_only=True)
class FieldType:
    class Meta:
        name = "field"

    content: list[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "order",
                    "type": ForwardRef("FieldType.Order"),
                },
                {
                    "type": ForwardRef("FieldType.Value"),
                },
            ),
        },
    )

    @dataclass(kw_only=True)
    class Order:
        value: str = field(
            default="",
            metadata={
                "required": True,
            },
        )

    @dataclass(kw_only=True)
    class Value:
        value: str = field(
            default="",
            metadata={
                "required": True,
            },
        )
