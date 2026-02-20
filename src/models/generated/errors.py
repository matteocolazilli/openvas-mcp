from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.error import Error


@dataclass(kw_only=True)
class Errors:
    class Meta:
        name = "errors"

    count: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    error: list[Error] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
