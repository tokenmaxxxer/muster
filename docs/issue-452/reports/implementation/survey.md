# Current-state survey — issue-452

## What exists today

- `docs/specs/enforcement-boundary.md` — the derived, per-mechanism
  verdict list (issue #441). Verdicts: `contract`, `contract,
  CI-supplement`, `out of scope — operator decision, 2026-08-07`,
  `repo-local`, `n/a (infrastructure)`. Only `contract, CI-supplement`
  rows (currently: `landing_readiness.py`) are contract-bound clauses
  that a zero-install consumer does NOT get enforcement for — the
  "unenforced clause" the issue means. `repo-local`/`n/a` rows are not
  consumer-facing contract clauses at all, so they are out of this
  list's scope by definition of the boundary spec itself.
- `gates/test_boundary.py` — mechanically checks that every
  `gates/*.py`, `on-the-record/hooks/*.sh`, `.github/workflows/*.yml`,
  and `spawn.py` has a recorded verdict row in the spec. It does not
  currently check anything about the plugin-deployed tree
  (`on-the-record/`) or about `run.md`'s text.
- `on-the-record/` (plugin payload actually shipped to consumers):
  `commands/run.md` (the contract text a consumer session reads),
  `hooks/*.sh`, `.claude-plugin/plugin.json`. `grep -rln
  enforcement-boundary on-the-record/` finds only a comment-string
  mention inside `contract-guard.sh` — no file with the list's content,
  and `run.md` has no reference line at all
  (confirmed: `grep -n "enforcement-boundary" on-the-record/commands/run.md`
  returns nothing).
- `docs/issue-441/reports/execution-observation.md` already diagnosed
  this exact gap (its "Open findings" section) and recommended, as
  option (b), "a plugin-shipped command or hook-emitted line surfacing
  `docs/specs/enforcement-boundary.md`'s unenforced rows inside a
  consumer session." Issue #452 is that follow-up, filed by the user.

## Write set this proposal expects

- `on-the-record/UNENFORCED-CLAUSES.md` (new) — the unenforced-clause
  list, shipped inside the plugin-deployed tree, zero-install readable.
- `on-the-record/commands/run.md` (edit) — one reference line pointing
  a consumer session at the new file.
- `gates/test_boundary.py` (edit) — new test case(s) per the issue's
  own Acceptance: (1) the list file exists inside `on-the-record/` and
  matches the spec's list, (2) `run.md` contains the reference line.
- `docs/specs/enforcement-boundary.md` (edit, small) — note that this
  file is now also the source `on-the-record/UNENFORCED-CLAUSES.md` is
  derived from/kept in sync with, so a future edit to one is expected
  to update the other (documentation-only change, not a new verdict).

## Design decision and why it is not open

The issue's own Acceptance section already pins the shape down to two
concrete `gates/test_boundary.py` cases (file-exists-and-matches,
reference-line-exists) and names the target location
(`on-the-record/`, referenced from "the contract the orchestrator
reads" — i.e. `run.md`). The remaining choice — one new small file
vs. copying the full spec verbatim vs. generating the file at
install/build time — is settled by the constraint already established
in `docs/specs/enforcement-boundary.md`'s own header: the boundary is
"derived from this file's completeness against the filesystem, not
maintained by hand elsewhere" (#333, #376). A hand-duplicated second
copy of the full spec would violate that same principle for the exact
same reason #441 built `test_boundary.py` in the first place, so a
small derived extract (just the unenforced rows, not the full
three-table spec) checked for content-match by a gate is the only
option consistent with prior, already-approved decisions in this repo
— not a new open design question. Per the scout-directive's skip
conditions, this counts as "the spec leaves no design decision open":
the shape is fixed by #441's already-adjudicated derivation principle,
so no scout sweep was run — recorded here as the mandatory skip
record.
