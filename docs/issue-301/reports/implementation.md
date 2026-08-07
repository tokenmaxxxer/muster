---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: phase-2-complete
---

# Implementation record — issue-301 (B2: push-rejection visibility)

Subject: issue-301. Proposal: `docs/issue-301/proposals/2026-08-07-push-rejection-visibility.md`
(approved via `APPROVE issue-301/implementation` comment, single-account mode,
`docs/specs/approvers.md`).

## What was done

- `ensure_pushed()` (spawn.py:2795) now returns
  `{"status": ..., "reason": <str|None>}` instead of `None`. Statuses:
  `nothing-to-push`, `push-rejected`, `pr-create-failed`, `pr-opened`,
  `pr-already-open`. Every existing `print(..., file=sys.stderr)` in the
  function is unchanged — the function gained a return value, not new side
  effects. `reason` is the same truncated `stderr.strip()[:200]` already
  computed at the push and `gh pr create` failure sites, now also returned.
- `_spawn_one()` (spawn.py:3290-3299) captures `push_result =
  ensure_pushed(...)`. After the existing `silent-failure` ->
  `uncommitted-work` upgrade, a second branch upgrades `silent-failure` ->
  `push-rejected` when `push_result["status"] == "push-rejected"` — checked
  second, so a session with both a dirty tree and a rejected push still
  reports `uncommitted-work` (the more locally-actionable fact), matching
  the proposal's stated precedence. A stderr line naming the rejection is
  printed at this point too.
- `ledger_write()`'s dict gains `"push_reason": push_result.get("reason")
  if push_result else None` — present (possibly `None`) on every record.
- `_append_event(events_path, "session-end", ...)` now sends
  `{"outcome": outcome, "reason": push_reason}` when a push reason exists,
  otherwise the bare `outcome` string unchanged from today. Checked against
  every consumer of `session-end` events in spawn.py (`session_end_verdict`,
  the `--follow` watch loop, `_await_bounded`) — all of them branch only on
  `ev.get("type")`, none inspect the `detail`/payload shape, so this is
  additive.
- Tests added to `test_spawn.py` (repo root — the file lives there, not
  under `test/`; see Rationale for deviations) in a new `EnsurePushedResult`
  class, one per scenario the issue names:
  1. `test_push_rejected_by_remote_is_named_and_distinct` — a bare-repo
     remote with a `pre-receive` hook that rejects the push, message
     containing "workflow" (mirroring the issue-290 case). Asserts
     `ensure_pushed` returns `push-rejected` with a non-empty `reason`, and
     that `_spawn_one`'s outcome-selection logic (reproduced inline, same
     as spawn.py:3292-3299) yields `push-rejected`, not `silent-failure`.
  2. `test_commits_ahead_but_dirty_tree_prefers_uncommitted_work` — same
     rejected push, but with a simulated dirty tree; outcome stays
     `uncommitted-work`, proving the two don't collide.
  3. `test_nothing_to_push_stays_silent_failure` — no branch for the
     issue/role exists on the remote at all; `ensure_pushed` returns
     `nothing-to-push`, outcome stays `silent-failure`, unchanged from
     today.

## Effect verification (per #298)

All three scenarios the issue names were run and observed distinguishable,
via the new tests (`python3 -m pytest test_spawn.py -k EnsurePushedResult -v`):

```
test_commits_ahead_but_dirty_tree_prefers_uncommitted_work PASSED
test_nothing_to_push_stays_silent_failure PASSED
test_push_rejected_by_remote_is_named_and_distinct PASSED
```

- (a) push rejected by the remote: `ensure_pushed` observed returning
  `{"status": "push-rejected", "reason": "refusing to allow an OAuth App to
  create or update workflow without workflow scope"}` (from the real
  `pre-receive` hook's stderr, captured by `git push`'s own stderr
  truncated to 200 chars) — record output: `_spawn_one` outcome
  `push-rejected`, distinct from `silent-failure`.
- (b) commits present locally, absent on remote, at session end (with a
  dirty tree — the scenario a session leaving unfinished work matches):
  observed `push_result["status"] == "push-rejected"` but outcome resolves
  to `uncommitted-work`, not `push-rejected` and not `silent-failure` — a
  third, distinguishable label.
- (c) session that genuinely produced nothing: observed `ensure_pushed`
  returning `{"status": "nothing-to-push", "reason": None}`, outcome stays
  `silent-failure` — unchanged, proving the fix is additive.

Full suite run once: `python3 -m pytest test_spawn.py -q` -> `236 passed`.

Applied to the motivating case (issue-290): with this change, the session's
`session-end` event would have carried `{"outcome": "push-rejected",
"reason": "refusing to allow an OAuth App to create or update workflow
\`.github/workflows/on-the-record-tests.yml\` without \`workflow\` scope"}`
instead of the bare string `"silent-failure"`, and the ledger row would
carry that same reason in `push_reason` — the rejection would have named
itself instead of reading as "nothing happened."

## What did not work

None.

## Doctrine ladder

No env var, config key, new dependency, migration, or setup step was
introduced — nothing to place in a handbook. No library-or-format choice
or changed public wire format beyond `ensure_pushed`'s own return type
(already covered by this record and the proposal's Rationale) — no
`docs/issue-301/decisions/` entry needed. No benchmark/investigation
numbers beyond the pass/fail counts already reported above.

## Hunt

Warrant-hunter dispatch skipped this turn: this session is headless/
single-shot (contract v3 s22 / the warrant directive's own subordination
clause) — a background dispatch whose result is not consumed before the
turn ends is prohibited, and there is no further turn in this session to
consume it. No `closed_checks:` entries this session as a result; verify's
own pass covers this transition.

## Rationale for deviations

The proposal's frozen write set names `test/test_spawn.py`. This repo has
no `test/` directory — the existing, only test file is `test_spawn.py` at
the repo root, already covering `ensure_pushed` and `_spawn_one` (see the
pre-existing `OrchestratorGitToken`/`Ledger`/`EventReporting` classes). The
new tests were added to that file. This is a path correction to the actual
target, not a scope change — no new file, no different content, same
symbols under test.

## Open findings

None outstanding.

## Out of scope / not done

- B1 (missing `workflow` OAuth scope) and landing the stranded
  `issue-290/implementation` commits — both explicitly out of scope per the
  issue and the approved proposal; no code path in this repo can fix either.
