from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class PortRange:
    class Meta:
        name = "port_range"

    id: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    start: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    end: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    type_value: str = field(
        metadata={
            "name": "type",
            "type": "Element",
            "required": True,
        }
    )
    comment: None | object = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
