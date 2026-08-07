---
status: landed
files:
  - gates/closure_sweep.py
  - test_gates.py
  - .github/workflows/closure-sweep.yml
  - docs/issue-383/reports/implementation/survey.md
  - docs/issue-383/reports/implementation.md
  - docs/issue-383/decisions/record-evidence-for-closure-sweep.md
---

## Request

Four delivered issues (otr #367, core #132/#133/#151) stay open because
the closing keyword `Closes #n` — the only thing that actually closed
issues — became optional the moment #284 (correct, not reverted) let a
phase-2 record file stand in as alternate evidence for the closes-gate.
`gates/closure_sweep.py` exists to catch exactly "merged delivery, issue
still open" but is itself keyword-anchored, so it reports clean while
four violations are live, and it is not wired into CI at all.

## Constraints

- #284 must not be reverted or weakened.
- The fix must not depend on a human remembering to type a keyword.
- `closure_sweep.classify()` stays a pure, network-free function
  (existing tests depend on this for testability).
- Role sessions cannot close GitHub issues (`gh-guard.sh` denies
  `gh issue close` — contract v3 s8/s9, two-account model); closing the
  four leaked issues is a human/orchestrator act, not something this
  proposal's code can perform directly.

## Rationale

Two candidate fixes, per the issue's own framing:

1. **Derive closure from #284's evidence** (chosen): teach
   `classify()` to also flag `MERGED_DELIVERY_ISSUE_OPEN` when a
   phase-2 record file exists with a non-empty `loop_state`, reusing
   `gates/ci.py::_phase2_record_evidence` verbatim. No change to how
   anyone authors a PR.
2. **Make keyword-emission the system's job** — rejected. It would mean
   auto-inserting `Closes #n` into PR bodies (a bot edit on a human-owned
   artifact) or enforcing it as a hard PR-authoring gate, which is the
   exact rigidity #284 removed on purpose (phase can flip after a PR is
   already open, and the record already carries the evidence). Rebuilding
   that requirement on the write side re-creates the problem #284 fixed;
   the sweep can do the same job read-only on the read side.

## What will be done

- `classify()` gains `has_record_evidence: bool = False`; the
  `MERGED_DELIVERY_ISSUE_OPEN` branch fires on `has_closes OR
  has_record_evidence`, keeping the phase-1 plain-ref case (neither
  true) still not a violation.
- `find_violations()` computes that evidence per subject/role via
  `ci._phase2_record_evidence` and passes it through.
- A GitHub Actions workflow (`closure-sweep.yml`) runs the sweep with
  `--post` on every push to `main`, daily on a schedule, and on manual
  dispatch — so it runs without anyone remembering to invoke it.
- Tests pin: the no-keyword+record-evidence violation case, the
  no-keyword+no-evidence non-violation (no noise), the properly-closed
  companion (no violation despite record evidence present), and that
  `find_violations` actually wires the record check end to end.

## Out of scope

- Propagating an equivalent sweep to `tokenmaxxxer-core` or the other
  org repos — `tokenmaxxxer-core` has no `gates/closure_sweep.py` of its
  own; that repo's gate system is a separate codebase and a separate
  write set.
- Enforcing the workflow via branch-protection required-check
  registration (same limitation `plan-aware-closes-gate.yml` already
  documents: needs a Settings change outside repo content).
- Closing the four leaked issues via this session — blocked by
  `gh-guard.sh` for role sessions; reported to the human/orchestrator
  instead (see implementation record).

## How you'll know it worked

- `python3 gates/closure_sweep.py` on this repo, before the fix,
  printed `종결 일관성 스윕: 위반 없음`; after, it prints the violation
  naming issue #367 / PR #368 — reproduced live in this session.
- `python3 -m pytest test_gates.py -k closure_sweep -q` — 8 passed,
  including the three new pinned cases and the wiring test.
- `grep -rn closure_sweep .github/` now finds `closure-sweep.yml`.
