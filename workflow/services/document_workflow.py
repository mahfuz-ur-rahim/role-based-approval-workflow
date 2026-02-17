from workflow.models.audit import AuditAction
from workflow.state_machine import (
    DocumentStatus,
    WorkflowAction,
    ActorContext,
    TransitionFailure,
    evaluate_transition,
)
from workflow.execution.context import WorkflowExecutionContext

from django.apps import apps
from django.db import transaction
import time

from workflow.observability import WorkflowEventLogger
from workflow.metrics import WorkflowMetrics
from workflow.execution.command import WorkflowCommand


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
        # Public contract unchanged
        self.actor = actor

    # -------------------------------------------------
    # Public API (UNCHANGED)
    # -------------------------------------------------

    def perform(self, *, document_id: int, action: WorkflowAction):

        execution_context = WorkflowExecutionContext(
            actor_id=self.actor.id,
            actor_roles=list(
                self.actor.groups.values_list("name", flat=True)
            ),
            source="ui",
            correlation_id=None,
        )

        command = WorkflowCommand(
            aggregate_type="document",
            aggregate_id=document_id,
            action=action,
            execution_context=execution_context,
        )

        return self._handle_command(command)

    # -------------------------------------------------
    # Internal Engine Boundary
    # -------------------------------------------------

    def _build_actor_context(
        self,
        *,
        document,
        execution_context: WorkflowExecutionContext,
    ) -> ActorContext:
        roles = set(execution_context.actor_roles)

        return ActorContext(
            is_owner=document.created_by_id == execution_context.actor_id,
            is_manager="Manager" in roles,
            is_admin="Admin" in roles,
        )

    def _handle_command(self, command: WorkflowCommand):
        """
        Internal execution boundary.
        All mutation logic lives here.
        """
        document_id = command.aggregate_id
        action = command.action
        execution_context = command.execution_context

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
                actor_id=execution_context.actor_id,
                document_id=document.id,  # type: ignore
                current_status=document.status,  # type: ignore
                action=action.name,
            )

            actor_ctx = self._build_actor_context(
                document=document,
                execution_context=execution_context,
            )

            result = evaluate_transition(
                current_status=DocumentStatus(document.status),  # type: ignore
                action=action,
                actor=actor_ctx,
            )

            # -------------------------------------------------
            # FAILURE PATH
            # -------------------------------------------------

            if not result.allowed:
                latency_ms = (time.monotonic() - start_time) * 1000

                WorkflowEventLogger.log_transition_result(
                    actor_id=execution_context.actor_id,
                    document_id=document.id,  # type: ignore
                    action=action.name,
                    allowed=False,
                    failure=result.failure.name if result.failure else "UNKNOWN",
                    latency_ms=latency_ms,
                )

                WorkflowMetrics.increment("workflow.transition.failure")
                WorkflowMetrics.record_latency(
                    "workflow.transition.latency_ms",
                    latency_ms,
                )

                if result.failure == TransitionFailure.PERMISSION:
                    raise PermissionViolationError(result.reason)

                raise InvalidTransitionError(result.reason)

            # -------------------------------------------------
            # IDEMPOTENT REPLAY PROTECTION
            # -------------------------------------------------

            if result.next_status.value == document.status:  # type: ignore
                latency_ms = (time.monotonic() - start_time) * 1000

                WorkflowEventLogger.log_transition_result(
                    actor_id=execution_context.actor_id,
                    document_id=document.id,  # type: ignore
                    action=action.name,
                    allowed=False,
                    failure="IDEMPOTENT_REPLAY",
                    latency_ms=latency_ms,
                )

                WorkflowMetrics.increment("workflow.transition.failure")
                WorkflowMetrics.record_latency(
                    "workflow.transition.latency_ms",
                    latency_ms,
                )

                raise InvalidTransitionError(
                    "Idempotent replay: transition already applied"
                )

            # -------------------------------------------------
            # APPLY MUTATION
            # -------------------------------------------------

            document.status = result.next_status.value  # type: ignore
            document.save(update_fields=["status", "updated_at"])

            # -------------------------------------------------
            # APPROVAL STEP
            # -------------------------------------------------

            if action in (WorkflowAction.APPROVE, WorkflowAction.REJECT):
                ApprovalStep.objects.create(
                    document=document,
                    decided_by_id=execution_context.actor_id,
                    status=document.status,  # type: ignore
                )

            # -------------------------------------------------
            # AUDIT LOG (EXACTLY ONE)
            # -------------------------------------------------

            AuditLog.log(  # type: ignore
                action={
                    WorkflowAction.SUBMIT: AuditAction.DOCUMENT_SUBMITTED,
                    WorkflowAction.APPROVE: AuditAction.DOCUMENT_APPROVED,
                    WorkflowAction.REJECT: AuditAction.DOCUMENT_REJECTED,
                }[action],
                actor=self.actor,  # ← restore original contract
                document=document,
                metadata={"document_id": document.id},  # type: ignore
            )

            # -------------------------------------------------
            # SUCCESS LOGGING + METRICS
            # -------------------------------------------------

            latency_ms = (time.monotonic() - start_time) * 1000

            WorkflowEventLogger.log_transition_result(
                actor_id=execution_context.actor_id,
                document_id=document.id,  # type: ignore
                action=action.name,
                allowed=True,
                failure=None,
                latency_ms=latency_ms,
            )

            WorkflowMetrics.increment("workflow.transition.success")
            WorkflowMetrics.record_latency(
                "workflow.transition.latency_ms",
                latency_ms,
            )

            return document
