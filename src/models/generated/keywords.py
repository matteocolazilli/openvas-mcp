from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.keyword import Keyword


@dataclass(kw_only=True)
class Keywords:
    class Meta:
        name = "keywords"

    keyword: list[Keyword] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
