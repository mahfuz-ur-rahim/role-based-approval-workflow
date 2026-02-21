from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from workflow.models import Document


class DocumentSubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(
            Document,
            pk=pk,
            created_by=request.user,  # ensures ownership
        )

        try:
            document.submit(request.user)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        messages.success(request, "Document submitted for approval.")
        return redirect("workflow:document-list")