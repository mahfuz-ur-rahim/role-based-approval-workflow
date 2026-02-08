import pytest

from workflow.models.approval import ApprovalStep
from workflow.models.audit import AuditAction, AuditLog
from workflow.services.document_workflow import DocumentWorkflowService, InvalidTransitionError
from workflow.state_machine import WorkflowAction


@pytest.mark.django_db
def test_idempotent_replay_creates_no_side_effects(manager, submitted_document):
    service = DocumentWorkflowService(actor=manager)

    service.perform(
        document_id=submitted_document.id,
        action=WorkflowAction.APPROVE,
    )

    with pytest.raises(InvalidTransitionError):
        service.perform(
            document_id=submitted_document.id,
            action=WorkflowAction.APPROVE,
        )

    # Side-effect guarantees
    assert ApprovalStep.objects.filter(document=submitted_document).count() == 1
    assert AuditLog.objects.filter(
        document=submitted_document,
        action=AuditAction.DOCUMENT_APPROVED,
    ).count() == 1
