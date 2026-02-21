import pytest

from workflow.models import Document, ApprovalStep


@pytest.mark.django_db
def test_manager_can_approve_submitted_document(manager, submitted_document):
    submitted_document.approve(manager)
    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.APPROVED

    # Verify ApprovalStep was created
    assert ApprovalStep.objects.filter(
        document=submitted_document,
        decided_by=manager,
        status=Document.Status.APPROVED,
    ).exists()


@pytest.mark.django_db
def test_employee_cannot_approve_document(employee, manager):
    # Create a submitted document owned by manager
    doc = Document.objects.create(
        title="Manager's Doc",
        content="content",
        created_by=manager,
        status=Document.Status.SUBMITTED,
    )
    with pytest.raises(PermissionError, match="Only managers or admins can approve."):
        doc.approve(employee)
    doc.refresh_from_db()
    assert doc.status == Document.Status.SUBMITTED


@pytest.mark.django_db
def test_manager_cannot_self_approve(manager):
    doc = Document.objects.create(
        title="Self Doc",
        content="x",
        created_by=manager,
    )
    doc.submit(manager)  # Move to SUBMITTED

    with pytest.raises(PermissionError, match="Self-approval is not allowed"):
        doc.approve(manager)

    doc.refresh_from_db()
    assert doc.status == Document.Status.SUBMITTED


@pytest.mark.django_db
def test_manager_can_reject_submitted_document(manager, submitted_document):
    submitted_document.reject(manager)
    submitted_document.refresh_from_db()
    assert submitted_document.status == Document.Status.REJECTED

    assert ApprovalStep.objects.filter(
        document=submitted_document,
        decided_by=manager,
        status=Document.Status.REJECTED,
    ).exists()