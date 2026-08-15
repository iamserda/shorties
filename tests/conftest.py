from __future__ import annotations

import os

# Importing app.main triggers configure_logging() at module import time.
# Tests run constantly and the resulting log file has no operational
# value, so keep file logging off for the whole test session — stdout
# logging (still exercised) is unaffected. Must be set before anything
# imports app.core.config, since Settings() is read once and cached.
os.environ.setdefault("LOG_TO_FILE", "False")

# app.main's lifespan runs `alembic upgrade head` against whatever
# DEV_DATABASE_URL resolves to (the real dev DB, or later a real
# Postgres server) — that must never run as a side effect of tests
# entering `with TestClient(app)`. Tests build and migrate their own
# isolated engine directly (see isolated_test_engine fixtures) and must
# never touch the app's real configured DB, full stop.
os.environ.setdefault("RUN_MIGRATIONS_ON_STARTUP", "False")
