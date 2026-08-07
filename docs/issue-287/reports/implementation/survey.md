# Survey — issue #287 ("can't check" reported as "checked clean")

## Scope confirmed (read each file/line the issue cites)

- `gates/closure_sweep.py`
  - `_issue_view` (53-56), `_pr_view_state_body` (59-68) return `None` on any
    `gh` failure (nonzero exit, or JSON decode failure for the PR call).
    `find_violations` (71-108) `continue`s on both `None`s — a subject whose
    `gh` calls fail is silently dropped from the sweep, indistinguishable
    from a subject with no violations.
  - `main` (142-157): `find_violations` returning `[]` (real "clean") and
    `[]` because every subject was skipped print the same
    `"종결 일관성 스윕: 위반 없음"` and both exit 0.
  - `_post_crash_comment`-style escalation isn't here, but the mirror case
    (S7) is: `post_sweep_comments` (121-139) posts via `subprocess.run` and
    never checks `.returncode`.
- `gates/flows.py`
  - `_pr_list_all` (45-62) / `_issue_list_all` (65-78): both return `[]` on
    nonzero exit or bad JSON. `flows_payload` (257+) has no branch that
    distinguishes "gh call failed" from "repo genuinely has zero open
    PRs/issues" — `decision_queue`, `flows`, and the `closure_sweep`
    sub-call (which reuses `issue_states` derived from `_issue_list_all`)
    all silently degrade to empty.
  - `_ledger_read` (146-159): `except ValueError: continue` on a bad JSONL
    line, no count kept anywhere in the returned list or in
    `flows_payload`'s `unattributed`/`ledger` aggregation.
  - `flows()` text renderer (422-448) has no place to print an error either
    — matches the payload's own gap.
- `on-the-record/hooks/deliverable-guard.sh`
  - Bash prefilter (`case "$payload" in *src/*|*test/*|*docs/*`, line 20)
    matches literal `test/`, not `tests/`. Same gap mirrored in the Python
    regex `re.search(r"(^|/)(src|test|docs)/", n)` (line 47).
  - Python heredoc: `except ValueError: sys.exit(0)` (36), non-dict `sys.exit(0)`
    (38), missing/empty `file_path` `sys.exit(0)` (44). All three are ALLOW
    outcomes on a malformed or unreadable payload, in a hook whose own
    header (line 11) claims "fail closed on non-0/2" — that trap only
    covers uncaught crashes (line 12), not these explicit `sys.exit(0)`
    paths, which the trap's condition (`rc != 0 and rc != 2`) explicitly lets
    through.
