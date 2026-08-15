from __future__ import annotations

import os

# Importing app.main triggers configure_logging() at module import time.
# Tests run constantly and the resulting log file has no operational
# value, so keep file logging off for the whole test session — stdout
# logging (still exercised) is unaffected. Must be set before anything
# imports app.core.config, since Settings() is read once and cached.
os.environ.setdefault("LOG_TO_FILE", "False")
