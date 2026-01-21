from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from workflow.models import Document


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'workflow/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        user = self.request.user

        # Admins see all, others see their own
        if user.is_superuser or user.groups.filter(name='Admin').exists():
            return Document.objects.all().order_by('-created_at')

        return Document.objects.filter(created_by=user).order_by('-created_at')
