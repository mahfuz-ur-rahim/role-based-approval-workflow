import uuid
import contextvars

# Request-scoped correlation ID
correlation_id_var = contextvars.ContextVar("correlation_id", default=None)


def get_correlation_id():
    return correlation_id_var.get()


class CorrelationIdMiddleware:
    """
    Assigns a correlation ID per request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get(
            "X-Correlation-ID") or str(uuid.uuid4())
        correlation_id_var.set(correlation_id)  # type: ignore

        response = self.get_response(request)
        response["X-Correlation-ID"] = correlation_id

        return response
