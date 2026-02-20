from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.keywords import Keywords


@dataclass(kw_only=True)
class Filters:
    class Meta:
        name = "filters"

    id: object = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    term: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    filter: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    keywords: Keywords = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
