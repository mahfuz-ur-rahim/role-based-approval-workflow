import pytest
from django.urls import reverse
from workflow.models import Document, AuditLog, AuditAction

pytestmark = pytest.mark.django_db


def test_dashboard_access_employee(client_logged_in, employee):
    """Employee should not have access to dashboard (redirect or 403)."""
    client = client_logged_in(employee)
    response = client.get(reverse("workflow:dashboard"))
    # ManagerRequiredMixin returns 403 for non-managers
    assert response.status_code == 403


def test_dashboard_access_manager(client_logged_in, manager):
    """Manager should have access to dashboard."""
    client = client_logged_in(manager)
    response = client.get(reverse("workflow:dashboard"))
    assert response.status_code == 200


def test_dashboard_access_admin(client_logged_in, admin):
    """Admin should have access to dashboard."""
    client = client_logged_in(admin)
    response = client.get(reverse("workflow:dashboard"))
    assert response.status_code == 200


def test_dashboard_context_data(client_logged_in, manager, employee):
    """Check that context contains correct document counts."""
    # Create some documents with various statuses
    doc1 = Document.objects.create(title="Doc1", content="c", created_by=employee, status=Document.Status.DRAFT)
    doc2 = Document.objects.create(title="Doc2", content="c", created_by=employee, status=Document.Status.SUBMITTED)
    doc3 = Document.objects.create(title="Doc3", content="c", created_by=manager, status=Document.Status.APPROVED)
    doc4 = Document.objects.create(title="Doc4", content="c", created_by=employee, status=Document.Status.REJECTED)
    doc5 = Document.objects.create(title="Doc5", content="c", created_by=employee, status=Document.Status.SUBMITTED)

    client = client_logged_in(manager)
    response = client.get(reverse("workflow:dashboard"))

    assert response.context["total_docs"] == 5
    assert response.context["draft_count"] == 1
    assert response.context["submitted_count"] == 2
    assert response.context["approved_count"] == 1
    assert response.context["rejected_count"] == 1
    # pending approvals: submitted documents not created by current user (manager)
    # submitted docs: doc2 (created by employee) and doc5 (employee) → both should be pending
    assert response.context["pending_approvals"] == 2


def test_dashboard_recent_logs(client_logged_in, manager, employee):
    """Check that recent audit logs appear in context."""
    # Create a document and some logs
    doc = Document.objects.create(title="LogTest", content="c", created_by=employee)
    # Create logs in reverse order to test ordering
    log1 = AuditLog.log(action=AuditAction.DOCUMENT_CREATED, actor=employee, document=doc)
    log2 = AuditLog.log(action=AuditAction.DOCUMENT_SUBMITTED, actor=employee, document=doc)
    log3 = AuditLog.log(action=AuditAction.DOCUMENT_APPROVED, actor=manager, document=doc)

    client = client_logged_in(manager)
    response = client.get(reverse("workflow:dashboard"))

    recent_logs = response.context["recent_logs"]
    assert len(recent_logs) == 3
    # Should be ordered by created_at descending (most recent first)
    assert recent_logs[0].id == log3.id # type: ignore
    assert recent_logs[1].id == log2.id # type: ignore
    assert recent_logs[2].id == log1.id # type: ignore


def test_dashboard_uses_correct_template(client_logged_in, manager):
    """Check that the correct template is used."""
    client = client_logged_in(manager)
    response = client.get(reverse("workflow:dashboard"))
    assert response.status_code == 200
    assert response.templates[0].name == "workflow/dashboard.html"