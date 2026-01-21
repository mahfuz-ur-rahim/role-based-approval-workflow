from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.views import View

from workflow.models import Document


class BaseDecisionView(LoginRequiredMixin, UserPassesTestMixin, View):
    decision_status = None  # must be overridden

    def test_func(self):
        return self.request.user.groups.filter(name="Manager").exists()

    def post(self, request, pk):
        with transaction.atomic():
            document = (
                Document.objects
                .select_for_update()
                .filter(pk=pk, status=Document.Status.SUBMITTED)
                .first()
            )

            if not document:
                raise Http404

            document.set_status(self.decision_status, by_user=request.user)

        return redirect("workflow:manager-document-list")


class DocumentApproveView(BaseDecisionView):
    decision_status = Document.Status.APPROVED


class DocumentRejectView(BaseDecisionView):
    decision_status = Document.Status.REJECTED
