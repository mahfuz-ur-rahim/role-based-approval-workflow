from django.urls import path
from .views.audit_log_list import AuditLogListView

app_name = "reports"

urlpatterns = [
    path(
        "audit-logs/",
        AuditLogListView.as_view(),
        name="audit-log-list",
    ),
]
