from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from workflow.services.document_workflow import (
    DocumentWorkflowService,
    InvalidTransitionError,
    PermissionViolationError,
)
from workflow.state_machine import WorkflowAction

class DocumentSubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = DocumentWorkflowService(actor=request.user)

        try:
            service.perform(
                document_id=pk,
                action=WorkflowAction.SUBMIT,
            )
        except PermissionViolationError:
            return HttpResponseForbidden()
        except InvalidTransitionError:
            return HttpResponseBadRequest()

        messages.success(request, "Document submitted for approval.")
        return redirect("workflow:document-list")