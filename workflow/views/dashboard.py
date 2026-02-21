from django.db.models import Count
from django.views.generic import TemplateView
from workflow.mixins import ManagerRequiredMixin
from workflow.models import Document, AuditLog

class DashboardView(ManagerRequiredMixin, TemplateView):
    template_name = "workflow/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Document counts by status
        context['total_docs'] = Document.objects.count()
        context['draft_count'] = Document.objects.filter(status=Document.Status.DRAFT).count()
        context['submitted_count'] = Document.objects.filter(status=Document.Status.SUBMITTED).count()
        context['approved_count'] = Document.objects.filter(status=Document.Status.APPROVED).count()
        context['rejected_count'] = Document.objects.filter(status=Document.Status.REJECTED).count()

        # Pending approvals (submitted not created by current user)
        context['pending_approvals'] = Document.objects.filter(
            status=Document.Status.SUBMITTED
        ).exclude(created_by=self.request.user).count()

        # Recent audit logs
        context['recent_logs'] = AuditLog.objects.select_related('actor', 'document').order_by('-created_at')[:10]

        return context