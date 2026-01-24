from django.views.generic import ListView
from workflow.models import Document
from workflow.mixins import ApproverRequiredMixin


class ApprovalQueueListView(ApproverRequiredMixin, ListView):
    model = Document
    template_name = "workflow/manager_document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        return Document.objects.filter(status=Document.Status.SUBMITTED).exclude(
            created_by=self.request.user
        )
