from django.db import transaction, DatabaseError
from django.apps import apps
from .base import WorkflowExecutionEngine


class EngineExecutionError(Exception):
    """Raised only for infrastructure-level engine failures."""


class SQLiteExecutionEngine(WorkflowExecutionEngine):

    def __init__(self, hook=None):
        self.hook = hook

    def run(self, *, command, handler):
        return self.execute(command=command, handler=handler)

    def execute(self, *, command, handler):

        Document = apps.get_model("workflow", "Document")
        ApprovalStep = apps.get_model("workflow", "ApprovalStep")
        AuditLog = apps.get_model("workflow", "AuditLog")

        try:
            with transaction.atomic():

                if self.hook:
                    self.hook.before_lock(command)

                document = (
                    Document.objects
                    .select_for_update()
                    .get(pk=command.aggregate_id)
                )

                if self.hook:
                    self.hook.after_lock(document)

                result = handler(
                    document=document,
                    models={
                        "ApprovalStep": ApprovalStep,
                        "AuditLog": AuditLog,
                    },
                )

                if self.hook:
                    self.hook.before_commit(document)

                return result

        except DatabaseError as e:
            raise EngineExecutionError(
                f"Database failure during workflow execution: {str(e)}"
            ) from e
