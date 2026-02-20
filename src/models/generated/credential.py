from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Credential:
    class Meta:
        name = "credential"

    id: object = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    name: None | object = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    type_value: None | object = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Element",
        },
    )
    trash: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
