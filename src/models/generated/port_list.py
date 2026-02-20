from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from src.models.generated.owner import Owner
from src.models.generated.permissions import Permissions
from src.models.generated.port_count import PortCount
from src.models.generated.port_ranges import PortRanges


@dataclass(kw_only=True)
class PortList:
    class Meta:
        name = "port_list"

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
    port_count: None | PortCount = field(
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
    port_ranges: None | PortRanges = field(
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
