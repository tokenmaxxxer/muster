---
status: proposed
files:
  - gates/acceptance_gate.py
  - gates/test_acceptance_gate.py
  - gates/test_setup_failure_propagates.py
  - docs/issue-416/decisions/provenance-and-empty-state.md
---

files:
- gates/acceptance_gate.py
- gates/test_acceptance_gate.py
- gates/test_setup_failure_propagates.py
- docs/issue-416/decisions/provenance-and-empty-state.md

## Request

A sibling project's If-Match CAS fix passed 8-goroutine/10-repeat
concurrency testing but shipped a fresh-install regression, because the
corpus never contained the initial empty state — found in 30 seconds by
actually launching the system, missed by code review and by the
verification that was run. Two decisions are asked for: (1) whether a
verification claim about behavior must state whether it was executed
against a running system, executed as a unit test, or derived by reading —
and whether reading may discharge a behavioral claim at all; (2) whether
initial/empty state is a required, checkable member of an acceptance
corpus. A third, narrower item — a setup step failing without failing the
run — is called out as independently checkable.

## Constraints

- This repo cannot inspect a sibling project's test files; the sibling
  repo's own test corpus is out of this repo's reach. Any mechanism this
  repo builds operates on issue/PR text this repo controls
  (`## Acceptance`, records), the same surface `acceptance_gate.py`
  already governs — not on a target repo's fixtures.
- Per #310, the mechanism must be an executable artifact, network-free,
  matching every existing gate's own convention (`gates/test_*.py` runnable
  directly, no `gh` calls in the unit-tested path).
- Do not touch `gates/skip_gate.py`'s skip/pass distinction — #416 is a
  different axis (claim provenance and corpus completeness), not skip
  detection.
- State honestly, per the issue's own framing, when a field only checks
  presence rather than truth — do not imply a stronger guarantee than a
  text gate can give.

## Rationale

Considered building a mechanism that inspects a target repo's actual test
files for empty-state fixtures (grep for `setUp`/fixture patterns with no
prior state, or run coverage instrumentation to detect an unexercised
"nothing exists yet" branch). Rejected: this repo has no access to a
sibling project's codebase at gate-check time (the gate runs against issue
text in *this* repo, not against an arbitrary cloned target repo), and even
with access, semantically detecting "this fixture represents the empty
state" from fixture code is not a text-pattern problem — it would need
running the target's tests with state-coverage instrumentation the target
project would have to opt into, which is a much larger mechanism than a
presence-checking gate and is not this repo's to build unilaterally for
every project it might govern.

Considered making finding 1's provenance field free-text (e.g. a sentence
describing how the claim was verified) instead of an enumerated field.
Rejected: free text is exactly what `acceptance_gate.py`'s docstring
already identifies as unenforceable — "prose does not discharge this" per
#310. An enumerated field (`executed-live` / `executed-unit` / `read`) is
mechanically greppable the same way `unverifiable:` already is; free text
would just move the same problem #416 reports (prose claims nothing checks)
one field over.

## What will be done

1. Extend `acceptance_gate.py`'s `check_issue_body` with two additive
   checks on the `## Acceptance` section, both modeled on the existing
   `unverifiable:` escape-hatch pattern:
   - `empty state:` line — required whenever the section references a
     test/corpus artifact (the existing `_ARTIFACT_REF` match) *and* the
     claim is behavioral (i.e., not already excused by `unverifiable:`).
     Accepts `empty state: <path or description>` or
     `empty state: not applicable — <reason>` (e.g. a pure read-only
     query with no "nothing exists yet" case). Presence-only: the gate
     cannot verify the named test file actually exercises the empty state,
     and the decision doc says so plainly.
   - `provenance:` line — required alongside any artifact reference,
     one of `provenance: executed-live`, `provenance: executed-unit`, or
     `provenance: read`. When `provenance: read` is used, `acceptance_gate`
     still passes (the issue asks whether reading may discharge a
     behavioral claim at all, and leaves that a live question — this
     proposal answers the *mechanical* half by making the claim type
     visible and greppable, not by banning `read`) but the check message
     text, when the gate blocks for a missing field, says so, so the
     provenance-vs-read question is visible per-issue instead of invisible.
2. `gates/test_acceptance_gate.py`: add cases mirroring the existing
   `t_*` style — missing `empty state:`/`provenance:` blocks, both present
   passes, `unverifiable:` still exempts both (no double-barrier), `empty
   state: not applicable` passes.
3. `gates/test_setup_failure_propagates.py` (finding 3, standalone from the
   acceptance-gate change): builds a throwaway copy of
   `tests/run-orchestrate-tests.sh`'s setup-step shape (a heredoc step
   whose exit code is checked before the real assertions), mutates it so
   the setup step fails, runs it, and asserts the harness's own exit code
   is nonzero. This is the "deliberately break a setup step and assert the
   suite goes red" check named directly in #416's "what needs deciding"
   item 3.
4. `docs/issue-416/decisions/provenance-and-empty-state.md`: records the
   ceiling honestly — `provenance:` and `empty state:` are presence checks,
   not truth checks; states which of #416's four "what needs deciding"
   items this proposal answers (1 partially — field made mechanical and
   visible, not a ban on `read`; 2 — yes, required and checkable at
   presence level; 3 — yes, checkable, test built; 4 — deferred, no
   distinct brief-surface exists in this repo to attach the field to) and
   names finding 4 as explicitly out of scope with the reason.

## Out of scope

- Finding 4 (orchestrator briefs requiring execution) — no distinct
  "brief" artifact exists in this repo separate from the directives already
  governing this session (see survey); building a second copy of the same
  field with no attachment point is speculative, not requested scope.
- Verifying a `provenance:` field's *truth* (that a claim marked
  `executed-live` really was) — stated as the mechanical ceiling per #416's
  own framing, not attempted.
- Any change to a sibling project's actual test corpus — out of this repo's
  reach entirely.
- Deciding whether `provenance: read` should be banned outright for
  behavioral claims — the mechanism makes the claim type visible and
  greppable; the policy question of banning `read` is left to the decision
  doc as an open question, not resolved unilaterally here.

## How you'll know it worked

`python3 gates/test_acceptance_gate.py` — new cases fail against the
current `acceptance_gate.py` (no `empty state:`/`provenance:` check exists
yet) and pass once the extension lands. `python3
gates/test_setup_failure_propagates.py` — asserts a synthetic harness with
a broken setup step exits nonzero; this is the executable artifact for
finding 3, runnable standalone per #310. Both are plain `python3
gates/test_*.py` invocations, no `gh` calls, matching every existing gate
test in this repo.
