---
status: proposed
files:
  - gates/absence_claims.py
  - test_absence_claims.py
  - docs/specs/survey-conventions.md
  - docs/issue-358/reports/implementation.md
---

## Request

Three phase-1 proposals filed today (#318/#320, #324, #341/#327) each wrote
"X does not exist" in a survey when the honest answer was "not visible from
this gitignored clone" or "not checked against the primary source" — and in
one case, wrong about the filename too (`runs/roster.json` vs. the actual
`runs/active.json`). A false absence terminates investigation instead of
being caught, which a false presence would be. #358 asks whether a role
session can even see operational state, whether absence claims must record
what was searched, and whether platform-capability questions need a
different answer path — then asks for the honest ceiling of what can be
checked mechanically, per #310.

## Constraints

- Per #310: acceptance needs an executable artifact that fails on
  regression, not a doc sentence. Per #358's own text: if the full claim is
  not mechanically checkable, say so and say why, rather than reaching for a
  stronger-sounding check that doesn't hold.
- Must not attempt semantic verification of whether a cited search was
  *adequate* — survey.md's "Mechanical-enforceability constraint" section
  establishes that classifying prose adequacy is a natural-language judgment
  call this project's own gates already refuse to attempt (#341 precedent).
- Must not fold in #287 (gates-layer fail-open fixes) or #298 (orchestrator
  enforcement) — distinct actors and surfaces, per survey.md's boundary
  section.

## Rationale

Two designs were considered for the mechanical artifact.

**(a) A hard gate that blocks a proposal/survey commit containing an
unevidenced absence claim** (a `PreToolUse`-style check, analogous to
`deliverable-guard.sh`). Rejected: this repo has no hook wired over prose
content today (only `SessionStart`, `UserPromptSubmit`, `PreToolUse` on
Write/Edit are declared in `on-the-record/hooks/hooks.json`, and
`PreToolUse` only inspects the file being written, not whether the sentence
inside it cites a real search). Building that hook is the same class of
infrastructure #298 already owns as its subject ("orchestrator is the only
unenforced actor... building that surface is the entire subject of the
already-open #298") — #318's survey drew exactly this boundary for a
sibling problem and #358 draws it the same way. A blocking gate would also
have to decide *adequacy* of a search, not just its presence, which survey.md
already establishes as unreachable without guessing.

**(b) A standalone, unit-testable syntactic checker plus two pinned
regression fixtures** — chosen. `gates/absence_claims.py` exposes
`check_absence_claims(text: str) -> list[Violation]`: it scans for a fixed
list of absence-claim phrases (English and Korean: "does not exist", "is
absent", "was not found", "존재하지 않는다", etc.) and flags each occurrence
whose containing paragraph carries no evidence marker (a file path, a
command like `grep`/`git show`/`find`, or a cited URL). This mirrors #318's
own chosen shape exactly: "a pure content-check function... no dependency on
hooks.json, fires no hook, and is fully unit-testable with string fixtures
the same way `gates/flows.py`'s markdown parsing is tested today." It
answers survey.md's honest-ceiling question directly: syntactic
evidence-adjacency is checkable; claim adequacy is not, and the function
does not pretend otherwise. The two regression fixtures
(`runs/active.json` is the real path, not `runs/roster.json`; a `Stop` hook
exists in Claude Code and can block) pin the two facts #358 itself proved
wrong, so a future survey cannot silently reintroduce either specific error.

The checker is not wired into any commit-time gate in this proposal (that
would be design (a), rejected above); it ships as a script a role session
can run against its own draft survey before committing, and as a pytest
module CI already collects. Wiring it into an actual blocking hook, if
wanted, is a follow-up in #298's territory, not this one's.

## What will be done

1. `gates/absence_claims.py` — `check_absence_claims(text)` per the design
   above, plus `KNOWN_CORRECTIONS` — the two pinned facts from this issue,
   checked as plain string/regex assertions against `spawn.py` and against a
   description of the Claude Code hooks surface (the second one recorded as
   a documented, sourced constant since it is a platform fact, not a
   repo-grep-able one).
2. `test_absence_claims.py` — fixtures: a survey excerpt with an unevidenced
   absence claim (flagged), one with an evidenced claim (not flagged), and
   the two regression assertions from (1).
3. `docs/specs/survey-conventions.md` — the convention itself, small: "cannot
   see" vs. "does not exist," what counts as evidence, and that platform
   capability questions must cite the primary source (e.g. the Claude Code
   docs), not this repo's own config, per #358's finding #3. This is the doc
   `on-the-record/commands/run.md` currently has no equivalent section for
   (confirmed in survey.md's "Where 'does not exist' gets written today").
4. `docs/issue-358/reports/implementation.md` — phase-2 record, stating
   plainly (per #358's own Acceptance) that full semantic adequacy-checking
   is not mechanically reachable and why, alongside what the shipped checker
   does cover.

## Out of scope

- Wiring `absence_claims.py` into any `PreToolUse`/commit-time gate —
  deferred as orchestrator/gate-enforcement infrastructure (#298's
  territory), not built here.
- Re-fixing #318/#320, #324, or #341/#327 themselves — already corrected on
  their own branches.
- Any change to `gates/closure_sweep.py`, `gates/flows.py`, or
  `deliverable-guard.sh` (#287's surfaces).
- Grading whether a cited search was *sufficient*, only whether one is
  *named* — per the Rationale's mechanical-enforceability limit.

## How you'll know it worked

- `pytest test_absence_claims.py` passes, including the two regression
  fixtures pinning `runs/active.json` and the `Stop` hook fact — either
  fixture fails if the underlying fact regresses (e.g. `spawn.py`'s
  `ROSTER` constant is renamed without the checker being updated) or if the
  checker's evidence-adjacency logic stops flagging the known-bad fixture
  string.
- `docs/specs/survey-conventions.md` exists and is readable from a fresh
  clone (no dependency on `runs/` or any gitignored path), and states the
  "cannot see" vs. "does not exist" distinction in its own text — checkable
  by grepping the file for both phrases.
