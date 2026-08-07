# Survey — issue #327

## Scope of the issue

Operator statement: deadlock, idle waiting, and unnecessary work are
user-facing defects. Nothing today registers them as a problem — every
existing check asks only whether output was correct, never whether it was
worth the wait. The issue explicitly defers "the fix" and asks first for a
name and a measurement.

## What already exists

- `spawn.py:1268` `classify(rc, result, delta, blocked)` — per-run
  three(+)-way verdict: `errored` / `progressed` / `waiting-on-human` /
  `refused` / `silent-failure`. `silent-failure` (nothing changed, nothing
  blocked) is already the closest existing name for "unnecessary work" —
  but it is report-only, consumed nowhere that fails anything.
- `spawn.py:1294` `session_end_verdict(work, log_path, now)` — per
  workspace: `normal` / `crashed` / `stalled` / `in-progress`. `stalled`
  (log silent past `WATCHDOG_SILENCE_MIN` = 90 min, `spawn.py:1452`) is
  already the existing name for "idle waiting." Also report-only.
- `spawn.py:1472` `watchdog_check_one(key, entry, now, state)` — scans one
  *live* roster entry and returns a list of anomaly strings across four
  signals (issue #90 phase-2 proposal):
  1. `log-silence` — no log mtime movement past `WATCHDOG_SILENCE_MIN`
     (idle waiting).
  2. `background-delegation-phrasing` — session talks about delegating to
     a background worker it never waits on (issue #180 lineage; a
     deadlock-shaped defect: work handed off, nobody consumes it).
  3. `denied-tool-calls` — `WATCHDOG_DENIAL_THRESHOLD`+ permission denials
     in one scan window (a session repeatedly hitting a wall it cannot
     get past — deadlock-shaped).
  4. `no-commits-late` — past `WATCHDOG_NO_COMMIT_MIN` elapsed with zero
     commits since `before_head` (unnecessary-work-shaped: time spent,
     nothing produced).
- `spawn.py:1542` `roster_watchdog(auto_respawn=False)` — calls
  `watchdog_check_one` over every live roster entry, prints anomalies to
  stdout, **always returns 0** regardless of what it found (checked: no
  branch in the function returns non-zero; the one call site,
  `spawn.py:2438`, passes that 0 straight through as the `spawn.py
  watchdog` CLI's exit code). Docstring calls it explicitly
  "observe-only": it does not fix, kill, or fail on what it finds.
  `auto_respawn=True` acts only on `crashed`; `stalled` and the four
  anomaly signals above are still report-only even in that mode.

**The gap is exactly the one the issue names.** The taxonomy for idle
waiting, deadlock-shaped blocking, and unnecessary work already exists
(`stalled`, `silent-failure`, and the four watchdog anomaly signals) and
is already computed on a schedule (`roster_watchdog`, called by the
orchestrator every 10-15 min per its docstring). But none of it is wired
to anything that *fails*. A CI-shaped consumer, or the orchestrator
calling this on a schedule, has no way to tell "anomalies were found" from
"scan ran clean" except by parsing stdout prose — there is no exit code,
no ledger field, no test that regresses when the always-0 return is
reintroduced after being fixed.

## Related prior work (no overlap, adjacent)

- `docs/issue-285/` — fixed orchestrator-side poll/spawn latency (flat
  `sleep(2)` → escalating poll, memoized checkout, deduped fetch, TTL,
  subprocess timeouts). This reduced actual wall-clock waste but did not
  add any pass/fail signal — it made the orchestrator faster, not the
  idle-detection mechanical.
- `docs/issue-296/` — fixed a regression #285 introduced (TTL marker
  dirtying every clone). Same layer, no overlap with #327's ask.
- `docs/issue-192/` — session log retention/naming
  (`_session_log_path()`), which `session_end_verdict`'s `stalled` check
  already depends on. No overlap; #327 consumes this, doesn't change it.

## Sibling issues from the same 2026-08-07 batch — boundary check

- **#330** ("nothing checks what a change reaches") is about
  cross-cutting impact analysis on deliverables. Different axis: #330 is
  about a change breaking *something adjacent*; #327 is about a *session*
  producing nothing while looking busy. No overlap.
- **#324** ("independent work is serialized") is about throughput/
  parallelism policy, not about detecting idle/stuck sessions. No overlap.
- **#326** ("interrupted work hides") is about resumption UX for
  in-progress work, a different failure shape than idle/deadlock/
  redundant. No overlap — #327 does not touch resumption.
- **#325** ("issues filed then silently dropped — no spawn, no
  monitoring") is about issues that never even get a session; #327 is
  about sessions that exist and are idle/stuck/spinning. Adjacent but
  distinct failure point (before-spawn vs. during-session).
- **#310** (this issue's own acceptance framing) and **#298**
  (orchestrator has no enforcement surface) are the standing constraints
  already reflected in this proposal's acceptance section.

## What #327 does NOT ask this proposal to solve

The issue text explicitly defers "the fix" for the underlying causes
(actually eliminating deadlocks, actually shortening polls) — it asks for
naming + measurement first. Per-step-kind tolerance calibration ("what is
a tolerable wait for *each* kind of step") is an open research question
the issue itself does not answer; this proposal does not invent per-kind
thresholds, it wires the existing binary anomaly/no-anomaly signal (which
already has a name per signal) to an exit code that fails.

## Alternative considered while surveying

A brand-new idle/deadlock detector module was considered and rejected at
survey time: the detection logic (four signals, `stalled`,
`silent-failure`) already exists, already runs on a schedule, and already
has korean-commented rationale for each signal's threshold. Building a
second detector would duplicate that logic and drift from it. The gap is
narrowly in the *consumption* of what's already computed, not in the
computation itself.
