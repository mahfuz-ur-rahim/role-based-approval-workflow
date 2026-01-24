from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from workflow.models import Document, AuditLog


class DocumentAuditLogView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AuditLog
    template_name = "reports/document_audit_log.html"
    context_object_name = "logs"
    paginate_by = 50

    def test_func(self):
        return self.request.user.groups.filter(name="Admin").exists()

    def get_queryset(self):
        self.document = get_object_or_404(Document, id=self.kwargs["document_id"])
        return (
            AuditLog.objects
            .filter(document=self.document)
            .select_related("actor")
            .order_by("created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["document"] = self.document
        return ctx
