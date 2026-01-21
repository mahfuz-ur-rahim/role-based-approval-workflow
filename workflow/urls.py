from django.urls import path
from workflow.views.home import home
from workflow.views.document_list import DocumentListView
from workflow.views.document_create import DocumentCreateView
from workflow.views.document_submit import DocumentSubmitView
from workflow.views import DocumentUpdateView
from workflow.views import ManagerDocumentListView
from workflow.views import DocumentApproveView
from workflow.views import DocumentRejectView




app_name = 'workflow'

urlpatterns = [
    path('', home, name='home'),
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('documents/create/', DocumentCreateView.as_view(), name='document-create'),
    path("documents/<int:pk>/edit/", DocumentUpdateView.as_view(), name="document_edit"),
    path(
        "documents/<int:pk>/edit/",
        DocumentUpdateView.as_view(),
        name="document-edit",
    ),
    path(
        'documents/<int:pk>/submit/',
        DocumentSubmitView.as_view(),
        name='document-submit',
    ),
    path(
        "manager/documents/",
        ManagerDocumentListView.as_view(),
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

]
