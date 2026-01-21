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

    def submit(self):
        """
        Transition: DRAFT -> SUBMITTED
        """
        if self.status != self.Status.DRAFT:
            raise ValueError("Only draft documents can be submitted")

        self.status = self.Status.SUBMITTED
        self.save(update_fields=["status", "updated_at"])

    def approve(self):
        """
        Transition: SUBMITTED -> APPROVED
        """
        if self.status != self.Status.SUBMITTED:
            raise ValueError("Only submitted documents can be approved")

        self.status = self.Status.APPROVED
        self.save(update_fields=["status", "updated_at"])

    def reject(self):
        """
        Transition: SUBMITTED -> REJECTED
        """
        if self.status != self.Status.SUBMITTED:
            raise ValueError("Only submitted documents can be rejected")

        self.status = self.Status.REJECTED
        self.save(update_fields=["status", "updated_at"])
    
    def set_status(self, new_status, by_user=None):
        self.status = new_status
        self.save(update_fields=["status"])


