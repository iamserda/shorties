# API Reference

Base path: `/{API_VERSION}` — `API_VERSION` defaults to `v1` (`Settings.api_version`), so every
path below is really `/v1/...` today. Source: [`src/app/api/routes/links.py`](../../src/app/api/routes/links.py),
[`src/app/api/routes/healthz.py`](../../src/app/api/routes/healthz.py).

## Health

| Verb | Path | Success | Failure | DB touched? |
|---|---|---|---|---|
| GET | `/healthz/` | `200 {"status": "alive"}` | — | No |
| GET | `/healthz/ready` | `200 {"status": "ready"}` | `503 {"status": "not ready"}` | Yes (`SELECT 1`) |

**Why two, not one:** `/healthz/` is a *liveness* check — "is the process up at all" — and
deliberately does **not** touch the database. `/healthz/ready` is a *readiness* check — "can this
instance actually serve a DB-backed request right now." The distinction matters operationally: a
platform that restarts a container on a failed liveness check would kill and restart a perfectly
healthy process just because the DB had a momentary blip, if liveness depended on the DB. A
readiness failure, by contrast, should just stop routing traffic there — no restart needed. See
decision [`0008`](../decisions/0008-healthz-liveness-readiness-split.md).

## Links

| Verb | Path | Success | Failure |
|---|---|---|---|
| GET | `/links/` | `200` | `422` (bad query params), `500` |
| POST | `/links/` | `201` | `422` (invalid body), `500` |
| GET | `/links/{key}` | `200` | `404`, `500` |
| PUT | `/links/{key}` | `200` | `404`, `422`, `500` |
| DELETE | `/links/{key}` | `204` | `404`, `500` |
| GET | `/links/{key}/visit` | `301` / `302` / `307` | `404`, `500` |
| GET | `/links/{key}/analytics` | `200` | `404`, `500` |

### `GET /links/`

Query params: `offset: int = 0`, `limit: int = 20 (max 20)`, `include_deleted: bool = False`.

Returns `200` with `{"urls": []}` when the table is empty — **not** a `404`. An empty collection
is a valid state, not an error; conflating "nothing here" with "something's wrong" is a real
anti-pattern worth naming out loud in an interview.

By default, filters `WHERE deleted_at IS NULL`. `include_deleted=true` is the escape hatch for
seeing soft-deleted rows — an admin/audit path, not exposed any other way.

### `POST /links/`

Body: `NewUrlSubmissionModel` — `url: AnyHttpUrl` (required, validated), `brand: str | None`,
`redirect_code: Literal[301, 302, 307] = 307`.

Returns `201` (not `200` — a new resource was created) with the full link, including the
generated `key`. Key generation retries up to `MAX_KEY_GENERATION_ATTEMPTS = 5` times on a unique
constraint collision:

```python
for _ in range(MAX_KEY_GENERATION_ATTEMPTS):
    shorti_key = alnum_generator()
    link = ShortiLink(shorti_key=shorti_key, ...)
    session.add(link)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        continue
    session.refresh(link)
    return _to_response_model(link)
raise HTTPException(status_code=500, detail="Could not generate a unique short link key...")
```

### `GET /links/{key}`, `PUT /links/{key}`, `DELETE /links/{key}`

Standard single-resource CRUD, all routed through a shared helper:

```python
def _get_link_or_404(session, shorti_key, *, include_deleted=False) -> ShortiLink:
    statement = select(ShortiLink).where(ShortiLink.shorti_key == shorti_key)
    if not include_deleted:
        statement = statement.where(col(ShortiLink.deleted_at).is_(None))
    link = session.exec(statement).first()
    if link is None:
        raise _not_found(shorti_key)
    return link
```

`DELETE` is a **soft** delete — sets `deleted_at`/`updated_at`, never removes the row — but the
response contract is identical to a hard delete: `204`, no body. A second `DELETE` on an
already-deleted key returns `404` (it's filtered out of the "exists" check the same as any other
deleted row), which makes the endpoint naturally idempotent from the caller's point of view.

`PUT`, not `PATCH`, despite every field in `UpdateUrlRequestModel` being optional (a partial
update). This is a known, minor REST-semantics mismatch — worth naming if asked, not worth
fixing reflexively (`PUT` here behaves correctly, it's just not the textbook verb for it).

### `GET /links/{key}/visit`

The actual redirect endpoint — the one a browser hits, not an API client. Resolves the link,
increments `hit_count`, stamps `last_accessed_at`, records a `LinkClickEvent`, then redirects
using the link's own `redirect_code`:

```python
link = _get_link_or_404(session, shorti_key)
now = utcnow()
link.hit_count += 1
link.last_accessed_at = now
session.add(link)
session.add(LinkClickEvent(
    shorti_link_id=link.id,
    clicked_at=now,
    referrer=request.headers.get("referer"),
    user_agent=request.headers.get("user-agent"),
    ip_address=request.client.host if request.client else None,
))
session.commit()
return RedirectResponse(url=link.shorti_url, status_code=link.redirect_code)
```

This is the one endpoint where the "success" status code isn't fixed — it's whatever
`redirect_code` was configured on the link at creation/update time.

### `GET /links/{key}/analytics`

Returns `hit_count`, `created_at`, `updated_at`, `last_accessed_at`, and the 20 most recent click
events (`RECENT_CLICKS_LIMIT = 20`), newest first.

## Error shape

Every 500-class error from within a route body follows the same envelope:

```json
{
  "detail": {
    "error": {
      "type": "DBEngineError",
      "description": "...",
      "status-code": 500,
      "message": "A server-side error occurred! ..."
    }
  }
}
```

`DBEngineError`/`DBSessionError` raised **during dependency resolution** (before a route body
even starts) don't go through a route's own `try/except` — they're caught by an app-level
`@app.exception_handler(DBEngineError)` in `main.py`, which produces the same envelope. This is a
direct consequence of how FastAPI's dependency injection works — see
[`04-request-lifecycle.md`](04-request-lifecycle.md).

## What's not here (yet)

No auth on anything — every endpoint above is fully open. No rate limiting. No CORS policy. These
are known, tracked gaps (see the roadmap phase 6), not oversights.
