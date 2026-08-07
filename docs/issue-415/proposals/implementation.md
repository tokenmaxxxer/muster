---
status: proposed
files:
  - gates/repo_scope.py
  - test_repo_scope_gate.py
  - docs/specs/survey-conventions.md
  - docs/issue-415/reports/implementation.md
---

## Request

`thaki-agent-security-controller` issue-234 concluded eight editing surfaces
were absent; `thaki-agent-security-console` had implemented them the same
day, under a sibling repository the investigating role could not see.
`spawn.py` gives each role exactly one repository clone (write isolation,
confirmed intentional in its own docstring) and nothing marks a "does
capability X exist" answer as scoped to that one clone. #415 asks (1)
whether a role can see sibling repos at all, (2) what makes an absence
claim's scope explicit if not, (3) which questions are inherently
cross-repo, and (4) how the orchestrator (which does span repos) gets
involved — and requires the answer state honestly whether the shipped
mechanism catches the general case or only flags that a claim is
repo-scoped.

## Constraints

- Per #310: acceptance needs an executable artifact that fails on
  regression, not a doc sentence — reused directly in `## How you'll know
  it worked` below.
- Per #390: this proposal was drafted against `05f266c` (main /
  `issue-415/implementation`, clean tree) — recorded in survey.md.
- Per #358 (`docs/issue-358/proposals/implementation.md`, status
  `proposed`, unapproved): its `gates/absence_claims.py` checker flags an
  unevidenced absence claim, but by its own design takes `text: str` with
  no repository-identity concept — survey.md confirms it does not and
  cannot reach a well-evidenced-but-single-repo claim. This proposal does
  not depend on #358 landing first; `gates/repo_scope.py` ships standalone
  and composes with `absence_claims.py` later if both land (two independent
  checks over the same text, not one subsuming the other).
