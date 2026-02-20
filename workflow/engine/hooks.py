class ExecutionHook:
    """
    Optional test-only execution hook for deterministic
    concurrency simulation.
    """

    def before_lock(self, command):
        pass

    def after_lock(self, document):
        pass

    def before_commit(self, document):
        pass