from django.shortcuts import redirect
from django.views import View
from django.contrib import messages
from workflow.mixins import ApproverRequiredMixin
from django.shortcuts import get_object_or_404
from workflow.models import Document
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from workflow.services.document_workflow import (
    DocumentWorkflowService,
    InvalidTransitionError,
    PermissionViolationError,
)
from workflow.state_machine import WorkflowAction


class DocumentApproveView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        # 1️⃣ Visibility Gate (document must exist)
        document = get_object_or_404(Document, pk=pk)

        # 2️⃣ Action Permission Gate — self-approval forbidden
        if document.created_by == request.user:
            return HttpResponseForbidden(
                "You cannot approve your own document."
            )

        service = DocumentWorkflowService(actor=request.user)

        try:
            service.perform(
                document_id=document.id,  # type: ignore
                action=WorkflowAction.APPROVE,
            )
        except PermissionViolationError:
            return HttpResponseForbidden(
                "You do not have permission to perform this action."
            )
        except InvalidTransitionError:
            return HttpResponseBadRequest(
                "This action is not allowed in the current document state."
            )

        messages.success(request, "Document approved.")
        return redirect("workflow:manager-document-list")


class DocumentRejectView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        # 1️⃣ Visibility Gate
        document = get_object_or_404(Document, pk=pk)

        # 2️⃣ Action Permission Gate — self-rejection forbidden
        if document.created_by == request.user:
            return HttpResponseForbidden(
                "You cannot reject your own document."
            )

        service = DocumentWorkflowService(actor=request.user)

        try:
            service.perform(
                document_id=document.id,  # type: ignore
                action=WorkflowAction.REJECT,
            )
        except PermissionViolationError:
            return HttpResponseForbidden(
                "You do not have permission to perform this action."
            )
        except InvalidTransitionError:
            return HttpResponseBadRequest(
                "This action is not allowed in the current document state."
            )

        messages.success(request, "Document rejected.")
        return redirect("workflow:manager-document-list")
