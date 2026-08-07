---
status: proposed
files:
  - docs/specs/requirements.md
  - gates/gates.py
  - gates/ci.py
  - test_gates.py
  - docs/issue-321/decisions/2026-08-07-registry-placement.md
---

## Request

기록이 많아짐으로써 사용자가 핵심으로 제시하는 요구사항들이 희석되는 문제
(operator's own words dilute as the record grows). The operator's stated
requirements need to stay identifiable as their own words, stay adjacent to
everything derived from them, and stay re-checkable against current system
state, rather than becoming one document among hundreds.

## Constraints

- Per #310 (a related, distinct rule): a promise, a memory note, a one-line
  list edit, or a doc sentence does not discharge a requirement. This
  proposal's acceptance must name an executable artifact that fails on
  regression.
- Per #330: this section states what the change reaches beyond its own
  acceptance — see "Beyond this issue's acceptance" below.
- Per role-handoff contract v3: document placement follows the doctrine
  ladder — a library/format choice over a named alternative goes to
  `docs/issue-321/decisions/`; the registry itself, being system design that
  should change only when the system's design changes, goes to `docs/specs/`.
- Scope boundary against #310: #310 governs *how a requirement is
  discharged* (must become an issue + check, not a promise/memory/list-edit/
  doc-sentence). #321 governs what happens *after* discharge, as the record
  accumulates — keeping the discharged requirement's own words durable,
  identifiable, and adjacent to its derived work. This proposal does not
  touch #310's discharge rule; it builds the registry #310 already assumes
  exists once a requirement lands as an issue.
- Scope boundary against #330: #330 is about impact analysis (what a change
  reaches). This proposal does not do impact analysis; it does not touch
  #330's territory.
