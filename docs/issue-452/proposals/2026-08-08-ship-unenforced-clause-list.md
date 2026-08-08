---
status: proposed
files:
  - on-the-record/UNENFORCED-CLAUSES.md
  - on-the-record/commands/run.md
  - gates/test_boundary.py
  - docs/specs/enforcement-boundary.md
---

# Ship the unenforced-clause list in the deployed plugin payload

## Request

Follow-up from issue #441's execution-observation verdict (PR #449):
criterion 4 was not discharged — a consumer project cannot read, with
zero installation beyond the plugin, which contract clauses are not
mechanically enforced for it. Ship the unenforced-clause list (derived
from `docs/specs/enforcement-boundary.md`) inside the deployed
`on-the-record/` tree, and reference it from the contract
(`run.md`), with `gates/test_boundary.py` cases asserting both.

## Constraints

- The list must live inside `on-the-record/` (the actual
  plugin-deployed tree), not only in `docs/specs/`, per the issue text.
- It must be *derived*, never hand-maintained separately — the same
  principle `docs/specs/enforcement-boundary.md`'s own header already
  states and `test_boundary.py` already enforces for the boundary
  spec itself (#333, #376).
- `run.md` (the contract a consumer's orchestrator reads) must carry a
  reference line pointing at the shipped list.
- `gates/test_boundary.py` gains: (a) a case asserting the list file
  exists inside `on-the-record/` and matches the spec's list, (b) a
  case asserting the reference line exists in `run.md`.

## Rationale

Considered generating `on-the-record/UNENFORCED-CLAUSES.md` at
install/build time (e.g. a hook or CI step that copies/derives it on
`self-update.sh`'s refresh) instead of committing it as a static file
kept in sync by a gate. Rejected: this repo has no build step between
"commit" and "consumer installs the plugin" — `self-update.sh` pulls
plugin files as they are on the branch, so a generated-at-install file
would need the generation logic itself shipped and run client-side,
adding a new moving part (and a new failure mode: generation fails
silently on a consumer's machine) to solve a problem a committed file
plus a gate already solves at zero runtime cost. A statically committed
file, kept honest by a `test_boundary.py` case that fails the build
when it drifts from the spec, matches the derivation principle
(content is derived and checked, not hand-maintained) without adding
install-time machinery.

## What will be done

- Add `on-the-record/UNENFORCED-CLAUSES.md`: the extract of
  `docs/specs/enforcement-boundary.md` rows whose verdict is
  `contract, CI-supplement` or an `out of scope — operator decision`
  variant — i.e. contract-bound clauses not reached by the zero-install
  baseline — plus the short framing paragraph from the spec's
  "Reachable vs. unreached" section. `repo-local`/`n/a (infrastructure)`
  rows are excluded: they are not consumer-facing contract clauses.
- Add a one-line reference in `on-the-record/commands/run.md` pointing
  a consumer session at `UNENFORCED-CLAUSES.md`.
- Add two `gates/test_boundary.py` cases: one parses
  `UNENFORCED-CLAUSES.md` and asserts its mechanism rows are *exactly*
  the set of `contract, CI-supplement` / `out of scope — operator
  decision` rows in `docs/specs/enforcement-boundary.md` — equal sets,
  not a one-directional subset check, so a truncated or emptied
  `UNENFORCED-CLAUSES.md` fails the gate instead of vacuously passing;
  one asserts the reference string is present in `run.md`.
- Add a short note in `docs/specs/enforcement-boundary.md` recording
  that `on-the-record/UNENFORCED-CLAUSES.md` is the derived,
  gate-checked extract of this file's unenforced rows.

## Out of scope

- Any change to the underlying enforcement mechanisms themselves
  (`landing_readiness.py`'s CI-supplement status, the operator's
  out-of-scope calls) — this issue only ships visibility, per its own
  Acceptance section.
- Board-wide drift detection, reusable consumer CI workflows, or any
  other item already ruled out of scope by the 2026-08-07 operator
  decision recorded in `docs/specs/enforcement-boundary.md`.
- A generated/build-time delivery mechanism (see Rationale).

## How you'll know it worked

`python3 gates/test_boundary.py` passes, including the two new cases;
`grep -n "UNENFORCED-CLAUSES" on-the-record/commands/run.md` finds the
reference line; `on-the-record/UNENFORCED-CLAUSES.md` exists and its
content matches the corresponding rows in
`docs/specs/enforcement-boundary.md`.
