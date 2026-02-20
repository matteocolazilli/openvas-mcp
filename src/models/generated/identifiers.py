from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.identifier import Identifier


@dataclass(kw_only=True)
class Identifiers:
    class Meta:
        name = "identifiers"

    identifier: list[Identifier] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
