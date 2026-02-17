from dataclasses import dataclass
from workflow.state_machine import WorkflowAction
from workflow.execution.context import WorkflowExecutionContext


@dataclass(frozen=True)
class WorkflowCommand:
    """
    Represents a single workflow execution intent.

    Engine-level input contract.
    """

    aggregate_type: str
    aggregate_id: int
    action: WorkflowAction
    execution_context: WorkflowExecutionContext
