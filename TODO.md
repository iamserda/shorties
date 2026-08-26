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

## Tests and developer tooling

- [ ] Make `make precommit-all` run the full pytest suite; only print the pytest success message after the tests actually pass.
- [x] Repair API test isolation by overriding the actual FastAPI database dependency instead of patching an unused `app.main.db_engine`; all eight tests pass with an isolated configured database.
- [ ] Make the checked-in GitHub Actions workflow pass from a clean checkout with no developer `.env` file.
- [ ] Add formal endpoint coverage beyond redirect paths for health, empty/populated list, create, delete, pagination, and error behavior.
- [ ] Add security tests for rejected URL schemes, unauthorized writes, and rate-limit enforcement as those controls are introduced.
