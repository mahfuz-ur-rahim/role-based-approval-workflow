import json
import logging
from datetime import datetime

from workflow.middleware import get_correlation_id


class JsonFormatter(logging.Formatter):
    """
    Production JSON log formatter.
    """

    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        # Include structured extras if present
        for key in (
            "actor",
            "document",
            "action",
            "allowed",
            "failure",
            "latency_ms",
        ):
            if hasattr(record, key):
                log_record[key] = getattr(record, key)

        return json.dumps(log_record)
