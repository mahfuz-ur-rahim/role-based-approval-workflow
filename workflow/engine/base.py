from abc import ABC, abstractmethod


class WorkflowExecutionEngine(ABC):
    """
    Responsible for:
    - Transaction boundary
    - Aggregate loading with locking semantics
    """

    @abstractmethod
    def run(self, func):
        pass

    @abstractmethod
    def load_document(self, document_id: int):
        pass
