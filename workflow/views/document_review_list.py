from workflow.mixins import ManagerRequiredMixin
from django.views.generic import ListView

from workflow.models import Document


class ManagerDocumentListView(ManagerRequiredMixin, ListView):
    model = Document
    template_name = "workflow/manager_document_list.html"
    context_object_name = "documents"

    def test_func(self):
        return self.request.user.groups.filter(name="Manager").exists()

    def get_queryset(self):
        return Document.objects.filter(status=Document.Status.SUBMITTED)
