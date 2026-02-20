from django.db import transaction, DatabaseError
from django.apps import apps
from .base import WorkflowExecutionEngine


class EngineExecutionError(Exception):
    """Raised only for infrastructure-level engine failures."""


class SQLiteExecutionEngine(WorkflowExecutionEngine):

    def run(self, *, command, handler):
        return self.execute(command=command, handler=handler)

    def execute(self, *, command, handler):

        Document = apps.get_model("workflow", "Document")
        ApprovalStep = apps.get_model("workflow", "ApprovalStep")
        AuditLog = apps.get_model("workflow", "AuditLog")

        try:
            with transaction.atomic():
                document = (
                    Document.objects
                    .select_for_update()
                    .get(pk=command.aggregate_id)
                )

                return handler(
                    document=document,
                    models={
                        "ApprovalStep": ApprovalStep,
                        "AuditLog": AuditLog,
                    },
                )

        except DatabaseError as e:
            # Only wrap infrastructure/database failures
            raise EngineExecutionError(
                f"Database failure during workflow execution: {str(e)}"
            ) from e
