from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Preference:
    class Meta:
        name = "preference"

    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    scanner_name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: int | str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
