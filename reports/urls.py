from django.urls import path
from .views.audit_log_list import AuditLogListView
from reports.views.document_audit import DocumentAuditLogView

app_name = "reports"

urlpatterns = [
    path(
        "audit-logs/", 
        AuditLogListView.as_view(), 
        name="audit-log-list",
    ),
    path(
        "documents/<int:document_id>/audit/",
        DocumentAuditLogView.as_view(),
        name="document-audit-log",
    ),
]
