from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Medium:
    class Meta:
        name = "medium"

    full: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    filtered: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
