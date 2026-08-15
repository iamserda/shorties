# 0006 — Introduce Alembic migrations (and the bug that proved it necessary)

**Status:** Accepted
**Date:** 2026-08-15
**Commit:** `9f4f88c`

## Who

Me. This one has an unusual origin: it wasn't planned as "next thing to build" — it was
triggered by a real, reproducible production-shaped bug the service owner hit while running the
app locally, right after [`0002`](0002-links-crud-analytics-soft-delete.md)'s schema changes
shipped.

## What

Replaced `SQLModel.metadata.create_all()` — the app's only schema-creation mechanism — with real
Alembic migrations: a historical baseline (`0001_initial_shortilink.py`) plus the analytics/
soft-delete columns as an actual versioned migration (`0002_add_analytics_and_soft_delete.py`),
run automatically via `alembic upgrade head` in the app's `lifespan` handler.

## When

2026-08-15, commit `9f4f88c`. The triggering incident happened the same session, immediately
after `0002` shipped.

## Where

New: `alembic.ini`, `alembic/env.py`, `alembic/versions/*.py`. Updated: `main.py` (migration
runner replaces `populate_db`), `core/config.py` (`run_migrations_on_startup` flag), `db/db.py`
(deleted `dev_create_db()` — see **Consequences**).

## Why — the incident

`GET /v1/links/` started returning `500 Internal Server Error`. The log (once file logging was
in place — see [`0005`](0005-structured-logging.md)) showed the real error under the generic
500:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: shortilink.redirect_code
```

Root cause: the service owner had a **real, persistent** SQLite file
(`DEV_DATABASE_URL=sqlite:///./src/app/db/shorties_database.db`, not the in-memory DB the test
suite uses) with 65 real rows in it, created before [`0002`](0002-links-crud-analytics-soft-delete.md)'s
six new columns existed. `SQLModel.metadata.create_all()`, the app's only schema-creation
mechanism, **only creates tables that don't exist yet** — it silently does nothing when a column
is added to a table that's already there. The new `linkclickevent` table got created fine (it
didn't exist); the six new columns on the already-existing `shortilink` table never did. Every
query built against the *current* `ShortiLink` model — which expects those columns — failed at
the DB level.

This is the textbook argument for migrations, made concrete instead of theoretical: "you should
use migrations because `create_all()` doesn't handle schema evolution" went from a sentence in a
roadmap to an actual `500` with an actual stack trace within the same working session.

## How

**The baseline migration** reconstructs the schema as it genuinely existed before this session's
changes — not a fabricated "let's pretend from empty" migration, an accurate historical one:

```python
# 0001_initial_shortilink.py
def upgrade() -> None:
    op.create_table(
        "shortilink",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shorti_key", sa.String(), nullable=False),
        sa.Column("shorti_url", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shortilink_shorti_key", "shortilink", ["shorti_key"], unique=True)
    op.create_index("ix_shortilink_shorti_url", "shortilink", ["shorti_url"], unique=False)
```

**The second migration** was generated via `alembic revision --autogenerate` against a scratch DB
seeded to `0001`, then hand-corrected for two gaps autogenerate left:

```python
# 0002_add_analytics_and_soft_delete.py — the critical part
with op.batch_alter_table("shortilink", schema=None) as batch_op:
    batch_op.add_column(sa.Column("redirect_code", sa.Integer(), nullable=False, server_default="307"))
    batch_op.add_column(sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"))
    batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=False,
                                    server_default=sa.text("CURRENT_TIMESTAMP")))
    # ...
```

The `server_default` on every `NOT NULL` column is not optional decoration — without it, this
migration fails immediately against any database with existing rows (SQLite, like most databases,
can't add a `NOT NULL` column with no way to backfill existing rows). Autogenerate doesn't add
these on its own; they were added by hand and are the specific detail that made this migration
safe to run against the real 65-row database rather than just a theoretically-correct one.

`op.batch_alter_table` (SQLite "batch mode," configured via `render_as_batch=True` in
`alembic/env.py`) exists because SQLite has extremely limited native `ALTER TABLE` support —
batch mode works around it by rebuilding the table under the hood, preserving data.

**Fixing the actual broken database**, rather than discarding it: backed up the file, dropped an
empty `linkclickevent` table that `create_all()` had already half-created, stamped the DB at
revision `0001` (its true shape), then ran `alembic upgrade head`. All 65 rows survived with
correctly backfilled defaults. Verified before calling it done:

```
sqlite> SELECT shorti_key, redirect_code, hit_count, created_at FROM shortilink LIMIT 1;
scap|307|0|2026-08-15 04:24:01
```

...and the exact originally-failing request, re-run against the fixed database, returned `200`.

**A second landmine removed in the same commit:** `db/db.py`'s `dev_create_db()` still called
`SQLModel.metadata.create_all()` directly — the exact same broken pattern that caused this
incident, left in place as something someone could accidentally run again later. Deleted.

## Alternatives considered

**"Just delete the DB file and let it regenerate"** was the fast option, explicitly offered and
explicitly rejected — the file had 65 real rows in it, and "throw away data to make a bug go
away" is a worse habit to build than the ten extra minutes migrations took.

**Single-migration baseline** (one migration representing the *current* full schema, applied to
an empty DB) was considered instead of the two-migration split. Rejected — it wouldn't reflect
actual schema history, and it couldn't be applied to the real dev DB without conflict (the DB
already had a `0001`-shaped table). The two-migration structure mirrors what genuinely happened
and reconciles cleanly with a database that was already partway there.

## Consequences

- Schema changes now go through a reviewable, ordered file — the exact category of change that
  caused this incident can no longer happen silently.
- `main.py`'s lifespan now runs migrations automatically on boot (`wait_for_db` +
  `alembic upgrade head`, gated by `Settings.run_migrations_on_startup`), which is convenient
  locally but is a real decision with a tradeoff: some teams prefer migrations as a distinct
  deploy step rather than baked into app startup, specifically so a bad migration can't take down
  every running instance simultaneously on a rolling deploy. Not solved here — worth revisiting
  once there's a real deploy pipeline (Docker/Render phases).
- `run_migrations_on_startup` had to be explicitly gated off during tests
  (`tests/conftest.py`, `RUN_MIGRATIONS_ON_STARTUP=False`) — without it, every `TestClient(app)`
  instantiation would run real Alembic migrations against whatever `DEV_DATABASE_URL` resolves to,
  which is exactly the "tests must never touch the real configured DB" rule this project holds to.
  Verified via checksum: a full test run leaves the real dev DB file byte-identical.
