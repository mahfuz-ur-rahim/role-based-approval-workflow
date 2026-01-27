from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.views import View
from django.http import Http404
from django.contrib import messages

from workflow.models import Document
from workflow.mixins import ApproverRequiredMixin


class BaseDecisionView(ApproverRequiredMixin, View):
    decision_status = None

    def post(self, request, pk):
        with transaction.atomic():
            document = (
                Document.objects.select_for_update()
                .filter(pk=pk, status=Document.Status.SUBMITTED)
                .first()
            )

            if not document:
                raise Http404

            if document.created_by_id == request.user.id:
                raise PermissionDenied("Self-approval is not allowed")

            document.set_status(self.decision_status, by_user=request.user)
            
        if self.decision_status == Document.Status.APPROVED:
            messages.success(request, "Document approved.")
        elif self.decision_status == Document.Status.REJECTED:
            messages.success(request, "Document rejected.")

        return redirect("workflow:manager-document-list")


class DocumentApproveView(BaseDecisionView):
    decision_status = Document.Status.APPROVED


class DocumentRejectView(BaseDecisionView):
    decision_status = Document.Status.REJECTED
