from django.db import models
from django.contrib.auth import get_user_model

from .document import Document

User = get_user_model()


class ApprovalStep(models.Model):
    """
    Immutable record of an approval decision
    made on a document.
    """
    document = models.ForeignKey(
        "workflow.Document",
        on_delete=models.CASCADE,
        related_name="approval_steps"
    )

    decided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="approval_steps"
    )

    status = models.CharField(
        max_length=20,
        choices=Document.Status.choices
    )

    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["decided_at"]
        indexes = [
            models.Index(fields=["document", "decided_at"]),
        ]

    def __str__(self):
        return f"{self.document_id} → {self.status} by {self.decided_by}"
