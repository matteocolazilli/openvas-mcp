from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class SnmpCredential:
    class Meta:
        name = "snmp_credential"

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
    trash: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
