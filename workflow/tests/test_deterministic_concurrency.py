import threading
import pytest
from workflow.state_machine import WorkflowAction
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
    # Use the default engine (no custom hook) to let threads race naturally
    from workflow.services.document_workflow import DocumentWorkflowService
    service1 = DocumentWorkflowService(actor=manager)
    service2 = DocumentWorkflowService(actor=manager)

    results = []
    errors = []

    def approve(service):
        try:
            service.perform(
                document_id=document.id,  # type: ignore
                action=WorkflowAction.APPROVE,
            )
            results.append("success")
        except Exception as e:
            errors.append(type(e).__name__)
            # Close the thread's database connection to allow test DB cleanup
        finally:
            from django.db import connection
            connection.close()

    t1 = threading.Thread(target=approve, args=(service1,))
    t2 = threading.Thread(target=approve, args=(service2,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    document.refresh_from_db()

    # Assertions

    assert document.status == "APPROVED"

    # Exactly one approval step
    assert ApprovalStep.objects.filter(document=document).count() == 1

    # Exactly one audit log
    assert AuditLog.objects.filter(document=document).count() == 1

    # One success, one failure
    assert len(results) == 1
    assert len(errors) == 1
