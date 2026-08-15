# Request Lifecycle — Low-Level Design

This traces two requests through every layer, in the order things actually execute — the level
of detail I'd want if someone asked me "walk me through what happens when..." in an interview.

## App startup, before any request can be served

```python
# main.py, module level (runs once, at import time)
_settings = get_settings()
configure_logging(log_to_file=_settings.log_to_file, log_dir=_settings.log_dir)
db_engine: Engine = create_db_engine()          # cached (lru_cache) — one Engine, ever

# main.py, lifespan (runs once per process, before uvicorn accepts connections)
@asynccontextmanager
async def lifespan(app: FastAPI):
    if _settings.run_migrations_on_startup:
        wait_for_db(db_engine, max_attempts=..., base_delay_seconds=...)  # retry/backoff
        run_migrations()                         # alembic upgrade head
    yield
```

Two things worth being able to explain here:

1. **`create_db_engine()` is `@lru_cache`d.** Every call anywhere in the process — module import,
   a route's dependency resolution, a test — returns the *same* `Engine` object. Before this was
   cached, the app was silently building a new `Engine` (and, with the old default in-memory
   SQLite URL, a completely separate empty database) on every dependency resolution. See decision
   [`0001`](../decisions/0001-db-engine-session-lifecycle-fix.md).
2. **`wait_for_db` runs before `run_migrations`, both gated the same flag.** In `docker compose`
   (or any environment where the app and DB start together), the app can win the race and come up
   before Postgres is accepting connections. Without the retry, the very first DB touch — running
   migrations — would just crash the process on boot.

## Trace 1: `POST /v1/links/` (create a link)

1. **HTTP arrives** at uvicorn, routed by FastAPI to `create_link` in `api/routes/links.py`
   (matched via `router.include_router(links.router, prefix="/v1")` in `main.py`).
2. **Pydantic validates the body** against `NewUrlSubmissionModel` *before* the route function
   runs — `url: AnyHttpUrl` rejects a malformed URL here, which is why the route body never has to
   defensively re-check "is this a real URL."
3. **FastAPI resolves the route's dependencies**, including
   `session: Annotated[Session, Depends(get_db_session)]`. This is where it gets interesting:

   ```python
   # session.py
   def _get_current_engine() -> Engine:
       from app import main as main_module   # lazy import, breaks a circular import
       return main_module.db_engine           # reads the module attribute *at call time*

   def get_db_session(db_engine: Annotated[Engine, Depends(_get_current_engine)]):
       if not db_engine or not isinstance(db_engine, Engine):
           raise DBEngineError(...)
       with Session(db_engine) as session:
           yield session
   ```

   `_get_current_engine()` doesn't just return `create_db_engine()` directly — it reads
   `app.main.db_engine` fresh on every call. That's deliberate: it's the hook that lets tests swap
   in an isolated engine (`monkeypatch.setattr("app.main.db_engine", test_engine)`) without any
   test-specific branching in application code. See
   [`0001`](../decisions/0001-db-engine-session-lifecycle-fix.md) for why this wasn't always true
   — the session used to close itself before the route ever got to use it.
4. **If step 3 raises** (`DBEngineError`, e.g. the engine is `None`), it happens *before* the
   route body executes at all — a route's own `try/except` never sees it. That's why there's a
   dedicated `@app.exception_handler(DBEngineError)` registered on the `FastAPI` app itself in
   `main.py`:

   ```python
   @app.exception_handler(DBEngineError)
   async def db_engine_error_handler(request, exc):
       logger.exception(f"error: {exc}", exc_info=exc)
       return JSONResponse(status_code=500, content={"detail": {"error": {...}}})
   ```

   This is a direct, non-obvious consequence of how FastAPI's dependency injection is layered —
   worth stating explicitly if asked "where do your error handlers live and why."
5. **The route body runs**, with a live `session` in hand:

   ```python
   for _ in range(MAX_KEY_GENERATION_ATTEMPTS):        # 5
       shorti_key = alnum_generator()                   # secrets.choice, not random
       link = ShortiLink(shorti_key=shorti_key, shorti_url=str(submission.url), ...)
       session.add(link)
       try:
           session.commit()
       except IntegrityError:                            # unique constraint on shorti_key
           session.rollback()
           continue
       session.refresh(link)                              # pulls back DB-generated id, defaults
       return _to_response_model(link)
   raise HTTPException(500, "Could not generate a unique short link key...")
   ```

6. **Response serialization**: `_to_response_model(link)` maps the ORM row to
   `GetUrlResponseModel` (the *public* shape) — this is the seam between the DB schema and the API
   contract; adding an internal-only column to `ShortiLink` doesn't leak it into the API by
   accident, because the response model is explicit about what it includes.
7. **After the response is sent**, FastAPI closes the `with Session(...)` block from step 3 —
   this only happens *after* the route handler returns, because `get_db_session` is a generator
   dependency (`yield`, not `return`). Before this was fixed, the session closed itself before the
   route ever touched it.

## Trace 2: `GET /v1/links/{key}/visit` (the redirect)

This is the highest-traffic path in the system by design — it's what a browser hits, not an API
client — so it's worth tracing separately.

1. Same dependency resolution as above (`get_db_session`).
2. `_get_link_or_404` — a single `SELECT` filtered on `shorti_key` *and* `deleted_at IS NULL`
   (soft-deleted links 404 here exactly like a nonexistent key; the caller can't distinguish
   "never existed" from "was deleted," which is intentional).
3. **Three writes in one transaction**, then a single commit:
   ```python
   link.hit_count += 1
   link.last_accessed_at = now
   session.add(link)
   session.add(LinkClickEvent(shorti_link_id=link.id, clicked_at=now,
                               referrer=request.headers.get("referer"),
                               user_agent=request.headers.get("user-agent"),
                               ip_address=request.client.host if request.client else None))
   session.commit()
   ```
   The counter update and the event-log insert are committed together — a redirect that fails
   partway through (e.g. the event insert fails) rolls back the counter increment too, so
   `hit_count` and the count of `linkclickevent` rows for that link can never silently drift apart.
4. `RedirectResponse(url=link.shorti_url, status_code=link.redirect_code)` — the status code isn't
   hardcoded; it's whatever was configured on the link.

## What happens on a DB-layer failure mid-request (not at dependency-resolution time)

If the DB fails *during* the route body (step 5/3 above), it's caught by each route's own
`try/except Exception`, logged via `logger.exception(...)`, and turned into the same structured
500 envelope as the dependency-layer handler — so the client sees a consistent error shape
regardless of *where* in the request lifecycle the DB failure happened, even though the two code
paths that catch it are different (app-level handler vs. per-route `except`).

## Where a connection actually comes from

`Session(db_engine)` in `get_db_session` doesn't open a new physical DB connection by itself —
SQLAlchemy's `Engine` owns a **connection pool**, sized per DB type (see
[`0007`](../decisions/0007-postgres-connection-pooling.md)):

- In-memory SQLite: `StaticPool` — one shared connection, because in-memory SQLite is
  per-connection by default and a real pool would mean every "connection" sees an empty DB.
- SQLite file: default pool + `pool_pre_ping=True`.
- Anything else (Postgres): `QueuePool` sized via `Settings` (`pool_size`, `max_overflow`), plus
  `pool_recycle` (drop connections older than N seconds, since a managed Postgres instance closes
  idle connections server-side) and `pool_pre_ping` (catch a connection the server already
  dropped, before it surfaces as a request failure instead of after).
