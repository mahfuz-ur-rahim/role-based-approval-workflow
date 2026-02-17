from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class WorkflowExecutionContext:
    """
    Execution-scoped metadata passed into the workflow engine boundary.

    Decouples execution from Django request/user objects.
    """

    actor_id: int
    actor_roles: Iterable[str]
    source: str = "ui"  # ui | api | system
    correlation_id: Optional[str] = None
