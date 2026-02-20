from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Hosts:
    class Meta:
        name = "hosts"

    count: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
