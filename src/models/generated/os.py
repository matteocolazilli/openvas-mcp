from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Os:
    class Meta:
        name = "os"

    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    title: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    count: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
