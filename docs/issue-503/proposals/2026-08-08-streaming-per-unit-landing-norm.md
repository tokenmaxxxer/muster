---
status: proposed
files:
  - docs/issue-503/reports/implementation/survey.md
  - on-the-record/commands/run.md
  - gates/test_boundary.py
  - test_spawn.py
  - spawn.py
---

## Request

Issue #503: batch barriers (wait for all N fanned-out units before
processing any) serialize fan-out on the slowest unit — the #171
fleet rollout waited for all 10 per-repo workers before merging or
re-scanning any, and #501 measured that inter-session idle is
long-tail-dominated, which barriers make worse. Make per-unit streaming
completion (verify → merge → re-scan each unit as it completes) the
structural default, with a batch barrier allowed only when the plan
names a real cross-unit dependency. This must land as: (1) contract
text in run.md, (2) dispatch guidance for role sessions that fan out
their own sub-work, (3) orchestrator loop behavior that acts on
reconcile/watch events per-unit rather than batching by round.

## Constraints

- Mirror the existing #407 landing-is-per-PR precedent already in
  run.md (~line 279-289) rather than inventing a new vocabulary for the
  same idea.
- A barrier is only ever justified by a *named* cross-unit dependency
  stated in the plan — never by convenience or by "it's cleaner to wait."
- The change must be mechanically checked (per issue acceptance), not
  left as prose only: a run.md-section-presence gate, and a red-green
  fixture pair in test_spawn.py showing 3 simulated workers landing on
  their own schedule.
- No change to `spawn.py` unless the survey's fixture actually proves
  today's reconcile-loop call site batches — see Rationale.

## Rationale

**Chosen approach**: add the streaming norm as its own run.md
subsection placed next to the existing #407 per-PR-landing text and the
"병렬 스텝의 부분 반려" section (survey: these three rules are the same
family and currently scattered), add one presence-regex assertion to
`gates/test_boundary.py` modeled on the existing
`t_run_md_references_unenforced_clauses` pattern, and add a fan-out
timing fixture to test_spawn.py's existing `Reconcile`/
`RosterConcurrency` classes (which already own the roster/reconcile
test helpers this needs) rather than a new dedicated test class.

**Alternative considered and rejected — extend #407's text in place
instead of adding a new subsection**: the survey shows #407's existing
text is scoped specifically to the *merge* decision
(`BLOCKED_ON_SCOPE`-classified PRs), written for a coordinator reading
`landing_readiness.py` output. The issue's ask is broader — verify AND
merge AND re-scan, and it also has to reach role sessions that fan out
their *own* sub-work, not just the top-level coordinator. Folding the
new norm into #407's paragraph would either overload that paragraph
with a second concern or force role-session guidance to hang off a
merge-specific rule that doesn't apply to a role's own worker fan-out.
Rejected in favor of a sibling subsection that references #407 as
precedent rather than absorbing its text.

**Alternative considered and rejected — new spec-index-tracked run.md
gate module instead of extending `gates/test_boundary.py`**: the survey
found no existing "spec index" mechanism beyond
`enforcement-boundary.md` (which `test_boundary.py` already governs)
and no precedent for a standalone run.md-section-presence gate file.
Building a new gate module for one presence check is more moving parts
than the check needs; `t_run_md_references_unenforced_clauses` already
proves the regex-presence-in-run.md pattern living inside
`test_boundary.py` is an accepted, working shape. Rejected the new-module
path as unnecessary weight for what the acceptance criterion actually
asks (an assertion that a section exists).

**Alternative considered and rejected — pre-emptively editing
`spawn.py`'s `roster_reconcile`/`reconcile` now**: the survey's reading
of spawn.py:1913-1935 shows `roster_reconcile` already loops over
roster entries and acts (prints divergence + next_action) per entry in
the same iteration — it does not collect all entries' divergences
before acting. Changing code that already exhibits the target behavior,
before a fixture demonstrates an actual batching defect, would be
scope invention rather than a fix. Rejected editing `spawn.py` up
front; it stays in the write set only as a contingency the fixture
step may trigger (see What will be done).

## What will be done

1. Add a new run.md subsection ("스트리밍 랜딩이 기본이다" or
   equivalent), placed adjacent to the #407 per-PR-landing text and the
   "병렬 스텝의 부분 반려" section, stating: fan-out units are verified,
   merged, and re-scanned as each completes; a batch barrier requires a
   plan-stated named cross-unit dependency; this applies both to the
   top-level coordinator loop and to any role session that fans out its
   own sub-work (dispatch guidance). Cross-reference #171, #501, #407.
2. Add one assertion function to `gates/test_boundary.py` asserting the
   new section is present *as enforced policy*, not just as a bare
   substring anywhere in run.md — a plain `marker in run.md.read_text()`
   check (the shape `t_run_md_references_unenforced_clauses` uses) would
   also pass if the marker phrase merely appears inside a rejected-
   alternative aside or negated prose (issue-464 already hit and fixed
   this exact bare-substring/section-fallback bypass shape for a sibling
   gate — see `gates/test_boundary.py:146-151`). The new assertion must
   require the marker sentence itself to carry the streaming-is-default
   /barrier-exception disposition and must exclude matches found inside
   a "반려/rejected" subsection, mirroring issue-464's disposition-
   vocabulary fix rather than repeating the bare-substring shape.
3. Add a red-green fixture pair to `test_spawn.py` (in/near the
   `Reconcile`/`RosterConcurrency` classes) that simulates 3 roster
   entries completing at different times and asserts each is reconciled
   (action decided) at its own completion event, not held until the
   third arrives. Red state first (a naive "collect-then-act" harness
   fails it), green against `roster_reconcile`'s existing per-entry loop
   (survey found it already streams) — or, if the fixture surfaces a
   real batching point spawn.py does have, fix that call site as the
   green step and note it under `## Rationale for deviations` in the
   phase-2 record.
4. Regenerate/update whatever spec index is affected by the run.md
   section addition, if `gates/test_boundary.py` or another existing
   gate is found (at build time) to require it — per the acceptance
   criterion's "spec index regenerated" clause.

## Out of scope

- Rewriting `roster_watchdog` or the watchdog cadence (#90's territory,
  observe-only by design, unrelated lifecycle stage).
- Building a real distributed fan-out/merge system — the fixture is a
  simulation against existing roster/reconcile primitives, not a new
  execution engine.
- Retrofitting the #171 fleet rollout's actual run or any other past
  session's history.
- Any change to the freelunch directive's own worker-dispatch/hedging
  rules — this proposal's dispatch guidance is about landing order after
  workers return, not about how workers are spawned.

## How you'll know it worked

- `python3 gates/test_boundary.py` passes, including the new
  run.md-section-presence assertion.
- `python3 test_spawn.py` passes, including the new fan-out fixture; the
  fixture fails against a synthetic "collect-then-act" comparison
  harness (proving it actually tests the streaming property) and passes
  against the real reconcile path.
- run.md's new subsection is readable next to #407's text and states
  the named-cross-unit-dependency exception explicitly, not just "avoid
  barriers."
