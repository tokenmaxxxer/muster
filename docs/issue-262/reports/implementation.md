---
code_under_review:
  - gates/gates.py
  - test_gates.py
loop_state: landed
---

# Implementation record — issue #262

Phase 2, executing the approved proposal
(`docs/issue-262/proposals/2026-08-04-always-writable-proposal-glob-fix.md`,
approved via issue-level comment `APPROVE issue-262/implementation`,
single-account mode, role-handoff contract v3, PR author and approver
both jjongkwann).

## What was done

1. `gates/gates.py:472-475`, `_always_writable(role)`: changed the third
   returned entry from `f"docs/issue-*/proposals/{role}.md"` to the
   literal `"docs/issue-*/proposals/**"`, exactly as specified in the
   proposal's "What will be done" item 1. No other line in the function
   changed.
2. `test_gates.py`: added `t_role_scope_proposal_date_slug_filename_passes`
   (next to the other `role_scope` tests, before the `_fulfils_repo`
   section) — commits no file, leaves a date-slug-named file
   (`2026-08-04-always-writable-proposal-glob-fix.md`, the same name as
   this issue's own proposal file) uncommitted under
   `docs/issue-262/proposals/` on an `issue-262/implementation`-shaped
   branch, and asserts `gates.role_scope(...) == []`.

## Red-green regression proof (issue requirement 2)

Run 1 — test added, fix NOT yet applied (pre-fix `_always_writable`):

```
$ python3 -m pytest test_gates.py -q -k t_role_scope_proposal_date_slug_filename_passes
F                                                                        [100%]
=================================== FAILURES ===================================
_______________ t_role_scope_proposal_date_slug_filename_passes ________________
E   AssertionError: assert ['write_scope 이탈: docs/issue-262/proposals/2026-08-04-always-writable-proposal-glob-fix.md
    (역할 implementation, 허용: src/**, test/**, docs/issue-*/reports/implementation.md,
    docs/issue-*/reports/implementation/**, docs/issue-*/proposals/implementation.md)'] == []
1 failed, 71 deselected in 0.25s
```

Matches the issue's cited PR #257 failure shape exactly (`write_scope
이탈` on the phase-1 proposal file itself) — red confirmed.

Run 2 — one-line fix applied to `gates/gates.py`, same test:

```
$ python3 -m pytest test_gates.py -q -k t_role_scope_proposal_date_slug_filename_passes
.                                                                        [100%]
1 passed, 71 deselected in 0.15s
```

Green confirmed.

Run 3 — full suite after the fix, checking for regressions:

```
$ python3 -m pytest test_gates.py -q
71 passed, 1 failed in 7.12s
FAILED test_gates.py::t_repo_local_claude_config_stops_the_spawn - PermissionError:
  [Errno 1] Operation not permitted: '/Users/jk/.tokenmaxxxer/trusted-repo-config.json'
```

The one failure is the same pre-existing, unrelated, sandbox-filesystem-
permission failure already noted in PR #265's phase-1 test plan
(`t_repo_local_claude_config_stops_the_spawn`) — it writes outside the
repo to a fixed host path this sandbox denies; nothing about this
issue's change touches that test or its fixture. No `role_scope`,
`writeset`, or `record_*` test regressed.

Success-criterion check from the proposal ("How you'll know it
worked"): `grep -n 'proposals/{role}' gates/gates.py` returns nothing —
confirmed (exit code 1, no match).

## Requirement 3 — re-evaluating the `--closes-only` scope (issue's own ask)

**Conclusion: keep the required branch-protection check on
`gates/ci.py --closes-only`; do not widen to the full `ci.check()`
bundle yet.**

Reasons:

1. **Fixing `_always_writable()` removes only one of the two blockers.**
   The self-lock bug (every phase-1 proposal PR failing its own
   `write_scope` check) is fixed and proven above. But
   `.github/workflows/plan-aware-closes-gate.yml` checks out `ref: main`
   unconditionally (line 38), by deliberate design (its own comment,
   lines 30-35): `--closes-only` never needs the PR's file diff, only
   `gh pr view`/`gh issue view` metadata, so checking out `main` avoids
   trusting PR-supplied code. The full bundle's `role_scope`/`writeset`/
   `deps`/`record_*` checks all depend on `gates.changed_files()`, i.e.
   a real `git diff origin/main...HEAD` against the PR's actual commits
   — which requires checking out the PR's head ref, not `main`. Doing
   that reintroduces exactly the trust-boundary problem the workflow's
   own comment names: a PR could edit `gates/ci.py`/`gates/gates.py`
   itself and have the checked-out (attacker-controlled) copy of the
   script run against its own diff, neutering any check it doesn't like.
   This is a separate, structural gap this issue's write set (`gates/
   gates.py`, `test_gates.py`) cannot close — it needs its own design
   (e.g., pin the gate script from `main` while independently fetching
   the PR's diff via the GitHub API rather than a trusted local
   checkout) and is out of scope here per this proposal's Constraints
   and Out-of-scope sections.
2. **The fixed glob's trade-off is broader than "wrong role's
   `<name>.md`."** Hunt finding 2 below: `docs/issue-*/proposals/**`
   permits any filename, any extension, any nesting depth, under any
   role's own branch (including judgment roles whose declared
   `write_scope` is `[]`), and no other mechanical gate
   (`is_protected()`'s `PROTECTED_ROOT_DIRS`/`PROTECTED_DIRS`/
   `PROTECTED_GLOBS`, `gates/gates.py:25-38`) covers `docs/**` as a
   backstop. This is the same category of trade-off the proposal's
   Rationale already named and accepted (a `write_scope`-gate, not a
   role-identity gate, backstopped by human PR review, not by the
   mechanical gate) — not a reason to revert the fix — but it does mean
   the full bundle's `role_scope` check is more permissive under
   `docs/issue-*/proposals/` than its non-widened lines suggest, which
   weighs (mildly, alongside reason 1's structural blocker) toward
   proving out the checkout-trust redesign before leaning on the full
   bundle as a required, non-bypassable gate.

Actually flipping `.github/workflows/plan-aware-closes-gate.yml`'s
invocation away from `--closes-only` is unchanged — out of scope here,
same as the proposal stated.

## What did not work

None. The one-line fix and the new test matched the approved proposal's
"What will be done" on the first attempt; no false starts.

## Open findings

Two items are real but outside this issue's frozen write set (`gates/
gates.py`'s `_always_writable()` line and `test_gates.py` only — not
`gates/ci.py`, not `.github/workflows/`, per this proposal's
Constraints):

1. **The widened glob's accepted trade-off is broader than "wrong
   role's `<name>.md`."** Hunt finding 2, below: `docs/issue-*/
   proposals/**` drops per-role attribution, extension, and
   nesting-depth constraints simultaneously, and no other mechanical
   gate backstops `docs/**`. This was already the proposal's approved,
   frozen fix (not a bug to correct here), but it is more permissive
   than the proposal's Rationale framing suggested — folded into
   "Requirement 3" above as an argument for not yet widening the
   required CI check onto the full bundle. Resolution path, if ever
   pursued: a follow-up issue narrowing `_always_writable()`'s
   proposals-entry further (e.g. requiring a `.md` extension, or a
   single path segment) only if a concrete abuse case is found — not
   speculative hardening against this survey/hunt alone.
2. **`gates/ci.py`'s `check()` docstring is now stale.** It still cites
   the just-fixed `<role>.md` proposal-filename mismatch as live
   rationale for keeping the required check on `--closes-only`.
   `gates/ci.py` is outside this proposal's write set (issue #245's
   owned surface). Resolution path: update the docstring alongside
   whatever follow-up issue acts on this record's "Requirement 3"
   conclusion.

## Doc-placement ladder

- No new env var / dependency / migration -> N/A.
- No changed public signature or wire format -> N/A (`_always_writable`
  keeps its `(role) -> list[str]` signature; only a literal glob string
  changed).
- No new library-or-format choice over a named alternative requiring a
  `docs/issue-262/decisions/` entry -> per this proposal's own
  Constraints: "this is a one-line glob-literal fix on an existing,
  already-documented function... the reasoning... is carried in this
  proposal's Rationale and, at execution time, in the implementation
  record instead" (this record's "Requirement 3" section above).
- No benchmark/investigation numbers beyond the red/green proof above,
  which lives in this same record.

## Hunt

Stance: **adversarial-self** (rotated — issue-245's record states the
recency order at that point, after its own use of
assume-incomplete-coverage, became: assume-incomplete-coverage (245,
most recent) > assume-broken (236) > composition-regression (227) >
adversarial-self (229/223, LRU) — adversarial-self is next in rotation).
No registered `warrant-hunter` subagent type is available in this
harness (same gap prior records note) — `general-purpose` dispatched in
its place, foreground/synchronous, with an explicit adversarial-self
brief (assume the just-made fix is broken, try to break it) before this
record's commit.

Findings:

1. **CHECKED-NO-BUG.** `fnmatch` boundary probe: a sibling directory
   merely starting with `proposals` (e.g. `proposalsx/`) does not match
   `docs/issue-*/proposals/**` — the literal `/` immediately after
   `proposals` in the pattern blocks it. Empirically confirmed with
   `fnmatch.fnmatch()` snippets against equivalent placeholder strings.
2. **CONFIRMED, accepted (not fixed — matches approved scope).** The
   widened glob drops per-role attribution, extension, and nesting-depth
   constraints simultaneously (the old pattern only ever matched exactly
   one `<role>.md` file per role), and `is_protected()` does not cover
   `docs/**` as an independent backstop — so any role's branch,
   including a judgment role with an empty declared `write_scope`, can
   now commit an arbitrarily-nested, arbitrarily-typed file under any
   issue's `proposals/` tree without a `role_scope` violation. This is
   the same trade-off category the proposal's Rationale already named
   and accepted (a `write_scope` gate, not a role-identity gate; the PR
   diff stays visible to human review regardless) — the proposal's own
   literal fix (`docs/issue-*/proposals/**`) was frozen and approved, so
   this is not treated as an implementation bug to fix here, but it is
   folded into "Requirement 3" above as an argument for not yet widening
   the required CI check to rely on this line unattended.
3. **CHECKED-NO-BUG.** `test_gates.py`'s new test leaves its file
   uncommitted, matching every other `_scope_repo`-based `role_scope`
   test's existing convention (none of them commit; all rely on
   `_worktree_changes`). Full suite re-run (71 passed, 1 pre-existing
   unrelated failure) confirms no interaction with any other test.
4. **CHECKED-NO-BUG.** No other `test_gates.py` test references
   `docs/issue-*/proposals/`; `record_enums`/`record_wellformed`/
   `record_no_tool_residue` key off the `reports/` record path only,
   never `proposals/` — no cross-check interaction from this change.
5. **Noted, out of scope, not fixed here.** `gates/ci.py`'s `check()`
   docstring (around line 141-148) still cites the now-fixed
   `<role>.md` proposal-filename mismatch as live rationale for
   `--closes-only`. `gates/ci.py` is outside this proposal's write set
   (issue #245's owned surface per Constraints) — left for a future
   change alongside any decision to act on "Requirement 3" above (see
   "Open findings" item 2).
