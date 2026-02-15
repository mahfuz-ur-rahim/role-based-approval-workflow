from workflow.models.audit import AuditAction
from workflow.state_machine import (
    DocumentStatus,
    WorkflowAction,
    ActorContext,
    TransitionFailure,
    evaluate_transition,
)
from django.apps import apps
from django.db import transaction
import time
from workflow.observability import WorkflowEventLogger


class WorkflowError(Exception):
    """Base workflow exception"""


class InvalidTransitionError(WorkflowError):
    pass


class PermissionViolationError(WorkflowError):
    pass


class DocumentWorkflowService:
    """
    Single authority for document state mutations.
    """

    def __init__(self, *, actor):
        self.actor = actor

    def _actor_context(self, document):
        groups = set(self.actor.groups.values_list("name", flat=True))
        return ActorContext(
            is_owner=document.created_by_id == self.actor.id,
            is_manager="Manager" in groups,
            is_admin="Admin" in groups or self.actor.is_superuser,
        )

    def perform(self, *, document_id: int, action: WorkflowAction):
        Document = apps.get_model("workflow", "Document")
        ApprovalStep = apps.get_model("workflow", "ApprovalStep")
        AuditLog = apps.get_model("workflow", "AuditLog")

        with transaction.atomic():
            document = (
                Document.objects
                .select_for_update()
                .get(pk=document_id)
            )
            start_time = WorkflowEventLogger.log_transition_attempt(
                actor_id=self.actor.id,
                document_id=document.id,  # type: ignore
                current_status=document.status,  # type: ignore
                action=action.name,
            )

            actor_ctx = self._actor_context(document)

            result = evaluate_transition(
                current_status=DocumentStatus(document.status),  # type: ignore
                action=action,
                actor=actor_ctx,
            )

            if not result.allowed:
                latency_ms = (time.monotonic() - start_time) * 1000

                WorkflowEventLogger.log_transition_result(
                    actor_id=self.actor.id,
                    document_id=document.id,  # type: ignore
                    action=action.name,
                    allowed=False,
                    failure=result.failure.name if result.failure else "UNKNOWN",
                    latency_ms=latency_ms,
                )

                if result.failure == TransitionFailure.PERMISSION:
                    raise PermissionViolationError(result.reason)
                raise InvalidTransitionError(result.reason)

            if result.next_status.value == document.status:  # type: ignore
                latency_ms = (time.monotonic() - start_time) * 1000

                WorkflowEventLogger.log_transition_result(
                    actor_id=self.actor.id,
                    document_id=document.id,  # type: ignore
                    action=action.name,
                    allowed=False,
                    failure="IDEMPOTENT_REPLAY",
                    latency_ms=latency_ms,
                )

                raise InvalidTransitionError(
                    "Idempotent replay: transition already applied"
                )

            # ---- APPLY MUTATION ----
            document.status = result.next_status.value  # type: ignore
            document.save(update_fields=["status", "updated_at"])

            # ---- APPROVAL STEP ----
            if action in (WorkflowAction.APPROVE, WorkflowAction.REJECT):
                ApprovalStep.objects.create(
                    document=document,
                    decided_by=self.actor,
                    status=document.status,  # type: ignore
                )

            # ---- AUDIT LOG (EXACTLY ONE) ----
            AuditLog.log(  # type: ignore
                action={
                    WorkflowAction.SUBMIT: AuditAction.DOCUMENT_SUBMITTED,
                    WorkflowAction.APPROVE: AuditAction.DOCUMENT_APPROVED,
                    WorkflowAction.REJECT: AuditAction.DOCUMENT_REJECTED,
                }[action],
                actor=self.actor,
                document=document,
                metadata={"document_id": document.id},  # type: ignore
            )

            latency_ms = (time.monotonic() - start_time) * 1000

            WorkflowEventLogger.log_transition_result(
                actor_id=self.actor.id,
                document_id=document.id,  # type: ignore
                action=action.name,
                allowed=True,
                failure=None,
                latency_ms=latency_ms,
            )

            return document
