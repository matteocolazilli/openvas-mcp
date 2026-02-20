from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.port_range import PortRange


@dataclass(kw_only=True)
class PortRanges:
    class Meta:
        name = "port_ranges"

    port_range: list[PortRange] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
