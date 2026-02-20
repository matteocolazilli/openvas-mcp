from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Log:
    class Meta:
        name = "log"

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
