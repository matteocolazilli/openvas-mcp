from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Gmp:
    class Meta:
        name = "gmp"

    version: float = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
