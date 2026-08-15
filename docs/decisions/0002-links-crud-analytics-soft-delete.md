# 0002 — CRUD, redirect, analytics, and soft delete

**Status:** Accepted
**Date:** 2026-08-14
**Commit:** `440aa50`

## Who

Me, in response to "restructure the db and records stored to reflect a real service — hit count
and analytics, soft deletes, etc." Three sub-decisions inside this were explicitly put to a
choice rather than assumed (see **Alternatives considered**).

## What

Took the service from "list links, that's it" to a real CRUD API with a redirect endpoint, hit
tracking, per-click analytics, and non-destructive deletes. Concretely: `POST/GET/PUT/DELETE
/links/`, `GET /links/{key}/visit` (the actual redirect), `GET /links/{key}/analytics`, and six
new columns + one new table on the data model (see
[`02-data-model.md`](../architecture/02-data-model.md)).

## When

2026-08-14, commit `440aa50` (same commit as [`0001`](0001-db-engine-session-lifecycle-fix.md) —
the lifecycle fixes were found while building this).

## Where

`src/app/api/routes/links.py`, `src/app/db/models/models.py`, `src/app/schemas/schemas.py`,
`tests/links_crud_test.py`.

## Why

A URL shortener that can only list existing links isn't a service, it's a read-only view. "Real
service" specifically meant: something can create/change/remove its own data, and something
produces evidence of how it's actually being used — hit counts and analytics are what turn "a
link" into "a link someone can reason about."

Three specific design questions came up that had more than one reasonable answer, so they were
asked rather than assumed:

1. **Should `/visit` actually redirect, or just track hits some other way?** Chose to make it a
   real redirect endpoint — without one, `hit_count` has nothing that would ever increment it.
   "Track hits" implies something is being hit.
2. **Are soft-deleted links visible anywhere, or fully hidden?** Chose "hidden by default, with an
   `include_deleted` admin escape hatch" — full invisibility would make soft delete
   indistinguishable from hard delete from the API's point of view, defeating the point of doing
   it non-destructively.
3. **Counter-only analytics, or a full per-click event log?** Chose the full log
   (`LinkClickEvent`) — a single counter can't answer "who's actually visiting this and from
   where," which is the more interesting half of "analytics."

## How

```python
class ShortiLink(SQLModel, table=True):
    ...
    redirect_code: int = Field(default=307)
    hit_count: int = Field(default=0)
    last_accessed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = Field(default=None, index=True)

class LinkClickEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    shorti_link_id: int = Field(foreign_key="shortilink.id", index=True)
    clicked_at: datetime = Field(default_factory=utcnow, index=True)
    referrer: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    ip_address: str | None = Field(default=None)
```

Route-level, every soft-delete-aware read shares one filter helper (`_get_link_or_404`, see
[`04-request-lifecycle.md`](../architecture/04-request-lifecycle.md)) so "hide deleted rows" is
enforced in exactly one place rather than repeated per query.

## Alternatives considered

- **Hard delete instead of soft delete** — rejected per the "real service" framing itself: a real
  service doesn't lose data on a fat-fingered `DELETE`, and analytics on a deleted link should
  still be recoverable/auditable.
- **`updated_at` via a DB-level trigger/`onupdate`** instead of setting it explicitly in each
  mutating route — went with explicit, so the application always states clearly *when* and *why*
  a row changed, rather than that knowledge living implicitly in the DB.

## Consequences

- The public API surface roughly tripled (1 route → 7). More surface to test — landed with 26 new
  test cases (`tests/links_crud_test.py`) covering create, get, update, soft-delete, visit, and
  analytics, including the 404/idempotency edges.
- The event log (`LinkClickEvent`) is unbounded growth by design — nothing currently caps or
  archives it. Acceptable at current scale; a real gap at high traffic (tracked, not solved here).
- No auth on any of these new mutating endpoints — anyone can create/edit/delete any link. Known,
  explicit gap; see the roadmap's security/hardening phase.
