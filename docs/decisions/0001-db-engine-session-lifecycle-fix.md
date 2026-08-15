# 0001 — Fix the DB engine/session lifecycle

**Status:** Accepted
**Date:** 2026-08-14
**Commit:** `440aa50`

## Who

Me, during a code review of the DB layer I'd inherited from an earlier pass — the review found
four separate, compounding bugs in how the app created and used its database connection.

## What

Fixed the DB engine and session lifecycle: made `create_db_engine()` return a true process-wide
singleton, turned `get_db_session()` into a proper generator dependency instead of one that closed
its session before returning it, moved table creation into a FastAPI `lifespan` handler (off a
`__main__`-guarded block that never ran in uvicorn's reload subprocess), added an app-level
exception handler for `DBEngineError`, and deleted an `eval()` call on an environment variable.

## When

2026-08-14, landed in commit `440aa50` alongside the CRUD/analytics feature (see
[`0002`](0002-links-crud-analytics-soft-delete.md)) — found during the review that preceded that
feature work.

## Where

`src/app/db/engine.py`, `src/app/db/session.py`, `src/app/main.py`.

## Why

Four independent bugs, each one a plausible root cause of "the app works in dev but does
something inexplicable under load or on redeploy" — exactly the kind of bug that's expensive to
diagnose in production and cheap to fix in review:

**1. Multiple engines, silently.** `get_db_session()`'s original signature depended on
`create_db_engine` via normal FastAPI dependency injection, which called `create_db_engine()`
fresh on every resolution — a brand-new `Engine` per request, not the one built once at app
startup. With the *original* default DB URL being in-memory SQLite, "a new Engine" meant a
completely separate, empty database per request. The architecture comment literally said "create
this Engine once and reuse it for the entire app lifecycle" — and the code didn't do that.

**2. Sessions closed before they were used.**

```python
# before
def get_db_session(db_engine):
    ...
    with Session(db_engine) as session:
        return session          # __exit__ runs as part of `return`, closing the session
                                  # *before* the caller ever receives it
```

`return` inside a `with` block triggers `__exit__` as part of unwinding, before the value reaches
the caller. Every session this function handed out had already been closed at the moment of
receipt. Not an immediate crash (SQLAlchemy sessions can silently reopen a transaction on next
use), but the intended lifecycle — open at request start, close after — was inverted, and it was
the kind of bug that would eventually surface as something much stranger downstream.

**3. Table creation that never actually ran.**

```python
# before, in main.py
def populate_db(db_engine=Annotated[AsyncGenerator[Engine, None], Depends(create_db_engine)]):
    if isinstance(db_engine, Engine):
        SQLModel.metadata.create_all(bind=db_engine)
```

`Annotated[...]`/`Depends(...)` as a default value only means something when FastAPI resolves it
as a route dependency. Called directly (`populate_db()`), `db_engine` was literally the
`Annotated[...]` type object — `isinstance(db_engine, Engine)` was always `False`. This function
never actually created a table through this path. On top of that, it was called from inside
`if __name__ == "__main__":`, which never runs in uvicorn's `reload=True` worker subprocess (the
process that actually serves requests) — so even fixed, it was in the wrong place.

**4. `eval()` on an environment variable.**

```python
API_VERSIONS = (
    eval(os.getenv("API_VERSIONS", "[/v1]")) if os.getenv("API_VERSIONS") else ["/v1"]
)
```

`eval()` on anything derived from the environment is a real code-execution risk if that variable
is ever attacker-influenced (a compromised deploy config, an injected `.env`). Also just... never
needed a real parser here; it's a comma-separated list.

## How

```python
# after — engine.py
@lru_cache(maxsize=1)
def create_db_engine() -> Engine:
    ...
    return db_engine
```
`@lru_cache(maxsize=1)` makes every call — direct or via DI — return the same object. Simple,
and it's the correct tool here: this function takes no arguments that should vary, so a
size-1 cache is exactly "compute once."

```python
# after — session.py
def get_db_session(db_engine: Annotated[Engine, Depends(_get_current_engine)]):
    if not db_engine or not isinstance(db_engine, Engine):
        raise DBEngineError(...)
    with Session(db_engine) as session:
        yield session            # FastAPI closes the session *after* the route returns
```

```python
# after — main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    populate_db(db_engine)       # (later replaced by Alembic migrations, see 0006)
    yield

app = FastAPI(title="Shorties App", lifespan=lifespan)

API_VERSION = os.getenv("API_VERSION", "v1")   # (later moved into Settings, see 0004)
```

```python
@app.exception_handler(DBEngineError)
async def db_engine_error_handler(request, exc):
    ...
    return JSONResponse(status_code=500, content={...})
```

## Alternatives considered

For the closed-session bug, the alternative to a generator dependency was keeping `return` but
moving the `Session(...)` construction *outside* any `with` block and relying on FastAPI's
`request.state` teardown to close it manually. Rejected — a generator dependency is the idiomatic
FastAPI pattern for exactly this (open resource → yield → cleanup), and doesn't require manually
wiring a teardown hook.

## Consequences

- Every route's DB session now genuinely lives for the request and only the request — no more
  premature closes, no more silently-different Engines per call.
- The fix surfaced *because* of a broader review — it's a reminder that "the tests pass" and "the
  architecture does what its own comments say it does" are different claims, and worth checking
  both.
