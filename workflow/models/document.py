from django.db import models
from django.contrib.auth import get_user_model

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
    