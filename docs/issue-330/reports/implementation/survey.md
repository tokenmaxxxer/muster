# Survey — issue-330

Scout skip: pure infra/process change to this project's own mechanical
gates, no external product surface — the field is the codebase's own
`gates/` module and the docs it already governs, not a product category.

## What's already checked, and where

- `gates/gates.py` — deterministic, LLM-free checks: write-path restriction
  (`PROTECTED_*`), record path shape (`RECORD_PATH`), tool-tag residue,
  dependency-manifest registry checks. Runs against `origin/main...HEAD`
  diff (`_committed_changes`).
- `gates/ci.py` + `.github/workflows/plan-aware-closes-gate.yml` — the one
  gate actually wired to block a PR merge (closes-keyword vs. phase
  mismatch). Every other gate in `gates/` is invoked only inside role
  sessions (PreToolUse hooks), not in CI — so today only the closes-gate
  is unbypassable from outside the session.
- `record-shape-directive` (session hook, not a repo file) — steers
  `## What did not work` / `## Rationale for deviations` shape before
  write; `record-fields-gate.sh` (referenced by directives, lives in the
  rulebook skeleton under `docs/issue-170/_assets/...`, not in this
  repo's own `gates/`) checks frontmatter/heading presence at write time.
- None of the above compares a change's diff against anything **outside
  the issue's own write set**. Every check is intra-issue: does this PR's
  record have the right shape, does this PR's write-set stay inside its
  frozen list. No check reads what else in the repo depends on, or
  contradicts, the state this PR is changing.

## The concrete regression chain named in the issue

- #285 added a TTL pull marker → #296/#297 (`bench/run.py`'s provenance
  abort broke because #285 never checked what read the marker's old
  location).
- #297 fixed where new markers are written → #313 (old markers, already
  on disk, were never invalidated — #297 checked "does my write path
  work," not "what already-written state does my write path orphan").
- #140 widened a terminal-state vocabulary → #147 (#140 checked "does my
  list include the needed word," not "does contract §2's own vocabulary
  already have a word for this").

Common shape: every fix passed its own PR's checks (gates, tests,
review) because those checks only look at files the PR's own write set
names. Nothing reads (a) what other code depends on the specific
old-form of the thing being changed, or (b) what already-on-disk records
assume the pre-change behavior.

## What exists to build on

- `gates/gates.py::_committed_changes` already computes a full diff
  file-list per PR — the substrate an impact check needs is already
  there, just unused for anything but write-set membership.
- `RECORD_PATH` regex + the doctrine-ladder directive already establish
  that implementation records are the place structured, mechanically
  checked claims about a change go. Adding a required section there
  (rather than inventing a new document type) reuses a channel already
  gated and already read by the next role/human.
- No existing mechanism greps the repo for other files whose content
  names/imports/paths reference something the diff removes or moves —
  this is the actual gap and the smallest thing that would have caught
  all three named regressions (a marker path moved, a vocabulary word
  removed, a read-path left unmentioned).

## Constraints this proposal must respect

- #310: acceptance must name an executable artifact that fails on
  regression — a written "state your reach" convention with nothing
  checking it is exactly the discharge #310 forbids.
- Contract v3 s19 two-phase gate: this session is phase 1 only (no PR
  exists yet for issue-330/implementation). No code lands until a human
  Approve.
- Write-set must stay inside what CI/tests can exercise without
  new external dependencies (this repo has no network-dependent test
  infra beyond what `gates/` already uses).
