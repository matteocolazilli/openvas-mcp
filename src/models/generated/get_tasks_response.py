from __future__ import annotations

from dataclasses import dataclass, field

from src.models.generated.filters import Filters
from src.models.generated.info import (
    Task,
    Tasks,
)
from src.models.generated.sort import Sort
from src.models.generated.task_count import TaskCount


@dataclass(kw_only=True)
class GetTasksResponse:
    class Meta:
        name = "get_tasks_response"

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
    apply_overrides: int = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    task: list[Task] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
    filters: Filters = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    sort: Sort = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    tasks: Tasks = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    task_count: TaskCount = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
