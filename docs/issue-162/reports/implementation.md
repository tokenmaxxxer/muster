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
