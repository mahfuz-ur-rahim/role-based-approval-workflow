from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from workflow.models import Document
from workflow.forms import DocumentForm


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "workflow/document_form.html"

    def get_queryset(self):
        return Document.objects.filter(
            created_by=self.request.user,
            status=Document.Status.DRAFT,
        )

    def get_success_url(self):
        return reverse_lazy("workflow:document-list")
