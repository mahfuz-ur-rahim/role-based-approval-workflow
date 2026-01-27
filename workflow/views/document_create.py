from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from workflow.models.audit import AuditAction
from workflow.models import AuditLog
from workflow.models import Document
from workflow.forms import DocumentForm


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'workflow/document_form.html'
    success_url = reverse_lazy('workflow:document-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        messages.success(self.request, "Document created successfully.")

        AuditLog.log(
            action=AuditAction.DOCUMENT_CREATED,
            actor=self.request.user,
            document=self.object,
            metadata={"document_id": self.object.id},
        )
        return response

