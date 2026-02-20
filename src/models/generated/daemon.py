from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Daemon:
    class Meta:
        name = "daemon"

    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    version: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
