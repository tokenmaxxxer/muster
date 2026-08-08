---
status: landed
files:
  - gates/acceptance_gate.py
  - test/test_side_effect_round.py
---

## Request
`gates/acceptance_gate.py:20-24`'s `_ARTIFACT_REF` regex still accepts
a backtick-quoted `.github/workflows/...` path as a valid executable-
artifact reference, even though #460 deleted `.github/workflows/`
entirely. Remove the reference per #460's migration table, and flip the
#497 attempt-5 repro (`test/test_side_effect_round.py`) from
demonstrating the bug to demonstrating the fix, with the full suite
green.

Scout skip (stated per scout-directive): pure bugfix, no design decision
open — #460's migration table already decided this path's disposition.

## Constraints
- `python3 -m pytest -q` must end 0 failed.
- The fix must not weaken `_ARTIFACT_REF` for `test/` or `gates/` paths,
  which remain valid (nothing in #460 retired those).
- The flipped test must still document what it is testing (why the old
  behavior was wrong), not just assert an opaque `!= []`.

## Rationale
Alternative considered and rejected: instead of removing the
`.github/workflows/` alternative from the regex, add a runtime check
that resolves the referenced path against the filesystem and rejects
paths that don't exist. Rejected because that's a broader behavior
change (path-existence checking for *all* artifact references, not just
the retired one) that #499 doesn't ask for and the survey found no
other stale-path class needing it — `test/` and `gates/` are both live,
enforced directories. A regex-literal removal is the minimal change
that closes exactly the gap #497 found, matching the issue's own
"Remove/replace the reference" framing.

## What will be done
1. In `gates/acceptance_gate.py`, drop the `\.github/workflows/`
   alternative from `_ARTIFACT_REF` (keep `test/` and `gates/`).
   Update the docstring/comment at lines 51-52 and 65 that enumerate
   accepted path prefixes to match.
2. In `test/test_side_effect_round.py`, flip
   `test_acceptance_gate_accepts_phantom_github_workflows_reference` to
   assert the gate now flags the phantom `.github/workflows/`
   reference (non-empty violations), citing #460's migration table as
   the reason the reference is no longer accepted. Rename the test to
   reflect the new (fixed) expectation.
3. Run `python3 -m pytest -q` and confirm 0 failed.

## Out of scope
- Any other attempt-N repro in `test/test_side_effect_round.py` or
  `test/test_silent_failure_repros.py`.
- Path-existence validation for `test/`/`gates/` references.
- Changes to `docs/specs/enforcement-boundary.md` (already documents
  the retirement correctly).

## How you'll know it worked
`python3 -m pytest -q` reports 0 failed; the flipped test asserts
`check_issue_body` now returns a non-empty violation list for a
phantom `.github/workflows/` reference; `grep -n "github/workflows"
gates/acceptance_gate.py` returns no `_ARTIFACT_REF`-adjacent match.
