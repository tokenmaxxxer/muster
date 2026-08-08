# Survey — issue #445: silent-failure and spawn-path bug hunt

`code_under_review:` `0fa8a2c621e536bcfbd27876ae53b8e122f756ba` (main tip at session start).

## Upstream records

No coding/qa/review record exists for issue #445 — the issue assigns the
hunt directly to this role rather than verifying a prior deliverable. There
is nothing to cite-and-skip from `closed_checks:`; every attempt in the
proposal is self-devised against the current tree, sourced by file:line.

Issue #445 itself carries an `issue-bundling-gate` bot comment (fail-closed:
"and"-joined title, no `## Acceptance` section). Noted, not acted on — that
gate governs issue authoring, not this role's scope; branch/PR already
exist per invocation.

## Scope surfaces (issue text)

`spawn.py`, doctor probe, watch, workspace setup, rulebook fetch, session
teardown; `gates/`, `on-the-record/hooks/`, `scripts/`.

## Current state (measured)

`spawn.py` is 3643 lines with ~50 bare/narrow `except` blocks (grep count).
Most are already annotated with a prior hunt/issue reference in a preceding
comment (#180, #192, #224, #235, #255, #266, #288, #289) — this file has
been through several rounds of silent-failure hardening already. That
raises the bar: a fresh finding has to be a gap those rounds did not close,
not a re-discovery of what they already fixed.

Read in full: `issue_workspace()` (spawn.py:2888-2994), `checkout_issue_branch()`
(spawn.py:2997-3023), `_watch()` follow-loop (spawn.py:2171-2235),
`require_doctor()`/`doctor()` (spawn.py:2405-2476), `_session_log_path()`
(spawn.py:3096-3103), log-write loop (spawn.py:3390-3428), cleanup `except
Exception` (spawn.py:2718-2722), `_resolve_gh_token()` (spawn.py:2789-2809).

Confirmed already fixed (not re-attempted as findings):
- Log overwrite on respawn (#192): `_session_log_path()` mints a
  `ts+pid`-suffixed path per generation; `open(log_path, "w")` truncates
  only that generation's own file, not a shared one.
- Branch-name inheritance from origin-only branch (#235 family):
  `checkout_issue_branch()` explicitly tracks `origin/<br>` before falling
  back to creating from base.
- `--follow` watch treating a still-succeeding tail as a crash (#224,
  #266): pid-death check is gated on a present roster entry; absent entry
  is treated as unknown, not death.

## Candidate gaps carried into the proposal (self-devised, untested)

1. `issue_workspace()` `except OSError: pass` at spawn.py:2982 around the
   `.git/info/exclude` credential-leak guard (spawn.py:2964-2983) — if
   writing the exclude list fails, cloning proceeds silently with no
   exclude protection, and nothing downstream re-checks it before a
   session could `git add -A` (the exact leak spawn.py:2969-2973 exists to
   prevent).
2. `_watch(follow=True)` loop (spawn.py:2199-2235): when the roster entry
   is absent (`pid is None`), the loop has no bound at all — not
   `stall_timeout_min`, not any counter — it re-polls forever. Comment at
   spawn.py:2227-2231 justifies treating entry-absence as "unknown, wait",
   but does not bound how long "wait" can run if the entry never
   reappears (e.g. spawn crashed before ever registering).
3. `doctor()` cost-per-spawn: `require_doctor()` is called once per
   `spawn.py` process invocation (main-path and `drive`), gated by
   `runs/doctor-ok` containing the matching CLI version string — cheap
   unless the version changed underneath a long-lived orchestrator
   session. Worth one concrete repro: does a version bump mid-session
   trigger a live paid probe inside what the caller expects to be a
   routine spawn, with no warning before the charge.
4. `gates/issue_bundling.py` comment-only enforcement: the bot posted a
   fail-closed comment on #445 itself but the issue stayed open and
   assignable — worth checking whether `issue_bundling.py`/its workflow
   actually blocks anything downstream (PR merge, spawn) or only ever
   posts a comment nobody is forced to act on, i.e. renders as a "gate"
   while being advisory in effect.

## Scouting

Skipped. Reason: this is a defect-hunt/audit task against existing code,
not a product-shaped deliverable with an open design/direction decision —
there is no exemplar product to benchmark against. (Skip condition: "spec
literally leaves no design decision open" — the task is reproduce-or-not
against the current implementation, not choose-a-direction.)
