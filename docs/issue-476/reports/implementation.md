---
code_under_review: HEAD
loop_state: landed
---

## What was done

Built H1 and H2 per `docs/issue-476/proposals/implementation.md`,
approved on issue #476 (`APPROVE issue-476/implementation`,
2026-08-08T10:11:33Z, single-account mode).

**H1**
- `gates/claim_scan.py` — `scan_text()`: regex-matches claim vocabulary,
  requires adjacent evidence (fenced block or `Repro:`/`Verify:` line
  within `ADJACENCY_LINES`), and when `repo_targets` is supplied,
  requires the evidence's cited target to actually exist in the
  repo/diff. CLI wrapper (`main()`) reads a file and checks against
  `git ls-files`.
- `gates/reexecution_gate.py` — `run_reexecution()`: `git worktree add
  --detach <sha>`, runs the cited command inside it under a timeout,
  writes `.reexecution/<issue>-<role>.json` via `write_verdict()`.
  Worktree-creation failure and timeout both yield `error` (fail
  closed), never a silent skip.
- `gates/landing_readiness.py` — new `reexecution_blocking_cause()`:
  reads a PR's reexecution verdict and, on `fail`/`error`, returns a
  `blocking_causes` entry scoped to that PR's own
  `docs/issue-<n>/reports/<role>.md` (not a `gates/`-prefix scope —
  closes the after-proposal hunt's bypass, proposal §3). Wired into
  `main()`.
- `.gitignore` — added `.reexecution/`.

**H2**
- `roles/implementation.json`, `roles/architecture.json` —
  `record_fields.loop_state` gains `refused`, `not-needed`,
  `cannot-verify`, inserted *before* `landed` (see deviation below).
- `gates/gates.py` — new `record_refusal_reasoned()`, colocated with
  `record_enums`: when a changed record's `loop_state` is one of
  `REFUSAL_STATES`, requires a non-empty `reason:` field. Registered in
  `ALL` as `record_refusal_reasoned`. Same fail-closed-on-missing-role
  shape as `record_enums`.

**Tests** (all pass, run this session):
- `python3 gates/test_claim_scan.py` — 9 passed
- `python3 gates/test_reexecution_gate.py` — 7 passed (throwaway local
  git repos, no network)
- `python3 gates/test_gates_refusal.py` — 8 passed (see deviation: not
  named `test_gates.py` as proposed)
- `python3 -m pytest gates/test_landing_readiness.py -q` — 14 passed
  (4 new cases for `reexecution_blocking_cause`)
- `python3 -m pytest gates/ -q` — 136 passed (full existing suite, no
  regressions)
- `python3 -m pytest test_gates.py -q` — 109 passed (existing root
  self-check suite; unaffected by the H1/H2 additions)

## Why

Per issue #476: honest work (H1, mechanized re-execution of
claim-adjacent commands, verdict never role-writable) and honest
refusal (H2, a first-class `refused`/`not-needed`/`cannot-verify`
vocabulary at equal structural cost to `landed`) must both be cheaper
than performing the gate. Detail in
`docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md`.

## Upstream

Basis: `docs/issue-476/proposals/implementation.md`
(`docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md`).

## What did not work

- Proposed `gates/test_gates.py` collided with the pre-existing
  repo-root `test_gates.py` — same basename, no `__init__.py`
  boundary, breaks `pytest` collection (exactly the shape
  `gates.duplicate_test_basenames` exists to catch; it caught it).
  Renamed to `gates/test_gates_refusal.py`.
- First attempt appended the three new `loop_state` values *after*
  `landed` in `roles/implementation.json`/`architecture.json`. Broke:
  `gates.py:_terminal_loop_state()` reads the *last* declared value as
  the role's terminal state (undocumented in the proposal/ADR, found
  only by running the full `gates/` suite) — with `landed` no longer
  last, `cannot-verify` silently became the terminal value instead,
  and `gates/test_closes_gate_ci.py`'s checked-CI-claims tests (which
  depend on `landed` being terminal) started failing. Fixed by
  reordering: `landed` stays last; the three refusal values are
  inserted before it. `record_refusal_reasoned()` and `record_enums()`
  check `loop_state` membership directly, not via
  `_terminal_loop_state()`, so this reordering does not weaken H2's own
  check.
