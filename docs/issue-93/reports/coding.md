# Issue #93 — coding record

loop_state: landed

## code_under_review
spawn.py, test_spawn.py, README.md @ branch issue-93/coding (pre-implementation)

## why
PR #94 (phase-1 survey + proposal, docs/issue-93/proposals/coding.md)
received a human Approve review, which under role-handoff contract v3 s19
is the basis authorizing phase-2 execution of the approved write set on
this same branch/PR.

## Upstream basis
docs/issue-93/proposals/coding.md (approved), docs/issue-93/reports/coding/survey.md

## What was done
- `spawn.py`: `resolved_role_model()`'s terminal path changed from
  `return read_role_model_config()` to
  `return read_role_model_config() or "sonnet"` — env > config >
  built-in "sonnet", never `""`. Docstring updated. The two call-site
  comments (`spawn_cmd()`'s `--model` block, the `--dry-run` branch in
  `main()`) updated to describe the built-in default instead of "no
  `--model` attached."
- `README.md`: precedence sentence around line 88-100 now reads
  `MUSTER_ROLE_MODEL (env) > role_model.txt (config) > sonnet (built-in
  default)`; the "missing/whitespace-only ... same as unset" sentence
  rewritten to state the built-in default attaches in that case, not "no
  `--model` flag."
- `test_spawn.py`: flipped the seven tests that previously asserted
  `assertNotIn("--model", cmd)` / `assertNotIn("model", out)` in the
  double-unset case (env absent, env whitespace-only, config
  whitespace-only, config non-UTF8, config file absent — 5 in the
  `SpawnCmd` class calling `spawn_cmd()`; 2 in `DryRunModelReflection`
  calling the dry-run output path) to assert `--model sonnet` /
  `out["model"] == "sonnet"` instead. Added
  `test_resolved_role_model_builtin_default_is_sonnet`, asserting
  `spawn.resolved_role_model() == "sonnet"` with both env and config
  absent. Tests already asserting override behavior (env-set,
  config-only, env-overrides-config) left unchanged.
- Ran `python3 -m unittest test_spawn.py -v`: 72 passed, 0 failed.
- Manually confirmed `resolved_role_model()` returns `"sonnet"` with
  `MUSTER_ROLE_MODEL` unset and no `role_model.txt` present (direct
  Python call; the `spawn.py --dry-run` CLI path itself hit an unrelated
  sandbox permission error reading `.claude/agents` in
  `require_no_repo_config()`, outside this change's write set — the
  equivalent output-assembly logic is exercised and green via
  `test_unset_output_reflects_builtin_default`).

## Plan (per approved proposal)
Per docs/issue-93/proposals/coding.md: single-line terminal-return
change in `resolved_role_model()`, comment/docstring updates at its two
call sites, README precedence rewrite, and flipping/adding the issue-#60
tests that exercised the old double-unset case. No new env var,
dependency, or config schema change; #35 strip semantics preserved;
`doctor()`'s haiku probe and `role_model.txt` file handling out of scope.

## What did not work
(none — implementation matched the proposal on the first pass)

## Open findings
- warrant-hunter (docs/reports/2026-07-29-hunt-role-model-builtin-sonnet-default.md):
  `README.ko.md` (~lines 84-95) still documents the pre-#93 terminal-case
  behavior ("both env and config empty → no `--model` flag") and now
  contradicts `spawn.py`'s `resolved_role_model()` and the updated
  `README.md`. `README.ko.md` is outside this proposal's frozen write
  set (`spawn.py`, `README.md`, `test_spawn.py` — docs/issue-93/proposals/coding.md).
  Per the SCOPE-EXCEEDED RULE this is left unfixed here and reported as
  the next proposal's scope, not widened into mid-build.

## Next steps
Follow-up proposal (or an amendment to this one) to bring `README.ko.md`
in sync with the `README.md` precedence rewrite.

## Open-finding resolution path
warrant-hunter finding above is scope-exceeded (touches a file outside
the frozen write set), not a defect in the delivered write set — no
resolved_findings entry required to unblock this record; it is deferred
to a follow-up issue-93 (or new) proposal.

## closed_checks
- `python3 -m unittest test_spawn.py -v` — 72 passed, 0 failed
  (code_under_review: this commit).
- warrant-hunter dispatched before phase-2 completion (hunt cadence) —
  one finding returned, scope-exceeded per above
  (code_under_review: this commit).
