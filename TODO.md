# Shorties TODO

Personal repository checklist. Status was reviewed against local branch
`new_feature_00001` at commit `3f9cc85`.

## Fix urgently

- [ ] Require strict HTTP/HTTPS URL validation for submitted destinations; remove the `AnyHttpUrl | str` validation bypass and add redirect-abuse tests.
- [ ] Add authentication and authorization for write operations, especially link deletion; the public list endpoint currently exposes every key needed to delete a link.
- [ ] Add rate limiting and abuse protection for link creation and deletion.
- [x] Fail fast when the configured database URL is missing or empty instead of silently using an in-memory database.
- [ ] Make CI supply an isolated test database configuration before importing the app; the checked-in workflow currently fails during test collection without `DEV_DATABASE_URL`.
- [ ] Stop forcing SQLAlchemy `echo=True` at application startup so destination URLs and SQL parameters are not indiscriminately written to logs outside development.
- [ ] Keep database configuration out of request parameters: `Depends(get_db_engine)` currently exposes `db_url` (an environment-variable name) and `dev_mode` as client-controlled query parameters. Resolve both from server configuration and verify they disappear from OpenAPI and cannot change database selection or SQL logging through a request.
- [ ] Stop returning raw exception text from the create route's catch-all handler; return a generic server-error response while retaining diagnostic details in logs. Add a regression check that an injected internal exception message is absent from the response.

## API correctness and error handling

- [x] Fix the leading-slash mismatch in API-prefix validation so the configured value is not silently rewritten.
- [ ] Restrict API-version configuration to the only implemented API (`v1`) until genuine version-specific routers and contracts exist.
- [x] Return `200` with `[]` when `GET /links` finds no links.
- [ ] Stop raising and traceback-logging a `ValueError` for the normal empty-list case; return `[]` directly or use non-error control flow.
- [ ] Replace dictionary-valued `ValueError` control flow for actual `GET /links` failures with explicit database exception classes and structured engine/session errors.
- [ ] Simplify redirect 404 handling so an `HTTPException` is not caught and wrapped into a larger nested error response.
- [ ] Rename the `offeset` query parameter to `offset` and apply offset/limit pagination to the database query.
- [ ] Remove the unreachable `raise Exception(status_code=..., detail=...)` after the successful create response.
- [ ] Retry generated-key collisions instead of returning a client-facing integrity error for a server-generated key.
- [ ] Correct the delete-not-found response so it interpolates the requested key instead of returning the literal `{shorti_key}` placeholder.
- [ ] Make `shorti_url` required instead of defaulting to a sample image URL: posting `{}` currently creates a link successfully. Verify missing destinations return a validation error without inserting a row.
- [ ] Resolve the ignored `redirect_code` request field: either persist and honor the supported codes or remove the option from the request contract. A link created with `redirect_code=301` currently redirects with `307`; test the exact chosen behavior.

## Architecture and maintainability

- [ ] Move logging setup, database-engine creation, and table creation out of module-import time and into an explicit application lifecycle.
- [ ] Finish or remove the remaining empty stubs, including `core/config.py` and `schemas/links.py`.
- [ ] Remove production `print()` debugging from the delete route and database-session helpers; use configured logging where appropriate.
- [ ] Use `logging.getLogger(__name__)` instead of directly constructing `Logger`, and avoid exception-level tracebacks for expected 404/empty-result behavior.
- [ ] Separate liveness from database readiness; an empty but reachable database should not report its connection as `unknown`.
- [ ] Replace automatic `SQLModel.metadata.create_all()` startup behavior with a controlled schema-migration workflow before production deployment.
- [ ] Build and verify a functional Dockerfile and Docker Compose development/deployment workflow.
- [ ] Make `.env.example` copy-ready with safe local defaults or document every required value clearly enough that Quickstart works as written.
- [ ] Update README claims that no longer match the reviewed branch, including pagination, active route/session modules, and what `make precommit-all` executes.
- [ ] Reuse one application-owned database engine across requests and dispose it at shutdown, while keeping sessions scoped to requests. `get_db_engine()` currently constructs a new engine on every call; verify reuse separately from moving startup work into the lifecycle.
- [ ] Preserve downstream HTTP errors in `get_session`: its broad exception handler currently turns an `HTTPException(404)` thrown through the yielded session into a `500`. Narrow the database-error boundary and test that intended HTTP statuses survive session cleanup.
- [ ] Register the table models before `create_dev_db()` calls `SQLModel.metadata.create_all()`. Importing the bootstrap module alone currently leaves metadata empty; verify the standalone bootstrap creates the `ShortiLink` table in a temporary SQLite database and can be rerun safely.

## Tests and developer tooling

- [ ] Make `make precommit-all` run the full pytest suite; only print the pytest success message after the tests actually pass.
- [x] Repair API test isolation by overriding the actual FastAPI database dependency instead of patching an unused `app.main.db_engine`; all eight tests pass with an isolated configured database.
- [ ] Make the checked-in GitHub Actions workflow pass from a clean checkout with no developer `.env` file.
- [ ] Add formal endpoint coverage beyond redirect paths for health, empty/populated list, create, delete, pagination, and error behavior.
- [ ] Add security tests for rejected URL schemes, unauthorized writes, and rate-limit enforcement as those controls are introduced.
- [ ] Settle the database-factory exception contract and align implementation and tests without weakening assertions. In the reviewed working tree, the non-string and empty-URL tests expect `TypeError`/`ValueError`, but receive `HTTPException`/`DbUrlInvalidError`; both fail. Keep database-layer failures distinct from HTTP translation and treat server configuration failures as server errors rather than client `400` responses.
