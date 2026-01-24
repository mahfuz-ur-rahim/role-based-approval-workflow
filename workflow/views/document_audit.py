from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from workflow.models import Document, AuditLog


class DocumentAuditLogView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = "reports/document_audit_log.html"
    context_object_name = "logs"
    paginate_by = 20

    def get_queryset(self):
        self.document = get_object_or_404(Document, pk=self.kwargs["pk"])
        return (
            AuditLog.objects
            .filter(document=self.document)
            .select_related("actor")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        return context
