---
status: proposed
files:
  - gates/landing_readiness.py
  - gates/test_landing_readiness.py
  - on-the-record/commands/run.md
---

## Request

The orchestrator lands finished work in batches instead of per item: a
delivery that is complete and green sits until the orchestrator's next
turn happens to notice it. On 2026-08-07, thirty PRs were open, most
landable; when the merged tree broke on a `gates/`-only collection defect
(#398), all nineteen remaining merges were halted on a reasoning that
generalized a `gates/`-scoped cause to every pending PR. Fix the mechanism
so readiness is computed per PR, and a stop must name what it blocks and
which PRs it actually covers.

## Constraints

- Per #310: no prose-only fix. The deliverable is an executable artifact
  that fails when this regresses.
- Per #363: state what generated the defect and whether the fix removes
  the generator. The generator is the absence of any per-PR readiness
  check — the orchestrator's only signal today is whatever it happens to
  re-derive from `gh` state at the top of a turn, so a real cause (a
  `gates/`-scoped collection break) gets applied to every PR because
  nothing computes a narrower scope. Renaming `gates/test_gates.py` (the
  #398 symptom itself) does not remove this generator — a different
  partial failure next time would trigger the same over-generalization.
- Boundary: do not touch #398's own fix (module-collision rename/packaging
  is #398's write set), do not touch spawn-time serialization (#324), do
  not touch human-decision-pending display (#374), do not re-litigate
  #341 itself (only apply its "name your enforcer/scope" principle here).
- No Stop hook exists in this repo yet (checked `on-the-record/hooks/
  hooks.json`); building one is out of scope for this proposal — see Out
  of scope.

## Rationale

Two designs were considered.

**Chosen: a pure per-PR readiness classifier (`gates/landing_readiness.py`)
modeled on `gates/closure_sweep.py:classify`.** Given already-fetched `gh`
state for a PR (checks status, whether its `docs/issue-<n>/reports/
<role>.md` record exists, whether approval was recorded) it returns READY
or BLOCKED(reason, scope). A thin `main()` wraps it with the actual `gh`
calls, same shape as `closure_sweep.py`. This is unit-testable without
network access, and it gives the orchestrator (and any future hook) a
single call that answers "is *this* PR ready" without waiting for a
full-board re-scan — and, symmetrically, a call that can express "the
failure I just hit covers exactly these PRs, not all of them."

**Rejected: a Stop hook that inspects the orchestrator's own reply text
for batching language.** This is the mechanism #298's 2026-08-07 comment
describes as available, and it would give #407 direct behavioral
enforcement (block a reply that says "halting all merges" without a
per-PR scope). It was rejected for *this* proposal because it requires
designing what counts as an acceptable vs. unacceptable stop statement in
free-form prose — a heuristic classifier prone to false blocks on
legitimately-scoped stops — and this repo has zero existing Stop hooks to
extend or pattern-match against (confirmed empty in the survey). Building
one well is a separate, larger unit of work than the readiness classifier,
and the classifier is a prerequisite for it anyway (the hook would need
something to compare the reply's claimed scope against). It is named here
as the natural next proposal, not folded in.

## What will be done

1. `gates/landing_readiness.py`: a `classify(pr_state, checks, has_record,
   has_approval, blocking_causes=())` function returning one of
   `READY`, `BLOCKED_ON_PR` (this PR's own checks/record/approval), or
   `BLOCKED_ON_SCOPE` (an external cause, carrying which PRs it actually
   covers — computed by intersecting each cause's declared file-scope
   against each PR's changed files, so a `gates/`-only cause never covers
   a PR that touched no path under `gates/`). A `main()` wrapping it with
   `gh pr list`/`gh pr checks`/`gh pr diff --name-only` calls, invocable
   standalone (`python3 gates/landing_readiness.py`) to print each open
   PR's classification — this is the executable artifact #310 requires:
   running it against the current open-PR set is itself the check that
   fails (non-empty spurious-BLOCKED list) if per-item scoping regresses.
2. `gates/test_landing_readiness.py`: unit tests against `classify()`
   directly (no network), including a case reconstructing the measured
   #398 shape — a `gates/`-scoped `blocking_causes` entry, a set of PRs
   where only some touch `gates/` — asserting only the `gates/`-touching
   PRs come back `BLOCKED_ON_SCOPE` and the rest come back `READY`. The
   exact historical 30-PR list is not recoverable (checked: `gh pr list
   --state merged --search 398` against the board repo returns nothing,
   and #398 is still open with no linked PR list) — the test uses a
   reconstructed scenario sized off the measured facts (30 open, 19
   halted) stated as reconstructed, not claimed as the literal historical
   data.
3. `on-the-record/commands/run.md`, step 6: add a sentence requiring that
   any stop not scoped to one PR's own checks must run
   `gates/landing_readiness.py` (or cite its output) and report only the
   PRs it actually returns `BLOCKED_ON_SCOPE` for — the rest proceed
   through the existing per-item accept/merge path (line 229 today,
   unchanged). This is a direction change to the orchestrator prompt, not
   the enforcement itself — enforcement is the script in (1), which is
   what a future Stop hook (see Out of scope) would call to check the
   orchestrator's claim mechanically.

## Out of scope

- A Stop hook that mechanically inspects the orchestrator's reply text
  against `landing_readiness.py`'s output (rejected alternative above) —
  next proposal, once this classifier exists to check against.
- Fixing #398's module-name collision itself.
- Decoupling reporting from landing (#407 point 3) and distinguishing
  rhythm-wait from human-decision-wait in the board display (#407 point
  4, boundary with #374) — both are board/display concerns
  (`on-the-record/commands/run.md`'s board section, not step 6) and need
  their own scoping; folding them in here would widen the write set
  beyond what the survey covers.

## How you'll know it worked

- `python3 -m pytest -q gates/test_landing_readiness.py` passes, including
  the reconstructed-#398-shape case (mixed scope → only `gates/`-touching
  PRs BLOCKED_ON_SCOPE).
- `python3 gates/landing_readiness.py` runs against this repo's real open
  PRs (network-dependent, run once as the honest-claims confirmation) and
  prints a classification per PR without crashing.
- `python3 -m pytest -q --ignore=gates` still passes at the same baseline
  (385 passed, 1 pre-existing unrelated failure) — no regression from this
  change.
