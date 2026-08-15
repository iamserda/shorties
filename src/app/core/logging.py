from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from datetime import timezone

_RESERVED_RECORD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__)


class JSONFormatter(logging.Formatter):
    """Renders each log record as one JSON object per line.

    Structured, stdout-only logging is what container platforms (Render
    included) actually capture — a file written inside the container's
    filesystem disappears the moment the instance recycles, and plain
    text log lines aren't queryable once they leave the box.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Pick up structured fields passed via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger to emit one JSON object per line to stdout.

    Idempotent — safe to call more than once (e.g. once from the app and
    once from a standalone script entrypoint) without duplicating handlers.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
