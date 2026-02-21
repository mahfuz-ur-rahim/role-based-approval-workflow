import pytest
from django.db import transaction

from workflow.models import Document, ApprovalStep, AuditLog, AuditAction


@pytest.mark.django_db
def test_submit_creates_single_audit_log(employee, draft_document):
    draft_document.submit(employee)
    draft_document.refresh_from_db()
    assert draft_document.status == Document.Status.SUBMITTED

    logs = AuditLog.objects.filter(
        document=draft_document,
        action=AuditAction.DOCUMENT_SUBMITTED,
    )
    assert logs.count() == 1


@pytest.mark.django_db
def test_double_approval_is_blocked(manager, submitted_document):
    # First approval succeeds
    submitted_document.approve(manager)
    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.APPROVED

    # Second approval should fail
    with pytest.raises(ValueError, match="Only submitted documents can be approved"):
        submitted_document.approve(manager)

    # Only one audit log and one approval step should exist
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

    with pytest.raises(PermissionError, match="Self-approval is not allowed"):
        doc.approve(manager)

    # No audit log or approval step should be created (transaction rolled back)
    assert not AuditLog.objects.filter(document=doc).exists()
    assert not ApprovalStep.objects.filter(document=doc).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_like_approval_results_in_single_decision(manager, submitted_document):
    # First approve
    submitted_document.approve(manager)
    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.APPROVED

    # Attempt reject after approval – should fail
    with pytest.raises(ValueError, match="Only submitted documents can be rejected"):
        submitted_document.reject(manager)

    # Status remains approved
    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.APPROVED