from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Schedule:
    class Meta:
        name = "schedule"

    id: object = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    name: None | object = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    trash: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
