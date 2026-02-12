import pytest
from django.urls import reverse
from workflow.models import Document


@pytest.mark.django_db
def test_employee_cannot_submit_other_users_document(
    client_logged_in, employee, manager
):
    other_doc = Document.objects.create(
        title="Other Doc",
        content="x",
        created_by=manager,
    )

    client = client_logged_in(employee)

    resp = client.post(
        reverse("workflow:document-submit", args=[other_doc.id])
    )

    assert resp.status_code == 404


@pytest.mark.django_db
def test_employee_cannot_view_other_users_audit(
    client_logged_in, employee, manager
):
    other_doc = Document.objects.create(
        title="Audit Doc",
        content="x",
        created_by=manager,
    )

    client = client_logged_in(employee)

    resp = client.get(
        reverse("workflow:document-audit-log", args=[other_doc.id])
    )

    assert resp.status_code == 404


@pytest.mark.django_db
def test_employee_cannot_access_approve_endpoint(
    client_logged_in, employee, submitted_document
):
    client = client_logged_in(employee)

    resp = client.post(
        reverse("workflow:document-approve", args=[submitted_document.id])
    )

    assert resp.status_code == 403


@pytest.mark.django_db
def test_manager_cannot_approve_draft_document(
    client_logged_in, manager, draft_document
):
    client = client_logged_in(manager)

    resp = client.post(
        reverse("workflow:document-approve", args=[draft_document.id])
    )

    assert resp.status_code == 400


@pytest.mark.django_db
def test_admin_can_approve_submitted_document(
    client_logged_in, admin, submitted_document
):
    client = client_logged_in(admin)

    resp = client.post(
        reverse("workflow:document-approve", args=[submitted_document.id])
    )

    assert resp.status_code == 302
