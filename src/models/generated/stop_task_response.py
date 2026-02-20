from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class StopTaskResponse:
    class Meta:
        name = "stop_task_response"

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
