from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.preference import Preference


@dataclass(kw_only=True)
class Preferences:
    class Meta:
        name = "preferences"

    preference: list[Preference] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