- Wiring `landing_readiness.py`/`gates.py` into the two new modules
  tripped an *existing* gate, `gates/test_boundary.py`
  (`t_all_gates_modules_recorded`,
  `t_unenforced_clauses_file_matches_spec_exactly`): every
  `gates/*.py` module needs a row in
  `docs/specs/enforcement-boundary.md`, mirrored into
  `on-the-record/UNENFORCED-CLAUSES.md`. Neither file was in the
  frozen write set (see deviation below).

## Rationale for deviations

- **File rename**: `gates/test_gates.py` (proposal's literal name) →
  `gates/test_gates_refusal.py`. The proposal's write set predates
  discovery of the basename collision with the pre-existing root
  `test_gates.py`; the collision is not a design choice to relitigate,
  it is a filesystem fact the proposal could not see. Renaming keeps
  the same tests, same coverage, same file count — it is the
  `duplicate_test_basenames` gate itself resolving the only viable
  path.
- **loop_state ordering**: proposal said "gains `refused`,
  `not-needed`, `cannot-verify` alongside the existing four values"
  without specifying position; appending naively breaks
  `_terminal_loop_state()`'s undocumented last-element convention.
  Inserting before `landed` preserves the existing terminal-state
  contract for `parse_checked_claims`/`record_checked_claims` (both
  outside this proposal's write set) while still making the refusal
  values available to `record_enums`/`record_refusal_reasoned`, which
  check membership, not position.
- **Two files outside the frozen write set**:
  `docs/specs/enforcement-boundary.md` and
  `on-the-record/UNENFORCED-CLAUSES.md`. Not a scope expansion of the
  build itself — `gates/test_boundary.py` (pre-existing, unrelated to
  this proposal) mechanically requires every `gates/*.py` module to
  have a row in the spec, mirrored into the derived file, before the
  frozen write set's own tests (`gates/test_boundary.py` is part of
  `python3 -m pytest gates/ -q`, which the proposal's "How you'll know
  it worked" section already commits to running clean) can pass. Both
  rows record `claim_scan.py`/`reexecution_gate.py` as `contract,
  CI-supplement`, same verdict class as `landing_readiness.py`, since
  they fold into `landing_readiness.py`'s existing CI-only enforcement
  path and add no new install surface.

## Open findings

Before-landing warrant hunt (stance 1, `docs/reports/2026-08-08-hunt-implementation.md`,
"before-landing" section) found: `gates/ci.py:_phase2_record_evidence()`
and `gates/closure_sweep.py`'s `has_record_evidence` path check only
`loop_state` non-emptiness, not its value (issue #284's deliberate
design). This diff's H2 refusal states (`refused`/`not-needed`/
`cannot-verify`) now satisfy that same non-empty check, so a merged
phase-2 PR whose record explicitly declares no delivery occurred
silently waives the "Closes #issue" CI requirement — the opposite of
what a refusal state should mean. `gates/ci.py` and
`gates/closure_sweep.py` are outside this proposal's frozen write set
(`docs/issue-476/proposals/implementation.md`'s `files:` list); fixing
them is scope-exceeded for this build and is not done here.

## Next steps

Follow-up issue/proposal needed: teach `_phase2_record_evidence()` and
`closure_sweep`'s evidence check to exclude the new refusal states
(treat `refused`/`not-needed`/`cannot-verify` as NOT closing-intent
evidence), so a refused/not-needed/cannot-verify record does not
silently waive the Closes-issue requirement. Step 4
(execution-observation / conformance-review — measuring the issue's
pre-registered metrics against threshold) remains the issue's own next
step and is unaffected by this finding.

## Resolution path

The open finding above resolves via a new proposal scoped to
`gates/ci.py`/`gates/closure_sweep.py`, filed against issue #476 (or a
follow-up issue) once triaged by the user/orchestrator.
