from django.db import IntegrityError
import pytest

from workflow.models.approval import ApprovalStep
from workflow.models.document import Document


@pytest.mark.django_db
def test_cannot_create_multiple_approval_steps(submitted_document, manager):
    ApprovalStep.objects.create(
        document=submitted_document,
        decided_by=manager,
        status=Document.Status.APPROVED,
    )
    with pytest.raises(IntegrityError):
        ApprovalStep.objects.create(
            document=submitted_document,
            decided_by=manager,
            status=Document.Status.REJECTED,
        )
