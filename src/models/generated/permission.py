from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Permission:
    class Meta:
        name = "permission"

    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
