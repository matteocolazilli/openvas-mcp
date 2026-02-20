from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from src.models.generated.alive_tests import AliveTests
from src.models.generated.esxi_credential import EsxiCredential
from src.models.generated.krb5_credential import Krb5Credential
from src.models.generated.owner import Owner
from src.models.generated.permissions import Permissions
from src.models.generated.port_list import PortList
from src.models.generated.smb_credential import SmbCredential
from src.models.generated.snmp_credential import SnmpCredential
from src.models.generated.ssh_credential import SshCredential
from src.models.generated.ssh_elevate_credential import SshElevateCredential


@dataclass(kw_only=True)
class Target:
    class Meta:
        name = "target"

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
    trash: None | int = field(
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
    comment: None | object = field(
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
    hosts: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    exclude_hosts: None | object = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    max_hosts: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    port_list: None | PortList = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ssh_credential: None | SshCredential = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    smb_credential: None | SmbCredential = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    esxi_credential: None | EsxiCredential = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    snmp_credential: None | SnmpCredential = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ssh_elevate_credential: None | SshElevateCredential = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    krb5_credential: None | Krb5Credential = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    reverse_lookup_only: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    reverse_lookup_unify: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    allow_simultaneous_ips: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    alive_tests: None | AliveTests = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
