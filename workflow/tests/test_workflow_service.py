import pytest
from django.db import transaction

from workflow.services.document_workflow import (
    DocumentWorkflowService,
    InvalidTransitionError,
    PermissionViolationError,
)
from workflow.state_machine import WorkflowAction, TransitionFailure
from workflow.models import Document, AuditLog, ApprovalStep, AuditAction


@pytest.mark.django_db
def test_submit_creates_single_audit_log(employee, draft_document):
    service = DocumentWorkflowService(actor=employee)

    service.perform(
        document_id=draft_document.id,
        action=WorkflowAction.SUBMIT,
    )

    draft_document.refresh_from_db()
    assert draft_document.status == Document.Status.SUBMITTED

    logs = AuditLog.objects.filter(
        document=draft_document,
        action=AuditAction.DOCUMENT_SUBMITTED,
    )
    assert logs.count() == 1


@pytest.mark.django_db
def test_double_approval_is_blocked(manager, submitted_document):
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

    logs = AuditLog.objects.filter(
        document=submitted_document,
        action=AuditAction.DOCUMENT_APPROVED,
    )
    assert logs.count() == 1

    steps = ApprovalStep.objects.filter(document=submitted_document)
    assert steps.count() == 1


@pytest.mark.django_db
def test_self_approval_creates_no_audit_or_step(manager):
    doc = Document.objects.create(
        title="Self Doc",
        content="x",
        created_by=manager,
        status=Document.Status.SUBMITTED,
    )

    service = DocumentWorkflowService(actor=manager)

    with pytest.raises(PermissionViolationError):
        service.perform(
            document_id=doc.id,  # type: ignore
            action=WorkflowAction.APPROVE,
        )

    assert not AuditLog.objects.filter(document=doc).exists()
    assert not ApprovalStep.objects.filter(document=doc).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_like_approval_results_in_single_decision(manager, submitted_document):
    service = DocumentWorkflowService(actor=manager)

    service.perform(
        document_id=submitted_document.id,
        action=WorkflowAction.APPROVE,
    )

    # simulate stale second attempt
    with pytest.raises(InvalidTransitionError):
        service.perform(
            document_id=submitted_document.id,
            action=WorkflowAction.REJECT,
        )

    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.APPROVED
