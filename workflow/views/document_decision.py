from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from workflow.mixins import ApproverRequiredMixin
from workflow.models import Document


class DocumentApproveView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)

        # Early self-approval check (optional, model also enforces it)
        if document.created_by == request.user:
            return HttpResponseForbidden("You cannot approve your own document.")

        try:
            document.approve(request.user)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        except PermissionError as e:
            return HttpResponseForbidden(str(e))

        messages.success(request, "Document approved.")
        return redirect("workflow:manager-document-list")


class DocumentRejectView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)

        if document.created_by == request.user:
            return HttpResponseForbidden("You cannot reject your own document.")

        try:
            document.reject(request.user)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        except PermissionError as e:
            return HttpResponseForbidden(str(e))

        messages.success(request, "Document rejected.")
        return redirect("workflow:manager-document-list")