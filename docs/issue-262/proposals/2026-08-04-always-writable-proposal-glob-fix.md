---
role: implementation
subject: issue-262
loop_state: scope-proposed
---

files: `gates/gates.py`, `test_gates.py`

Survey: [[survey.md]](../reports/implementation/survey.md).

## Request

`gates/gates.py`'s `_always_writable(role)` hardcodes the phase-1
proposal-file pattern it always permits as `docs/issue-*/proposals/<role>.md`
(`gates/gates.py:472-475`). This repo's actual proposal files never
reliably follow that shape — many are dated-slug names
(`docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`)
or free-form slugs with no role token at all
(`docs/issue-160/proposals/role-taxonomy.md`). Issue #245's own delivery
PR (#257) hit this directly in a dry-run: running the full
`gates/ci.py --pr 257 --issue 245 --phase phase1` bundle blocked on its
*own* phase-1 proposal file as a `write_scope` violation. Wiring the full
`ci.check()` bundle as a required, non-bypassable branch-protection check
while this defect stands would self-lock the repo — every historical and
future phase-1 proposal PR, including phase-2 delivery PRs on those same
branches, would fail this one check. Issue #245 sidestepped it by scoping
its required check to `gates/ci.py --closes-only`, which skips
`role_scope()` (and thus `_always_writable()`) entirely
(`docs/issue-245/reports/implementation.md`, "Rationale for deviations"
item 1 / "Open findings" item 1). Fix the pattern itself, prove the fix
with a regression test that is red before and green after, and record a
fresh conclusion on whether the required check can now safely widen
beyond `--closes-only`.

## Constraints

- `gates/ci.py`'s `--closes-only` code path and `.github/workflows/` stay
  untouched — issue #245's owned surface. This proposal's write set is
  `gates/gates.py` and `test_gates.py` only; it does not flip which mode
  the required branch-protection check runs.
- `gates/pr_reference.py`'s judgment logic stays untouched — issue #228's
  owned surface.
- No new `docs/issue-*/decisions/` file: this is a one-line glob-literal
  fix on an existing, already-documented function, not a new
  library/format/signature choice — the reasoning that would otherwise go
  in a decision doc is carried in this proposal's Rationale and, at
  execution time, in the implementation record instead.

## Rationale

**Chosen: widen `_always_writable()`'s proposal-file entry from
`docs/issue-*/proposals/{role}.md` to `docs/issue-*/proposals/**`,
keeping every other line (reports entries, the issue segment) unchanged.**
This is the minimal edit that makes the reported case pass: it drops
exactly the constraint the survey found to be false (that a proposal
filename encodes the role name) and nothing else. `fnmatch` (the only
matcher this codebase uses for glob checks — `gates/gates.py:67,190,524`)
treats `*` and `**` identically, matching across `/` with no path-aware
distinction (confirmed directly in the survey); `**` is used here purely
to match the sibling reports-glob's existing style
(`f"docs/issue-*/reports/{role}/**"`, `gates/gates.py:474`), not because
it is functionally required.

- **Rejected alternative — bind the glob to the specific issue number
  parsed from the branch, not just `docs/issue-*`.** `_always_writable`
  would need a new `issue` parameter, `BRANCH_ROLE`
  (`gates/gates.py:465`) would need to capture and pass the issue segment
  it currently discards, and `role_scope()`'s one call site would need
  updating to match. Rejected for two reasons: first, it is a materially
  bigger diff than the reported bug needs — the issue segment was already
  `docs/issue-*` (unbound to any specific issue) in the *pre-existing,
  unpatched* code, so this widening does not newly expose other issue
  trees (survey finding, confirmed by reading `BRANCH_ROLE`'s discarded
  capture group). Second, it would not even close the one side effect the
  survey found to be real — same-issue-tree, cross-role proposal-file
  writes (an `implementation` branch touching `docs/issue-31/proposals/qa.md`)
  — because `docs/issue-31/proposals/` already legitimately holds
  multiple roles' own proposal files side by side
  (`coding.md`/`qa.md`/`verify.md`); binding by issue number does nothing
  to separate roles sharing one issue tree. It would add complexity
  without actually buying the isolation it might appear to promise.
- **Rejected alternative — require the role name to appear somewhere in
  the filename** (e.g. `docs/issue-*/proposals/*{role}*`), preserving
  *some* role-scoping while still allowing free-form names. Rejected
  because the survey's own naming-practice data contradicts it: the
  issue's own trigger file
  (`docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`,
  role `coding`) and multiple other real proposals
  (`docs/issue-132/proposals/session-end-trichotomy.md`,
  `docs/issue-160/proposals/role-taxonomy.md`,
  `docs/issue-172/proposals/flows-json.md`) carry no role token at all —
  this pattern would still block the exact class of file the issue
  reports as broken, failing requirement 1's own "임의 파일명" (arbitrary
  filename) ask.
