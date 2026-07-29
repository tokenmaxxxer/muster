# Issue #60 — coding record

loop_state: landed

## code_under_review
spawn.py, test_spawn.py, README.md @ branch issue-60/coding (pre-implementation)

## why
PR #62 (phase-1 survey + proposal, docs/issue-60/proposals/coding.md)
received a human Approve review, which under role-handoff contract v3 s19
is the basis authorizing phase-2 execution of the approved write set on
this same branch/PR.

## Upstream basis
docs/issue-60/proposals/coding.md (approved), docs/issue-60/reports/coding/survey.md

## What was done
- Added `ROLE_MODEL_CONFIG = ROOT / "role_model.txt"`,
  `read_role_model_config()`, and `resolved_role_model()` to spawn.py,
  placed just above `spawn_cmd()`.
- `spawn_cmd()`'s `--model` block and the `--dry-run` branch in `main()`
  now both call `resolved_role_model()` instead of reading
  `os.environ.get("MUSTER_ROLE_MODEL")` directly, so they cannot drift.
- `role_settings()` and `roles/*.json` untouched, per proposal (issue #58
  boundary).
- Added test_spawn.py cases: config-only sets `--model`, env overrides
  config, whitespace-only config behaves like unset, missing config file
  behaves like unset, and a `DryRunModelReflection` case for config-only
  dry-run output. Existing env-only and haiku-probe tests untouched and
  still pass.
- Extended the `MUSTER_ROLE_MODEL` README paragraph in place with the
  `role_model.txt` config file and the full env > config > none
  precedence chain.
- Ran `python3 -m pytest test_spawn.py -q`: 49 passed (was 44 before this
  change; 5 new cases added, all existing cases unmodified and still
  green).

## Plan (per approved proposal)
- Repo-root plain-value config file `role_model.txt`.
- `read_role_model_config()`: reads `ROOT / "role_model.txt"`, returns
  stripped content or `""` on missing file / read error.
- `resolved_role_model()`: env checked first with its own strip,
  precedence env > config > none.
- `spawn_cmd()` and the `--dry-run` branch in `main()` call
  `resolved_role_model()` instead of reading `os.environ` directly.
- Tests alongside existing `test_role_model_*` / `DryRunModelReflection`.
- README `MUSTER_ROLE_MODEL` paragraph extended with config file + precedence.
- Out of scope (unchanged): `role_settings()`, `roles/*.json` (issue #58).

## What did not work
(none yet)

## Open findings
(none yet)

## Next steps
Implement the plan above (spawn.py helpers + call-site edits), add tests,
extend README, run the suite, update this record to loop_state: landed.

## Open-finding resolution path
No open findings yet; warrant-hunter runs before phase-2 completion per
hunt cadence and any finding will be logged here with its resolution.

## closed_checks
- `python3 -m pytest test_spawn.py -q` — 50 passed, 0 failed
  (code_under_review: this commit).
- warrant-hunter finding: `read_role_model_config()` caught only
  `OSError`; a non-UTF-8 `role_model.txt` raised `UnicodeDecodeError`,
  crashing spawn.py instead of degrading to `""` as the docstring
  promises. Resolved: now catches `(OSError, UnicodeDecodeError)`; added
  regression test `test_role_model_non_utf8_config_is_unchanged`.
