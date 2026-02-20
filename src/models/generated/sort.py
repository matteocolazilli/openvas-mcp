from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.field_mod import FieldType


@dataclass(kw_only=True)
class Sort:
    class Meta:
        name = "sort"

    field_value: FieldType = field(
        metadata={
            "name": "field",
            "type": "Element",
            "required": True,
        }
    )
