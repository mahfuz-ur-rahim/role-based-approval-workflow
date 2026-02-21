from django.db import models, transaction
from django.contrib.auth import get_user_model

from .audit import AuditLog, AuditAction

User = get_user_model()


class Document(models.Model):
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

    def submit(self, user):
        """Submit a draft document for approval."""
        if self.status != self.Status.DRAFT:
            raise ValueError("Only draft documents can be submitted.")
        if user != self.created_by:
            raise PermissionError("Only the owner can submit.")
        with transaction.atomic():
            self.status = self.Status.SUBMITTED
            self.save(update_fields=["status", "updated_at"])
            AuditLog.log(
                action=AuditAction.DOCUMENT_SUBMITTED,
                actor=user,
                document=self,
            )

    def approve(self, user):
        """Approve a submitted document."""
        from .approval import ApprovalStep

        if self.status != self.Status.SUBMITTED:
            raise ValueError("Only submitted documents can be approved.")
        if user == self.created_by:
            raise PermissionError("Self-approval is not allowed.")
        if not (user.groups.filter(name__in=["Manager", "Admin"]).exists() or user.is_superuser):
            raise PermissionError("Only managers or admins can approve.")
        with transaction.atomic():
            self.status = self.Status.APPROVED
            self.save(update_fields=["status", "updated_at"])
            ApprovalStep.objects.create(
                document=self,
                decided_by=user,
                status=self.Status.APPROVED,
            )
            AuditLog.log(
                action=AuditAction.DOCUMENT_APPROVED,
                actor=user,
                document=self,
            )

    def reject(self, user):
        """Reject a submitted document."""
        from .approval import ApprovalStep

        if self.status != self.Status.SUBMITTED:
            raise ValueError("Only submitted documents can be rejected.")
        if user == self.created_by:
            raise PermissionError("Self-rejection is not allowed.")
        if not (user.groups.filter(name__in=["Manager", "Admin"]).exists() or user.is_superuser):
            raise PermissionError("Only managers or admins can reject.")
        with transaction.atomic():
            self.status = self.Status.REJECTED
            self.save(update_fields=["status", "updated_at"])
            ApprovalStep.objects.create(
                document=self,
                decided_by=user,
                status=self.Status.REJECTED,
            )
            AuditLog.log(
                action=AuditAction.DOCUMENT_REJECTED,
                actor=user,
                document=self,
            )