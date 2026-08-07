# Survey — issue #334 (skipped test counted as passing)

## Current state

- No test in this repo currently uses `pytest.mark.skip` / `unittest.skip` /
  `skipIf` / `SkipTest` (grep across `*.py` returns nothing). The failure
  mode the issue names has not happened *inside this repo's own suite* yet.
- The repo's documented self-check (`docs/handbooks/operations.md`, "자체
  점검" / "Self-check") is `python3 test_gates.py` or `python3 -m pytest`.
  `pytest.ini` sets `python_functions = test_* t_*` and has no other
  options — no `-ra` summary flag, no `--strict-markers`, nothing that
  would make a skip visible or fail the run.
- No CI workflow runs the test suite at all
  (`.github/workflows/plan-aware-closes-gate.yml` is the only workflow and
  it never invokes pytest/`test_gates.py`). Running the suite and reporting
  its result is entirely a human/role act today — exactly the surface the
  issue is about: a role session runs it, sees exit 0, and reports "tests
  pass" without the skip/pass distinction being mechanically enforced.
- Plain `pytest` (no flags) exits 0 and prints a green summary line even
  when some collected tests were skipped — skipped count is folded into a
  line like `227 passed, 1 skipped in 3.2s`, not a failing status. A
  session that reads exit code alone, or reads the line without parsing
  the skip count, gets the exact false-positive #334 describes.
- Confirmed by running the actual suite: `python3 -m pytest -q` — exits 0,
  `227 passed` (no skips currently present, so nothing to observe live;
  behavior of skip-in-summary is standard pytest and doesn't need
  reproducing to confirm since it's pytest's documented contract).
- Prior art, same shape, different surface: issue #287 ("can't-check
  reported as checked-clean") — `gates/closure_sweep.py`,
  `gates/flows.py`, `deliverable-guard.sh` all silently converted
  "could not check" into "clean". Its fix direction: give the
  unknown/skipped outcome a distinct, non-zero, named report instead of
  folding it into "no problem found". #334 is that same pattern applied
  to test skips instead of gate lookups.
- `gates/` already hosts several small, focused, deterministic Python
  gate scripts with their own `test_*.py` sibling (`gates/ci.py` +
  `gates/test_closes_gate_ci.py`, `gates/flows.py`/`gates/gates.py` +
  `test_gates.py`). That's the established pattern for "small mechanical
  check with its own test" in this repo — a new skip-detection gate
  belongs in `gates/` following that shape, not as a one-off shell
  one-liner.
- `docs/handbooks/operations.md` is the doctrine home for anything a role
  is told to run as part of its workflow (per the record-shape ladder in
  this session's directives: setup step → handbook, same turn). The
  self-check section there is the right place to point at the new gate
  once it exists — updating that pointer to keep the self-check "green"
  meaningful.

## Write set implied by the gap

- `gates/skip_gate.py` (new) — runs the suite, parses pytest's own
  terse-summary skip count, exits non-zero and prints which tests were
  skipped when skipped > 0.
- `gates/test_skip_gate.py` (new) — exercises the gate against a fixture
  suite with a skipped test (must fail) and a fixture suite with no skips
  (must pass), so the gate's own regression is mechanically caught.
- `docs/handbooks/operations.md` — self-check section updated to point at
  `gates/skip_gate.py` instead of/alongside bare `pytest`.

## Alternatives considered while surveying (feeds the proposal's Rationale)

- Add `-ra` / `--strict-markers` to `pytest.ini` alone, no new gate script:
  makes skips appear in the terminal summary but still exits 0 — doesn't
  change the exit code a role/CI would key off, so the false-positive
  survives. Rejected as insufficient on its own but the two are not
  mutually exclusive.
- Fail on ANY `SKIPPED` unconditionally (bare `pytest -x --strict` style)
  vs. an explicit allowlist for legitimately-environment-gated skips (the
  issue's own example: a CLI controller not present in this environment).
  This distinction is a real design fork for the proposal.
