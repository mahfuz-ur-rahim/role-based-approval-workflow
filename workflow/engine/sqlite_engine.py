from django.db import transaction
from django.apps import apps
from .base import WorkflowExecutionEngine


class SQLiteExecutionEngine(WorkflowExecutionEngine):

    def run(self, func):
        with transaction.atomic():
            return func()

    def load_document(self, document_id: int):
        Document = apps.get_model("workflow", "Document")

        # SQLite ignores row locks but keeps API uniform
        return (
            Document.objects
            .select_for_update()
            .get(pk=document_id)
        )

    def execute(self, *, command, handler):
        """
        handler(document, models) -> result

        Engine responsibilities:
        - open transaction
        - lock aggregate
        - call handler
        """
        Document = apps.get_model("workflow", "Document")
        ApprovalStep = apps.get_model("workflow", "ApprovalStep")
        AuditLog = apps.get_model("workflow", "AuditLog")

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
