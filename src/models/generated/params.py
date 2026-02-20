from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.param import Param


@dataclass(kw_only=True)
class Params:
    class Meta:
        name = "params"

    param: list[Param] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
