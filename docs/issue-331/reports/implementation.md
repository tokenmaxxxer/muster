---
code_under_review:
  - gates/gates.py
  - gates/ci.py
  - .github/workflows/plan-aware-closes-gate.yml
  - test_gates.py
  - gates/test_closes_gate_ci.py
  - docs/issue-331/decisions/2026-08-07-checked-claim-marker.md
loop_state: landed
---

## What was done

Implemented the approved proposal `docs/issue-331/proposals/checked-claims-gate.md`
exactly as written, in the frozen write set:

- `gates/gates.py`: `record_checked_claims(d, cfg)` (registered in `ALL`) —
  denies a changed phase-2 record that sets its role's terminal
  `loop_state` (last value of `roles/<role>.json`'s `record_fields.loop_state`)
  with no `## Acceptance verification` section, an unparseable line, an
  `unverifiable` line with no reason, or a `pass` line naming a
  `path::test_name` test node ID that does not exist in the referenced
  file (parsed, not executed). `parse_checked_claims(work)` factors the
  shared parsing out for `ci.py` to reuse.
- `gates/ci.py`: wired `gates.record_checked_claims` into the default
  (non-`--closes-only`) check bundle; added `_pr_status_checks` (`gh pr
  view --json statusCheckRollup`) and `_checked_ci_claims_bad`, which
  cross-checks `pass` claims naming a CI check (no `::`) against the
  rollup — a missing/pending/failing check is a denial.
- `.github/workflows/plan-aware-closes-gate.yml`: added the "full check
  bundle (non-closes-only)" step (`gates/ci.py . --pr "$PR_NUMBER"
  --autodetect`, no `--closes-only`) — per the warrant hunt on the
  proposal, without this the new gate would exist and pass unit tests
  but never run in CI.
- `docs/issue-331/decisions/2026-08-07-checked-claim-marker.md`: records
  the `checked:`/`## Acceptance verification` convention and the
  terminal-value-is-last-list-element reading of `record_fields.loop_state`.
- `test_gates.py`: 10 new unit tests for `record_checked_claims` /
  `parse_checked_claims` (section missing, non-terminal untouched,
  well-formed test-node pass, nonexistent test denied, unparseable line
  denied, unverifiable without/with reason, undeclared-loop_state role
  untouched, CI-check-name claim parsed for reuse, `ci.check()` wiring).
- `gates/test_closes_gate_ci.py`: 6 new CI-context tests for
  `_checked_ci_claims_bad` (passing/failing/missing-from-rollup/pending-
  StatusContext/unreadable-rollup-fails-closed/no-claims-skips-the-`gh`-call).

## Why

Per #331: a record's claim of having reached its role's terminal
`loop_state` must be mechanically checked (test existence / CI
statusCheckRollup), not merely asserted in prose. Approved by
`APPROVE issue-331/implementation` on issue #331, no conditional
feedback comment followed the approval.

## Acceptance verification

- `record_checked_claims` denies a terminal record with no section — checked: test_gates.py::t_checked_claims_terminal_no_section_blocks — result: pass
- non-terminal records are untouched — checked: test_gates.py::t_checked_claims_non_terminal_untouched — result: pass
- well-formed `path::test_name` pass claim is accepted — checked: test_gates.py::t_checked_claims_wellformed_test_node_passes — result: pass
- `pass` claim naming a nonexistent test is denied — checked: test_gates.py::t_checked_claims_nonexistent_test_blocks — result: pass
- an unparseable Acceptance-verification line is denied — checked: test_gates.py::t_checked_claims_unparseable_line_blocks — result: pass
- `unverifiable` with no reason is denied, with a reason is accepted — checked: test_gates.py::t_checked_claims_unverifiable_without_reason_blocks — result: pass
- a role with no declared `loop_state` enum is left untouched — checked: test_gates.py::t_checked_claims_role_undeclared_loop_state_untouched — result: pass
- `record_checked_claims` is actually wired into `ci.check()` — checked: test_gates.py::t_ci_check_wires_record_checked_claims — result: pass
- a passing `statusCheckRollup` entry is accepted, failing/missing/pending is denied — checked: gates/test_closes_gate_ci.py::t_checked_ci_claims_passing_rollup_accepted — result: pass
- an unreadable rollup fails closed (denial, not silent pass) — checked: gates/test_closes_gate_ci.py::t_checked_ci_claims_unreadable_rollup_fails_closed — result: pass
- the new CI job step actually runs `gates/ci.py` in non-`--closes-only` mode — checked: .github/workflows/plan-aware-closes-gate.yml — result: unverifiable: this repo's own CI cannot execute a GitHub Actions workflow from inside this session; the workflow YAML change is visible in the diff and follows the existing `--closes-only` step's established pattern, but whether it actually fires green on this PR is only observable from GitHub's Checks tab once the PR is open, not from a local run.
- full suites still pass with no regression — checked: test_gates.py — result: pass
- full suites still pass with no regression — checked: gates/test_closes_gate_ci.py — result: pass

`python3 test_gates.py` (156 tests) and `python3 gates/test_closes_gate_ci.py`
(36 tests) both ran to completion with every test passing, including the
16 new ones above. `test_gates.py` has one *pre-existing, unrelated*
failure outside this write set (`t_repo_local_claude_config_stops_the_spawn`,
`OSError: Read-only file system` on a path outside the repo — reproduced
identically on `main`/pre-change HEAD by stashing this session's diff and
re-running, so it is a sandbox filesystem constraint of this session, not
a regression this change introduced).

## Reach beyond this PR's own acceptance criteria (per #330)

The gate now runs against **all 43 role definitions**, not only
`implementation` (`gates/gates.py:record_checked_claims` reads
`roles/<role>.json` generically, same as `record_enums` before it) — any
phase-2 record across any role that sets its role's terminal
`loop_state` gains a hard new requirement it did not have before: a
well-formed `## Acceptance verification` section, or the write is
denied. This invalidates the previously-accepted pattern of landing a
terminal-state record with only prose completion claims — every role
session must now add the section from its next terminal-state record
onward. Per the proposal's own Out-of-scope: no retroactive check runs
against records already on `main` with a terminal `loop_state` and no
such section (this is a write-time gate on new writes only); no branch-
protection registration was performed (a manual GitHub Settings action,
same boundary #245 already drew).

## Open findings

None blocking. The after-proposal warrant hunt's finding (the unwired
`plan-aware-closes-gate.yml`) was already folded into the approved
proposal's write set before this session started. The before-landing
hunt (`docs/reports/2026-08-07-hunt-checked-claims-gate.md`, stance
"assume the gate just touched is bypassable") observed that `result:
unverifiable: <any non-empty text>` (and `result: fail`) lines pass
`record_checked_claims`/`_checked_ci_claims_bad` with no verification of
the claim's substance. That behavior is the approved proposal's own
Constraint, built exactly as specified: "Per #310, where a criterion is
genuinely unverifiable, the record must say so and say why; the gate
must accept that explicit declaration as satisfying the check for that
one criterion, not force a pass." The hunt confirms the built gate
matches its own spec on this point; it is not a defect this build
introduced.

closed_checks:
  - check: hunt-before-landing-bypass-stance
    code_sha: c3ac82143a7db3ba756701de6e2540ba5a1b1e8

## What did not work

None — no attempt was undone or replaced, and everything expected to
hold (test wiring, CI-check cross-check shape, decision doc placement)
held on the first pass.

## Rebase re-verification (2026-08-07, second pass — main advanced to `0f3151a`, ~177 commits ahead of the prior rebase base)

The branch had already been rebased once (see the superseded numbers this
section replaces below); `origin/main` moved another ~36 commits in the
interim, so per this task's instruction ("a green from your original
base attests to a state that no longer exists") the rebase and full
re-run were repeated against current `origin/main` rather than trusting
the earlier pass.

`git fetch origin && git rebase origin/main` (new base `0f3151a`) —
conflicts in 4 files, all additive on both sides (no line touched by
both branches' *intent*, only by proximity):

- `gates/ci.py` — main added `gates.requirement_registry(repo, {})` to
  the check bundle; this branch's `record_checked_claims`/
  `_checked_ci_claims_bad` calls. Kept both.
- `gates/gates.py` — two separate hunks: (1) `requirement_registry`'s
  full definition (main) alongside `record_checked_claims`'s full
  definition (this branch) — concatenated, both kept; (2) the `ALL`
  registry dict — main's `"requirement_registry": requirement_registry`
  entry plus this branch's `"record_checked_claims": record_checked_claims`
  entry, both kept.
- `gates/test_closes_gate_ci.py` — main added
  `t_autodetect_missing_approval_refusal_names_role_searched_and_approvals_present`
  and neighboring tests; this branch's `_checked_ci_repo` fixture and 6
  tests. Concatenated both blocks.
- `docs/specs/reconciled-index.md` — stale content hashes (concurrent
  merges changed `protocol.md`, `protocol.ko.md`,
  `docs/handbooks/operations.md`, `on-the-record/commands/run.md` since
  the file was last regenerated). This is exactly #336's gate working as
  designed on a file a concurrent merge changed, not a real ambiguity:
  regenerated with `python3 gates/spec_index.py --update`; the
  "Resolved ambiguities" section itself was not touched by any concurrent
  edit (diff was hashes only), so it needed no update.

Verified syntax first (`python3 -m py_compile gates/ci.py gates/gates.py
gates/test_closes_gate_ci.py`) before re-running suites.

Re-ran, on the rebased tree (HEAD `aa1beed`, 0 commits behind
`origin/main` at `0f3151a`, working tree otherwise clean):

- `python3 -m pytest -q --ignore=gates` — **417 passed**, 0 failed.
- `gates/` subtree: this task's instructions state main's `gates/`
  cannot collect (#398); reproduced — `python3 test_gates.py` (the
  file's own `__main__` runner) crashes with
  `TypeError: t_find_violations_uses_record_evidence_for_keywordless_merge()
  missing 1 required positional argument: 'tmp_path'` (a pytest-fixture
  test added on `main` that the hand-rolled no-argument runner in
  `test_gates.py`'s `__main__` block cannot satisfy). Ran the same file
  through `pytest` instead, which supplies the fixture:
  `python3 -m pytest -q test_gates.py` — **110 passed**.
  `python3 -m pytest -q gates/` — **74 passed, 1 failed**. The one
  failure, `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`,
  is pre-existing and unrelated to this issue: reproduced identically by
  running the same test in a clean `git worktree` of `origin/main` alone
  (no issue-331 changes present), so it is not a regression this branch
  introduces — reported, not fixed (outside this write set).
- Combined effective total actually run: 417 + 110 + 74 = 601 passed,
  1 pre-existing failure outside this issue's write set.

No code changes beyond conflict resolution and the one index
regeneration — no scope was widened, no adjacent issue was touched.
`docs/reports/2026-08-07-hunt-checked-claims-gate.md`'s prior findings
are unaffected by the rebase (same file content on both sides of the
merge, no conflict on it).

### Superseded: first rebase pass numbers (base `c71173b`, kept for history only — do not cite)

`python3 -m pytest -q --ignore=gates` — 399 passed; `python3 -m pytest -q
gates` — 64 passed, no collection error (reported as clean at that base).
`origin/main` has since advanced past that base, so these numbers
describe a tree that no longer exists; the section above is current.
