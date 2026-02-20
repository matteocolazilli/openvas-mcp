from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Protocol:
    class Meta:
        name = "protocol"

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
