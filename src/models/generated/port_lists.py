from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class PortLists:
    class Meta:
        name = "port_lists"

    start: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    max: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
