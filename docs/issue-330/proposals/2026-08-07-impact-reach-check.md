---
status: proposed
files:
  - gates/gates.py
  - gates/test_gates.py test_gates.py additions (impact/reach checks)
  - docs/issue-330/reports/implementation.md
---

## Request

The operator's complaint: no role checks what its change does to its
surroundings, so a fix that satisfies its own issue breaks something
adjacent, which becomes the next issue. Requested: impact analysis as a
first-class, owned step — what does this change reach, what depended on
the old behavior, what already-on-disk state does it invalidate — backed
by an executable check per #310, not a promise or a doc sentence.

## Constraints

- #310: acceptance must name something executable that fails on
  regression; an unchecked convention is not an acceptable discharge.
- Contract v3 s19: this PR is phase 1 only — proposal and survey, no
  code, no gate wiring. Code lands only after a human Approve.
- Stay inside `gates/` — the module already holds every other
  deterministic, network-free check in this repo (`gates/gates.py`,
  `gates/ci.py`), and `_committed_changes` already computes the diff
  file-list this check needs.
- No new external dependency, no network call — every existing gate in
  `gates/` runs offline against `git diff`.

## Rationale

**Chosen approach**: (1) require a `## Reach` section in phase-2
implementation records (same channel as the existing `## What did not
work` requirement, extended rather than duplicated), stating what the
change reaches beyond its own acceptance criteria and what on-disk state
it invalidates; (2) a mechanical gate function in `gates/gates.py` that
computes, from the diff, every path the PR deletes, renames, or moves,
then greps the rest of the repo (outside the PR's own diff) for
references to those old paths — if a live reference survives and the
`## Reach` section doesn't name it as handled, the gate fails.

**Alternative considered and rejected — full static dependency graph**:
build an import/reference graph across the repo and diff it pre/post
change, the way a type-checker or build-graph tool would. Rejected: this
repo is mostly markdown/shell/Python glue with no uniform module system:
the actual regressions named in the issue (#285→#296/#297, #297→#313,
#140→#147) were a moved file path, orphaned already-written files, and a
vocabulary word — none of them a language-level import edge a
dependency-graph tool would see. Building and maintaining a graph tool
for edges that don't exist in this codebase is disproportionate to the
three concrete failures the issue names.

**Alternative considered and rejected — checklist-only ("state your
reach" in the record, unchecked)**: this is exactly the shape #310
already forbids (a doc sentence). It was the shape of the current
`record-shape-directive`'s prose expectations, and the issue is filed
precisely because prose expectations did not hold in practice.

**Alternative considered and rejected — per-role subjective impact
judgment (each role guesses what else its change affects)**: this is
what already happens today ("every role verifies its own change against
its own acceptance criteria") — it is the status quo the issue reports
as failing, not a new step.

## What will be done

1. Extend `docs/issue-<n>/reports/implementation.md`'s required shape
   (already governed by `record-shape-directive` / `record-fields-gate`
   pattern) with a mandatory `## Reach` heading, present even when
   "None." — same convention as the existing `## What did not work`.
2. Add `gates/gates.py::orphaned_references(work, base=BASE)`: from
   `_committed_changes`'s diff, collect paths with git status `D` (delete)
   or the old side of `R`/rename; grep the working tree (excluding the
   PR's own changed files) for literal references to each such path;
   return the list of (old_path, referencing_file) hits found outside the
   diff.
3. Add `gates/gates.py::reach_check(work, record_text, base=BASE)`: calls
   `orphaned_references`; for each hit, checks whether the old path (or
   its containing directory) is named anywhere in the record's `## Reach`
   section text; anything unmatched is a finding. Returns the finding
   list (empty = pass).
4. Unit tests in `gates/test_gates.py` (same no-network convention as
   `gates/test_closes_gate_ci.py`): a fixture diff that deletes a path
   still referenced elsewhere and omits it from `## Reach` must fail;
   the same diff with the path named in `## Reach` must pass; a diff
   with no deletions/renames must pass trivially.
5. Record in `docs/issue-330/reports/implementation.md` (phase 2, after
   Approve) which of the three named regressions (#296/#297, #313, #147)
   `reach_check` would have caught, run against their actual historical
   diffs, as the acceptance evidence.

## Out of scope

- Wiring `reach_check` into the CI-blocking workflow
  (`.github/workflows/plan-aware-closes-gate.yml` or a new workflow) —
  that is a `.github/` change with its own review weight (branch
  protection registration, the same caveat #245's gate carries); this
  proposal delivers the check as a callable, tested function first. A
  follow-up issue covers CI wiring once the check's false-positive rate
  is known from real records.
- Semantic/behavioral impact (e.g., "this changed a function's return
  type and a caller assumed the old one") — this proposal only catches
  path-shaped reach (files/paths deleted, renamed, or moved and still
  referenced). Content-level behavioral impact is a different, harder
  problem than what the three named regressions actually were.
- Retroactively adding `## Reach` sections to already-merged records.

## How you'll know it worked

`python3 gates/test_gates.py` (or pytest, matching `test_gates.py`'s
existing convention) includes new tests for `orphaned_references` and
`reach_check` that fail red on a synthetic diff shaped like #285→#296/
#297 (a moved marker path still referenced elsewhere, undeclared in
`## Reach`) and pass green once the path is declared — i.e., a
regression in this exact shape trips a test, not a human noticing.
