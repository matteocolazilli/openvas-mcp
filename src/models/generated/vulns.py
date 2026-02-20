from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Vulns:
    class Meta:
        name = "vulns"

    count: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
