from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class StartTaskResponse:
    class Meta:
        name = "start_task_response"

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
    report_id: str = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
