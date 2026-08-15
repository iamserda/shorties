# 0009 — Startup DB connection retry with exponential backoff

**Status:** Accepted
**Date:** 2026-08-15
**Commit:** `81e5b4c`

## Who

Me, closing out phase 1's fourth and final item.

## What

Added `wait_for_db(engine, max_attempts, base_delay_seconds)` — blocks until the DB accepts a
trivial query or gives up, backing off exponentially between attempts. Runs in `main.py`'s
`lifespan`, immediately before Alembic migrations, gated by the same
`run_migrations_on_startup` flag used in [`0006`](0006-alembic-migrations.md).

## When

2026-08-15, commit `81e5b4c`.

## Where

`src/app/db/engine.py` (new function), `src/app/main.py` (wired into `lifespan`),
`src/app/core/config.py` (`db_connect_max_attempts`, `db_connect_retry_base_delay_seconds`).

## Why

This is specifically about `docker compose` (and any environment where the app and its database
start together, which phase 2 of the roadmap is about to introduce): the app container can win
the startup race and come up *before* Postgres finishes accepting connections. Without a retry,
the very first real DB touch at boot — running migrations — just crashes the process instead of
waiting the handful of seconds Postgres needs. That's the specific, named failure mode this fixes
— not a generic "be more resilient" gesture.

## How

```python
def wait_for_db(engine: Engine, *, max_attempts: int, base_delay_seconds: float) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            delay = base_delay_seconds * (2 ** (attempt - 1))   # 1s, 2s, 4s, 8s, ...
            logger.warning(f"DB not reachable yet (attempt {attempt}/{max_attempts}), "
                            f"retrying in {delay:.1f}s", exc_info=True)
            time.sleep(delay)
```

A blocking `time.sleep()` inside an `async def lifespan` looks wrong at first glance — it isn't,
here: this runs once, during startup, before uvicorn accepts any connections at all. There's no
concurrent request handling to block; the whole point of a lifespan startup phase is that nothing
is served until it completes.

**Verified by literally reproducing the race, not just unit-testing the retry math:**

```
$ (sleep 4; pg_ctl start ...) &     # Postgres comes back 4s into the retry loop
$ python -c "wait_for_db(engine, max_attempts=8, base_delay_seconds=1.0)"
DB not reachable yet (attempt 1/8), retrying in 1.0s
DB not reachable yet (attempt 2/8), retrying in 2.0s
DB not reachable yet (attempt 3/8), retrying in 4.0s
DB became reachable after 7.2s
```

Three failed attempts (backing off 1s → 2s → 4s) while Postgres was down; by attempt 4, Postgres
had come up and the connection succeeded — recovery happened automatically, with no process
restart. The exhaustion path was verified separately (Postgres left down for the whole run):
`wait_for_db` correctly gave up and re-raised `OperationalError` after 3 attempts / 0.9s, rather
than retrying forever or hanging silently.

## Alternatives considered

**Fixed-delay retry** (same wait every attempt) instead of exponential backoff — rejected;
exponential backoff is the standard choice specifically because it adapts to "how long has this
actually been down" without either hammering a struggling service with constant reconnect
attempts or waiting unnecessarily long once it's already back.

**Retrying forever** (no `max_attempts` cap) — rejected; a DB that's *actually* misconfigured
(wrong URL, wrong credentials) should fail loudly and relatively quickly, not hang the process
indefinitely pretending it might still connect.

## Consequences

- Closes out phase 1 (Postgres & migrations) — migrations, tuned pooling, a DB-checking readiness
  probe, and now startup retry are all in place and each individually verified against a real
  Postgres instance.
- This is a good preview of exactly what `docker-compose.yaml` (phase 2, next) needs to formalize
  properly: a Postgres service with a healthcheck, and the app's `depends_on` gated on
  `condition: service_healthy` — which does at the orchestration layer what `wait_for_db` does at
  the application layer. Having both isn't redundant: compose's healthcheck avoids even starting
  the app container prematurely most of the time, and `wait_for_db` is the defense-in-depth layer
  for the cases that race past it anyway (or for running outside compose entirely, e.g. against a
  remote Render Postgres instance where nothing coordinates startup order at all).
