from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class SslCerts:
    class Meta:
        name = "ssl_certs"

    count: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
