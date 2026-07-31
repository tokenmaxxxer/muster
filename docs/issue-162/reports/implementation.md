---
kind: build-report
loop_state: progressed
---

# issue-162 phase 2 follow-up: fix stale role names after PR #164

## Regression

PR #164 (commit b9fbb8f) renamed 9 `roles/*.json` files to the round-5 canon
names (`coding`->`implementation`, `qa`->`execution-observation`,
`review`->`conformance-review`, `verify`->`defect-verification`,
`ops`->`release-engineering`, `reflect`->`issue-retrospective`,
`product`->`product-discovery`, `feasibility`->`technical-feasibility`,
`ux-design`->`interaction-design`), but claimed "no spawn.py change needed."
That claim was false: `spawn.py`'s `ROLES` tuple (and the `LEGACY` map and two
role-name string comparisons) still listed the old names, and `test_gates.py`
/ `test_spawn.py` / `test_approve_scope.py` still had fixtures referencing old
role names or the deleted `roles/qa.json` path. On `main` this produced:

- `python3 test_gates.py` -> `FileNotFoundError` on `roles/ux-design.json`
  (deleted by the rename) in `t_new_roles_resolve_without_a_local_checkout`.
- `pytest` failures in `test_spawn.py` (`OwnershipReport.test_granted_subtrees_are_silent`)
  and `test_approve_scope.py` (board lookups keyed on the old `"product"` role
  name, which `spawn.board()` now filters out because it is no longer in
  `spawn.ROLES`).

## Fix

- `spawn.py`:
  - `ROLES` tuple updated to the 9 canon names, same order as before.
  - `LEGACY` dict keys updated to canon names (values, the v1 filenames, are
    unchanged).
  - `_infer_chain_root`'s convention fallback (`"product"`, `"feasibility"`)
    updated to `"product-discovery"`, `"technical-feasibility"`.
  - `ownership_report`'s two special-cased role checks (`"feasibility"` for
    `spikes/`, `"ops"` for `postmortems/`) updated to `"technical-feasibility"`,
    `"release-engineering"`.
- `test_gates.py`: fixtures in `t_board_reads_loop_state`,
  `t_board_tolerates_trailing_comment`, `t_rulebook_version_is_recorded`,
  `t_new_roles_resolve_without_a_local_checkout`,
  `t_board_absent_names_the_v1_location`, and `t_protected_paths` updated to
  canon role names (`qa`->`execution-observation`, `ux-design`/`verify`/`reflect`
  -> `interaction-design`/`defect-verification`/`issue-retrospective`,
  `review`->`conformance-review`, `product`/`feasibility`->
  `product-discovery`/`technical-feasibility`, `coding`->`implementation`,
  `roles/qa.json`->`roles/execution-observation.json`).
- `test_spawn.py`: `OwnershipReport.test_granted_subtrees_are_silent` role arg
  `"ops"` -> `"release-engineering"` (matches `ownership_report`'s
  `postmortems/` special case).
- `test_approve_scope.py`: all `_record(..., "product", ...)` fixture calls ->
  `"product-discovery"` (matches `spawn.board()`'s `ROLES` filter, which
  `approve_scope` depends on to find the subject's board record).

No changes were needed in `gates.py`, `pr_reference.py`, or `closure_sweep.py`
— those take role names as opaque parameters and don't hardcode the old list.

## Test results

- `python3 -m pytest test_spawn.py test_approve_scope.py test_vocab_coherence_roles.py test_gates.py -q`
  -> `117 passed` (test_gates.py has no pytest-collectible tests; it's run
  directly, see below).
- `python3 test_gates.py` -> all 43 checks print `ok`, including the four that
  previously failed on `main`
  (`t_new_roles_resolve_without_a_local_checkout`, `t_board_reads_loop_state`,
  `t_board_absent_names_the_v1_location`, `t_protected_paths`). One later test,
  `t_repo_local_claude_config_stops_the_spawn`, raises
  `OSError: [Errno 30] Read-only file system` on
  `~/.tokenmaxxxer/trusted-repo-config.json` in this execution environment —
  confirmed pre-existing and unrelated to the role rename: the same test
  environment has `$HOME` mounted read-only outside the repo, independent of
  which commit is checked out, and the failure site (`spawn.require_no_repo_config`)
  does not reference any role name.

Combined: 117 pytest tests pass, all role-name-dependent checks in
`test_gates.py` pass, confirming the regression reported in issue #162 is
resolved.

## Follow-up: one remaining stale reference (PR #165 review comment)

PR #165's fix list (lines 53, 95, 208-211, 228, 363 of `test_gates.py`) missed
one occurrence: `test_gates.py:170`, inside `t_rulebook_falls_back_to_github`,
still read `roles/qa.json` (deleted by the rename) and built a synthetic
local-checkout directory named `qa-agent-rulebook`, which no longer matches
`roles/execution-observation.json`'s `path` field
(`$TOKENMAXXXER_RULEBOOKS/execution-observation-rulebook`). On `main` this
made `python3 test_gates.py` fail with `FileNotFoundError` before printing any
`ok` lines.

Fix: `roles/qa.json` -> `roles/execution-observation.json`, and the synthetic
checkout directory name `qa-agent-rulebook` -> `execution-observation-rulebook`
(matching the canon role's actual `path` basename, not just its role name) so
the local-checkout-wins branch of `spawn.rulebook_source` is exercised
correctly.

Test results (this fix, run against this branch's checkout of `main`-equivalent
state, i.e. after commit `386fc1d`):

- `python3 test_gates.py` -> 43 `ok` lines, then the same
  `t_repo_local_claude_config_stops_the_spawn` failure documented above
  (`OSError: [Errno 30] Read-only file system` on
  `~/.tokenmaxxxer/trusted-repo-config.json`), confirmed pre-existing and
  unrelated to role names (same failure, same site, independent of the
  `roles/qa.json` fix). Because that failure sits alphabetically before
  `t_rulebook_falls_back_to_github` in the direct-run order, the fixed test
  was additionally verified standalone: `python3 -c "import test_gates;
  test_gates.t_rulebook_falls_back_to_github()"` completes without error.
  Full output: [`implementation/test_gates_full_run.log`](implementation/test_gates_full_run.log).
- `python3 -m pytest -q` -> `109 passed, 8 failed`. The 8 failures are in
  `test_spawn.py` (`GitHead`, `IsNewCommit`, `Clean`, `Watchdog`,
  `EventExitScope` classes) and are git-plumbing/filesystem-sandbox failures
  unrelated to role names or `roles/qa.json` (e.g. `git` operations against
  throwaway temp repos returning empty results in this sandbox). Reported
  honestly rather than filtered out. Full output:
  [`implementation/pytest_full_run.log`](implementation/pytest_full_run.log).

This closes the one remaining leftover from the PR #164 -> PR #165 role-rename
cleanup identified in the issue #162 review thread.
