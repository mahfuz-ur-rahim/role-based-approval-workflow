from abc import ABC, abstractmethod


class WorkflowExecutionEngine:
    """
    Abstract execution engine contract.
    Owns:
    - Transaction boundary
    - Aggregate loading
    - Locking strategy
    """

    def execute(self, *, command, handler):
        raise NotImplementedError