class WorkflowError(Exception):
    """Base workflow exception"""


class InvalidTransitionError(WorkflowError):
    pass


class PermissionViolationError(WorkflowError):
    pass


from django.db import transaction
from django.apps import apps

from workflow.state_machine import (
    DocumentStatus,
    WorkflowAction,
    ActorContext,
    TransitionFailure,
    evaluate_transition,
)

from workflow.models.audit import AuditAction


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

            actor_ctx = self._actor_context(document)

            result = evaluate_transition(
                current_status=DocumentStatus(document.status),
                action=action,
                actor=actor_ctx,
            )

            if not result.allowed:
                if result.failure == TransitionFailure.PERMISSION:
                    raise PermissionViolationError(result.reason)
                raise InvalidTransitionError(result.reason)
            
            if result.next_status.value == document.status:
                raise InvalidTransitionError(
                    "Idempotent replay: transition already applied"
                )

            # ---- APPLY MUTATION ----
            document.status = result.next_status.value
            document.save(update_fields=["status", "updated_at"])

            # ---- APPROVAL STEP ----
            if action in (WorkflowAction.APPROVE, WorkflowAction.REJECT):
                ApprovalStep.objects.create(
                    document=document,
                    decided_by=self.actor,
                    status=document.status,
                )

            # ---- AUDIT LOG (EXACTLY ONE) ----
            AuditLog.log(
                action={
                    WorkflowAction.SUBMIT: AuditAction.DOCUMENT_SUBMITTED,
                    WorkflowAction.APPROVE: AuditAction.DOCUMENT_APPROVED,
                    WorkflowAction.REJECT: AuditAction.DOCUMENT_REJECTED,
                }[action],
                actor=self.actor,
                document=document,
                metadata={"document_id": document.id},
            )

            return document
