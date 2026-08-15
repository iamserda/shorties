# 0003 — Remove dead dependencies and scratch files

**Status:** Accepted
**Date:** 2026-08-14
**Commit:** `6f43414`

## Who

Me, as the first step of a "foundation cleanup" phase before touching anything Postgres/Docker
related.

## What

Dropped `redis` from `pyproject.toml` (declared, never imported anywhere in `src/` or `tests/`)
and deleted `temp/temp.py` + `temp/temp2.py` — untracked scratch files containing an old,
commented-out draft of the key generator that `alnumgen.py` now implements properly.

## When

2026-08-14, commit `6f43414`.

## Where

`pyproject.toml`, `poetry.lock`; `temp/` (deleted, was never git-tracked).

## Why

An unused dependency is unaudited surface — it ships in the lockfile, gets scanned by every
security tool pointed at the repo, and adds nothing. Verified with a plain grep before removing
it (`grep -rn "redis" src/ tests/` — zero hits) rather than assuming; "looks unused" and "is
provably unused" are different claims.

The scratch files were dead weight for a different reason: they were a superseded draft of logic
that now lives properly in `alnumgen.py`, sitting in the repo purely as clutter. `temp/*` was
already `.gitignore`d, so removing them touched no git history — pure local cleanup.

## How

```diff
 dependencies = [
     "fastapi (>=0.128.0,<0.129.0)",
     "uvicorn (>=0.40.0,<0.41.0)",
-    "redis (>=7.1.0,<8.0.0)",
     "pydantic (>=2.12.5,<3.0.0)",
     "sqlmodel (>=0.0.32,<0.0.33)",
     "python-dotenv (>=1.2.2,<2.0.0)",
 ]
```

`poetry lock && poetry install` afterward confirmed nothing else depended on `redis` transitively.

## Alternatives considered

Could have wired `redis` up for something real (rate-limit counters, a cache) instead of removing
it, since a URL shortener plausibly wants both eventually. Rejected for now — adding
infrastructure "because it's already a dependency" without a concrete use is how unused
dependencies accumulate in the first place. If rate limiting lands later (roadmap phase 6), the
decision to reach for Redis specifically can be made then, on its own merits.

## Consequences

- Smaller lockfile, one fewer thing to patch/scan for CVEs with no corresponding benefit.
- If rate limiting is built later and Redis-backed, this dependency comes back deliberately, with
  actual code depending on it from day one — not re-added speculatively.
