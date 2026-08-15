# 0011 — Why containerize, and why Docker specifically (planned)

**Status:** Planned — not yet implemented. This document exists so the *reasoning* is captured
before the work starts, not reconstructed after the fact. The current `Dockerfile` is empty and
`docker-compose.yaml` references `ubuntu(latest)` — not a valid image, and not this application.

## Who

Me — writing down the reasoning ahead of doing the work (roadmap phase 2), specifically because
the service owner asked to understand *why* this is planned, not just that it is.

## What (planned)

A real multi-stage `Dockerfile` (Poetry-based builder stage, slim non-root runtime stage,
`HEALTHCHECK`), a working `docker-compose.yaml` (app + Postgres, named volume, healthcheck-gated
startup), and a `.dockerignore`.

## When

Not yet — next phase after this document, in the roadmap's ordering (phase 2, immediately after
the now-complete phase 1: [`0006`](0006-alembic-migrations.md)–[`0009`](0009-startup-retry-backoff.md)).

## Where (planned)

`Dockerfile`, `docker-compose.yaml`, `.dockerignore`, all at the project root.

## Why containerize at all

Three reasons, in order of how concrete they are:

1. **"Works on my machine" stops being a real answer once there's a real deploy target.** Render
   (the planned deploy target) runs containers — there's no path to deploying this service there
   that doesn't go through a container image, so this isn't really an optional step, it's a
   prerequisite.
2. **Reproducibility.** A container image pins the Python version, the OS-level dependencies, and
   the exact package versions (via the Poetry lockfile) into one artifact. "It works because my
   laptop happens to have Postgres 17 via Homebrew and Python 3.14 via pyenv" (which is literally
   how phase 1's Postgres testing was done, manually, in this session — see
   [`0007`](0007-postgres-connection-pooling.md)) is not a repeatable deployment story. A
   Dockerfile makes the environment part of the repo, not part of whoever's machine happens to run
   it.
3. **This session already hit the exact problem containerization solves.** The startup-retry work
   ([`0009`](0009-startup-retry-backoff.md)) exists *because* an app and its database starting
   together is a real race condition — that's specifically a `docker compose` problem (two
   containers, no inherent startup ordering) that doesn't exist when there's one process on one
   machine. Phase 2 is where that race gets a second, complementary defense: a compose healthcheck
   that gates the app container's start on Postgres actually being ready, rather than relying on
   `wait_for_db`'s retry loop to do all the work alone.

## Why Docker specifically (not, e.g., a bare VM image, or Nix, or nothing)

- **It's the de facto standard for "here's a runnable unit" in modern deployment platforms** —
  Render, and virtually every other PaaS/container platform, take a Dockerfile or a container
  image as the primary deployment interface. Choosing anything else would mean fighting the
  platform instead of using it.
- **`docker compose` solves the exact local-multi-service problem this project has right now** —
  "run the app and a real Postgres together, locally, without each developer hand-rolling their
  own `initdb`" (which is literally what had to be done manually, once, to verify phase 1's work
  against real Postgres). Compose is the tool built for exactly that.
- **Multi-stage builds solve a real, specific problem this project would otherwise have**: a
  single-stage image would ship Poetry, the C toolchain needed to build some dependencies, and
  every dev dependency (ruff, mypy, pytest) into the *production* image. A builder stage that
  exports a locked dependency set, followed by a slim runtime stage that copies only the built
  app, keeps the deployed image small and reduces its attack surface — dev tooling has no business
  being present in a production container at all.

## Alternatives considered

**Deploy without containers at all** (Render also supports native Python buildpacks for some
service types) — rejected: it would work for a single simple service, but it means the platform's
buildpack — not this repo — decides the exact runtime environment, which is a worse reproducibility
story than pinning it explicitly. It also wouldn't solve the local "run the app plus a real
Postgres together" problem at all, since buildpacks don't give you `docker compose`'s local
multi-service story.

## What this will cost (being honest about the tradeoff, not just the benefit)

- A new class of things that can break: the Dockerfile itself, image build time, image size,
  container-specific bugs (file permissions under a non-root user, path differences). None of
  these exist in a "just run `poetry run uvicorn`" world.
- Local development gets a step slower (image build/rebuild) compared to running the app directly
  — worth mitigating with proper layer caching (dependencies installed in a layer that only
  invalidates when the lockfile changes, not on every source edit), planned as part of the actual
  Dockerfile work, not yet built.

## Consequences (once built)

This document should be updated with a **Status: Accepted** header, the actual commit hash, and a
verification section (does the image build, does compose bring up app+Postgres cleanly, does the
app pass its own health/readiness checks inside the container) the same way every other decision
in this log has one — written *after* the work lands, following the same pattern as
[`0007`](0007-postgres-connection-pooling.md) through [`0009`](0009-startup-retry-backoff.md).
