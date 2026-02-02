from enum import Enum
from dataclasses import dataclass


class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class WorkflowAction(str, Enum):
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class TransitionResult:
    allowed: bool
    reason: str | None = None
    next_status: DocumentStatus | None = None


@dataclass(frozen=True)
class ActorContext:
    is_owner: bool
    is_manager: bool
    is_admin: bool


def evaluate_transition(
    *,
    current_status: DocumentStatus,
    action: WorkflowAction,
    actor: ActorContext,
) -> TransitionResult:
    """
    Pure decision function.
    No side effects. No I/O.
    """

    # ---- SUBMIT ----
    if action == WorkflowAction.SUBMIT:
        if current_status != DocumentStatus.DRAFT:
            return TransitionResult(
                allowed=False,
                reason="Only draft documents can be submitted",
            )
        if not actor.is_owner:
            return TransitionResult(
                allowed=False,
                reason="Only the document owner can submit",
            )
        return TransitionResult(
            allowed=True,
            next_status=DocumentStatus.SUBMITTED,
        )

    # ---- APPROVE ----
    if action == WorkflowAction.APPROVE:
        if current_status != DocumentStatus.SUBMITTED:
            return TransitionResult(
                allowed=False,
                reason="Only submitted documents can be approved",
            )
        if actor.is_owner:
            return TransitionResult(
                allowed=False,
                reason="Self-approval is not allowed",
            )
        if not (actor.is_manager or actor.is_admin):
            return TransitionResult(
                allowed=False,
                reason="Only managers or admins may approve",
            )
        return TransitionResult(
            allowed=True,
            next_status=DocumentStatus.APPROVED,
        )

    # ---- REJECT ----
    if action == WorkflowAction.REJECT:
        if current_status != DocumentStatus.SUBMITTED:
            return TransitionResult(
                allowed=False,
                reason="Only submitted documents can be rejected",
            )
        if actor.is_owner:
            return TransitionResult(
                allowed=False,
                reason="Self-rejection is not allowed",
            )
        if not (actor.is_manager or actor.is_admin):
            return TransitionResult(
                allowed=False,
                reason="Only managers or admins may reject",
            )
        return TransitionResult(
            allowed=True,
            next_status=DocumentStatus.REJECTED,
        )

    # ---- FALLBACK ----
    return TransitionResult(
        allowed=False,
        reason="Unknown workflow action",
    )
