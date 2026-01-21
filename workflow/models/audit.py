from django.db import models
from django.contrib.auth import get_user_model

from .document import Document

User = get_user_model()


class AuditLog(models.Model):
    """
    Immutable audit trail entry.
    Captures who did what and when.
    """

    action = models.CharField(max_length=255)

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs"
    )

    document = models.ForeignKey(
        "workflow.Document",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_logs"
    )

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        return f"{self.created_at} | {self.action} | {self.actor}"
