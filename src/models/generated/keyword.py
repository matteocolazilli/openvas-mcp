from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Keyword:
    class Meta:
        name = "keyword"

    column: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    relation: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: str | int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
