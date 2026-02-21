import threading
from workflow.engine.hooks import ExecutionHook


class BarrierAfterLockHook(ExecutionHook):
    """
    Pauses execution after row lock acquisition.
    Used for deterministic interleaving tests.
    """

    def __init__(self, barrier: threading.Barrier):
        self.barrier = barrier

    def after_lock(self, document):
        self.barrier.wait()
