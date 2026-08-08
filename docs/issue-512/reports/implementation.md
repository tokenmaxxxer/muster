---
code_under_review: HEAD
loop_state: phase-2-complete
---

# Implementation record: issue #512

Subject: #512

## What was done

Executed the approved proposal
(`docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md`,
approved via `APPROVE issue-512/implementation` issue comment, single-account
mode):

1. `on-the-record/hooks/call-shape-guard.sh` (new) — ports gates.py's
   subprocess_call_shape_divergence (repo-wide git ls-files-scoped) and
   sibling_mention_check (diff-scoped to the write, checked against the
   local working-tree branch record). Fulfills proposal "What will be
   done" items 1-2.
2. `on-the-record/hooks/accumulation-claim-guard.sh` (new) — ports
   accumulation.py's check_accumulation_claim, field-presence
   strengthened. Fulfills item 3.
3. Both hooks registered in `on-the-record/hooks/hooks.json` under
   PreToolUse+Write|Edit|MultiEdit. Fulfills the "New PreToolUse hook
   scripts exist and are registered" acceptance line.
4. `gates/accumulation.py`: `_ACCUMULATION_HEADING` changed from
   heading-existence to heading-plus-non-empty-body
   (function _has_filled_accumulation); same strengthening kept in
   lockstep in accumulation-claim-guard.sh's inline copy. Fulfills item
   4 / proposal requirement 3.
5. `gates/closure_sweep.py`: added accumulation_trend() and
   format_accumulation_trend() functions — counts shape-1/shape-5
   instances in the merged tree, diffs against the previous tick's
   persisted counts (`runs/accumulation_trend.json`), advisory only.
   spawn.py's _board_wide_sweep() calls it each watchdog tick, not
   folded into anomaly_count. Fulfills item 5 / proposal requirement 4.
6. `docs/specs/enforcement-boundary.md`: added rows for
   call-shape-guard.sh and accumulation-claim-guard.sh (verdict
   `contract`), updated the accumulation.py and closure_sweep.py rows to
   note the changes. Fulfills item 6.
7. Unit tests added: `on-the-record/hooks/test_call_shape_guard.py`,
   `on-the-record/hooks/test_accumulation_claim_guard.py`, new cases in
   `gates/test_accumulation.py` for the field-presence strengthening,
   and a new AccumulationTrend test class in
   `gates/test_closure_sweep.py`. Fulfills item 7.

## Proposal clauses -> fulfilling commit/hunk

- "What will be done" #1 (call-shape-guard.sh, shape-divergence check) ->
  `on-the-record/hooks/call-shape-guard.sh` check-1 block (git ls-files
  *.py, functions _call_flag_set/calls_by_cmd).
- "What will be done" #2 (sibling_mention_check, diff-scoped) ->
  `on-the-record/hooks/call-shape-guard.sh` check-2 block (functions
  _marked_defs, pattern _SIBLINGS_SECTION).
- "What will be done" #3 (accumulation-claim-guard.sh) ->
  `on-the-record/hooks/accumulation-claim-guard.sh` (shape-1/shape-5
  detection + local-proposal-file check).
- "What will be done" #4 (field-presence strengthening, both places) ->
  gates/accumulation.py's _has_filled_accumulation function +
  accumulation-claim-guard.sh's inline copy of the same function.
- "What will be done" #5 (watchdog-tick trend) ->
  gates/closure_sweep.py's accumulation_trend/format_accumulation_trend
  functions + spawn.py's _board_wide_sweep function's new call.
- "What will be done" #6 (enforcement-boundary.md rows) ->
  `docs/specs/enforcement-boundary.md` new/updated rows.
- "What will be done" #7 (unit tests) -> the test files/additions listed
  above.
- Constraint "zero-install... root discovered by walking up from cwd" ->
  both new hook scripts' .git-directory walk-up block.
