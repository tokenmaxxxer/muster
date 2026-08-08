Scout skip (stated per scout-directive): pure bugfix, no design decision
open — #460's migration table already decided `.github/workflows/`'s
disposition (retired, no replacement path), so the only question is
mechanical: stop `acceptance_gate.py` from accepting a phantom reference
to it.

## Current state

`gates/acceptance_gate.py:22` — `_ARTIFACT_REF` regex:
```
r"`[^`]*(?:test/|gates/|\.github/workflows/)[^`]*`"
```
still lists `.github/workflows/` as an accepted executable-artifact
path fragment. #460 deleted `.github/workflows/` entirely
(`docs/specs/enforcement-boundary.md:82-88`, "retired, issue #460" —
no replacement possible, enforcement moved to the shipped hook surface
and locally runnable gate commands). Since the directory no longer
exists, any backtick-quoted `.github/workflows/...` reference an issue
cites can never execute — the gate should not accept it as satisfying
the executable-artifact requirement.

`test/test_side_effect_round.py` (`test_acceptance_gate_accepts_phantom_github_workflows_reference`,
lines 22-42) is the attempt-5 repro from #497's side-effect round
(`docs/issue-497/reports/defect-verification.md`): it currently asserts
the CURRENT (buggy) behavior — that the gate accepts the phantom
`.github/workflows/` reference — with an explicit comment saying "if
this now fails, the phantom-path bug has been fixed and this test
should be updated to assert the gate flags it instead." That is exactly
the flip #499 asks for.

Full suite: `python3 -m pytest -q` → 704 passed, 0 failed (confirmed
just now). No other file references `.github/workflows/` inside
`_ARTIFACT_REF` or an equivalent acceptance-list; `grep -rn
"github/workflows" gates/` shows only this one regex hit plus
`test_boundary_workflow_migration.py`'s existence check (unrelated —
that asserts the directory is absent/empty, not an acceptance-gate
regex).

## Write set implied

- `gates/acceptance_gate.py` — drop `.github/workflows/` from
  `_ARTIFACT_REF`.
- `test/test_side_effect_round.py` — flip the attempt-5 repro to assert
  the fixed behavior (gate now flags the phantom reference), per #499's
  explicit acceptance line.

No other file needs to change: `docs/specs/enforcement-boundary.md`
already documents the retirement and needs no update for this
regex-only fix.
