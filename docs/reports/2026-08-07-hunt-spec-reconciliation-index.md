---
proposal: docs/issue-336/proposals/2026-08-07-spec-reconciliation-index.md
---

# Hunt record — spec-reconciliation-index

## after-proposal — stance 1: find a path phase-2 will need that the proposal's files: list omits

Verdict: FINDING — the only file that actually invokes gates/ci.py in CI, .github/workflows/plan-aware-closes-gate.yml, is not in the write set, and its existing invocation (checkout ref: main, plus --closes-only) makes step 4 of the proposal ("wire gates/spec_index.py into gates/ci.py ... so it runs on every CI invocation") false as stated: the new gate would never actually run in the one CI trigger this repo has, and phase-2 would need to edit this workflow file to make the acceptance claim ("CI itself blocks a PR") true.
Kind: design-error
Seed: docs/issue-336/proposals/2026-08-07-spec-reconciliation-index.md (files: docs/specs/reconciled-index.md, gates/spec_index.py, test_spec_index.py, gates/ci.py, docs/handbooks/on-the-record.md, docs/handbooks/operations.md)
cap_seconds: 90
tier: default
diff_stat_lines: <200 (3 new docs files)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:06:00Z

### Reproduce
cat .github/workflows/plan-aware-closes-gate.yml   # sole CI trigger of gates/ci.py

Shows: on: pull_request, then actions/checkout@v4 with ref: main (never the PR's own branch/diff), then: python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only

gates/ci.py's own check() docstring confirms closes_only=True skips write_scope/protected-path/deps/record checks entirely and returns bad before reaching any of the non-closes-only checks (gates.record_enums, gates.record_wellformed_in, etc.) where a new spec_index call added "alongside the existing gate calls" per step 4 would have to live.

### Observed
The workflow that is the repo's only live CI entrypoint for gates/ci.py always checks out main (not the PR diff) and always passes --closes-only, which the code's own docstring documents as skipping every check outside the plan-aware Closes gate. A spec_index check wired into check()'s non-closes-only body per step 4 of the proposal would never execute in this workflow, and even if reached, it would be checking main's files, not the PR's.

### Expected
For "CI itself blocks a PR that edits a spec-shaped doc without updating the index" (the proposal's own "How you'll know it worked" claim) to hold, phase-2 must also edit .github/workflows/plan-aware-closes-gate.yml (or add a new required workflow) so the new gate actually runs against the PR's own changed files — a path the files: list in this proposal does not name.
