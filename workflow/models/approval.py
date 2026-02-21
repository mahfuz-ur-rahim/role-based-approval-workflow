from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ApprovalStep(models.Model):
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
        choices=[
            ("DRAFT", "Draft"),
            ("SUBMITTED", "Submitted"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ]
    )
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["decided_at"]
        indexes = [
            models.Index(fields=["document", "decided_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["document"],
                name="unique_approval_per_document",
            ),
            models.CheckConstraint(
                name="approvalstep_terminal_status_only",
                condition=models.Q(
                    status__in=["APPROVED", "REJECTED"]
                ),
            ),
        ]

    def __str__(self):
        return f"{self.document_id} → {self.status} by {self.decided_by}" # type: ignore