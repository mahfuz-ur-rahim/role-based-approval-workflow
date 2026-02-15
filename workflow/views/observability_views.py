from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET

from workflow.metrics import WorkflowMetrics


@require_GET
@staff_member_required
def workflow_metrics_view(request):
    """
    Read-only observability endpoint.
    Returns in-memory workflow metrics snapshot.
    Admin/staff only.
    """
    snapshot = WorkflowMetrics.snapshot()

    return JsonResponse(
        {
            "service": "workflow",
            "metrics": snapshot,
        }
    )
