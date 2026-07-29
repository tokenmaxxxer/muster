---
kind: verify-proposal
loop_state: phase-1-proposal
code_under_review: "44c4a09"
---

# Issue 31 — verify phase-1 proposal

## code_under_review
`44c4a09` (merge commit of PR #33 on `main`, the current head as of this
survey). All attempts below target this sha unless noted.

## Attempt list

1. **Re-reproduce F4 (qa's open defect report)**: call `spawn.spawn_cmd`
   directly with `MUSTER_ROLE_MODEL="   "` and record the resulting argv.
   Tests qa's finding F4 (`docs/issue-31/reports/qa.md`, "F4 — edge:
   MUSTER_ROLE_MODEL='   ' (whitespace-only) — BUG"). Already reproduced
   once during phase-1 scouting (survey.md item 1); phase-2 re-attempt is
   for a fresh, execution-phase evidence pointer, not a re-derivation of
   scope.

2. **Confirm issue #35 still accurately tracks F4 and remains open** (no
   silent fix landed on main since qa's record). `closed_checks` I can
   cite without re-deriving: none yet — this is itself the re-derivation
   qa's `resolution_path` asked for. code_sha to cite against: `44c4a09`.

3. **Re-verify the acceptance-criteria pair (F1/F2 in qa's record)**:
   `MUSTER_ROLE_MODEL=sonnet` → `--model sonnet` present;
   unset → absent. Tests review requirement "MUSTER_ROLE_MODEL pins the
   model" marked Present by coding/qa. My own call via `spawn.spawn_cmd`,
   not a citation of qa's F1/F2 output.

4. **Probe one path neither coding nor qa's records claim to have tried**:
   a `MUSTER_ROLE_MODEL` value containing shell metacharacters or embedded
   quotes (e.g. `sonnet; rm -rf /` or `"sonnet"`), to check whether the
   unstripped/unvalidated value is a real command-injection surface. Since
   `spawn_cmd`'s `cmd` list is passed to `subprocess`-style argv (not a
   shell string), this is expected to be inert (F4's class of bug, not an
   injection), but neither record probed it directly — closes that gap
   with a first-party attempt rather than an assumption.

5. **Confirm the gate discrepancy's current state**: re-run
   `gh pr view 32/33 --json reviews,comments` at execution time to see if
   a formal review was later submitted retroactively (unlikely, but the
   attempt must be live, not cached from phase-1 scouting).

6. **Re-run `test_spawn.py` full suite** at execution time for a fresh
   evidence pointer (pass count + timestamp), not a citation of coding's or
   qa's reported "35 passed."

## closed_checks I will cite vs re-derive
- Cite (already independently verified against `44c4a09` in phase-1
  scouting, no re-derivation needed unless sha changes): README
  documentation present (`README.md:48`), `--dry-run` reflection present
  (`spawn.py:1300-1313`), haiku probe isolation (source read, unchanged
  since qa's record — `spawn.py:1095-1136` not touched by either PR).
- Re-derive (attempts 1-6 above): F4 reproduction, issue #35 status,
  F1/F2 acceptance pair, injection-surface probe, gate-discrepancy live
  state, full test-suite run.

## Scope boundary
This proposal does not re-litigate coding's or qa's per-requirement
verdicts, and does not hold a holistic quality opinion on the feature. It
tests: (a) whether qa's one blocking finding (F4) still reproduces on the
code actually merged to main, (b) whether one untried defect class turns
up anything qa/coding missed, and (c) whether the authorization gate qa
flagged is still open. `cleared` requires no unresolved blocking finding
from my own reproduction attempts, or an explicit human waiver.
