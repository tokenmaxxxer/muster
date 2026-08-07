---
code_under_review: gates/landing_readiness.py, gates/test_landing_readiness.py, on-the-record/commands/run.md
loop_state: phase-2-complete
---

# Implementation record — issue #407

Phase-2 delivery per the approved proposal at
`docs/issue-407/proposals/2026-08-07-per-item-landing-readiness.md`
(approval: exact-match `APPROVE issue-407/implementation` issue comment,
2026-08-07T09:11:10Z).

## What was done

1. `gates/landing_readiness.py`: added a `classify(pr_state, checks,
   has_record, has_approval, pr_files, blocking_causes)` pure function
   returning `(READY | BLOCKED_ON_PR | BLOCKED_ON_SCOPE, reason)`, modeled
   on `closure_sweep.py:classify`. `blocking_causes` entries carry a
   `scope` (a set of path prefixes, or `None` for a board-wide cause) and
   only cover a PR when its changed files intersect that scope — this is
   the mechanism that stops a `gates/`-only cause from blocking a PR that
   never touched `gates/`. `main()` wraps it with real `gh` calls
   (`gh pr list`, `gh pr checks`, `gh pr diff --name-only`) and, for
   `has_record`/`has_approval`, reuses existing helpers
   (`ci._phase2_record_evidence`, `ci._approved_roles_on_issue`,
   `ci._issue_and_role_from_branch`) instead of stubbing them — a PR with
   no phase-2 record or no recorded approval genuinely comes back
   `BLOCKED_ON_PR`, not a hardcoded pass-through. Runnable standalone:
   `python3 gates/landing_readiness.py`.
2. `gates/test_landing_readiness.py`: 10 unit tests against `classify()`
   directly, no network — own-PR gates (checks/record/approval), a
   board-wide cause, a scoped cause that does and does not cover a given
   PR, and a reconstructed #398-shape scenario (mixed-scope PR set,
   asserting only the `gates/`-touching PRs come back `BLOCKED_ON_SCOPE`).
3. `on-the-record/commands/run.md`, step 6: added a bullet requiring that
   any stop not scoped to one PR's own checks run/cite
   `gates/landing_readiness.py` and name only the PRs it actually returns
   `BLOCKED_ON_SCOPE` for; the rest continue through the existing
   per-item accept/merge path (unchanged). Regenerated
   `docs/specs/reconciled-index.md` via `gates/spec_index.py --update`
   so the hash-consistency gate (`test_spec_index.py`) reflects the edit.

## Why

Issue #407: the orchestrator's only per-item signal was whatever it
happened to re-derive from `gh` state at the top of a turn, so a real but
narrow cause (a `gates/`-scoped collection break, #398) got applied to
every open PR — nineteen halted merges when the actual scope was
`gates/`-touching PRs only. `classify()` makes "is this PR ready" and "does
this cause actually cover this PR" both computable per item instead of
inferred from the orchestrator's rhythm. Per #363: the generator was the
absence of any per-PR readiness check, not the #398 symptom itself (a
rename there would not have stopped the next partial failure from being
over-generalized the same way) — this change removes that generator by
giving the orchestrator a mechanical per-PR classification to consult
instead of a blanket stop.

## Open findings

None — the after-proposal warrant hunt (dispatched under the phase-1
proposal turn) and the pre-landing hunt below returned no blocking
findings against this write set.

## What did not work

None.

## Closed checks (hunt input)

- `python3 -m pytest -q gates/test_landing_readiness.py` → 10 passed.
- `python3 gates/landing_readiness.py` (honest-claims confirmation run,
  network) → ran against this repo's real open PR set (#436, #434, #421,
  #343, #305, #295), printed one classification line per PR, no crash.
- `python3 -m pytest -q` (full suite, no `--ignore`) → 13 failed,
  491 passed. All 13 failures are in `gates/test_closes_gate_ci.py`
  (`ValueError: not enough values to unpack` from
  `spawn._issue_comments`), pre-existing on `main` from #435 (in flight,
  not this branch's write set) — none touch `gates/landing_readiness.py`
  or `gates/test_landing_readiness.py`. No new failures introduced.
- `python3 gates/spec_index.py --update` → resolved the
  `on-the-record/commands/run.md` hash drift the step-6 edit caused;
  re-ran the full suite after to confirm the count above.

## Rationale for deviations

None — no divergence from the approved proposal's `## What will be
done`. Record/approval evidence in `main()` reuses existing `ci.py`
helpers rather than being left unspecified; the proposal did not name the
exact fields but did require `main()` to be a real `gh`-backed wrapper,
and stubbing `has_record`/`has_approval` to `True` would have violated
the no-mock direction (a placeholder disabling two of three gate
conditions in real use) without being a scope change — no new files
outside the frozen write set were touched to do this.
