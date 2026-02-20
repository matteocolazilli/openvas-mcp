from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Scanners:
    class Meta:
        name = "scanners"

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
