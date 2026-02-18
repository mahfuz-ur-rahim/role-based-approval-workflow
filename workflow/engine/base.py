from abc import ABC, abstractmethod
from django.db import transaction


class WorkflowExecutionEngine(ABC):
    """
    Defines transactional + locking contract
    for workflow state transitions.
    """

    @abstractmethod
    def run_in_transaction(self, func, *args, **kwargs):
        pass

    @abstractmethod
    def load_document_for_update(self, document_id):
        pass
