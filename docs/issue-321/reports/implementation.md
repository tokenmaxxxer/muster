---
code_under_review:
  - docs/specs/requirements.md
  - gates/gates.py
  - gates/ci.py
  - test_gates.py
  - docs/issue-321/decisions/2026-08-07-registry-placement.md
loop_state: landed
open_findings: none
---

Subject: issue-321

## Summary

Built the requirements registry approved in
`docs/issue-321/proposals/2026-08-07-requirements-registry.md`: an
append-only registry file plus a mechanical gate that fails when a
registered requirement's `check` artifact stops existing at HEAD.

## What was done

- `docs/specs/requirements.md`: new append-only registry, format documented
  inline (fields: `quote`, `source_issue`, `check`, `status`). Seeded with
  `R001` for this issue's own requirement, `check` pointing at the gate
  function itself, per #310's "no exemption for the rule that creates the
  rule."
- `gates/gates.py`: added `_parse_requirements()` and
  `gates.requirement_registry(d, cfg)`. Parses the registry, and for every
  entry whose `check` is not the `UNVERIFIABLE:` literal, verifies the
  path portion (before `::`) exists in the repo at HEAD. Missing registry
  file passes (nothing to check yet); a parseable entry missing a required
  field is a block, not a skip (fail-closed, matching `record_enums` and
  `record_fulfils_diff`'s existing precedent). Registered in `gates.ALL`.
- `gates/ci.py`: wired `gates.requirement_registry(repo, {})` into
  `check()` right after `record_fulfils_diff`, so it runs whenever
  `gates/ci.py` runs record-layer checks (the same wiring point, same
  scope, as every other record gate — including the pre-existing
  `--closes-only` narrowing that keeps it out of the one currently-required
  CI check, flagged in the proposal's Constraints, not a regression this
  change introduces).
- `test_gates.py`: added `t_requirement_registry_no_file_passes`,
  `t_requirement_registry_live_check_passes`,
  `t_requirement_registry_stale_check_blocks`,
  `t_requirement_registry_unverifiable_passes`,
  `t_requirement_registry_missing_field_blocks`, and
  `t_ci_check_wires_requirement_registry` (the wiring-regression guard
  pattern already used for `record_fulfils_diff`).
- `docs/issue-321/decisions/2026-08-07-registry-placement.md`: recorded why
  the registry lives under `docs/specs/` rather than `docs/issue-321/`.

## Completed items (doctrine ladder)

- [x] Library/format decision -> `docs/issue-321/decisions/2026-08-07-registry-placement.md`
- [x] No new env var, dependency, or migration introduced — nothing owed to
  a component handbook.
- [x] No benchmark/investigation numbers produced — nothing owed to
  `docs/issue-321/reports/`.

## Verification actually run (per #310/#334 — no self-review, just the confirmation run)

Ran the six new test functions directly via a standalone Python
invocation (import `test_gates`, call each `t_requirement_registry_*` and
`t_ci_check_wires_requirement_registry` by name):

```
ok t_requirement_registry_no_file_passes
ok t_requirement_registry_live_check_passes
ok t_requirement_registry_stale_check_blocks
ok t_requirement_registry_unverifiable_passes
ok t_requirement_registry_missing_field_blocks
ok t_ci_check_wires_requirement_registry
```

All six passed for real — not skipped. `python3 test_gates.py` (the full
suite) was also run; it fails partway through on
`t_repo_local_claude_config_stops_the_spawn` with
`OSError: [Errno 30] Read-only file system:
/home/jwjung/.tokenmaxxxer/trusted-repo-config.json` — a sandbox
filesystem restriction on a path outside this repo's write set, unrelated
to this change. Confirmed pre-existing by `git stash`-ing this change and
re-running the full suite on the unmodified `7cccc09` tree: the identical
failure reproduces at the identical line with no code from this change
present. New tests were therefore run standalone to get a real pass/fail
signal instead of a blocked one.

`python3 gates/ci.py` end-to-end was not run (it expects a full
`work`-repo layout with `--pr`/`--issue`/`gh` access not available
headless here); the acceptance bar is discharged by the direct
`gates.requirement_registry()` calls above, which are the same function
`ci.check()` calls, plus `t_ci_check_wires_requirement_registry`, which
calls `ci.check()` itself and confirms the wiring fires.

## Per #358 — what was searched for and found absent

Searched for any existing requirements-registry-shaped mechanism before
building a new one: `grep -rn "requirement" gates/ roles/ docs/specs/`
and `find docs -iname "*requirement*"` — no prior file or gate under that
name existed on this branch's tree before this change (only this issue's
own phase-1 survey/proposal, already known). `runs/` was not consulted —
it is gitignored and absent from this clone, so it cannot evidence either
presence or absence of anything; not searched, not cited as evidence
either way.

## What did not work

None.

## Open findings

None outstanding. No blocking finding has been addressed to this record.

## Rebase onto main (2026-08-07, post-#398)

`main` moved ~141 commits ahead while this PR sat (~40 PRs landed same
day). Rebased `issue-321/implementation` onto `origin/main`
(`c71173b`, "Merge pull request #410 from
tokenmaxxxer/issue-398/implementation").

Conflicts, both mechanical additive collisions (main added
`spec_index.check` / `duplicate_test_basenames_gate`, this branch added
`requirement_registry` at the same insertion points):

- `gates/ci.py`: `check()` — kept `spec_index.check(repo)` (main) and
  `gates.requirement_registry(repo, {})` (this branch), both now called.
- `gates/gates.py`: `ALL` dict — kept `duplicate_test_basenames` (main)
  and `requirement_registry` (this branch) as separate keys.
- `test_gates.py`: auto-merged clean, no markers.

No resolution touched `docs/specs/requirements.md` or the
`_parse_requirements`/`requirement_registry` function bodies themselves —
only their registration points.

**Re-run on the rebased tree** (per #390 — a green from the old base
attests to a state that no longer exists):

- `python3 -m pytest test_gates.py -k requirement_registry -v`: all 6 of
  this change's tests pass — `t_requirement_registry_no_file_passes`,
  `t_requirement_registry_live_check_passes`,
  `t_requirement_registry_stale_check_blocks`,
  `t_requirement_registry_unverifiable_passes`,
  `t_requirement_registry_missing_field_blocks`,
  `t_ci_check_wires_requirement_registry`.
- `python3 -m pytest -q --ignore=gates`: **395 passed** (main's own
  verification note states 389 on its own tree; the +6 here are this
  change's `test_gates.py::t_requirement_registry_*` additions, which
  `--ignore=gates` does not exclude since `test_gates.py` lives at repo
  root, not under `gates/`).
- `python3 -m pytest -q gates`: ran and **58 passed** on this tree —
  contrary to the module-name-collision-blocks-collection note filed
  under #398. Not investigated further (out of this issue's scope); flagging
  the discrepancy rather than silently trusting either number.
- `python3 gates/ci.py` end-to-end: still not run, same reason as the
  original verification section (`--pr`/`--issue`/`gh` access not
  available headless here) — unchanged by the rebase.

No code changes beyond the two conflict resolutions above; no scope
widened, no adjacent issues fixed.
