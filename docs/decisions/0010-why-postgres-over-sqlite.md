# 0010 — Why move from SQLite to Postgres

**Status:** Accepted (infrastructure built and verified; default cutover still pending)
**Date:** 2026-08-15 (this document; the underlying work spans `9f4f88c` through `81e5b4c`)

## Who

Me — this is a synthesis document tying together four separate commits
([`0006`](0006-alembic-migrations.md)–[`0009`](0009-startup-retry-backoff.md)) into the single
answer to a question that's genuinely one decision, even though it landed as four.

## What

The service's *default* is still SQLite (`sqlite:///:memory:` if `DEV_DATABASE_URL` is unset).
What changed is that the app now **fully supports Postgres** — migrations, connection pooling,
readiness checks, and startup retry are all built and independently verified against a real
Postgres 17 instance. Flipping the default (and deploying against Render's managed Postgres) is
the next concrete step, not a separate redesign.

## When

Infrastructure work: 2026-08-15. The actual cutover (making Postgres the deployed default)
depends on the Docker (phase 2) and Render deploy (phase 4) work, still ahead.

## Where

Spans `db/engine.py`, `alembic/`, `api/routes/healthz.py`, `core/config.py` — see the individual
decision records for each piece.

## Why — the actual argument, not just "Postgres is more popular"

**SQLite's limits are real and specific, not vague "it's not enterprise enough":**

1. **Concurrent writers.** SQLite locks the entire database file for a write. That's fine for a
   single process on a laptop; it's a real bottleneck the moment more than one process (or more
   than one uvicorn worker) needs to write at the same time — which any real deployment with more
   than one instance running for availability will have.
2. **Ephemeral filesystems.** A SQLite file lives on local disk. On a container platform, local
   disk doesn't survive a restart or redeploy unless it's explicitly backed by a persistent
   volume — and even with one, a single-file database doesn't horizontally scale the way a real
   database server does. This project's own file-logging decision
   ([`0005`](0005-structured-logging.md)) is the same "ephemeral filesystem" argument applied to a
   different resource — the reasoning generalizes.
3. **No real connection pooling story.** SQLite doesn't have a server to pool connections *to* —
   the "pool" tuning that matters for Postgres ([`0007`](0007-postgres-connection-pooling.md))
   doesn't have an equivalent on SQLite because there's no network hop, no server-side connection
   limit, no server-side idle timeout to guard against.
4. **In-memory SQLite is per-connection unless forced otherwise** — this project actually hit this
   directly: `sqlite:///:memory:` gives each new connection a *separate, empty* database unless a
   `StaticPool` forces every connection to share one. That's a workaround for a limitation, not a
   feature — Postgres has no equivalent gotcha because it's a real client-server database where
   "the database" means one thing regardless of how many connections are open to it.

**What SQLite is genuinely good for, and why it's still the dev default:** zero setup, a single
file, no server process to run. For local development and the test suite (isolated in-memory
engines, see `tests/conftest.py`), those properties are exactly right — fast, hermetic,
no external dependency. The decision isn't "SQLite is bad," it's "SQLite and Postgres are good
at different things, and a service meant to run in production needs the one built for
production."

## How — the shape of what "supporting both" actually required

Every one of these had to be built *because* SQLite and Postgres genuinely behave differently,
not as pattern-matching "best practice checklist" items:

- **Migrations** ([`0006`](0006-alembic-migrations.md)) — needed regardless of which DB, but the
  SQLite-specific "batch mode" (`render_as_batch=True`) exists because SQLite can't do a real
  `ALTER TABLE`; verified the same migrations apply unmodified to Postgres, where batch mode is
  simply a no-op.
- **Pooling** ([`0007`](0007-postgres-connection-pooling.md)) — `StaticPool` for SQLite's
  in-memory quirk vs. a tuned `QueuePool` for Postgres are solving *different* problems that
  happen to live in the same function.
- **Readiness check** ([`0008`](0008-healthz-liveness-readiness-split.md)) — matters more for
  Postgres than SQLite: a SQLite file being "unreachable" basically means a disk failure; a
  Postgres *server* being unreachable (network partition, the DB instance restarting) is a
  routine, expected failure mode in production that a readiness probe exists specifically to
  catch.
- **Startup retry** ([`0009`](0009-startup-retry-backoff.md)) — has no SQLite equivalent at all;
  there's no "SQLite isn't ready yet" the way there's "Postgres hasn't finished starting yet" in a
  multi-container environment.

## Alternatives considered

**Skip SQLite entirely, require Postgres even for local dev** — rejected. It would mean every
contributor needs a running Postgres instance (or Docker) just to run the test suite, which is a
real friction cost for a project whose test suite currently runs in well under a second against
in-memory SQLite. The dual-support approach costs more *implementation* complexity (branching pool
config, etc.) in exchange for less *contributor* friction — a deliberate tradeoff, not the only
correct one.

## Consequences

- The codebase now has to correctly handle three DB-URL shapes (in-memory SQLite, SQLite file,
  everything else) instead of one — more branching in `engine.py`, verified by dedicated
  tests/manual runs against each shape rather than assumed to work by symmetry.
- Until the default actually flips (pending Docker/Render), "the service supports Postgres" is a
  true but slightly aspirational claim — accurate to say in an interview, worth being precise
  about the distinction between "built and verified" and "is what's actually deployed today."
