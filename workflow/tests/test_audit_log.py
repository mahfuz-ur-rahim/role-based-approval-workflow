import pytest
from django.urls import reverse
from workflow.models import AuditLog, AuditAction, Document

@pytest.mark.django_db
def test_audit_log_created_on_document_create(
    client_logged_in, employee
):
    client = client_logged_in(employee)

    resp = client.post(
        reverse("workflow:document-create"),
        data={
            "title": "Audit Test Doc",
            "content": "content",
        },
    )

    assert resp.status_code == 302

    doc = Document.objects.get(title="Audit Test Doc")

    log = AuditLog.objects.filter(
        action=AuditAction.DOCUMENT_CREATED,
        document=doc,
        actor=employee,
    )

    assert log.count() == 1

@pytest.mark.django_db
def test_audit_log_created_on_approval(
    client_logged_in, manager, submitted_document
):
    client = client_logged_in(manager)

    client.post(
        reverse("workflow:document-approve", args=[submitted_document.id])
    )

    log = AuditLog.objects.filter(
        action=AuditAction.DOCUMENT_APPROVED,
        document=submitted_document,
        actor=manager,
    )

    assert log.count() == 1

@pytest.mark.django_db
def test_audit_log_created_on_rejection(
    client_logged_in, manager, submitted_document
):
    client = client_logged_in(manager)

    client.post(
        reverse("workflow:document-reject", args=[submitted_document.id])
    )

    log = AuditLog.objects.filter(
        action=AuditAction.DOCUMENT_REJECTED,
        document=submitted_document,
        actor=manager,
    )

    assert log.count() == 1

@pytest.mark.django_db
def test_no_audit_log_created_on_failed_self_approval(
    client_logged_in, manager
):
    doc = Document.objects.create(
        title="Self Audit Doc",
        content="x",
        created_by=manager,
    )
    doc.submit()

    client = client_logged_in(manager)

    resp = client.post(
        reverse("workflow:document-approve", args=[doc.id])
    )

    assert resp.status_code == 403

    assert not AuditLog.objects.filter(
        document=doc,
        action=AuditAction.DOCUMENT_APPROVED,
    ).exists()