- Must not implement cross-repo read access itself (issue's decision 1) —
  that is a write-isolation-model change with security and correctness
  weight of its own kind, and the issue lists it as a decision to make, not
  a foregone one; deferred, see Out of scope.
- Must not build orchestrator-side enforcement (issue's decision 4) —
  #298's declared territory, per #358's own boundary reasoning, reused
  here for the same reason.

## Rationale

Two designs were considered for what ships now.

**(a) Give roles read-only access to declared sibling repositories**, so a
capability question can actually be checked cross-repo instead of merely
flagged as under-scoped. Rejected for this proposal: this is the issue's
own decision 1, explicitly still open ("whether a role can see sibling
repositories at all, and in what mode" — the issue does not pre-answer it).
It also changes `spawn.py`'s write-isolation model, which its own docstring
frames as a deliberate choice with its own tradeoffs (auth vs. container
isolation, settings merge behavior) — widening it to read access needs its
own proposal and its own approval, not a paragraph inside this one. Building
it here would also make the acceptance artifact untestable within this
sandbox (no sibling repos are reachable — confirmed in survey.md), so any
claim of having verified it would be exactly the kind of unverified claim
#415 exists to stop.

**(b) A standalone syntactic checker that flags a capability/contract-
shaped absence claim lacking an explicit scope statement** ("as of `<sha>`
in `<repo>`" or equivalent) — chosen. It answers the issue's decision 2
directly: makes the scope of an absence claim mechanically checkable,
without pretending to check the claim's *truth* across repositories it
cannot see. This mirrors #358's own chosen shape (a pure `text -> list[Violation]`
function, no hook wiring, unit-testable with string fixtures) for the same
reason #358 chose it: no `PreToolUse` hook in this repo inspects prose
content today, and building that hook is #298's surface, not this one's.
The alternative of merging this logic *into* `gates/absence_claims.py`
directly was also considered and rejected, since that file does not exist
on `main` yet (#358 unapproved) — coupling this proposal's landing to
another proposal's approval would block #415 on a decision this issue does
not control.

**Honest ceiling, stated per the issue's explicit ask**: this mechanism
does not catch the general case. It cannot verify that a capability is
truly absent across a multi-repo system — that would require actually
reading the sibling repository, which design (a) above defers. What it
does is narrower and still concrete: it flags a capability/contract-shaped
absence sentence that carries no scope statement, forcing the sentence to
become either "absent from `<repo>` as of `<sha>`" (a defensible, narrower
claim) or to name where else was checked. It cannot judge whether the
scope statement is honest, whether the right repos were checked, or
whether "as of `<sha>`" is stale — the same evidence-adjacency-not-adequacy
ceiling #358 already established for its own checker. A false absence
claim that includes a scope statement, correct or not, will not be flagged
by this mechanism; only a bare, unscoped capability claim is caught.

A further gap, surfaced by the after-proposal warrant hunt (stance:
bypass, `docs/reports/2026-08-07-hunt-issue-415-implementation.md`): the
phrase list in item 1 is fixed and closed, so an unscoped absence claim
phrased with a synonym or contraction outside that list ("isn't
implemented", "there's no fallback for it") never reaches the
scope-adjacency check at all — it passes silently, not because it is
scoped, but because the checker never recognized it as an absence claim in
the first place. This is not a bug to fix before landing; it is a second,
narrower boundary on the same ceiling already stated above, and phase 2's
record must state it in those terms rather than implying the phrase list
is exhaustive.

## What will be done

1. `gates/repo_scope.py` — `check_repo_scope(text: str) -> list[Violation]`.
   Scans for capability/contract-shaped absence phrases (a fixed English +
   Korean phrase list, reusing #358's own list where the shape overlaps:
   "does not exist", "is not implemented", "존재하지 않는다", etc.) whose
   grammatical subject is a bare capability/feature/contract noun phrase
   with no file path in the same sentence (the syntactic signal identified
   in survey.md's "which questions are cross-repo" section) and flags any
   such sentence lacking an adjacent scope phrase (`as of <sha>`, `in
   <repo-name>`, `checked <repo path>`, or equivalent — a small fixed
   pattern list, documented in the module docstring).
2. `test_repo_scope_gate.py` — fixtures: (a) the shape reproduction from
   survey.md as a pinned regression — a sentence of the exact "capability X
   not found" shape with no scope statement must be flagged; (b) the same
   sentence with `"...not found in <repo> as of <sha>"` appended must not be
   flagged; (c) a file-scoped claim ("function Z does not exist in
   `foo.py:12`") must not be flagged, confirming the checker does not
   over-fire on the in-scope case the issue explicitly excludes (decision
   3's second example).
3. `docs/specs/survey-conventions.md` — add a "Capability and contract
   claims are repo-scoped" section (create the file if #358 has not landed
   it first; append the section if it has — checked at write time, not
   assumed). States the convention: a capability/contract absence claim
   must name the repository and commit checked, in the issue's own words
   ("not present in `<repo>` as of `<sha>`" is defensible; "absent" is
   not), and cross-references #415 and #358.
4. `docs/issue-415/reports/implementation.md` — phase-2 record, stating
   the honest ceiling from this proposal's Rationale in its own text (per
   the issue's explicit acceptance requirement), not just implied by what
   shipped.

## Out of scope

- Any change to `spawn.py`'s clone/isolation model, or any read-only
  cross-repo access mechanism — issue's decision 1, left open for its own
  proposal.
- Orchestrator-side answering of cross-repo questions — issue's decision
  4, #298's territory.
- Wiring `gates/repo_scope.py` into any commit-time `PreToolUse` gate —
  same reasoning as #358's equivalent exclusion; this ships as a script/
  pytest module, not a blocking hook.
- Judging whether a cited scope statement is *true* (right repo actually
  checked, sha actually current) — only whether one is *present*, per the
  Rationale's stated ceiling.
- Merging with or modifying `gates/absence_claims.py` — that file does not
  exist on `main`; if #358 lands first, a follow-up can compose the two,
  not this proposal.

## How you'll know it worked

- `pytest test_repo_scope_gate.py` passes, including the three fixtures in
  `## What will be done` item 2 — each fails independently if the checker
  regresses (stops flagging the unscoped case, starts over-flagging the
  scoped or file-anchored cases).
- `docs/specs/survey-conventions.md` contains the phrase "repo-scoped" and
  the issue's own defensible-vs-not example sentence, checkable by
  grepping the file.
- `docs/issue-415/reports/implementation.md` states plainly, in its own
  prose, that the shipped mechanism only flags missing repo-scope on a
  claim and does not verify cross-repo truth — checkable by reading the
  record for that sentence, not inferring it from the code.
