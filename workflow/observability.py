import logging
import time
from typing import Optional

logger = logging.getLogger("workflow.observability")


class WorkflowEventLogger:
    """
    Passive structured logger for workflow transitions.
    Must never raise exceptions.
    """

    @staticmethod
    def log_transition_attempt(
        *,
        actor_id: int,
        document_id: int,
        current_status: str,
        action: str,
    ) -> float:
        """
        Logs the start of a transition attempt.
        Returns start timestamp for latency calculation.
        """
        start_time = time.monotonic()

        try:
            logger.info(
                "workflow.transition.attempt",
                extra={
                    "actor_id": actor_id,
                    "document_id": document_id,
                    "current_status": current_status,
                    "action": action,
                },
            )
        except Exception:
            # Observability must never break workflow
            pass

        return start_time

    @staticmethod
    def log_transition_result(
        *,
        actor_id: int,
        document_id: int,
        action: str,
        allowed: bool,
        failure: Optional[str],
        latency_ms: float,
    ) -> None:
        """
        Logs the outcome of a transition attempt.
        """
        try:
            logger.info(
                "workflow.transition.result",
                extra={
                    "actor_id": actor_id,
                    "document_id": document_id,
                    "action": action,
                    "allowed": allowed,
                    "failure": failure,
                    "latency_ms": round(latency_ms, 2),
                },
            )
        except Exception:
            pass

    @staticmethod
    def log_exception(
        *,
        actor_id: int,
        document_id: int,
        action: str,
        exc: Exception,
    ) -> None:
        """
        Logs unexpected exceptions.
        """
        try:
            logger.exception(
                "workflow.transition.exception",
                extra={
                    "actor_id": actor_id,
                    "document_id": document_id,
                    "action": action,
                    "exception_class": exc.__class__.__name__,
                },
            )
        except Exception:
            pass
