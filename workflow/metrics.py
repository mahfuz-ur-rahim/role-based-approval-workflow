import threading
from collections import defaultdict


class WorkflowMetrics:
    """
    In-process metrics collector.
    Thread-safe.
    Never raises.
    """

    _lock = threading.Lock()
    _counters = defaultdict(int)
    _latencies = defaultdict(list)

    @classmethod
    def increment(cls, metric: str) -> None:
        try:
            with cls._lock:
                cls._counters[metric] += 1
        except Exception:
            pass

    @classmethod
    def record_latency(cls, metric: str, value_ms: float) -> None:
        try:
            with cls._lock:
                cls._latencies[metric].append(value_ms)
        except Exception:
            pass

    @classmethod
    def snapshot(cls):
        """
        Returns a copy of metrics.
        For debugging / admin inspection.
        """
        with cls._lock:
            return {
                "counters": dict(cls._counters),
                "latencies": {
                    k: {
                        "count": len(v),
                        "avg_ms": sum(v) / len(v) if v else 0,
                        "max_ms": max(v) if v else 0,
                    }
                    for k, v in cls._latencies.items()
                },
            }
