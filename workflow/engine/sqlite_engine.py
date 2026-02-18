from django.db import transaction
from workflow.models import Document
from .base import WorkflowExecutionEngine


class SQLiteExecutionEngine(WorkflowExecutionEngine):

    def run_in_transaction(self, func, *args, **kwargs):
        with transaction.atomic():
            return func(*args, **kwargs)

    def load_document_for_update(self, document_id):
        # SQLite has no row-level locking
        # We rely on atomic block only
        return Document.objects.select_for_update(
            nowait=False
        ).get(id=document_id)
