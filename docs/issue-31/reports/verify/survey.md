---
kind: verify-survey
loop_state: phase-1-survey
---

# Issue 31 — verify phase-1 current-state survey

## Subject
Issue #31 (`spawn.py`: `MUSTER_ROLE_MODEL` env var pins the model for spawned
role sessions). Coding (PR #32) and QA (PR #33) both merged to main.
Merge commit for the QA PR: `44c4a09`. Latest touched sha per coding's own
record: `09d76cceb31622c0ba7e27d2af72f519f6ea36ce`.

## What coding's record (docs/issue-31/reports/coding.md) claims
- `spawn_cmd` (`spawn.py:1166-1171`) reads `MUSTER_ROLE_MODEL` via
  `os.environ.get`, appends `["--model", role_model]` to `cmd` only when
  truthy; unset/empty unchanged.
- `README.md` documents `MUSTER_ROLE_MODEL` near the `MUSTER_AGENT_GH_TOKEN`
  paragraph.
- `test_spawn.py` covers this: 3 cases in `SpawnCmd` + 2 in a new
  `DryRunModelReflection` class = 35 total passing.
- Phase-3 hunt fix: `--dry-run` branch (`spawn.py:1298-1313`) now reflects
  `MUSTER_ROLE_MODEL` in printed settings + an echoed `--model <value>` line,
  closing a gap where the issue's own literal acceptance command exercised
  nothing.
- Haiku probe (`doctor()`, untouched) does not go through `spawn_cmd`.

## What qa's record (docs/issue-31/reports/qa.md) claims
- Ran full `test_spawn.py` suite: 35/35 pass.
- Executed the issue's literal acceptance commands live (via scratch cwd to
  dodge this checkout's own `.claude/` tripping `require_no_repo_config`):
  F1 (`MUSTER_ROLE_MODEL=sonnet` → `--model sonnet`) PASS, F2 (unset → no
  flag) PASS, F3 (empty string → no-op like unset) PASS.
- F4 (whitespace-only `"   "` → literal unstripped `--model "   "`): **FAIL**,
  reproduced twice, left **UNFILED** per QA role boundary (QA does not file
  GitHub issues).
- F5/F6 (haiku-probe isolation, attended/unattended parity): PASS via source
  read, not live execution (haiku probe launches a real billed session).
- Gate discrepancy: `gh pr view 33 --json reviews` returned an empty array;
  the "APPROVE issue-31/qa" that unlocked qa's phase-2 was a PR *comment* by
  the PR author, not a submitted GitHub review object. QA proceeded anyway
  on the operator's explicit instruction, and recorded this as an open
  finding rather than blocking.
- Overall qa verdict: **FAIL** (blocking: F4).

## My own independent reproduction (this session, phase-1 scouting)
Read-only checks run directly against `main` (`44c4a09`), not a re-statement
of coding's or qa's conclusions:

1. **F4 / whitespace-only bug — reproduced independently.** Called
   `spawn.spawn_cmd('/tmp/s.json', 'qa', False)` directly with
   `MUSTER_ROLE_MODEL='   '` set:
   ```
   ['claude', '-p', '--settings', '/tmp/s.json', '--permission-mode',
    'acceptEdits', '--output-format', 'stream-json', '--verbose',
    '--model', '   ']
   ```
   Confirms the unstripped whitespace-only value reaches `cmd` verbatim, on
   `main` today. `spawn.py:1169-1171` still reads
   `role_model = os.environ.get("MUSTER_ROLE_MODEL"); if role_model: cmd +=
   ["--model", role_model]` — no `.strip()` present. Bug is real and
   currently unfixed on main.

2. **Issue #35 exists and correctly describes F4.** `gh issue view 35`:
   title "spawn_cmd: whitespace-only MUSTER_ROLE_MODEL yields --model
   '   '", body cites "Found by QA on issue #31 (PR #33 record, finding
   F4, previously UNFILED)", open, filed by JiwonJung94 (the human/repo
   owner, not QA — consistent with QA's role boundary of not filing
   issues itself). This closes the loop qa's record left open
   ("UNFILED... user/maintainer decides whether to file").

3. **Gate discrepancy — reproduced independently, and found to be systemic,
   not a one-off.** `gh pr view 33 --json reviews,comments`: `reviews: []`,
   one issue *comment* "APPROVE issue-31/qa" by JiwonJung94 (self, PR
   author). Same pattern on **PR #32** (coding's own unlock):
   `gh pr view 32 --json reviews,comments` → `reviews: []`, comment
   "APPROVE issue-31/coding" by the same author. `docs/specs/approvers.md`
   lists exactly one approver: `JiwonJung94`. So both phase-2 unlocks in
   this issue's chain (coding and qa) proceeded on a PR *comment* from the
   listed approver, never a submitted `gh pr review --approve`. Per
   contract v3: "Human decisions are GitHub acts only: review Approve...
   A comment is never an approval, however affirmative it reads."

4. **Independently re-ran `test_spawn.py` on main:** `35 passed in 0.24s` —
   matches both records' claimed count.

5. **README documents the var** (`README.md:48`): "Optional: `export
   MUSTER_ROLE_MODEL=<model>` pins the model used by..." — matches coding's
   claim.

6. **`--dry-run` reflection present on main**: `spawn.py:1300-1313` reads
   `MUSTER_ROLE_MODEL` and reflects it into the printed settings dict and an
   echoed `--model <value>` line — matches coding's phase-3 hunt-fix claim.

## Open findings carried into phase-2 attempt list
- F4 whitespace-only defect: confirmed still present on main; correctly
  filed as issue #35. Not a *new* defect for me to raise (already tracked),
  but I will independently verify no regression/silent-fix landed between
  qa's record and now (it has not — reproduced above).
- Gate discrepancy: confirmed independently, and is systemic across both
  PR #32 and PR #33, not limited to PR #33 as qa's record states. This is
  a process/authorization question about how phase-2 got unlocked twice in
  this issue's chain, not a code defect in the shipped feature. I will
  record it as a verify finding (advisory, addressed to the human/process
  layer) since it bears on whether qa's own phase-2 execution — and by
  extension the record I'm verifying — was validly authorized, but it is
  outside my mandate to re-litigate or block the shipped code on.

## Next steps (phase-2, pending human Approve)
Attempt list (see proposal): re-attempt F4 reproduction at execution time
for a fresh evidence pointer, spot-check for any defect class qa's report
didn't probe (e.g. `--model` value containing embedded quotes/shell
metacharacters, since `subprocess` argv is not shell-interpreted so this is
low-risk but unverified by either prior record), and confirm the gate
discrepancy's current status (still open, no formal review submitted) at
verify time. Write `docs/issue-31/reports/verify.md` with per-attempt
reproduced/not-reproduced outcomes and a cleared/not-cleared verdict.
