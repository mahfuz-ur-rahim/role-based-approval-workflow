from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import Http404

from workflow.models import Document

class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = "workflow/document_detail.html"
    context_object_name = "document"

    def get_object(self, queryset=None):
        document = get_object_or_404(Document, pk=self.kwargs["pk"])
        user = self.request.user

        if not (
            document.created_by == user
            or user.groups.filter(name__in=["Manager", "Admin"]).exists()
            or user.is_superuser
        ):
            raise Http404

        return document
