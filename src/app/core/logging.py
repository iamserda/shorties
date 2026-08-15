from __future__ import annotations

import json
import logging.handlers
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

_RESERVED_RECORD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__)
_CONFIGURED_ATTR = "_shorties_logging_configured"

FILE_ROTATION_BACKUP_COUNT = 14  # keep this many rotated daily log files


class JSONFormatter(logging.Formatter):
    """Renders each log record as one JSON object per line.

    Structured logging is what lets both a human `tail`/`grep` a local
    file and a container platform's log aggregator parse the same
    output without a second format to maintain.
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


def configure_logging(
    level: int = logging.INFO,
    *,
    log_to_file: bool = True,
    log_dir: str = "logs",
) -> None:
    """Configure the root logger to emit one JSON object per line.

    Always logs to stdout — that's what a container platform's log
    aggregator captures, and the only copy that survives an instance
    being recycled. Optionally *also* logs to a daily-rotating file
    under `log_dir` (relative to the current working directory) for
    local review — kept for FILE_ROTATION_BACKUP_COUNT days, then
    dropped automatically. On a platform like Render that file is only
    as durable as the running instance; it's a local convenience, not
    the system of record there.

    Idempotent — safe to call more than once (e.g. once from the app
    and once from a standalone script entrypoint) without duplicating
    handlers.
    """
    root_logger = logging.getLogger()

    if getattr(root_logger, _CONFIGURED_ATTR, False):
        return

    root_logger.setLevel(level)
    formatter = JSONFormatter()

    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    if log_to_file:
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_dir_path / "app.log",
            when="midnight",
            backupCount=FILE_ROTATION_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    setattr(root_logger, _CONFIGURED_ATTR, True)
