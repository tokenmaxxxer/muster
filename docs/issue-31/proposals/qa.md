# QA phase-2 proposal — issue #31

## Plan
1. Run full `test_spawn.py` suite (not just the two new classes) — confirm no
   regression elsewhere, evidence via command+output.
2. Execute (not read) the acceptance-criteria commands verbatim from the issue:
   - `MUSTER_ROLE_MODEL=sonnet python3 spawn.py <role> "<task>" --dry-run ...`
     → assert `--model sonnet` appears in composed command.
   - Same command without the env var → assert no `--model` flag.
3. Probe edge cases by direct execution:
   - `MUSTER_ROLE_MODEL=""` — empty string set.
   - `MUSTER_ROLE_MODEL="  "` — whitespace-only.
   - Confirm `doctor()`'s haiku probe is unaffected when `MUSTER_ROLE_MODEL` is set
     (execute `doctor()`/equivalent path, not just re-read the test).
   - Confirm both attended and unattended spawn paths append `--model` identically.
4. Record every verdict (pass/fail/blocked) with command+output evidence in
   `docs/issue-31/reports/qa.md`.

## Timebox
~30 minutes of execution.

## Deliverable
`docs/issue-31/reports/qa.md` (session sheet: time breakdown, evidenced findings,
loop_state updates) + any `UNFILED(...)` bug reports if defects are confirmed by
reproduction.
