from django.shortcuts import redirect
from django.views import View
from django.contrib import messages
from workflow.mixins import ApproverRequiredMixin
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from workflow.services.document_workflow import (
    DocumentWorkflowService,
    InvalidTransitionError,
    PermissionViolationError,
)
from workflow.state_machine import WorkflowAction

class DocumentApproveView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        service = DocumentWorkflowService(actor=request.user)
        try:
            service.perform(
                document_id=pk,
                action=WorkflowAction.APPROVE,
            )
        except PermissionViolationError:
            return HttpResponseForbidden()
        except InvalidTransitionError:
            return HttpResponseBadRequest()

        messages.success(request, "Document approved.")
        return redirect("workflow:manager-document-list")


class DocumentRejectView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        service = DocumentWorkflowService(actor=request.user)
        try:
            service.perform(
                document_id=pk,
                action=WorkflowAction.REJECT,
            )
        except PermissionViolationError:
            return HttpResponseForbidden()
        except InvalidTransitionError:
            return HttpResponseBadRequest()

        messages.success(request, "Document rejected.")
        return redirect("workflow:manager-document-list")

