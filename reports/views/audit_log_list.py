from datetime import datetime
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_date
from django.views.generic import ListView
from workflow.models import AuditLog
from workflow.mixins import AdminRequiredMixin


class AuditLogListView(AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "reports/audit_log_list.html"
    context_object_name = "logs"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            AuditLog.objects
            .select_related("actor", "document")
            .all()
        )

        action = self.request.GET.get("action")
        if action:
            qs = qs.filter(action__icontains=action)

        actor = self.request.GET.get("actor")
        if actor:
            qs = qs.filter(actor__username__icontains=actor)

        date_from = self.request.GET.get("date_from")
        if date_from:
            parsed = parse_date(date_from)
            if parsed:
                dt = make_aware(datetime.combine(parsed, datetime.min.time()))
                qs = qs.filter(created_at__gte=dt)
        return qs
