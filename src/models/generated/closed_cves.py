from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class ClosedCves:
    class Meta:
        name = "closed_cves"

    count: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
