from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.permission import Permission


@dataclass(kw_only=True)
class Permissions:
    class Meta:
        name = "permissions"

    permission: list[Permission] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
