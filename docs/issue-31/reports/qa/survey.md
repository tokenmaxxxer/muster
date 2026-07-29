# QA phase-1 survey — issue #31

## Scope
QA the merged issue #31 change (PR #32): `MUSTER_ROLE_MODEL` pinning in `spawn_cmd`,
`--dry-run` model reflection, README docs, `SpawnCmd`/`DryRunModelReflection` tests.

## App-up confirmation
```
$ python3 spawn.py
프로젝트: muster-issue-31-qa   경로: ...
subject: issue-31
  [coding] loop_state: committed-pending-push
...
보드가 누구를 깨우는지: spawn.py wake
```
Exit 0. App launches; no server/daemon to boot — `spawn.py` is a CLI invoked directly.

## What landed (read, not yet executed as verdict)
- `spawn.py:1166-1171` — `spawn_cmd` reads `MUSTER_ROLE_MODEL` from env; if set, appends
  `["--model", role_model]` to the role-session argv. `doctor()`'s haiku probe
  (`spawn.py:1121`, hardcoded `--model haiku`) is untouched — separate code path.
- `spawn.py:1300-1313` — `--dry-run` path reads the same env var independently (since it
  never calls `spawn_cmd`) and prints `--model <value>` when set.
- `README.md:48` documents `MUSTER_ROLE_MODEL` next to `MUSTER_AGENT_GH_TOKEN`.
- `test_spawn.py` — `SpawnCmd` class: `test_role_model_unset_is_unchanged`,
  `test_role_model_set_appends_flag`, `test_role_model_does_not_affect_haiku_probe`.
  `DryRunModelReflection` class: `test_unset_output_has_no_model_key`,
  `test_set_output_reflects_model`.

## Existing test convention
`python3 -m unittest test_spawn.py` (stdlib unittest, no pytest). Ran the two relevant
classes already as a smoke check — 10/10 pass (not a verdict, phase-1 recon only).

## Acceptance criteria (from issue #31)
1. `MUSTER_ROLE_MODEL=sonnet python3 spawn.py <role> "<task>" --dry-run ...` shows
   `--model sonnet` in the composed command.
2. Without the variable, the composed command has no `--model` flag.
3. Applies to every role-session spawn path (attended + unattended); haiku probe stays as-is.
4. README documents the variable.

## Edge cases not obviously covered by existing tests — targets for phase 2
- Empty string (`MUSTER_ROLE_MODEL=""`): falsy-but-set. Does `spawn_cmd`/`--dry-run`
  treat this as "unset" (no flag) or append `--model ""`? `os.environ.get` returns `""`,
  which is falsy in a truthiness check but not `None` — behavior depends on whether the
  code checks `if role_model:` vs `if role_model is not None:`.
- Whitespace-only value (`MUSTER_ROLE_MODEL="  "`): truthy string, likely passed through
  verbatim to `--model`, producing a garbage argv token — worth confirming it's not
  silently stripped/rejected.
- Interaction with the haiku probe path (`doctor()`): confirm `MUSTER_ROLE_MODEL` set in
  env does not leak into `doctor()`'s `--model haiku` call (test exists —
  `test_role_model_does_not_affect_haiku_probe` — re-verify by execution, not just reading).
- Unattended vs attended spawn path parity: both should append `--model` identically.
