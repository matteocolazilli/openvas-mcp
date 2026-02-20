from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Param:
    class Meta:
        name = "param"

    id: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    default: int | str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    description: str = field(
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
    mandatory: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
