from django.db import transaction

from workflow.models import Document, ApprovalStep, AuditLog


class DocumentService:
    """
    Orchestrates document lifecycle transitions
    and their side-effects.
    """

    @staticmethod
    @transaction.atomic
    def submit(document: Document, actor):
        raise NotImplementedError

    @staticmethod
    @transaction.atomic
    def approve(document: Document, actor):
        raise NotImplementedError

    @staticmethod
    @transaction.atomic
    def reject(document: Document, actor):
        raise NotImplementedError
