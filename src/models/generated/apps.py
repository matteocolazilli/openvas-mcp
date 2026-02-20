from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Apps:
    class Meta:
        name = "apps"

    count: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
