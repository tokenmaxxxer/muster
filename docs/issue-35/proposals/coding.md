# Proposal: issue-35 — strip MUSTER_ROLE_MODEL before truthiness check

## Request (paraphrased intent)
`spawn_cmd` in `spawn.py` treats a whitespace-only `MUSTER_ROLE_MODEL`
(e.g. `"   "`) as set, appending a literal `--model "   "` to the role
session's argv. Empty string already falls back correctly; whitespace-only
should behave the same way. Also fix the `--dry-run` reflection path in
`main()`, which mirrors the same env var read.

## Constraints
- Small, located defect (QA finding F4 on issue #31, PR #33).
- Keep existing behavior for unset/empty/non-blank values unchanged.

## What will be done
- files: `spawn.py`, `test_spawn.py`
- In `spawn_cmd` (spawn.py ~1241) and in `main()`'s `--dry-run` branch
  (spawn.py ~1377), read `MUSTER_ROLE_MODEL`, strip it, and use the
  stripped value for both the truthiness check and the appended flag/value:
  `role_model = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()`.
- Add `test_role_model_whitespace_only_is_unchanged` next to the existing
  `SpawnCmd` model cases, and `test_whitespace_only_output_has_no_model_key`
  next to the existing `DryRunModelReflection` cases (also fixed that
  class's `_dry_run_output` helper, which reproduces the same read).

## Out of scope
- Any other env var validation/trimming.

## How it will be verified
- `python3 -m pytest test_spawn.py -q` — full suite green, including the
  two new whitespace-only cases.
