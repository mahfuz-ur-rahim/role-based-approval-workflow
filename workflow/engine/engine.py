from dataclasses import dataclass
from workflow.state_machine import (
    DocumentStatus,
    TransitionFailure,
    evaluate_transition,
)
from workflow.execution.effects import (
    UpdateDocumentStatus,
    CreateApprovalStep,
    CreateAuditLog,
)
from workflow.models.audit import AuditAction


@dataclass(frozen=True)
class WorkflowDecision:
    allowed: bool
    next_status: DocumentStatus | None
    failure: TransitionFailure | None
    reason: str | None
    effects: tuple = ()   # ← NEW FIELD


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

        # ----------------------------------------
        # FAILURE → no effects
        # ----------------------------------------

        if not result.allowed:
            return WorkflowDecision(
                allowed=False,
                next_status=None,
                failure=result.failure,
                reason=result.reason,
                effects=(),  # ← explicit
            )

        # ----------------------------------------
        # SUCCESS → produce declarative effects
        # ----------------------------------------

        effects = []

        # 1️⃣ Always update status
        effects.append(
            UpdateDocumentStatus(result.next_status.value)  # type: ignore
        )

        # 2️⃣ Approval / rejection creates step
        if action.name in ("APPROVE", "REJECT"):
            effects.append(
                CreateApprovalStep(result.next_status.value)   # type: ignore
            )

        # 3️⃣ Audit action mapping
        audit_map = {
            "SUBMIT": AuditAction.DOCUMENT_SUBMITTED,
            "APPROVE": AuditAction.DOCUMENT_APPROVED,
            "REJECT": AuditAction.DOCUMENT_REJECTED,
        }

        effects.append(
            CreateAuditLog(audit_map[action.name])
        )

        return WorkflowDecision(
            allowed=True,
            next_status=result.next_status,
            failure=None,
            reason=None,
            effects=tuple(effects),  # ← immutable
        )
