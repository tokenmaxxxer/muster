---
status: proposed
---

files:
- on-the-record/commands/run.md
- gates/acceptance_gate.py
- gates/pr_reference.py
- gates/test_acceptance_gate.py
- docs/issue-310/reports/implementation.md

## Request

Nothing currently stops the orchestrator from "closing" a user's stated
requirement with a behavior promise, a private memory note, a one-line
hardcoded-list edit, or a doc sentence — all four happened in one session
on 2026-08-07 (#298, #303, #309, #147/#140), each caught by the user, not
the system. #310 asks for: (1) contract text naming these four as
non-discharges, stating the orchestrator may discharge a requirement only
by drafting an issue routed to a role, and that an interim mitigation
lands *with* the issue rather than closing it; (2) an issue-shape rule
that acceptance criteria must name an executable artifact, not prose;
(3) a mechanical gate — modeled on `record_enums` (record-fields-gate) —
that blocks phase-2 issue closure unless the issue's Acceptance section
names an executable check, or explicitly states the requirement is
unverifiable and why; and its own acceptance must satisfy the rule it
creates (no exemption for the rule that makes the rule).

## Constraints

- Human closes GitHub state per contract v3; this gate blocks the
  phase-2 *closing keyword* on the PR (same enforcement point
  `pr_reference.check_body` already owns), not `gh issue close` itself —
  it never adds a new actor that closes issues.
- Must fail closed on unreadable input, matching every other gate in
  `gates/gates.py` (`record_wellformed_in`, `writeset`, `parse_new_deps`)
  — "can't check" is a block, not a pass.
- Must not block the existing issue-228 incomplete-plan check already in
  `check_body` — the new check composes with it, not replaces it.
- Escape hatch for genuinely unverifiable requirements must be an
  explicit, greppable marker (not the absence of an artifact reference),
  so an issue can't drift into "unverifiable" by default.

## Rationale

Two splice points exist for the mechanical piece: `closure_sweep.py`
(board-wide, post-hoc, comment-only — already used for issue/PR state
drift) and `pr_reference.check_body()` (merge-time, blocking, already
gates the phase-2 `Closes #n` keyword and already reads issue body
content for plan-parsing per issue-228). `closure_sweep` was rejected:
it only *reports* violations after the fact via issue comments, which is
exactly the "sentence added to a doc" failure mode #310 is about — a
comment nobody is forced to act on is not a check that fails. Extending
`pr_reference.check_body()` was chosen because it already blocks the
phase-2 close at the same enforcement point (contract v3's existing
"Closes/Fixes/Resolves" requirement), so the new requirement rides the
same mechanism instead of adding a second, weaker one.

For the check's own shape, inlining the logic into `pr_reference.py`
directly (vs. a standalone `gates/acceptance_gate.py`) was rejected:
every existing network-free predicate in this codebase
(`classify()` in `closure_sweep.py`, `dep_names()` in `gates.py`) is kept
separate from its `gh`-calling wrapper specifically so it is unit
testable without a live repo — inlining would make the new rule the one
exception to that pattern, and #310's own acceptance line demands a
runnable failing/passing demonstration, which needs a pure function to
test against synthetic issue bodies.

## What will be done

1. `on-the-record/commands/run.md`: add a section naming the four
   non-discharges (promise, memory note, hardcoded-list edit, doc
   sentence) verbatim, stating a requirement is discharged only by an
   issue drafted and routed to a role, and that an interim mitigation
   (e.g. #304 → #303's list edit) lands *with* the issue and does not
   close it — contrasted with #140 → #147 as the failure shape. Add to
   the issue-drafting instructions that Acceptance criteria must name an
   executable artifact (a test file path, a gate name, or a CI job) —
   not prose — or explicitly mark the requirement unverifiable and say
   why.
2. `gates/acceptance_gate.py` (new): a pure function
   `check_issue_body(issue: int, body: str) -> list[str]` that scans an
   issue body's `## Acceptance` section for either (a) a reference
   matching an executable-artifact shape — a backtick-quoted path under
   `test/`, `gates/`, `.github/workflows/`, or a `gate:`/`check:`
   line — or (b) an explicit `unverifiable:` line followed by a reason.
   Returns a violation string if neither is present; fails closed
   (returns a violation, not `[]`) when no `## Acceptance` section
   exists at all.
3. `gates/pr_reference.py`: in `check()`'s `phase == "phase2"` branch,
   after the existing closing-keyword check passes, call
   `acceptance_gate.check_issue_body(issue, issue_body)` (issue body is
   already fetched there for plan-parsing) and fold any violations into
   the returned list — same fail-closed shape as the existing
   `_issue_view_body is None` branch.
4. `gates/test_acceptance_gate.py` (new): unit tests against synthetic
   issue bodies, network-free, including the two scenarios #310's own
   acceptance line requires — a prose-only Acceptance section (fails)
   and one naming an artifact (passes) — plus one exercising the
   `unverifiable:` escape (passes) and one with no `## Acceptance`
   section at all (fails, fail-closed).
5. `docs/issue-310/reports/implementation.md`: phase-2 record per
   record-shape-directive, with the test run's actual output as the
   effect-verification evidence for #310's own acceptance line.

## Out of scope

- Rewriting `closure_sweep.py`'s report-only board sweep to also block —
  it stays detection-only; the blocking gate lives in `pr_reference.py`
  per the Rationale above.
- Retrofitting acceptance criteria onto already-open issues; the gate
  applies going forward, at phase-2 close time, to whatever issue body
  exists then.
- Enforcing artifact-naming on phase-1 proposal PRs — phase-1 never
  carries a closing keyword, so `check_body`'s phase-1 branch is
  untouched.
- A UI/authoring aid for writing the Acceptance section — the gate only
  checks what's already there.

## How you'll know it worked

`python3 gates/test_acceptance_gate.py` (or the project's usual pytest
entry point) run and shown passing, with the two required cases visible
in the output: a synthetic issue closed with a prose-only Acceptance
section makes `check_issue_body` return a non-empty violation list, and
one naming an artifact (or carrying an explicit `unverifiable:` reason)
returns `[]`. That test run's actual output is quoted in
`docs/issue-310/reports/implementation.md` as the effect-verification
evidence — this issue's acceptance is satisfied by the same mechanism it
creates, not by this document's prose.
