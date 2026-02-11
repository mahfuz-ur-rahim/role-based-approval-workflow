from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.contrib import messages
from django.shortcuts import get_object_or_404
from workflow.models import Document
from django.http import HttpResponseBadRequest
from workflow.services.document_workflow import (
    DocumentWorkflowService,
    InvalidTransitionError,
)
from workflow.state_machine import WorkflowAction

class DocumentSubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # 1️⃣ Visibility Gate — owner only
        document = get_object_or_404(
            Document,
            pk=pk,
            created_by=request.user,
        )

        service = DocumentWorkflowService(actor=request.user)

        try:
            service.perform(
                document_id=document.id,
                action=WorkflowAction.SUBMIT,
            )
        except InvalidTransitionError:
            return HttpResponseBadRequest(
                "This action is not allowed in the current document state."
            )

        messages.success(request, "Document submitted for approval.")
        return redirect("workflow:document-list")