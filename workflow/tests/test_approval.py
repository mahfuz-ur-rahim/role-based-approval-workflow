import pytest
from django.urls import reverse
from workflow.models import Document, ApprovalStep
from workflow.services.document_workflow import DocumentWorkflowService, PermissionViolationError
from workflow.state_machine import WorkflowAction


@pytest.mark.django_db
def test_manager_can_approve_submitted_document(
    client_logged_in, manager, submitted_document
):
    client = client_logged_in(manager)

    resp = client.post(
        reverse("workflow:document-approve", args=[submitted_document.id])
    )

    assert resp.status_code == 302

    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.APPROVED
    assert ApprovalStep.objects.filter(
        document=submitted_document,
        decided_by=manager,
        status=Document.Status.APPROVED,
    ).exists()


@pytest.mark.django_db
def test_employee_cannot_approve_document(
    client_logged_in, employee, submitted_document
):
    client = client_logged_in(employee)

    resp = client.post(
        reverse("workflow:document-approve", args=[submitted_document.id])
    )

    # ApproverRequiredMixin → permission failure
    assert resp.status_code in (302, 403)

    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.SUBMITTED


@pytest.mark.django_db
def test_manager_cannot_self_approve(
    client_logged_in, manager
):
    from workflow.models import Document

    doc = Document.objects.create(
        title="Self Doc",
        content="x",
        created_by=manager,
    )
    owner_service = DocumentWorkflowService(actor=manager)
    owner_service.perform(
        document_id=doc.id,  # type: ignore
        action=WorkflowAction.SUBMIT,
    )

    # attempt self-approval
    approval_service = DocumentWorkflowService(actor=manager)
    with pytest.raises(PermissionViolationError):
        approval_service.perform(
            document_id=doc.id,  # type: ignore
            action=WorkflowAction.APPROVE,
        )

    client = client_logged_in(manager)

    resp = client.post(
        reverse("workflow:document-approve", args=[doc.id])  # type: ignore
    )

    assert resp.status_code == 403

    doc.refresh_from_db()
    assert doc.status == Document.Status.SUBMITTED


@pytest.mark.django_db
def test_manager_can_reject_submitted_document(
    client_logged_in, manager, submitted_document
):
    client = client_logged_in(manager)

    resp = client.post(
        reverse("workflow:document-reject", args=[submitted_document.id])
    )

    assert resp.status_code == 302

    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.REJECTED
