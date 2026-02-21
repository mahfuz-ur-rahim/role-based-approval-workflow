import threading
import pytest
from django.db import connections
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from workflow.models import Document, ApprovalStep, AuditLog


@pytest.mark.django_db(transaction=True)
def test_deterministic_single_winner_under_concurrency():
    User = get_user_model()
    owner = User.objects.create_user(username="owner")
    manager = User.objects.create_user(username="manager")
    group, _ = Group.objects.get_or_create(name="Manager")
    manager.groups.add(group)

    document = Document.objects.create(
        title="Test",
        content="Test",
        created_by=owner,
        status=Document.Status.SUBMITTED,
    )

    results = []
    errors = []

    def approve_doc():
        try:
            # Fetch a fresh instance for each thread
            doc = Document.objects.get(pk=document.pk)
            doc.approve(manager)
            results.append("success")
        except Exception as e:
            errors.append(type(e).__name__)
        finally:
            connections.close_all()

    t1 = threading.Thread(target=approve_doc)
    t2 = threading.Thread(target=approve_doc)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    document.refresh_from_db()
    assert document.status == Document.Status.APPROVED
    assert ApprovalStep.objects.filter(document=document).count() == 1
    assert AuditLog.objects.filter(document=document).count() == 1
    assert len(results) == 1
    assert len(errors) == 1