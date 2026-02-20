from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.source import Source


@dataclass(kw_only=True)
class Detail:
    class Meta:
        name = "detail"

    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    source: Source = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
