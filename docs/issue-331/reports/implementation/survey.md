# Survey — issue #331 (completion is self-asserted, nothing checks the claim)

## Skip record

Scouting skipped: on-the-record has no external product category to
benchmark against — the deliverable is a gate inside this repo's own
mechanical-check layer (`gates/`), following an existing in-repo pattern
(`record_fulfils_diff`, issue #155). This is the scout directive's
second skip condition — the spec (extend the existing gate family with
one more diff-checkable claim) leaves no open design-category decision
to research externally.

## Sibling-issue boundary

- **#310** (open, no `docs/issue-310/` tree yet): requires that a stated
  *requirement* land as an issue whose *acceptance criteria* name an
  executable artifact. That is about how a requirement is authored.
  #331 is about a different moment: whether a role's *claim that it
  finished* is checked against what actually happened, once work is
  already in flight. An issue can carry a perfect #310-shaped acceptance
  section and still have its record say "done" without the check having
  been run. This proposal does not touch issue authoring/acceptance
  wording — it adds a check on the *record's claim*, and where a
  criterion is genuinely unverifiable it reuses #310's requirement that
  the record say so explicitly (this proposal enforces that the "why"
  line exists, it does not relitigate #310's rule).
- **#330** ("nothing checks what a change does to its surroundings" —
  open, no tree yet): that is impact/regression analysis — does the
  change break something elsewhere. #331 is narrower: does the record's
  own completion claim match the record's own evidence. No overlap in
  write set; #330 would touch a different check entirely (a diff-vs-
  affected-surface sweep), not the record-claim gate this proposal adds.
- **#312** ("closes-gate misattributes phase on cross-role handoff" —
  touches `gates/ci.py`'s phase detection) and **#245** (`--closes-only`
  wiring) are adjacent (same file) but orthogonal: they are about which
  phase a PR is in, not about whether the record's claim inside that
  phase is evidenced. No functions touched by #312/#245 are edited here.

None of the three overlap this proposal's write set. Boundary: this
proposal adds exactly one new gate function plus its CI wiring and
tests; it does not touch requirement-authoring (#310), impact analysis
(#330), or phase detection (#312).

## Current state

`gates/gates.py` already implements the pattern this issue needs, for a
narrower claim shape:

- `record_fulfils_diff` (`gates/gates.py:411-462`, issue #155): a
  phase-2 record may carry opt-in `fulfils: delete|create|move <path>`
  lines. The gate cross-checks each claim against the *actual committed
  diff* (`_committed_changes_with_status`) and denies the write if the
  claim ("I deleted X") does not match what the diff shows. This is
  exactly the "claim vs. reality, mechanically" shape #331 asks for —
  but it only covers file delete/create/move claims, not "I ran the
  check and it passed."
- `record_wellformed` / `record_no_tool_residue` / `record_enums`
  (`gates/gates.py:296-405`) are structural-only: they check the record
  parses and its enum fields are declared values. None of them read the
  record's *prose claims* against anything external.
- `gates/ci.py` is the network-aware CI entry point (`gh pr view`,
  `gh issue view` already used at `gates/ci.py:53-127` for head-ref,
  title, commits, reviews). It already resolves issue number and phase
  from the branch name (`_issue_and_role_from_branch`,
  `gates/ci.py:65`) and already fetches PR body/commit data over `gh`.
  There is no existing call that reads the linked issue's own body
  text or the PR's check-run rollup.
- `ALL` (`gates/gates.py:527-531`) is the registry `check()` iterates;
  `gates/ci.py`'s `check()` (`gates/ci.py:229-267`) is the router that
  decides which named checks run for a given PR/phase — this is the
  wiring point for a new check.
- Roles declare a terminal `loop_state` value per `roles/<role>.json`
  (`record_fields.loop_state`); for `implementation` that is `"landed"`
  (`roles/implementation.json`). Every role file examined
  (`roles/*.json`, 43 files) declares its own terminal value inside the
  same `loop_state` enum — there is no single hardcoded terminal-value
  string shared across roles, so a generic check must read it from the
  role file rather than assume the string `"landed"`.
- Nothing today reads a record's completion language ("완료", "성공",
  "통과", "done", "passed", "complete") and requires it to be paired
  with anything. A role can write `loop_state: landed` and prose saying
  every acceptance item passed with zero mechanical cross-check —
  confirmed by grep: no gate function name or test in `gates/`,
  `test_gates.py`, or `gates/test_closes_gate_ci.py` matches
  `checked|evidence|acceptance` (only `record_fulfils_diff` exists, and
  it is diff-only, not check-run/test-output related).

## What will change (projected write set)

- `gates/gates.py` — one new pure function, registered in `ALL`,
  following `record_fulfils_diff`'s exact shape (opt-in marker parsed
  from changed phase-2 records, fail-closed on unparseable marker
  lines, no network).
- `gates/ci.py` — wiring into the network-aware default check list
  (this check needs `gh issue view` for the acceptance-criteria count
  and, optionally, `gh pr view --json statusCheckRollup` for named CI
  checks — both already-used call shapes in this file).
- `test_gates.py` — unit tests for the new pure function (mirrors the
  existing `record_fulfils_diff` test block).
- `gates/test_closes_gate_ci.py` — CI-context tests for the wiring.
- `docs/issue-331/decisions/` — the new record convention (a changed
  contract surface: what a phase-2 record must contain to claim
  completion) belongs here per the doctrine ladder, not just this
  report.
- `docs/issue-331/reports/implementation.md` — phase-2 record (this
  session stops at phase 1; written when phase 2 opens).

No new dependency, no new env var, no schema/migration.
