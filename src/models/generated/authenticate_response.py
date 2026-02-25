from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class AuthenticateResponse:
    class Meta:
        name = "authenticate_response"

    status: int = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    status_text: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    role: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    timezone: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
