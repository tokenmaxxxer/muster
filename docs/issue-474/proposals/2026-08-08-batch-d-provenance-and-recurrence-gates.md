---
status: proposed
files:
  - gates/repo_scope.py
  - gates/test_repo_scope_gate.py
  - docs/specs/survey-conventions.md
  - gates/acceptance_gate.py
  - gates/test_acceptance_gate.py
  - gates/test_setup_failure_propagates.py
  - docs/issue-416/decisions/provenance-and-empty-state.md
  - gates/gates.py
  - gates/ci.py
  - gates/test_gates.py
  - spawn.py
  - gates/accumulation.py
  - gates/test_accumulation.py
  - on-the-record/commands/run.md
  - docs/issue-474/reports/implementation.md
---

## Request

Batch D of the #467 ADR: deliver deployed-surface enforcement + a named,
red-green check for four class-B disposition rows — #415 (a role session
must not conclude a feature is absent from reading only its own repo),
#416 (a behavioral claim must carry provenance, not be discharged by
reading code alone), #419 (structurally identical code that is not
textually identical is still a recurrence), #424 (a proposal must state
what the codebase becomes after N more changes of the same shape). The
shared `gates/test_boundary.py` disposition table already landed in
Batch A (#471); this batch adds only its own four rows' checks, per the
issue's own scope line.

## Constraints

- Per #310: acceptance is an executable artifact that fails on
  regression, not a doc sentence.
- `gates/gates.py` and `gates/ci.py` are under `PROTECTED_ROOT_DIRS`
  (`gates.py:36`) — this batch's diff to those files routes to mandatory
  human review regardless of this proposal's own content. Expected, not
  worked around.
- #415, #416, #419 already have approved, merged designs on `main`
  (`docs/issue-415/proposals/implementation.md`,
  `docs/issue-416/proposals/2026-08-07-provenance-and-empty-state-gates.md`,
  `docs/issue-419/proposals/2026-08-07-pattern-recurrence-checks.md`) —
  this proposal does not redesign them; it adopts each design verbatim as
  Batch D's `## What will be done` for that row, per the ADR's hand-off
  instruction (`docs/issue-467/reports/architecture.md:109-113`: "build
  each batch's ... named check(s) ... per the ADR").
- #424 has no concrete module named by its own proposal (least-specified
  row per the ADR, `docs/issue-467/decisions/2026-08-08-...md:39`) — this
  proposal designs it fresh, scoped to the two survey-named instances that
  actually have repetition to fixture against (instance 1: 6 inline `gh`
  call sites; instance 5: 43 identical `roles/*.json` edits), not a
  general accumulation detector.
- Must not modify `gates/test_boundary.py`'s `ISSUE_467_DISPOSITION_ROWS`
  table — already landed by Batch A; re-touching it here would violate
  the issue's own "add only this batch's rows' checks" line.

## Rationale

**For #415/#416/#419: adopt the already-merged per-row proposal verbatim
vs. redesigning from the issue text directly — adopt verbatim, chosen.**
Redesigning would ignore three proposals that already went through their
own phase-1 approval, each with a stated, narrow ceiling and (for #415
and #419) a warrant-hunt finding folded into the design. Rebuilding from
scratch risks silently dropping those ceilings/findings and duplicates
work contract v3 s19 already paid for. The ADR itself frames Batch D as
"build ... per the ADR," and the ADR's own per-row table cites each row's
PR (#418, #417, #423) as "already-merged design" — adoption is the
literal instruction, not a default.

**For #424: a general "accumulation cost" detector (flag any list/loop
that grows across commits) vs. two named, evidence-backed instances —
named instances, chosen.** #419's own proposal (Rationale, "considered a
single structural-similarity detector — rejected") already established
why a generic recurrence/accumulation detector over this repo produces
false-positive floods that train reviewers to ignore the check; the same
argument applies to accumulation. The survey
(`docs/issue-424/reports/architecture/survey.md`) names 5 instances but
only two (1 and 5) show actual N>1 repetition in this repo's own history
to build a red-green fixture from — instances 2-4 are single occurrences,
so a check "against" them would have no failing-then-passing case to
demonstrate, which is exactly the un-testable-claim shape #416 exists to
refuse. Scoping to instances 1 and 5 keeps the check's claim inside what
it can actually prove.

**For #424: extending `duplicate_test_basenames`'s existing dedup gate
in place vs. a new standalone module — new module (`gates/accumulation.py`),
chosen.** `duplicate_test_basenames` checks name-collision, a single
mechanical predicate; the accumulation question ("does a proposal say
what happens after N more of these") is a text-presence check over
`## Accumulation` proposal content, a different input and different
predicate family. Folding it into the existing function would repeat
#419's own rejected pattern (bundling two unrelated requirements under
one heading/function) for the second time in this batch — rejected for
the same stated reason.

## What will be done

1. **#415** — `gates/repo_scope.py::check_repo_scope(text: str) -> list[Violation]`
   per `docs/issue-415/proposals/implementation.md` item 1; `gates/test_repo_scope_gate.py`
   with the three fixtures from that proposal's item 2 (unscoped absence
   claim flags; scoped claim does not; file-anchored claim does not);
   `docs/specs/survey-conventions.md` gets the "Capability and contract
   claims are repo-scoped" section (create if absent). Record must restate
   both stated ceilings: no cross-repo truth verification, and the
   fixed-phrase-list gap the warrant hunt found.
2. **#416** — extend `gates/acceptance_gate.py::check_issue_body` with the
   `empty state:` and `provenance:` checks per
   `docs/issue-416/proposals/2026-08-07-provenance-and-empty-state-gates.md`
   item 1; `gates/test_acceptance_gate.py` cases per item 2;
   `gates/test_setup_failure_propagates.py` per item 3 (synthetic setup-
   step-failure harness); `docs/issue-416/decisions/provenance-and-empty-state.md`
   per item 4, stating the presence-not-truth ceiling.
3. **#419** — `gates/gates.py`: add `subprocess_call_shape_divergence`
   and `sibling_mention_check` to `ALL`, whole-tree grouped (not per-file
   or diff-only, per the proposal's warrant-hunt-driven correction);
   `gates/ci.py`: wire both into the existing non-`--closes-only` chain;
   `gates/test_gates.py`: fixtures per the proposal's item 4 (the #388
   shape flags, identical-flag-set pair does not; marked-and-mentioned
   sibling pair passes, marked-and-unmentioned fails, unmarked returns
   `[]`); apply `# sibling: core_version` / `# sibling: core_root` to the
   real pair in `spawn.py`.
4. **#424** — new `gates/accumulation.py::check_accumulation_claim(body: str) -> list[str]`:
   requires an `## Accumulation` line in a proposal whose write set
   touches either of two named recurrence-prone shapes — an inline
   `subprocess`/`gh` call site added to a file already having 2+ such
   sites with no shared helper (instance 1's shape), or a single-line
   addition to a list/constant that has grown across 3+ prior commits in
   `git log -p` for that symbol (instance 5's shape) — stating, in the
   proposal's own words, what the file/list looks like after N more
   deliveries of the same shape (N left to the author, presence-checked
   only, same ceiling style as #416's `provenance:`). `gates/test_accumulation.py`:
   fixture reproducing instance 1 (a 7th inline `gh` call added to
   `gates/ci.py`'s shape with no `## Accumulation` line) must flag; the
   same fixture with an `## Accumulation` line present must not; a change
   touching neither named shape returns `[]` regardless of proposal text.
5. **`on-the-record/commands/run.md`** — four new subsections before
   "## 하지 않는 것" (line 396), one per row, following Batch A's
   established placement (`git show 9554c53`): #415's repo-scope
   convention, #416's provenance/empty-state fields, #419's recurrence-
   check conventions (`# sibling:` marker syntax), #424's `## Accumulation`
   line convention.
6. `docs/issue-474/reports/implementation.md` — phase-2 record, restating
   each row's own ceiling in its own text (not merely implied), per #416's
   own precedent that a behavioral/coverage claim must be stated, not
   assumed from what shipped.

## Out of scope

- Re-deriving or altering #415/#416/#419's own already-approved designs —
  adopted verbatim per the Rationale above; any disagreement with those
  designs is a new proposal against their own issues, not this batch.
- A general accumulation/duplication detector covering #424's survey
  instances 2, 3, or 4 (signature drift, growing named constant beyond
  the two chosen shapes, parallel "delivered" definitions) — no
  repeated-N-times evidence exists for those in this repo's history to
  build a red-green fixture from; named here per the issue's own honesty
  requirement rather than silently unaddressed.
- Re-touching `gates/test_boundary.py`'s `ISSUE_467_DISPOSITION_ROWS`
  table or its `t_class_b_disposition_rows_cited` check — already landed
  by Batch A (#471); this batch's rows are already listed there.
- Any change to `spawn.py`'s clone/isolation model or cross-repo read
  access (#415's own out-of-scope, reused) beyond the two `# sibling:`
  marker comments (#419's own out-of-scope, reused for the same pair).
- Wiring `gates/repo_scope.py` into any commit-time `PreToolUse` hook —
  ships as a script/pytest module per #415's own design, not a blocking
  hook.

## How you'll know it worked

- `python3 gates/test_repo_scope_gate.py`, `python3 gates/test_acceptance_gate.py`,
  `python3 gates/test_setup_failure_propagates.py`, and
  `python3 gates/test_accumulation.py` each pass standalone (no `gh`
  calls, network-free, matching every existing gate test's convention).
- `python3 -m pytest gates/test_gates.py -k "subprocess_call_shape_divergence or sibling_mention" -v`
  passes.
- `python3 -m pytest -q --ignore=gates` from repo root, and separately
  `python3 -m pytest gates/test_*.py -q` run from inside `gates/` (per
  #398's module-collision constraint) — both outputs recorded in the
  phase-2 record, not only the one that happens to pass.
- Each of the four new/extended test files demonstrates red-then-green
  against the shape it targets (e.g. `gates/test_accumulation.py`'s
  fixture fails against a 7th unguarded `gh` call site before the check
  exists conceptually, and the checker flags it once implemented) — per
  #416's own acceptance requirement that a corpus exercise the broken
  state, not only the fixed end-state.
- `gates/test_boundary.py::t_class_b_disposition_rows_cited` stays green
  unmodified (Batch D adds no table changes).
