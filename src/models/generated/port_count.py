from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class PortCount:
    class Meta:
        name = "port_count"

    all: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    tcp: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    udp: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
