from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from src.models.generated.family_count import FamilyCount
from src.models.generated.nvt_count import NvtCount
from src.models.generated.owner import Owner
from src.models.generated.permissions import Permissions


@dataclass(kw_only=True)
class Config:
    class Meta:
        name = "config"

    id: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    owner: None | Owner = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    name: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    comment: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    creation_time: None | XmlDateTime = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    modification_time: None | XmlDateTime = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    writable: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    in_use: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    permissions: None | Permissions = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    family_count: None | FamilyCount = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    nvt_count: None | NvtCount = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    type_value: None | int = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Element",
        },
    )
    usage_type: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    predefined: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    trash: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
