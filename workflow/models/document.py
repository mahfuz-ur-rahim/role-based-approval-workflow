from django.db import models
from django.contrib.auth import get_user_model
from workflow.state_machine import DocumentStatus as DomainStatus

User = get_user_model()


class Document(models.Model):
    """
    Core business document.
    Owns its lifecycle state and enforces valid transitions.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    title = models.CharField(max_length=255)
    content = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="document_status_valid",
                condition=models.Q(
                    status__in=[
                        "DRAFT",
                        "SUBMITTED",
                        "APPROVED",
                        "REJECTED",
                    ]
                ),
            ),
        ]

    def __str__(self):
        return f"{self.title} [{self.status}]"

    def set_status(self, *args, **kwargs):
        raise RuntimeError(
            "Document.set_status() is deprecated. "
            "Use DocumentWorkflowService instead."
        )

    def submit(self, *args, **kwargs):
        raise RuntimeError(
            "Document.submit() is deprecated. "
            "Use DocumentWorkflowService instead."
        )
    
# === Guard: Ensure domain and model status sets are identical ===
model_status_values = {choice[0] for choice in Document.Status.choices}
domain_status_values = {member.value for member in DomainStatus}
assert model_status_values == domain_status_values, \
    f"Status mismatch: model {model_status_values} vs domain {domain_status_values}"
