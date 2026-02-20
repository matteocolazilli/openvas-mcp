from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Owner:
    class Meta:
        name = "owner"

    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