- Known limitation, not introduced by this proposal: `.github/workflows/
  plan-aware-closes-gate.yml` is the only required CI status check, and it
  always invokes `gates/ci.py` with `--closes-only`, which returns before
  `gates.record_enums`/`record_wellformed_in`/`record_no_tool_residue_in`/
  `record_fulfils_diff` run (gates/ci.py:267-278, documented as a deliberate
  narrowing in issue-245's own decision record). Wiring
  `requirement_registry` the same way those existing record gates are wired
  means it inherits the same non-required status — it runs when `gates/
  ci.py` is invoked without `--closes-only` (e.g. locally, or by the router),
  but not in the one CI check GitHub currently enforces as required. This
  proposal does not widen `.github/` (a protected path per `gates.py`'s
  `PROTECTED_DIRS`, requiring human eyes) to fix that pre-existing gap — it
  is the same gap every other record gate already has, not a regression
  this proposal introduces. Flagged here per #330 so it is visible rather
  than discovered later.

## Rationale

Two alternatives were considered and rejected (full reasoning in
`docs/issue-321/reports/implementation/survey.md`):

1. Extending `ledger/collect.py` to also parse operator-quote blocks.
   Rejected because `ledger/` answers "is review effective over time"
   (verdict drift) — a different question from "does this exact requirement
   wording still exist and still have a live check." Merging them would make
   one file answer two unrelated questions — the dilution problem one level
   down, inside the fix itself.
2. A gate that enumerates issue bodies live via `gh issue list` instead of a
   materialized file. Rejected because `gates/ci.py`'s existing local-only
   check mode (documented in its own module docstring) cannot depend on live
   `gh` calls, and issues can be closed/edited upstream with nothing left to
   diff against. A versioned, materialized registry file is diffable in the
   same PR that discharges or re-checks a requirement, and survives after
   the originating issue is closed.

The chosen approach — a single append-only registry file plus a mechanical
gate — mirrors the precedent already in this repo (`gates/record_enums`,
`gates/record_fulfils_diff`): small, structured, machine-checked files that
sit alongside the bulk of generated docs without competing with it for
attention, because nothing else writes to them.

## What will be done

1. Create `docs/specs/requirements.md`: an append-only registry. Each entry:
   - `id`: sequential (`R001`, ...).
   - `quote`: the operator's verbatim words (Korean or English, unedited).
   - `source_issue`: the GitHub issue number the quote came from.
   - `check`: path to the executable artifact that fails on regression
     (a test file, a gate function name, a CI job) — or, when genuinely
     unenforceable mechanically, the literal string `UNVERIFIABLE: <reason>`
     naming why, per #310's own precedent for stating that plainly rather
     than letting an unchecked rule pass as enforced.
   - `status`: `open` | `enforced` | `stale` (the gate computes `stale`;
     humans/roles set the other two).
2. Add `gates.requirement_registry(d, cfg)` to `gates/gates.py`: parses
   `docs/specs/requirements.md`, and for every entry whose `check` is a
   real path (not `UNVERIFIABLE: ...`), verifies that path still exists in
   the repo at HEAD. An entry pointing at a deleted or renamed check is
   exactly the failure mode #321 names — a requirement quietly losing its
   enforcement as the codebase moves — so the gate fails the check for that
   entry instead of staying silent.
3. Wire `requirement_registry` into `gates/ci.py`'s `check()` dispatch,
   following the existing `record_enums` wiring at gates/ci.py:275, so it
   runs on every PR the same way the other record gates do.
4. Add unit tests to `test_gates.py`: entry with a live check passes; entry
   with a check path that does not exist at HEAD fails; entry using the
   `UNVERIFIABLE:` literal passes without requiring a path; malformed entry
   (missing required field) fails closed, matching this gate layer's
   documented "uncertain → block" principle (gates/gates.py's own module
   docstring).
5. Record the placement decision (`docs/specs/` vs `docs/issue-321/reports/`)
   in `docs/issue-321/decisions/2026-08-07-registry-placement.md`.

This proposal does **not** retroactively populate the registry with past
requirements (#298, #303, #309, #147's underlying contract text, etc.) —
backfill is a separate, larger unit (each entry needs a human or role to
locate the real originating quote and a real check), and per the
scope-exceeded rule that work is out of scope here and becomes its own
follow-up once this mechanism exists to receive it.

## Out of scope

- Backfilling historical requirements into the registry (see above).
- #310's discharge-path contract change (separate, already-filed issue).
- #330's impact-analysis mechanism (separate, already-filed issue).
- Any UI/dashboard for browsing the registry — it is a plain file, read the
  same way every other `docs/specs/` file is read.
- Automatically drafting registry entries from issue text — entries are
  written by whichever role discharges a requirement into an issue; this
  proposal builds the file format and the regression gate, not an extraction
  pipeline.

## How you'll know it worked

- `python3 gates/ci.py <repo>` (or the equivalent pytest invocation added to
  `test_gates.py`) fails when a `docs/specs/requirements.md` entry's `check`
  path no longer exists at HEAD — this is the executable artifact that
  fails on regression, per #310's acceptance bar.
- `test_gates.py::test_requirement_registry_*` (new tests) pass for the
  live-check, stale-check, and `UNVERIFIABLE:` cases described above.
- `docs/specs/requirements.md` exists, is non-empty (seeded with this
  proposal's own entry per #310's "no exemption for the rule that creates
  the rule" precedent), and is parseable by the new gate function.

## Beyond this issue's acceptance (per #330)

- **What this reaches beyond its own scope**: every future issue that
  discharges an operator-stated requirement (per #310) now has a place to
  register that requirement's enforcement — roles authoring phase-1
  proposals gain a new expected step (add/update a registry entry) that
  did not exist before. This is additive, not a behavior change to
  existing gates.
- **Already-on-disk state this invalidates**: none. No existing file is
  removed, renamed, or given new semantics. `docs/specs/requirements.md`
  is a new file; `gates/gates.py` and `gates/ci.py` gain a new function and
  a new dispatch entry without altering existing ones (`writeset`,
  `record_enums`, `record_wellformed`, `record_fulfils_diff`, `deps`
  continue unchanged).
- **What it does not invalidate that a reader might expect it to**: it does
  not retroactively make #147-style silent vocabulary drift detectable —
  that instance predates the registry and has no entry to check against
  until backfilled (explicitly out of scope above).
