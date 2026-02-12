from django.urls import path
from workflow.views.document_detail import DocumentDetailView
from workflow.views.home import home
from workflow.views.document_list import DocumentListView
from workflow.views.document_create import DocumentCreateView
from workflow.views.document_submit import DocumentSubmitView
from workflow.views import DocumentUpdateView
from workflow.views import ApprovalQueueListView
from workflow.views import DocumentApproveView
from workflow.views import DocumentRejectView
from workflow.views import DocumentAuditLogView


app_name = "workflow"

urlpatterns = [
    path(
        "", 
        home, 
        name="home"
    ),
    path(
        "documents/", 
        DocumentListView.as_view(), 
        name="document-list"
    ),
    path(
        "documents/create/", 
         DocumentCreateView.as_view(), 
         name="document-create"
    ),
    path(
        "documents/<int:pk>/",
        DocumentDetailView.as_view(),
        name="document-detail",
    ),
    path(
        "documents/<int:pk>/edit/",
        DocumentUpdateView.as_view(),
        name="document-edit",
    ),
    path(
        "documents/<int:pk>/submit/",
        DocumentSubmitView.as_view(),
        name="document-submit",
    ),
    path(
        "documents/approvals/",
        ApprovalQueueListView.as_view(),
        name="manager-document-list",
    ),
    path(
        "documents/<int:pk>/approve/",
        DocumentApproveView.as_view(),
        name="document-approve",
    ),
    path(
        "documents/<int:pk>/reject/",
        DocumentRejectView.as_view(),
        name="document-reject",
    ),
    path(
        "documents/<int:pk>/audit/",
        DocumentAuditLogView.as_view(),
        name="document-audit-log",
    ),
]