- **Rejected alternative — leave `_always_writable()` unfixed and keep
  the required CI check permanently on `--closes-only`.** This is exactly
  issue #245's current landed state. Rejected because issue #262
  requirement 3 explicitly asks for a fresh, recorded conclusion on
  whether the check can now widen — permanently avoiding the fix would
  foreclose that question rather than answer it, and would leave
  `role_scope`/`deps`/`record_*` un-required indefinitely for a reason
  (a known, named, fixable defect) rather than a considered trade-off.

The newly-accepted trade-off (same-issue-tree cross-role proposal-file
writes go unflagged by `role_scope`) is not engineered around here: it
is a real but narrow widening — `role_scope` is a `write_scope` gate, not
a role-identity gate, and it already permits cross-role writes to the
*reports* record path once landed content exists there in other checks
(`record_enums`/`record_wellformed`); a stray proposal-file write by the
wrong role in the wrong issue tree is still visible in the PR diff for
human review, matching the existing division of labor between the
mechanical gate (catches protected-path and gross out-of-scope writes)
and the human PR review (catches everything else).

## What will be done

1. In `gates/gates.py`, change `_always_writable()`'s third returned
   entry from `f"docs/issue-*/proposals/{role}.md"` to
   `"docs/issue-*/proposals/**"` (a literal, no longer role-interpolated,
   matching the survey's confirmed `fnmatch` semantics).
2. In `test_gates.py`, add a `role_scope` regression test that commits a
   dated-slug file under `docs/issue-<n>/proposals/` (not `<role>.md`) on
   a role-shaped branch and asserts `gates.role_scope(...) == []` — this
   test must be run against the pre-fix code first to confirm it fails
   red (issue requirement 2), then again after the one-line fix to
   confirm green, with both results captured in the phase-2
   implementation record.
3. Re-run the full `test_gates.py` suite after the fix to confirm no
   existing `role_scope` test (`test_gates.py:824-919`) regresses —
   none of those tests touch `docs/issue-*/proposals/`, so none should be
   affected by narrowing what the change actually touches.
4. Re-evaluate, and record a conclusion for, issue requirement 3: whether
   `.github/`'s required check can now safely widen from
   `gates/ci.py --closes-only` to the full `ci.check()` bundle now that
   the `_always_writable()` defect is fixed. This conclusion (widen or
   keep, with reasons) is written into
   `docs/issue-262/reports/implementation.md` during phase 2 execution —
   actually flipping `.github/workflows/`'s required-check invocation is
   explicitly a separate decision/PR, not part of this write set (issue
   #262's own "실제 확장은 별도 결정" instruction, and this proposal's own
   Constraints).

## Out of scope

- Any change to `gates/ci.py`'s `--closes-only`/`--autodetect` code paths
  or `.github/workflows/*.yml` (issue #245's owned surface; this
  proposal's Constraints).
- Any change to `pr_reference.py`'s phase1/phase2 judgment logic (issue
  #228's owned surface; this proposal's Constraints).
- Actually widening the required branch-protection check to the full
  `ci.check()` bundle — this proposal only produces the recorded
  conclusion (requirement 3); executing a widening is a separate future
  change.
- Binding `_always_writable()`'s glob to a specific issue number, or any
  other narrowing of the proposals-path match beyond dropping the
  `{role}.md` filename constraint (both considered and rejected above).
- Any change to `roles/*.json` `write_scope` declarations — none of them
  declare a `docs/issue-*/proposals/` entry themselves; this pattern
  lives solely inside `_always_writable()`.

## How you'll know it worked

- The new `test_gates.py` regression test (dated-slug proposal file,
  role-shaped branch) fails against the pre-fix `_always_writable()` and
  passes against the post-fix version — both runs' output captured in
  the phase-2 implementation record, per issue requirement 2.
- `python3 -m pytest test_gates.py -q` is fully green after the fix (no
  regression in any existing `role_scope`/`writeset`/`record_*` test).
- `gates/gates.py`'s `_always_writable()` no longer contains the string
  `{role}.md` in its proposals entry — `grep -n 'proposals/{role}' gates/gates.py`
  returns nothing.
- The phase-2 implementation record states an explicit conclusion
  (widen the required check to the full bundle, or keep
  `--closes-only`) with reasons, for issue requirement 3 — without
  itself changing `.github/workflows/`.
