from enum import Enum
from dataclasses import dataclass

class TransitionFailure(Enum):
    PERMISSION = "permission"
    INVALID_STATE = "invalid_state"
    IDEMPOTENT_REPLAY = "idempotent_replay"

class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class WorkflowAction(str, Enum):
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"

"""
TransitionResult is a pure, side-effect-free evaluation outcome.

Contract guarantees:
- allowed == True  => next_status is not None, failure is None
- allowed == False => next_status is None, failure is not None
- reason is stable and user-facing
- evaluate_transition() MUST NOT mutate state or touch the database
"""

@dataclass(frozen=True)
class TransitionResult:
    allowed: bool
    next_status: DocumentStatus | None = None
    failure: TransitionFailure | None = None
    reason: str | None = None

@dataclass(frozen=True)
class ActorContext:
    is_owner: bool
    is_manager: bool
    is_admin: bool

def _finalize(result: TransitionResult) -> TransitionResult:
    if result.allowed:
        assert result.next_status is not None
        assert result.failure is None
    else:
        assert result.next_status is None
        assert result.failure is not None
    return result

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
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Only draft documents can be submitted",
                    failure=TransitionFailure.INVALID_STATE,
                )
            )
        if not actor.is_owner:
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Only the document owner can submit",
                    failure=TransitionFailure.PERMISSION,
                )
            )
        return _finalize(
            TransitionResult(
                allowed=True,
                next_status=DocumentStatus.SUBMITTED,
            )
        )

    # ---- APPROVE ----
    if action == WorkflowAction.APPROVE:
        if current_status != DocumentStatus.SUBMITTED:
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Only submitted documents can be approved",
                    failure=TransitionFailure.INVALID_STATE,
                )
            )
        if actor.is_owner:
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Self-approval is not allowed",
                    failure=TransitionFailure.PERMISSION,
                )
            )
        if not (actor.is_manager or actor.is_admin):
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Only managers or admins may approve",
                    failure=TransitionFailure.PERMISSION,
                )
            )
        return _finalize(
            TransitionResult(
                allowed=True,
                next_status=DocumentStatus.APPROVED,
            )
        )

    # ---- REJECT ----
    if action == WorkflowAction.REJECT:
        if current_status != DocumentStatus.SUBMITTED:
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Only submitted documents can be rejected",
                    failure=TransitionFailure.INVALID_STATE,
                )
            )
        if actor.is_owner:
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Self-rejection is not allowed",
                    failure=TransitionFailure.PERMISSION,
                )
            )
        if not (actor.is_manager or actor.is_admin):
            return _finalize(
                TransitionResult(
                    allowed=False,
                    reason="Only managers or admins may reject",
                    failure=TransitionFailure.PERMISSION,
                )
            )
        return _finalize(
            TransitionResult(
                allowed=True,
                next_status=DocumentStatus.REJECTED,
            )
        )

    # ---- FALLBACK ----
    return _finalize(
        TransitionResult(
            allowed=False,
            reason="Unknown workflow action",
            failure=TransitionFailure.INVALID_STATE,
        )
    )
