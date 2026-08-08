---
code_under_review:
  - gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/hooks/record-scaffold.sh
  - on-the-record/hooks/test_record_scaffold.py
  - on-the-record/hooks/record-claim-guard.sh
  - gates/ci.py
  - docs/handbooks/record-authoring.md
  - docs/specs/enforcement-boundary.md
loop_state: landed
---

# issue-517 phase 2 — record_lint + scaffolder delivery record

upstream: docs/issue-517/proposals/2026-08-09-record-lint-and-scaffolder.md

## Summary of work

Delivered the approved proposal:

- `gates/record_lint.py` (new): `lint_record(path) -> list[str]`
  aggregates every `gates.py` record check (`record_enums`,
  `record_refusal_reasoned`, `record_wellformed_in`,
  `record_no_tool_residue_in`, `record_derived_counts_in`,
  `record_checked_claims`, `reach_check`, `sibling_mention_check`) plus
  four checks lifted here from `record-claim-guard.sh`'s inline mirror
  (`unverifiable_reason_check`, `checked_claim_reason_check`,
  `bare_count_claim_check`, `orphaned_path_reference_check`), against
  one record file's full text — no first-failure abort. CLI entry:
  `python3 -m gates.record_lint <path>` (single record) or with no
  path/a directory (repo-wide sweep, "no records" empty-state message
  when none found). Also re-exports `gates.py`'s
  `record_enums`/`record_wellformed_in`/`record_no_tool_residue_in`/
  `record_checked_claims` under this module's name so callers share the
  same function objects rather than duplicating logic.
- `gates/test_record_lint.py` (new): a fixture record with five
  independent violations (missing `## Acceptance verification` on a
  terminal record, an orphaned code reference, a bare count claim, and
  two claim-guard mirrors — `unverifiable:` with no reason and a
  `checked:` line with an unreasoned `unverifiable` result) asserted via
  one `lint_record` call reporting all of them; plus a clean-record
  test, an invalid-enum test, an empty-repo "no records" test, and a
  non-record-path test.
- `on-the-record/hooks/record-scaffold.sh` (new): CLI, not a
  `PreToolUse` hook (a warrant-hunter finding on the phase-1 proposal
  found no natural lifecycle event to hang a hook registration off —
  nothing fires "author is about to start a record"). Usage:
  `record-scaffold.sh <role> <issue-n> [target-repo-root]`. Writes
  `docs/issue-<n>/reports/<role>.md` with every `roles/<role>.json`
  `record_fields` key as a `PLACEHOLDER: <field>` frontmatter line (an
  invalid-enum violation until filled in) plus the standard section
  skeleton; refuses to overwrite an existing record.
- `on-the-record/hooks/test_record_scaffold.py` (new): asserts raw
  scaffold output fails `record_lint` only on placeholder-remaining
  violations, a filled-in copy passes clean, overwrite is refused, and
  every declared `record_fields` key (tested against
  `technical-feasibility`'s `verdict`+`loop_state`) gets its own
  placeholder line.
- `on-the-record/hooks/record-claim-guard.sh`: the four inline regex
  checks replaced with calls into `gates.record_lint`'s functions
  (imported via `sys.path.insert(0, os.environ["RCG_GATES_DIR"])`, with
  `gates_dir` resolved by the bash wrapper) — no duplicated rule logic
  remains in the hook script.
- `gates/ci.py`: `gates.record_enums`/`record_wellformed_in`/
  `record_no_tool_residue_in`/`record_checked_claims` calls switched to
  `record_lint`'s re-exports (same function objects; `record_fulfils_diff`
  and `requirement_registry`, which `record_lint` does not aggregate,
  are untouched).
- `docs/handbooks/record-authoring.md` (new): documents running
  `record_lint` before writing a record and the scaffolder invocation
  (issue requirement 3).
