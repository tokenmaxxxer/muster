# Survey — issue-321

## What exists today

- `docs/issue-<n>/` trees hold six standing buckets per issue (`_assets`,
  `decisions`, `handbooks`, `proposals`, `reports`, `specs`); 100+ issue
  directories exist under `docs/` already. Nothing distinguishes, within any
  of them, the operator's verbatim words from generated material — an issue
  body mixes the operator's `## Operator statement` blockquote (a convention
  used in #310, #321, #330, but not mechanically required) with the filer's
  own prose in the same file, at the same visual weight.
- `gates/gates.py` is the deterministic gate layer (`record_enums`,
  `record_wellformed`, `record_fulfils_diff`, `writeset`, `deps`, ...),
  wired into `gates/ci.py`'s `check()`. Gates read PR diffs and record
  frontmatter; none of them read issue bodies or cross-reference an issue's
  originating text against anything.
- `ledger/collect.py` measures review-verdict drift (Present/Surface/
  Absent/Incorrect) across `docs/issue-<n>/reports/review.md` history. This
  is the closest existing precedent for "durable, re-checkable against
  current state," but it tracks review verdicts, not requirement text, and
  has no notion of "the operator's own words."
- No `docs/requirements/` or equivalent registry exists. `grep -rn
  "requirement"` in `protocol.md` returns two incidental hits, no defined
  concept.
- #310 (open, unmerged) establishes the adjacent but distinct rule: a
  requirement may be discharged only by landing as an issue whose acceptance
  names an executable check — it governs the *moment of discharge*. #321 is
  about what happens *after* discharge, as issues accumulate: the discharged
  requirement's own text becomes one file among hundreds and stops being
  findable/adjacent to the work it produced. #330 is about impact analysis
  (what a change reaches) — orthogonal to #321's dilution problem.
- #147 (cited as the motivating instance) is a merged PR that widened a
  terminal-state vocabulary list with words absent from contract §2 — the
  reviewer/merger had no adjacent view of the original contract text to
  check the addition against.

## Write set this proposal will need

- `docs/specs/requirements.md` — new: the durable registry itself (a
  `docs/specs/` file, per contract v3's placement rule for system design
  that "changes only when the system's design changed").
- `gates/gates.py` — new function `requirement_registry(...)` alongside the
  existing `record_*` gates.
- `gates/ci.py` — wire the new check into `check()`'s dispatch, following
  the existing `record_enums` wiring pattern (gates/ci.py:275).
- `test_gates.py` — unit tests for the new gate function, following the
  existing test file's per-gate-function structure.
- `docs/issue-321/decisions/` — the format/placement decision for the
  registry (why `docs/specs/` and not `docs/issue-321/reports/`).

## Alternatives visible from this state

1. **Extend `ledger/collect.py`** to also parse operator-quote blocks instead
   of adding a new registry file. Rejected in the proposal: `ledger/` measures
   review-cycle *effectiveness* (verdict drift over time) — a fundamentally
   different question from "does this exact wording still exist and is it
   still checked." Bolting requirement-tracking onto it would make one file
   answer two unrelated questions, exactly the kind of dilution #321
   complains about, one level down.
2. **A gate that greps every issue body directly via `gh issue list`**
   instead of a materialized registry file. Rejected: `gates/ci.py`'s own
   docstring explains why *local-only* checks exist as a separate mode from
   PR-context checks — a gate that requires live `gh` calls to enumerate all
   issues cannot run in the local/offline path the other gates support, and
   there is nothing to diff against once an issue is closed/deleted
   upstream. A materialized, versioned file is diffable and survives issue
   lifecycle changes.
