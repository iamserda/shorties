# Shorties — Engineering Documentation

This folder exists so I can explain this service front-to-back — to an interviewer, a future
teammate, or my own future self six months from now who's forgotten why any of this is the way
it is. It's written the way I'd actually explain it out loud: what the thing is, why it's built
this way, what broke and how I found out, what I'd still change.

## How this folder is organized

```
docs/
├── README.md                          — you are here
├── architecture/
│   ├── 01-overview.md                 — HLD: what the service does, the shape of the system
│   ├── 02-data-model.md               — LLD: the schema, field-by-field, why each field exists
│   ├── 03-api-reference.md            — every endpoint, verb, status code, and why
│   └── 04-request-lifecycle.md        — LLD: tracing one request through every layer
└── decisions/
    ├── 0001-...md                     — one file per real engineering decision, in order
    ├── 0002-...md
    └── ...
```

**`architecture/`** describes the system *as it is right now* — current state, kept up to date.
If it drifts from the code, it's wrong and should be fixed, not treated as history.

**`decisions/`** is a chronological log and never gets rewritten — each file is a snapshot of a
decision at the time it was made, including ones that were later superseded. If a later decision
changes an earlier one, the later file says so and links back; the earlier file stays as-is,
because "why did we used to do X" is a real question worth being able to answer.

## The rule going forward

**Every time something new and architecturally relevant ships, it gets a decision record before
the work is considered done** — not "eventually," not "when I have time," as part of the change
itself. A decision record answers, in order:

- **Who** — who made the call (usually me, sometimes a constraint external to me made it)
- **What** — the actual change, in one or two sentences
- **When** — date, and the commit(s) it landed in
- **Where** — which files/components it touches
- **Why** — the reasoning. This is the part interviewers actually ask about, and the part that's
  gone forever if I don't write it down while I still remember it
- **How** — enough of the actual implementation (code snippets, not just prose) that reading this
  file later is equivalent to reading the diff, without needing to find the diff

Plus, where relevant: **what I considered and rejected**, and **what it cost me** (tradeoffs are
not free — if a decision has a real downside, the record says so instead of pretending it's
strictly better in every dimension).

If the change is also a shift in the system's shape (not just an internal fix), `architecture/`
gets updated in the same pass so it never goes stale.

## Reading order, if starting from zero

1. `architecture/01-overview.md` — the 5-minute version
2. `architecture/02-data-model.md` and `03-api-reference.md` — the concrete surface
3. `architecture/04-request-lifecycle.md` — how a request actually moves through the system
4. `decisions/` in order — the story of how it got this way, and why
