from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Warning:
    class Meta:
        name = "warning"

    deprecated: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    full: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    filtered: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    value: None | int = field(default=None)
