from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.views.generic import ListView

from workflow.models import Document, AuditLog


class DocumentAuditLogView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = "reports/document_audit_log.html"
    context_object_name = "logs"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user

        document = get_object_or_404(Document, pk=self.kwargs["pk"])

        # Visibility Gate
        if not (
            document.created_by == user
            or user.groups.filter(name__in=["Manager", "Admin"]).exists()
            or user.is_superuser
        ):
            raise Http404

        self.document = document

        return (
            AuditLog.objects
            .filter(document=document)
            .select_related("actor")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        return context