- `spawn.py`
  - `_issue_comments` (923-949) returns `[]` on `gh api` failure or bad
    JSON, same shape as `_pr_list_all`/`_issue_list_all`.
  - `approve_scope` (988-1057): when `_issue_comments` fails silently,
    `comments` is `[]`, `match` is `None`, and the exit message at
    1031-1033 says "승인 코멘트를 못 찾았다" (didn't find the comment) — same
    message text whether the comment doesn't exist or `gh` couldn't be
    asked.
  - `gates/ci.py:_phase_from_approval` (144-166) reuses
    `spawn._issue_comments` + `flows._pr_approved` the same way — a failed
    `gh` call here silently classifies an approved PR as phase 1 (fail
    direction is safe — never over-grants — but the reason is invisible).
  - `_post_crash_comment` (1754-1775): `subprocess.run(["gh", "api", ...])`
    at 1774 — returncode never read, matches S7's `closure_sweep.py:138-139`
    exactly.

## Existing conventions to reuse (found during survey)

- `flows._stage_for` (36-42) already returns a `(value, derived: bool)`
  pair specifically to let a caller distinguish "we computed this" from
  "this is a raw fallback" — the same shape issue #287 needs for "checked"
  vs "could not check". `flows_out[].stage_derived` in the payload is the
  precedent for a payload-level boolean flag placed next to the value it
  qualifies, and `flows()`'s renderer already prints `(raw)` next to a
  non-derived stage (line 434) — direct precedent for how the text
  renderer should flag an unknown/unchecked value too.
- `_append_event(..., "unverified-refusal", ...)` (spawn.py:1690-1699) is
  the project's existing pattern for "we know something happened but
  can't confirm which specific thing" — named outcome, not a dropped
  event and not a false-positive label.
- `docs/specs/flows-schema.md` is the frozen contract for `flows --json`
  output — adding a `hygiene.errors` / per-list error field is a schema
  change and belongs there (already listed in the proposal's write set).
- Tests in this repo live at the root as `test_<module>.py` (`test_flows.py`,
  `test_gates.py`, `test_spawn.py`, `test_approve_scope.py`) or under
  `gates/test_*.py` for gate-local tests; there is no `test/` or `tests/`
  tree for python tests (`tests/` exists only for a bash integration
  harness, `tests/run-orchestrate-tests.sh`). New tests for S1-S3, S6, S7
  extend the existing root/`gates/` test files; the deliverable-guard
  tests are best added as a bash case list next to
  `tests/run-orchestrate-tests.sh`'s existing convention, since
  `deliverable-guard.sh` has no python entry point to unit-test directly.

## Write set this proposal will need

- `gates/closure_sweep.py` — distinguish "gh failed" from "no violations";
  non-zero, distinctly-worded exit on failure; check `post_sweep_comments`'s
  `subprocess.run` returncode (S7 mirror).
- `gates/flows.py` — `_pr_list_all`/`_issue_list_all` report failure
  distinctly from empty; `_ledger_read` counts and reports skipped lines;
  `flows_payload` surfaces both as an explicit error field; `flows()` text
  renderer prints it.
- `spawn.py` — `_issue_comments` reports failure distinctly from empty;
  `approve_scope`'s error message distinguishes "no matching comment" from
  "could not read comments"; `_post_crash_comment` checks its `gh api`
  returncode and reports if the escalation post itself failed.
- `gates/ci.py` — `_phase_from_approval` reads the same failure signal (no
  behavior change needed beyond consuming the new return shape; direction
  is already fail-closed per the issue).
- `on-the-record/hooks/deliverable-guard.sh` — deny (exit 2) on unparseable
  JSON payload, non-dict, or missing `file_path`; extend prefilter/regex to
  match `tests/` alongside `test/`.
- `docs/specs/flows-schema.md` — document the new `hygiene`/list-level
  error fields.
- Tests: `test_flows.py`, `test_spawn.py`, `gates/test_closure_sweep.py`
  (new — no closure_sweep test file exists yet), `tests/` bash cases for
  `deliverable-guard.sh` (unparseable stdin, non-dict JSON, missing
  `file_path`, `tests/` path).

## Alternatives considered (for the proposal's Rationale)

1. **Raise an exception instead of a sentinel/tuple return.** Every `gh`
   wrapper (`_pr_list_all`, `_issue_list_all`, `_issue_comments`,
   `_issue_view`, `_pr_view_state_body`) already returns `None`/`[]` on
   failure by established convention across this codebase, and callers
   (`flows_payload`, `find_violations`, `approve_scope`) are plain
   functions, several of them library-usable from tests
   (`classify`, `find_violations` take pre-fetched dicts precisely to stay
   network-free and testable). Exceptions would require try/except at
   every call site and break the "network-free, dict-in" testability the
   code already relies on (`closure_sweep.find_violations(..., issue_states=...)`
   is used exactly this way by `flows_payload`). Rejected in favor of a
   distinguishable return value (tuple or a small result object), matching
   the `_stage_for` precedent already in this codebase.
2. **Global "degraded mode" flag on the module instead of a per-call
   signal.** Simpler to add, but loses which specific list/lookup failed
   when several `gh` calls happen in one `flows_payload` run — the
   ledger-skip count and the PR-list failure are different failures that
   an operator needs to see separately (issue's own acceptance list: "flows
   payload carries an explicit error", "skipped ledger lines are counted").
   Rejected — the payload needs field-level, not payload-level, granularity.
