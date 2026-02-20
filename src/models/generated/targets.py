from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Targets:
    class Meta:
        name = "targets"

    start: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    max: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
