# Scout brief — issue #247

Field: this repo's own codebase and `docs/decisions/`, not external products.
Why: the deliverable is an internal reliability/ops mechanism for a bespoke
agent-orchestration framework (bounded-retry-then-escalate on a headless
session's abandoned work), not a product-shaped surface — the repo's own
accumulated decisions on this exact problem class (issues #90, #132, #205,
#223) are a closer comparable than generic process-supervisor docs would be.
No WebSearch/WebFetch was invoked this session; the freelunch STEP-1 tally
already scored external search angles at width ~0 (1-2 query lookups), so
this scout pass stayed batched-sequential codebase archaeology, 1 stage,
inside the current-state survey itself (survey-first order).

Must-bes the repo's own precedent already established (adopt, don't
reinvent):
- Bounded auto-action, capped at `RESPAWN_MAX_ATTEMPTS = 2`, then an
  idempotent issue-comment escape hatch (`_post_crash_comment`,
  spawn.py:1594) — issue #132.
- Auto-action never substitutes for the approval gate; it only re-runs a
  task a human already authorized once (issue #132 proposal Constraints).
- Atomic `O_CREAT|O_EXCL` claim files guard every concurrency-sensitive
  auto-action (`.respawn-claim-{ts}` issue #132, `.spawn-claim` issue #223)
  — never `fcntl.flock()` (rejected twice already, issue #223 Rationale).
- "Observe-only" vs "auto-act" stays a hard split per verdict value —
  `stalled` is never auto-acted on (`roster_watchdog` docstring,
  spawn.py:1439-1448).

Performance axes this fix competes on: detection latency (in-process at the
moment the bad outcome is known, vs. waiting for a periodic watchdog tick),
false-positive rate (must not fire on `refused`/`waiting-on-human`, which are
legitimate stops needing a human, not a bug), and attempt-cap transparency
(same escape hatch shape already proven in #132).

Adopt: reuse `RESPAWN_STATE`/`RESPAWN_MAX_ATTEMPTS`/cap-comment machinery
wholesale (spawn.py:1577-1608) rather than a second counter family.
Skip: extending `session_end_verdict`'s roster-scan trichotomy
(spawn.py:1191) to catch this — GAP LINE: `roster_remove` (spawn.py:2849)
runs synchronously inside the same process before it exits, so a normally-
exited session is never a "dead-but-registered" roster entry for any
watchdog tick to find; the correct outcome signal
(`uncommitted-work`/`failed-no-commit`, spawn.py:2884-2911) is already
computed in-process at the exact moment of exit, one call frame away from
where `_auto_respawn_check`'s reusable logic already lives.

Background convention (labeled assumption, not a sourced finding — no fetch
performed): bounded auto-restart-then-escalate is the common shape in
process supervisors generally (e.g. systemd `Restart=on-failure` +
`StartLimitBurst`, supervisord `autorestart`) — noted only as a name for
the pattern already adopted above, not as new evidence.

Sources: spawn.py:1165-1272, spawn.py:1349-1354, spawn.py:1439-1472,
spawn.py:1577-1678, spawn.py:2848-2952, docs/issue-132/proposals/session-end-trichotomy.md,
docs/issue-205/proposals/session-end-defects.md,
docs/issue-223/proposals/spawn-one-issue-role-claim.md,
docs/issue-223/reports/implementation.md,
docs/decisions/2026-07-29-headless-cli-measured-facts.md, protocol.md,
roles/implementation.json.
