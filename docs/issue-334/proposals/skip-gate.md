---
status: proposed
files:
  - gates/skip_gate.py
  - gates/test_skip_gate.py
  - docs/handbooks/operations.md
---

## Request

A skip means a check did not run; a pass means it ran and was correct.
This repo's documented self-check (`python3 -m pytest` / `test_gates.py`)
exits 0 and prints a routine-looking green summary even when some tests
were skipped, so a role session reading exit code (or a summary line) has
no mechanical way to tell "verified" from "never ran." Per #334, fix that
by making a skip surface as a distinct, non-passing outcome instead of
folding into the green run.

## Constraints

- No test in this repo currently uses `pytest.mark.skip`/`skipIf`/
  `SkipTest` (confirmed by grep) — nothing to migrate, this is a new gate.
- Per #310: acceptance must name an executable artifact that fails on
  regression; a doc/handbook edit alone does not discharge the
  requirement.
- Follow the existing `gates/` shape: a small deterministic script paired
  with its own `test_*.py` (as `gates/ci.py`/`gates/test_closes_gate_ci.py`
  and `gates/flows.py`+`gates/gates.py`/`test_gates.py` already do).

## Rationale

Considered adding `-ra`/`--strict-markers` to `pytest.ini` alone, with no
new gate script. Rejected: `-ra` only changes what's *printed* in the
terminal summary — pytest's own exit code stays 0 when tests are skipped,
so a role or CI step that keys off exit status (the actual mechanism any
completion claim would rely on) still reads the skip-containing run as a
clean pass. The false positive #334 reports lives in the exit code, not
in the summary's verbosity, so only a wrapper that inspects the skip
count and changes the exit code closes it.

Also considered: make the gate silently allowlist "expected" skips (e.g.
environment-gated ones like the issue's own CLI-controller example) so it
only fails on *unexpected* skips. Rejected for this pass: an allowlist
needs a place to record *why* a skip is expected, and inventing that
format now, with zero real skips in the suite to calibrate against, would
be speculative. Simpler and matching the issue's own conclusion — "a
completion claim resting on a skipped test must not be able to call
itself verified" — is to fail closed on any skip; a role that hits a
genuinely-expected skip says so explicitly in its own record, which is a
human/role act, not something the gate should paper over automatically.

## What will be done

- `gates/skip_gate.py`: runs `python3 -m pytest -q -ra <passthrough args>`
  as a subprocess, parses the terse `-ra` summary for `SKIPPED` entries.
  Exits 0 only when the run itself exited 0 AND zero tests were skipped.
  Otherwise exits 1 and prints each skipped test's nodeid and reason on
  stderr, plus a one-line verdict (`N passed, M SKIPPED — not verified`)
  so the output can't be mistaken for a clean pass at a glance.
- `gates/test_skip_gate.py`: two fixture suites under a temp dir — one
  with a single `pytest.mark.skip`, one with no skips — asserting
  `skip_gate.main()` (or its subprocess entry point) exits 1 for the
  first and 0 for the second. This is the executable regression artifact
  #310 requires: it fails if `skip_gate.py` ever regresses to treating a
  skip as a pass.
- `docs/handbooks/operations.md`: update the "자체 점검"/"Self-check"
  section to run `python3 gates/skip_gate.py` alongside/instead of bare
  `pytest`, with one line on why (skip-vs-pass distinction, links #334).

## Out of scope

- Retrofitting an allowlist mechanism for intentionally-expected skips —
  noted as a real design fork in the survey, deferred since no real skip
  exists yet to calibrate the format against.
- Wiring `skip_gate.py` into `.github/workflows/` as a required CI check
  — this repo currently runs no test suite in CI at all (confirmed in the
  survey); adding that wiring is a separate, larger change outside what
  #334 asks for.
- Touching `gates/ci.py`'s PR-gating logic or any other existing gate —
  this is a new, additive, standalone script.

## How you'll know it worked

`python3 gates/test_skip_gate.py` (or `python3 -m pytest gates/test_skip_gate.py`)
passes, demonstrating the gate fails on a fixture suite containing a
skip and passes on one without — the executable artifact that fails when
this regresses, per #310.
