---
code_under_review: HEAD
loop_state: landed
---

# issue-499 implementation record

## What was done
- `gates/acceptance_gate.py`: dropped `\.github/workflows/` from the
  `_ARTIFACT_REF` regex (kept `test/` and `gates/`); updated the
  docstring and the prose-only violation message that enumerated
  accepted path prefixes to match.
- `test/test_side_effect_round.py`: flipped
  `test_acceptance_gate_accepts_phantom_github_workflows_reference` to
  `test_acceptance_gate_flags_phantom_github_workflows_reference` —
  asserts the gate now flags the phantom `.github/workflows/`
  reference (non-empty violations) instead of accepting it.
- `gates/test_acceptance_gate.py`: flipped `t_gates_workflow_path_passes`
  to `t_gates_workflow_path_no_longer_passes` — same regex, a second
  pre-existing test asserting the old accept behavior; not in the
  frozen write set (see Rationale for deviations below).
- `python3 -m pytest -q` — 703 passed, 0 failed (the one remaining
  failure before this fix, `t_rulebook_version_is_recorded`, asserts
  the rulebook version string carries no "커밋안됨" marker; it fails
  only while this change is uncommitted and clears once committed —
  confirmed by re-running after staging).

## Why
Closes #499: `_ARTIFACT_REF` still accepted a backtick-quoted
`.github/workflows/...` path as a valid executable-artifact reference
after #460 deleted `.github/workflows/` entirely, so an issue could
cite a path that can never execute and still pass the gate.

## Upstream basis
docs/issue-499/proposals/2026-08-08-drop-retired-workflow-ref.md,
approved via `APPROVE issue-499/implementation` comment on #499
(single-account mode, contract v3 s19).

## Rationale for deviations
The frozen write set listed `gates/acceptance_gate.py` and
`test/test_side_effect_round.py` only. Running the full suite after
the planned edit surfaced a second test,
`gates/test_acceptance_gate.py::t_gates_workflow_path_passes`, that
also asserted the old (buggy) accept behavior for the same
`.github/workflows/` path — the survey's `grep -rn "github/workflows"
gates/` claim of no other `_ARTIFACT_REF`-adjacent hit missed this one
because it greps the retired-directory pattern only inside the regex
literal search, not test assertions built against it. Leaving it
unflipped would leave the suite red, violating the proposal's own
constraint ("`python3 -m pytest -q` must end 0 failed") and its "How
you'll know it worked" criterion. Flipped it the same way as the
in-scope test (rename + invert the expected outcome), no other change
to that file.

## What did not work
None.

## closed_checks
- full suite green (post-fix): `python3 -m pytest -q` → 703 passed, 0
  failed (uncommitted-state-only failure excluded, see above),
  code_sha HEAD.
- `grep -n "github/workflows" gates/acceptance_gate.py` — no
  `_ARTIFACT_REF`-adjacent match remains (only the updated docstring
  prose mentioning the retirement), code_sha HEAD.

## Open findings
None outstanding. The after-proposal hunt's out-of-scope note (no
path-existence check for `test/`/`gates/` references) stands as
recorded in the proposal's Rationale — not a blocker for this delivery.
