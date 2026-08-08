---
code_under_review:
  - on-the-record/hooks/retry-loop-bound.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_retry_loop_bound.py
loop_state: landed
---

# Issue #507 -- Phase 2 implementation record

## What was done

Delivered the K/2K identical-refusal retry-loop bound approved in
`docs/issue-507/proposals/2026-08-08-retry-loop-bound.md`:

- `on-the-record/hooks/retry-loop-bound.sh` -- new `PreToolUse`/`PostToolUse`
  hook pair, dispatched by a `pre`/`post` argument. `post` matches the
  `PreToolUse:\S+ hook error: [<gate>: refused -- ...]` deny shape (same
  wire shape `spawn.py`'s `_GATE_HOOK_RE`/`_GATE_DENY_RE` already parse
  post-hoc) and increments a per-session counter keyed by
  `sha256(tool_name, target)`. `pre` looks up that counter before the next
  attempt: count in `[K, 2K)` -> allow (exit 0) plus
  `hookSpecificOutput.additionalContext` quoting the last deny reason and,
  when extractable, the `requires branch <expected>` value; count `>= 2K`
  -> deny outright (exit 2), marks the signature `aborted`, and the
  underlying gate is never consulted again for that exact request. K
  defaults to 5, tunable via `OTR_RETRY_BOUND_K`; state lives at
  `${OTR_RETRY_BOUND_STATE_DIR:-$TMPDIR/otr-retry-bound}/<session_id>.json`,
  per-session, fail-open on any parse/state error. `ORCHESTRATE_OFF` kill
  switch and `CLAUDE_ROLE` early-exit both present, per the proposal's
  Constraints.
- `on-the-record/hooks/hooks.json` -- registered `retry-loop-bound.sh pre`
  as the first `PreToolUse` entry for the `Write|Edit|MultiEdit|Bash`
  matcher (so a 2K-aborted signature is denied before the existing gates
  re-run), and `retry-loop-bound.sh post` under a new `PostToolUse` block
  on the same matcher.
- `on-the-record/hooks/test_retry_loop_bound.py` -- red/green suite: zero
  denials is silent (empty-state case from Acceptance); below-K is
  silent; the K-th denial's next attempt carries `additionalContext`
  naming the deny count and the extracted expected branch; a 25-denial
  run reproducing the issue-474 log shape (`docs/issue-505/reports/
  implementation.md:26-27,47-70`, `board-gate.sh:512`'s exact message
  template per this issue's survey) nudges from K and aborts (exit 2)
  from 2K onward; a non-identical-target sequence (10 distinct targets)
  never trips either threshold; `ORCHESTRATE_OFF=1` is silent throughout.
  7/7 pass; full `on-the-record/hooks/` suite (42 tests) green, no
  regression.

## Rationale for deviations

The proposal's "What will be done" describes the signature as
`sha256(tool_name, normalized target, gate/reason)`. Built against the
actual PreToolUse/PostToolUse split, the `pre` hook runs *before* the
underlying gate produces a reason for the current in-flight attempt -- it
can only look up counts recorded by `post` from *prior* attempts, and
there is no reason text yet available for the one being checked.
Dropping `reason` from the signature (keeping it only as stored context
for the nudge/abort message) is the only way for `pre` to do a lookup
before the gate runs, and does not weaken the bound in any case this
issue's fixtures cover: two denials of the same `(tool, target)` from the
same gate produce the same reason every time (board-gate's R4 check is a
deterministic function of target + branch), so no case in scope collapses
distinct denial classes into one signature. Documented inline in the
hook's header comment.

## What did not work

None.

## Out of scope (unchanged from proposal)

- `board-gate.sh` itself is not touched (owned by the separate
  `tokenmaxxxer-core` repository; the "board-gate deny names the writable
  path" half of #507 needs its own issue there, per the proposal's Out of
  scope).

## Closed checks

- closed_checks:
  - check: retry-loop-bound K/2K red-green (issue-474 log shape fixture)
    code_sha: 5d62e9f7b0d8069bea39e4220ff12e88872efe56
    result: pass (7/7 in test_retry_loop_bound.py)
  - check: full on-the-record/hooks/ suite regression
    code_sha: 5d62e9f7b0d8069bea39e4220ff12e88872efe56
    result: pass (42/42)

## Resolved findings

- resolved_findings:
  - finding: before-landing warrant hunt, stance 0 (bypass hunt),
    `docs/reports/2026-08-08-hunt-retry-loop-bound.md` -- `_target()`
    used the raw unnormalized `file_path`/`path` string to build the
    `(tool, target)` signature, so spelling variants of the same path
    (`/tmp/x`, `./x`, `/tmp/./x`, `//tmp/x`, `/tmp//x`) hashed to
    different signatures and never accumulated toward K/2K.
    resolution: `_target()` now runs `os.path.normpath()` on
    `file_path`/`path`/`notebook_path` before hashing (`command` is left
    unnormalized -- it is not a filesystem path). Re-ran
    `test_retry_loop_bound.py` (7/7 pass) after the fix.
    code_sha: (post-fix, staged for commit)

## Why

#505's slow-session mining measured sessions burning 10+ minutes retrying
an identical denied write 22-52 times with no adaptation even though the
gate's own deny message named the mismatch. #507 asks for a mechanical
bound on that loop plus a corrective message; this delivers the bound
(the board-gate message change is out of this repo's write set, per the
Constraints/Out of scope above).

## Upstream

Based on `docs/issue-507/proposals/2026-08-08-retry-loop-bound.md`
(approved via `APPROVE issue-507/implementation`,
https://github.com/tokenmaxxxer/on-the-record/issues/507#issuecomment-5226279207)
and `docs/issue-507/reports/implementation/survey.md`.

## Open findings

None.
