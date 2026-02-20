from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Nvt:
    class Meta:
        name = "nvt"

    oid: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    type_value: str = field(
        metadata={
            "name": "type",
            "type": "Element",
            "required": True,
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    cvss_base: float = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
