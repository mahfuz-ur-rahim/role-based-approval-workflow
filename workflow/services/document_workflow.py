from workflow.models.audit import AuditAction
from workflow.state_machine import (
    DocumentStatus,
    WorkflowAction,
    ActorContext,
    TransitionFailure,
)
from workflow.execution.context import WorkflowExecutionContext

from django.apps import apps
import time

from workflow.observability import WorkflowEventLogger
from workflow.metrics import WorkflowMetrics
from workflow.execution.command import WorkflowCommand
from workflow.engine.engine import WorkflowEngine
from workflow.execution.effects import (
    UpdateDocumentStatus,
    CreateApprovalStep,
    CreateAuditLog,
)
from workflow.engine.sqlite_engine import SQLiteExecutionEngine
import uuid


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

    def __init__(self, *, actor, engine=None):
        # Backward compatible
        self.actor = actor
        self.engine = engine or SQLiteExecutionEngine()

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
            idempotency_key=str(uuid.uuid4()),
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

        action = command.action
        execution_context = command.execution_context

        def _execute(*, document, models):

            ApprovalStep = models["ApprovalStep"]
            AuditLog = models["AuditLog"]

            start_time = WorkflowEventLogger.log_transition_attempt(
                actor_id=execution_context.actor_id,
                document_id=document.id,
                current_status=document.status,
                action=action.name,
            )

            actor_ctx = self._build_actor_context(
                document=document,
                execution_context=execution_context,
            )

            decision = WorkflowEngine.decide(
                current_status=DocumentStatus(document.status),
                action=action,
                actor_context=actor_ctx,
            )

            # FAILURE
            if not decision.allowed:
                latency_ms = (time.monotonic() - start_time) * 1000

                WorkflowEventLogger.log_transition_result(
                    actor_id=execution_context.actor_id,
                    document_id=document.id,
                    action=action.name,
                    allowed=False,
                    failure=decision.failure.name if decision.failure else "UNKNOWN",
                    latency_ms=latency_ms,
                )

                WorkflowMetrics.increment("workflow.transition.failure")
                WorkflowMetrics.record_latency(
                    "workflow.transition.latency_ms",
                    latency_ms,
                )

                if decision.failure == TransitionFailure.PERMISSION:
                    raise PermissionViolationError(decision.reason)

                raise InvalidTransitionError(decision.reason)

            # IDEMPOTENT
            current_status_enum = DocumentStatus(document.status)

            if decision.next_status == current_status_enum:
                latency_ms = (time.monotonic() - start_time) * 1000

                WorkflowEventLogger.log_transition_result(
                    actor_id=execution_context.actor_id,
                    document_id=document.id,
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

            # APPLY EFFECTS
            for effect in decision.effects:
                self._apply_effect(
                    effect=effect,
                    document=document,
                    execution_context=execution_context,
                    ApprovalStep=ApprovalStep,
                    AuditLog=AuditLog,
                )

            latency_ms = (time.monotonic() - start_time) * 1000

            WorkflowEventLogger.log_transition_result(
                actor_id=execution_context.actor_id,
                document_id=document.id,
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

        return self.engine.execute(
            command=command,
            handler=_execute,
        )

    def _apply_effect(
        self,
        *,
        effect,
        document,
        execution_context,
        ApprovalStep,
        AuditLog,
    ):
        """
        Executes a single domain effect.
        This is the only place where side effects occur.
        """

        if isinstance(effect, UpdateDocumentStatus):
            if effect.new_status not in dict(document.Status.choices):
                raise RuntimeError(
                    f"Domain produced invalid status '{effect.new_status}'. "
                    f"Allowed: {list(document.Status.values)}"
                )
            document.status = effect.new_status
            document.save(update_fields=["status", "updated_at"])

        elif isinstance(effect, CreateApprovalStep):
            ApprovalStep.objects.create(
                document=document,
                decided_by_id=execution_context.actor_id,
                status=effect.status,
            )

        elif isinstance(effect, CreateAuditLog):
            AuditLog.log(
                action=effect.action,
                actor=self.actor,
                document=document,
                metadata={"document_id": document.id},
            )
