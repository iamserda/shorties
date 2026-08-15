# 0008 — Split `/healthz` into liveness and DB-checking readiness

**Status:** Accepted
**Date:** 2026-08-15
**Commit:** `35b0363`

## Who

Me, second item of phase 1.

## What

`GET /healthz/` stays a pure liveness check (no DB access). Added `GET /healthz/ready`, which
runs a real `SELECT 1` through the connection pool and returns `503` if it fails.

## When

2026-08-15, commit `35b0363`.

## Where

`src/app/api/routes/healthz.py`.

## Why

The original `/healthz/` returned a hardcoded `{"status": "alive"}` regardless of DB state —
useless for telling a deploy platform "stop sending traffic here, the DB is unreachable." The fix
isn't "make `/healthz/` check the DB" though — that would create a *worse* problem: a liveness
probe that depends on the database means a brief, transient DB blip gets a perfectly healthy
*process* killed and restarted by the platform for no reason (the process was never the thing
that was broken). Liveness and readiness are different questions with different consequences on
failure, and conflating them is a known operational anti-pattern (it's exactly what
Kubernetes's liveness-vs-readiness probe split exists to avoid).

## How

```python
@router.get("/")
async def health_check():
    """Liveness — deliberately does not touch the database."""
    return {"status": "alive"}

@router.get("/ready")
async def readiness_check(session: Annotated[Session, Depends(get_db_session)]):
    """Readiness — a real connectivity check through the actual pool."""
    try:
        session.execute(text("SELECT 1"))
    except Exception as db_error:
        logger.exception(f"readiness check failed: {db_error}", exc_info=True)
        raise HTTPException(status_code=503, detail={"status": "not ready"})
    return {"status": "ready"}
```

**Verified against a real Postgres instance, both directions** (same scratch `initdb`/`pg_ctl`
cluster as [`0007`](0007-postgres-connection-pooling.md)):

- DB up: both endpoints return `200`.
- DB stopped mid-process (`pg_ctl stop`): `/healthz/` still `200` (the process itself is fine),
  `/healthz/ready` correctly returns `503`, and the connection failure is captured in the log
  (`logger.exception`) — so the *cause* of the readiness failure is diagnosable from logs alone,
  not just its existence.

## Alternatives considered

A single endpoint returning different status codes based on an internal flag (e.g.
`/healthz?check=db`) was considered and rejected — two distinct paths map cleanly onto how
platforms actually configure liveness vs. readiness probes (Render, Kubernetes, and most others
expect two separate URLs, not one parameterized one).

## Consequences

- Deploying this behind a platform that only ever checks one endpoint (misconfigured to point
  liveness and readiness at the same path) would silently lose the benefit of the split — worth
  double-checking whatever deploy config eventually wires this up (Render phase, still ahead).
