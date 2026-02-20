from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class CreateTaskResponse:
    class Meta:
        name = "create_task_response"

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
    id: str = field(
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
