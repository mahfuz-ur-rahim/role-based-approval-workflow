from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from workflow.models import Document


class DocumentSubmitView(LoginRequiredMixin, View):
    """
    Handles Draft -> Submitted transition.
    POST-only, owner-only.
    """

    def post(self, request, pk):
        document = get_object_or_404(
            Document,
            pk=pk,
            created_by=request.user,
            status=Document.Status.DRAFT,
        )

        document.submit()

        return redirect('workflow:document-list')
