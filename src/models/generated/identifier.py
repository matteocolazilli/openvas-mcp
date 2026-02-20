from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from src.models.generated.os import Os
from src.models.generated.source import Source


@dataclass(kw_only=True)
class Identifier:
    class Meta:
        name = "identifier"

    id: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
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
    creation_time: XmlDateTime = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    modification_time: XmlDateTime = field(
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
    os: None | Os = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
