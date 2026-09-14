"""
Structured logging utilities.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from api.request_context import request_id

class JsonFormatter(logging.Formatter):
    """
    Format logs as JSON
    """
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id.get(),
        }

        # Add extra structured fields
        if hasattr(record, "extra_data"):
            log_record.update(
                record.extra_data
            )
        return json.dumps(
            log_record
        )

# def setup_logging(level: str = "INFO",):
#     handler = logging.StreamHandler()

#     handler.setFormatter(JsonFormatter())
#     root_logger = logging.getLogger()
#     root_logger.handlers.clear()
#     root_logger.addHandler(
#         handler
#     )
#     root_logger.setLevel(
#         level
#     )
def get_logger(
    name: str,
) -> logging.Logger:

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler()

    handler.setFormatter(
        JsonFormatter()
    )

    logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    logger.propagate = False

    return logger