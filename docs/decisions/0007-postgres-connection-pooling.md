# 0007 — Tune connection pooling for Postgres

**Status:** Accepted
**Date:** 2026-08-15
**Commit:** `0b218e9`

## Who

Me, first item of phase 1 ("Postgres & migrations") after [`0006`](0006-alembic-migrations.md).

## What

Added `psycopg` (v3) as a dependency and gave `create_db_engine()` a real, three-way pooling
strategy instead of a single SQLite-only `StaticPool` branch: in-memory SQLite unchanged,
SQLite-file gets a cheap `pool_pre_ping`, and anything else (Postgres) gets a properly sized
`QueuePool` with recycling.

## When

2026-08-15, commit `0b218e9`.

## Where

`src/app/db/engine.py`, `src/app/core/config.py` (three new `Settings` fields), `pyproject.toml`
(`psycopg[binary]`).

## Why

Before this, the only pool configuration in the codebase existed to work around SQLite's
in-memory quirks — a real server (Postgres) was getting SQLAlchemy's untouched defaults. Two
specific gaps that matter for a service actually talking to a network database:

- **No `pool_pre_ping`.** Without it, a connection the *server* already dropped (idle timeout, a
  restart, a network blip) gets handed back out of the pool anyway — the failure surfaces as a
  request-time error instead of being caught and silently replaced before the caller ever sees it.
- **No `pool_recycle`.** A managed Postgres instance (Render's included) will silently close
  connections that have been idle past some threshold, server-side, without telling the client.
  Without `pool_recycle`, SQLAlchemy has no idea a pooled connection has gone stale until it tries
  to use it.

## How

```python
if is_memory_sqlite:
    engine_kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
elif is_sqlite:
    engine_kwargs = {"pool_pre_ping": True}      # cheap, harmless, no real server to time out
else:
    engine_kwargs = {
        "pool_size": settings.db_pool_size,           # default 5
        "max_overflow": settings.db_max_overflow,     # default 10
        "pool_recycle": settings.db_pool_recycle_seconds,  # default 1800 (30 min)
        "pool_pre_ping": True,
    }
```

All three Postgres-specific values live in `Settings`, tunable per environment without a code
change.

**This was verified against a real Postgres server, not asserted from the kwargs alone.** No
Docker was available in the working environment, so a throwaway local Postgres 17 cluster was
stood up directly (`initdb` + `pg_ctl` on a scratch port):

```python
engine = create_db_engine()
print(type(engine.pool).__name__)   # QueuePool
print(engine.pool.size())           # 5
print(engine.pool._max_overflow)    # 10
print(engine.pool._pre_ping)        # True
print(engine.pool._recycle)         # 1800
```

...followed by running the Alembic migrations from [`0006`](0006-alembic-migrations.md)
unmodified against it (they applied cleanly — SQLite's batch mode is simply a no-op on a dialect
that supports real `ALTER TABLE`), and a full `create → visit → analytics` cycle through the
actual API, against real Postgres.

## Alternatives considered

`NullPool` (no pooling — a new connection per request) was the "simplest possible" alternative
for Postgres. Rejected — connection setup/teardown has real latency and Postgres has a hard cap
on total concurrent connections; a bounded, reused pool is the standard choice for exactly this
reason, and `pool_pre_ping`/`pool_recycle` exist specifically to make pooling *safe* rather than
give up on it.

## Consequences

- The service has never had a real Postgres-backed request fail from a genuinely dead pooled
  connection during this session's testing — though that's a small sample, not a guarantee at
  scale.
- `psycopg[binary]` is now a dependency even though the *default* DB is still SQLite — deliberate:
  until this decision, nothing in the codebase had ever actually connected to Postgres, so
  "Postgres pooling" was previously an untested claim rather than a verified one.
