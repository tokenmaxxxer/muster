# issue-149 — build proposal (coding)

references #149

## Request (paraphrased)
Two measured leaks: (A) a judgment role (feasibility) shipped `src/`
implementation in phase 2; (B) the reverse — a coding role could produce
another role's design/verdict artifacts. Nothing gates "PR diff matches
this role's declared output kind." The issue asks for: (1) explicit
bidirectional contract text (a role's phase-2 output must be its
declared `produces` kind; a needed *other* kind routes to the role that
produces it, never self-expanded); (2) a `write_scope` declared per role
in `roles/*.json`, checked against PR diff, overridable per board repo;
(3) a stated non-substitution principle (coding's self-test pass is a
merge-decision input, never a verification verdict); (4) a survey of the
leak path for incident (A) plus write_scope's own side-effect analysis
(coding's phase-1 proposal writing is legitimate design activity; some
board repos are docs-as-product); (5) an invariant that every role's own
record-writing obligation survives regardless of write_scope tightening.

## Constraints
- No schema/migration concern; `roles/*.json` has one prior consumer
  (`spawn.py`'s `roles` subcommand printer) plus the new gate.
- Must not block phase-1 proposal writing by coding
  (`docs/issue-<n>/proposals/coding.md`,
  `docs/issue-<n>/reports/coding/**`) — that is coding's own legitimate
  design output per contract v3 s19, not a boundary violation.
- Must not block any role's own record file
  (`docs/issue-<n>/reports/<role>.md`) even under a tightened board-repo
  override — item 5 of the issue is explicit that the documentation
  obligation is unconditional.
- Fail closed: an unresolvable role (branch doesn't match
  `issue-<n>/<role>`) or an undeclared `write_scope` blocks, mirroring
  `writeset()`'s existing fail-closed stance on an undeclared spec
  write-set.
- This repo (on-the-record) has no `src/` — a board repo's actual layout
  can only be known by that repo, so the override must live in the board
  repo, not be hardcoded here.

## What will be done
files: `roles/coding.json`, `roles/feasibility.json`, `roles/ux-design.json`,
`roles/product.json`, `roles/qa.json`, `roles/review.json`,
`roles/verify.json`, `roles/ops.json`, `roles/reflect.json`,
`gates/gates.py`, `gates/ci.py`, `test_gates.py`, `protocol.md`.

1. **`write_scope` per role** (`roles/*.json`): add a `write_scope` array
   of glob patterns describing the *kind* of path each role's phase-2
   output may touch, derived from that role's existing `produces` prose
   — e.g. coding: `["src/**", "test/**"]` plus the always-included record
   paths below; feasibility/review/qa/verify/product/ux-design/reflect/
   ops: their respective `docs/issue-*/reports/<role>.md` /
   `docs/issue-*/proposals/<role>.md` shapes, explicitly *not*
   `src/**`/`test/**`. Every role's `write_scope` always includes
   `docs/issue-*/reports/<role>.md`, `docs/issue-*/reports/<role>/**`,
   `docs/issue-*/proposals/<role>.md` regardless of what else is listed —
   this is the item-5 invariant, enforced structurally (the gate unions
   these in, see point 3) so no per-role edit can silently drop them.

2. **Per-repo override point**: a board repo may place
   `docs/specs/write_scope.md` at its root with per-role glob overrides
   (same `- write: <role>: <glob>` line shape `writeset()` already parses
   out of `spec.md`, extended with a role prefix — reuses proven parsing
   rather than a new format). When present for a role, its patterns
   **replace** that role's on-the-record default glob list for that repo
   (so e.g. a board repo with code at root instead of under `src/` can
   say `- write: coding: *.py`), but the always-included record paths
   from point 1 are still unioned in afterward — an override can widen or
   relocate what a role may build, never drop the record-writing duty.

3. **New gate `role_scope`** (`gates/gates.py`): resolves the acting role
   from the PR's branch name (`issue-<n>/<role>`, the same shape
   `board-gate.sh` already keys off, and the same "derive role from a
   structural signal, fail closed if it doesn't match" posture
   `RECORD_PATH`/`record_enums()` already uses for the record-file path).
   Loads `roles/<role>.json`'s `write_scope`, applies a board-repo
   `docs/specs/write_scope.md` override for that role if present, unions
   in the always-included record-path patterns, then checks every changed
   file (reusing `changed_files()`) against the effective allow-list with
   `fnmatch`, exactly like `writeset()`'s existing match loop. Unresolvable
   role or missing `write_scope` declaration on the resolved role: fail
   closed (append a blocking reason), never silently skip — matching
   `writeset()`'s and `record_enums()`'s existing fail-closed precedent
   for "can't check" vs. "nothing to check."

4. **Wire into `gates/ci.py`**: `check()` gains the branch name (fetched
   via `gh pr view --json headRefName`, same call shape `pr_reference.py`
   already uses for `body`) and calls `gates.role_scope()`. Kept optional
   like the existing `pr`/`issue` args — CI invocations without PR context
   skip it, same posture the file already documents for `pr_reference`.

5. **Contract text** (`protocol.md`): add the bidirectional rule from the
   issue's point 1 — a role's phase-2 deliverable must be of the kind its
   `produces` declares; a needed different kind routes to the role that
   produces it (no self-expansion of scope; a boundary-crossing need gets
   recorded and the session ends, transition is an orchestrator+human
   call) — plus the non-substitution line from point 3 (a role's own
   self-test pass is a merge-decision input, never a verification role's
   verdict).

6. Tests in `test_gates.py`: role resolved and diff inside `write_scope`
   → pass; role resolved but diff outside `write_scope` (both directions —
   a judgment role touching `src/**`, and coding touching another role's
   `docs/issue-*/reports/<other>.md`) → blocked; branch doesn't match
   `issue-<n>/<role>` → fail closed; role's own record/proposal path stays
   allowed even under a board-repo override that omits it (item-5 union
   invariant) → pass; per-repo `write_scope.md` override changes the
   effective glob for a repo without touching `roles/*.json` → pass.

## Out of scope
- Editing the per-role rulebook repos themselves
  (`$TOKENMAXXXER_RULEBOOKS/<role>-agent-rulebook`, referenced by
  `roles/<role>.json`'s `path` field) — those are separate repos this
  session has no access to; if a rulebook's own directive text needs the
  same bidirectional-boundary language, that is a follow-up issue against
  each rulebook, not this one.
- Retroactively auditing already-merged PRs for past `write_scope`
  violations (incident A/B are already-landed history; this proposal is
  forward-gating only).
- A UI/report surface listing `write_scope` violations over time —
  gate output is the existing block-message list, matching every other
  gate in `gates.py`.

## How it'll be known to work
- Automated: new `test_gates.py` cases (point 6) pass under
  `python3 -m unittest test_gates.py`, alongside the full existing suite
  (no regression in `writeset`/`record_enums`/other gate tests).
- Manual: run `gates/ci.py` against a synthetic PR whose branch name is
  `issue-999/feasibility` with a diff touching `src/whatever.py`
  (incident-A shape) and confirm it now blocks; and against
  `issue-999/coding` with a diff touching
  `docs/issue-999/reports/review.md` (incident-B shape) and confirm it
  now blocks; and confirm a normal in-scope diff for each role still
  passes.