- Constraint "two-shape, evidence-backed" (no general duplication
  detector reopened) -> both hooks and accumulation_trend() only
  implement shape 1 (inline subprocess/gh calls) and shape 5
  (roles/*.json), no new detector added.
- Constraint "presence, never interpret free-text" -> the
  _has_filled_accumulation function checks non-blank-line presence only,
  never the line's content.
- Constraint "enforcement-boundary.md must stay complete" ->
  gates/test_boundary.py's completeness test passes (see Acceptance
  verification below).

## Why

`gates/accumulation.py` was called by nothing but its own unit test; the
call-shape checks lived only in gates.py/gates/ci.py, whose runner
disappeared when GitHub Actions was retired. Merged-code maintainability
was measured nowhere. Porting the checks to deployed PreToolUse hooks
per the record-claim-guard.sh zero-install pattern restores
authoring-time enforcement on arbitrary target repos, and the
watchdog-tick accumulation_trend advisory compensates for the
local-diff-only visibility a single session's hooks structurally can't
exceed (proposal's "Coverage tradeoff" section).

## Upstream

Based on: `docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md`

## Rationale for deviations

The issue's Acceptance section names "python3 -m pytest
gates/test_accumulation.py gates/test_gates.py -q" as a verification
command. A file named test_gates.py does not exist anywhere in this
repository (checked: no such filename under gates/) — this is not a
file the approved proposal's write set created or expected to create;
the proposal's own "How you'll know it worked" section names
gates/test_accumulation.py and gates/test_closure_sweep.py instead, with
no test_gates.py reference. Treated as a stale reference in the issue
text rather than a missing deliverable, and ran the proposal's actual
named test targets plus gates/test_recurrence.py (existing coverage for
the call-shape checks this delivery ports) in its place — see
Acceptance verification below.

## Acceptance verification

- checked: python3 -m pytest gates/test_accumulation.py
  gates/test_closure_sweep.py gates/test_boundary.py
  gates/test_recurrence.py on-the-record/hooks/test_call_shape_guard.py
  on-the-record/hooks/test_accumulation_claim_guard.py
  on-the-record/hooks/test_record_claim_guard.py -q — result: pass (55
  passed):
  ```
  55 passed in 1.49s
  ```
- checked: grep -E "call-shape-guard|accumulation-claim-guard"
  on-the-record/hooks/hooks.json — result: pass (both names present,
  registered under PreToolUse+Write|Edit|MultiEdit).
- checked: fixture test on a scratch TARGET repo built under $TMPDIR
  (git-initialized, outside this repo's tree, empty until populated by
  the fixture script itself) — result: pass. call-shape-guard.sh denied
  (exit 2) a divergent subprocess.run(["gh","api"]) write against an
  existing ["gh","api","-X","POST"] call site, and passed (exit 0) a
  clean write. accumulation-claim-guard.sh denied (exit 2) a shape-1
  write (three inline subprocess.run calls) against a proposal file with
  an empty ## Accumulation body, and passed (exit 0) a non-shape-touching
  write. Driver: a scratchpad Python script invoking both hook scripts
  with synthetic PreToolUse JSON payloads, cwd set to the fixture repo
  root.
- checked: accumulation_trend() invoked directly against the same
  empty-until-populated fixture repo (no prior
  runs/accumulation_trend.json) — result: pass. Returned
  {"current": {"shape1_sites": 2, "shape5_files": 0}, "has_prior":
  False} with no exception on first run; format_accumulation_trend()
  rendered "no prior tick data (first run)" — the required valid "no
  data" artifact for the empty state.

## What did not work

None — no reverted attempts this session.

## Open findings

- Pre-landing warrant hunt (stance 0: gate bypassability) found that
  both new hooks — and, pre-existing, record-claim-guard.sh — only fire
  on PreToolUse+Write|Edit|MultiEdit; a session routing an identical
  file write through the Bash tool (heredoc redirection, a Python
  one-liner, sed -i, etc.) bypasses both new guards entirely, unlike
  retry-loop-bound.sh's registration in the same hooks.json, which does
  include a Bash matcher arm. Reproduced; full repro in
  docs/reports/2026-08-09-hunt-authoring-time-maintainability-hooks.md.
  This is an inherited limitation of the pattern this proposal was
  directed to reuse (record-claim-guard.sh has the exact same
  Write|Edit|MultiEdit-only scope, already landed and accepted) — not a
  regression this delivery introduced, and adding a Bash-arm heuristic
  was not part of this proposal's approved "What will be done" (widening
  the write set mid-build is refused per contract). Left open for a
  follow-up issue.

## Next steps

None for this issue's approved scope — phase 2 complete. A follow-up
issue may want to extend Write|Edit|MultiEdit-scoped hooks (this one,
record-claim-guard.sh, and any future ones) to also see Bash-routed file
writes, per the open finding above.

## Resolution path

File a follow-up issue proposing a Bash-write detection heuristic (or a
shared helper) for the Write|Edit|MultiEdit-only hook family; out of
this issue's approved write set, so not resolved here.