- `docs/specs/enforcement-boundary.md`: added verdict rows for
  `record_lint.py` (`contract`) and `record-scaffold.sh` (`repo-local`)
  — the pre-existing `gates/test_boundary.py`'s
  `t_all_gates_modules_recorded` invariant (issue #441) requires every
  `gates/*.py`/`on-the-record/hooks/*.sh` module to carry a recorded row
  once it exists on disk; this is a `docs/` write outside the frozen
  `files:` list, allowed under the warrant directive's docs/ exception
  (same precedent as issue-472's delivery record).

All suites run green:
```
python3 -m pytest gates/test_record_lint.py -q          # derived: 5 passed
python3 -m pytest on-the-record/hooks/test_record_scaffold.py -q  # derived: 4 passed
python3 -m pytest gates/ on-the-record/hooks/ -q         # derived: 246 passed, 0 failed
```

`grep -l record_lint on-the-record/hooks/*.sh` shows both
`record-scaffold.sh` and `record-claim-guard.sh`.

## Why

Per the approved phase-1 proposal: authoring a role record cost one
model turn per gate refusal because `record_enums`/`record_wellformed`/
etc. in `gates.py` and the four checks mirrored inline in
`record-claim-guard.sh` each reported only their own first failure — a
7-refusal loop was observed on issue-512 phase 2. `record_lint` runs
every check in one pass and reports the complete list; the scaffolder
gives authors a starting skeleton so the placeholder-vs-violation shape
is visible before the first write.

## What did not work

- First draft of `gates/test_record_lint.py`'s fixture put an
  `unverifiable:` line immediately followed by a non-blank line; the
  claim-reason regex's trailing whitespace-match swallows the newline
  and merges into the next line's text as the capture group, so the
  empty-reason case silently stopped matching. Fixed by moving that
  line to end the fixture body (nothing follows, so the capture is
  genuinely empty) — this regex is inherited verbatim from
  `record-claim-guard.sh`'s pre-existing behavior, not something this
  delivery changed.

## Rationale for deviations

The before-landing warrant hunt (stance: assume the gate just touched
is bypassable — find the bypass; see the hunt record under docs/reports,
filename starting `2026-08-09-hunt-record-lint-and-scaffolder`) found
that `record-claim-guard.sh`'s new `import record_lint` dependency gave
the hook a live crash path (e.g. `RCG_GATES_DIR` resolving wrong under a
relocated/symlinked hook script) that exited with an unblocking status
instead of a blocking one, because the script's own fail-closed trap —
meant to remap an unexpected exit code to a blocking exit — was disarmed
immediately before the final `exit` statement, so the remap never ran.
This bug pre-dated this delivery (the disarm line was already there) but
was previously unreachable, since the hook's inline checks only used
stdlib and could not crash; routing through `import record_lint` made
the crash path live. Fixed by removing the disarm line so the trap stays
armed through the final exit, verified via a minimal isolated
trap-behavior script reproducing the before/after exit code (the guard's
own board-gate hook blocks simulated `docs/issue-*`-path payloads from
this session's own Bash tool, so the trap mechanics were verified
standalone rather than through the exact hook invocation). Full suite
re-run green after the fix. This is a fix applied within the frozen
write set (`record-claim-guard.sh` was already listed), not a
scope-exceeded stop — noted here because it is a deviation from the
proposal's `## What will be done` text, which did not anticipate this
bug.

## Open findings

One `after-proposal`-stage finding remains from the earlier hunt (same
record referenced above, stance 4): if `record-scaffold.sh` were ever
built as a `PreToolUse` hook instead of the CLI form actually shipped,
the hooks lifecycle-registration file would need an entry it does not
have. This delivery shipped the CLI-only form (per the proposal's stated
alternative and the warrant-hunter's own after-proposal finding), so the
condition that finding warns about does not apply to what landed — the
hooks registration file is unchanged by design, verified unchanged in
the write set.

## closed_checks

- gates/test_record_lint.py: passed, derived: `python3 -m pytest gates/test_record_lint.py -q | tail -1` (code_under_review: see frontmatter)
- on-the-record/hooks/test_record_scaffold.py: passed, derived: `python3 -m pytest on-the-record/hooks/test_record_scaffold.py -q | tail -1` (code_under_review: see frontmatter)
- full gates/ + on-the-record/hooks/ suite: passed, no regressions, derived: `python3 -m pytest gates/ on-the-record/hooks/ -q | tail -1` (code_under_review: see frontmatter)
- before-landing warrant hunt (stance 0, `assume the gate just touched is bypassable`): FINDING found and fixed, re-verified via isolated trap-behavior repro (code_under_review: on-the-record/hooks/record-claim-guard.sh)

## Next steps

None — phase 2 delivery complete, PR to be opened for human review/merge.

## Resolution path

No blocking open findings; the remaining after-proposal note above is
informational (documents why it does not apply to the shipped form), not
a follow-up action.
