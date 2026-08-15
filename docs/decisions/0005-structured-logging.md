# 0005 — Structured logging: stdout *and* a rotating file

**Status:** Accepted (revised once — see **What actually happened**)
**Date:** 2026-08-14
**Commits:** `35e4fd5` (stdout-only, then corrected), `a13464e` (added the file back)

## Who

Me, third step of foundation cleanup — and then corrected based on direct pushback from the
service owner. This one's worth documenting honestly including the correction, because the
correction is the more interesting engineering lesson.

## What

Replaced `logging.basicConfig(filename=...)` (writing to `src/app/logs/` — inside the package
directory) with a custom `JSONFormatter` emitting one JSON object per line, attached to **both** a
stdout handler and a `TimedRotatingFileHandler` (daily rotation, 14-day retention) writing to a
project-root `logs/` directory.

## When

2026-08-14. First pass (`35e4fd5`) was stdout-only. Corrected same day (`a13464e`) after review.

## Where

`src/app/core/logging.py` (new), consumed from `main.py` and `db/db.py`.

## Why

**The reasoning that was right:** `logging.basicConfig(filename=...)` wrote into
`src/app/logs/main.log` — inside the application's own source tree, and more importantly, inside
whatever filesystem the process happens to be running on. On a container platform (Render
included), that filesystem is ephemeral: the log is gone the instant the instance restarts or
redeploys. Structured JSON (rather than the old `"%(asctime)s %(levelname)s ..."` string format)
also matters for anything downstream that wants to parse logs programmatically — a log aggregator,
`jq`, an alert rule matching on a field.

**What actually happened — the part worth being honest about:** the first pass dropped file
logging *entirely*, reasoning "containers need stdout, therefore stdout is what we do." That
reasoning is correct for the deployed service and **wrong as a blanket rule** — it ignored that
the original file-based logging existed on purpose, for local review, and that intent doesn't go
away just because a different, also-true fact (containers want stdout) exists. The service owner's
exact framing: *"if I wanted to simply just print to stdout, I would have just kept on printing. I
did not. I instead saved in a file so I can review it later. I want this to continue to be the
case."*

That's the lesson worth being able to state plainly in an interview: **a better way to do
something doesn't retroactively make the original intent wrong.** The fix wasn't "restore the old
behavior" (a single ever-growing file) — it was "do both, correctly" — stdout for what a platform
actually captures, plus a *properly rotated* local file (the old version had no rotation at all,
just one file that grew forever) for the review use case that was always the point.

## How

```python
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():          # pick up logger.info(..., extra={...})
            if key not in _RESERVED_RECORD_ATTRS and key not in payload:
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(level=logging.INFO, *, log_to_file=True, log_dir="logs"):
    root_logger = logging.getLogger()
    if getattr(root_logger, _CONFIGURED_ATTR, False):
        return                                    # idempotent — safe to call from >1 entrypoint
    root_logger.setLevel(level)
    formatter = JSONFormatter()

    root_logger.addHandler(logging.StreamHandler(stream=sys.stdout))   # always

    if log_to_file:
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_dir_path / "app.log",
            when="midnight", backupCount=FILE_ROTATION_BACKUP_COUNT, encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    setattr(root_logger, _CONFIGURED_ATTR, True)
```

Controlled by `Settings.log_to_file` (default `True`) and `Settings.log_dir` (default `"logs"`,
project root) — per-environment overridable without a code change.

**A bug caught while fixing the idempotency guard:** the original guard checked
`isinstance(h, logging.StreamHandler)` to avoid double-registering handlers — but
`logging.FileHandler` is *itself* a subclass of `StreamHandler`, so that check would have
incorrectly treated "a file handler exists" as "stdout is already configured," silently skipping
the stdout handler once a file handler was added. Replaced with an explicit marker attribute
(`_shorties_logging_configured`) on the root logger instead of a type check.

**A second, unrelated fix bundled into the same commit:** the test suite imports `app.main` at
collection time, which triggers `configure_logging()` — meaning running `pytest` was creating a
`logs/app.log` in the repo root on every single run, with zero review value. Fixed via
`tests/conftest.py` forcing `LOG_TO_FILE=False` for the whole test session (stdout logging still
runs, just not the file).

## Alternatives considered

A third-party structured-logging library (`structlog`, `python-json-logger`) was the "don't
write it yourself" alternative. Rejected for now — the actual requirement (JSON lines, two
handlers, rotation) is small enough that a ~50-line custom formatter is less surface area than a
new dependency, and it doesn't preclude switching later if logging needs grow more complex
(structured context propagation across async calls, etc.).

## Consequences

- Two log destinations to reason about instead of one — slightly more moving parts, but each has
  a distinct, real job (platform capture vs. local review).
- `logs/` needed an explicit `.gitignore` entry (`/logs/`) — the pre-existing `*.log` pattern
  doesn't match `TimedRotatingFileHandler`'s rotated filenames (`app.log.2026-08-14`, not ending
  in `.log`), a real gap that would've leaked rotated log files into git without the fix.
