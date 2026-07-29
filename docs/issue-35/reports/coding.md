---
loop_state: landed
code_under_review: HEAD
---

# Coding record — issue-35

## Why
QA finding F4 on issue #31 (PR #33 record, previously UNFILED): a
whitespace-only `MUSTER_ROLE_MODEL` (e.g. `"   "`) is truthy in
`spawn_cmd`, producing a literal `--model "   "` in the role session's
argv — inconsistent with the empty-string case, which already falls back
to the default model correctly.

## Upstream basis
- Issue #35 (this issue's text, verbatim fix instruction: "strip the
  value before the truthiness check ... cover with a test next to the
  existing SpawnCmd cases").
- docs/issue-31/reports/qa.md (finding F4).

## Survey (phase 1, brief — small located defect)
`spawn_cmd` (spawn.py:1241) and the `--dry-run` reflection branch in
`main()` (spawn.py:1377) both read `MUSTER_ROLE_MODEL` and use it directly
in a truthiness check, so `"   "` is truthy and produces
`--model "   "` / `out["model"] = "   "`. Empty string already falls back
correctly. Write set: `spawn.py`, `test_spawn.py` (no new deps, no schema,
no env var added).

## What was done
- Stripped `MUSTER_ROLE_MODEL` before the truthiness check in both
  `spawn_cmd` (spawn.py:1241) and the `--dry-run` branch (spawn.py:1377):
  `role_model = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()`.
- Fixed the `_dry_run_output` test helper (test_spawn.py) that mirrors the
  same read, so the test double stays honest about the fixed behavior.
- Added `test_role_model_whitespace_only_is_unchanged` (SpawnCmd class)
  and `test_whitespace_only_output_has_no_model_key`
  (DryRunModelReflection class).

## What did not work
(none — straightforward fix, no reverted attempts)

## Verification run
`python3 -m pytest test_spawn.py -q` → 42 passed (was 40; +2 new cases).

## Hunt cadence
Fix is a two-line strip() applied at both existing read sites; no new
surface introduced. Stance: skeptic-of-completeness — checked for other
`MUSTER_ROLE_MODEL` reads via `grep -n MUSTER_ROLE_MODEL spawn.py` and
confirmed only the two sites above exist. No third finding.

## closed_checks
- whitespace-only MUSTER_ROLE_MODEL no longer reaches --model in spawn_cmd or --dry-run reflection (code_sha: HEAD)

## Open findings
None.
