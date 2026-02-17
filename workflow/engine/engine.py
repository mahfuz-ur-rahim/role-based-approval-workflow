from dataclasses import dataclass
from workflow.state_machine import (
    DocumentStatus,
    TransitionFailure,
    evaluate_transition,
)


@dataclass(frozen=True)
class WorkflowDecision:
    allowed: bool
    next_status: DocumentStatus | None
    failure: TransitionFailure | None
    reason: str | None


class WorkflowEngine:
    """
    Pure domain engine.
    No ORM.
    No logging.
    No metrics.
    """

    @staticmethod
    def decide(
        *,
        current_status: DocumentStatus,
        action,
        actor_context,
    ) -> WorkflowDecision:

        result = evaluate_transition(
            current_status=current_status,
            action=action,
            actor=actor_context,
        )

        if not result.allowed:
            return WorkflowDecision(
                allowed=False,
                next_status=None,
                failure=result.failure,
                reason=result.reason,
            )

        return WorkflowDecision(
            allowed=True,
            next_status=result.next_status,
            failure=None,
            reason=None,
        )
