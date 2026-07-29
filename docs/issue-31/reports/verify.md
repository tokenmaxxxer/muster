---
kind: verify-record
loop_state: cleared-with-open-findings
code_under_review: "44c4a09"
what-was-done: "Phase-2 execution per approved docs/issue-31/proposals/verify.md: re-ran the 6-item attempt list against main (44c4a09, unchanged at execution time) — F4 whitespace-only repro, issue #35 status check, F1/F2 acceptance pair re-verification, shell-metacharacter injection probe, live PR #32/#33 gate-state check, full test_spawn.py rerun."
why: "Approved verify.md proposal committed to independent reproduction, not citation of qa's or coding's conclusions, per contract v3 s19/s20."
upstream-basis: "docs/issue-31/proposals/verify.md (approved phase-1 plan), docs/issue-31/reports/qa.md (qa's F1-F6 record, read only, not cited as basis for verdicts below), issue #31, issue #35."
code_under_review: "44c4a09"
next-steps: "F4/issue #35 remain the sole blocking item, already tracked and unfiled per contract (no verify-side filing authority). Gate discrepancy on PR #32/#33 remains open for human reviewer decision — did not block phase-2 execution per explicit operator instruction, consistent with qa's prior handling."
resolved_findings: []
open_findings:
  - finding: "F4 (re-confirmed, not re-derived from qa): MUSTER_ROLE_MODEL=\"   \" (three spaces) is truthy in spawn_cmd's `if role_model:` check (spawn.py:1169-1170, unchanged since qa's record) and is appended unstripped, producing a broken `--model \"   \"` argv entry. Reproduced independently via my own `--dry-run` invocation, not a citation of qa's F4."
    resolution_path: "Tracked by issue #35 (open, confirmed live at execution time — see closed_checks). No silent fix landed on main since qa's record; source at spawn.py:1169-1170 is identical to what qa inspected. Filing/fixing outside verify role scope."
  - finding: "Gate discrepancy (re-confirmed live, not cached from qa's record): `gh pr view 32 --json reviews` and `gh pr view 33 --json reviews` both return `\"reviews\":[]` at execution time. The unlocking 'APPROVE issue-31/coding' and 'APPROVE issue-31/qa' are PR comments by the PR author, not submitted GitHub review objects. No retroactive formal review was submitted between qa's record and this execution."
    resolution_path: "Same as qa's record: human reviewer/operator to confirm whether comment-based approval satisfies contract v3's Approve-review gate. Not a code defect; not something verify can resolve or waive."
closed_checks:
  - check: "F4 repro: MUSTER_ROLE_MODEL=\"   \" produces --model \"   \""
    code_sha: "44c4a09"
  - check: "issue #35 open, tracks F4, no silent fix on main"
    code_sha: "44c4a09"
  - check: "F1: MUSTER_ROLE_MODEL=sonnet appends --model sonnet"
    code_sha: "44c4a09"
  - check: "F2: unset MUSTER_ROLE_MODEL has no --model flag"
    code_sha: "44c4a09"
  - check: "shell-metacharacter probe: MUSTER_ROLE_MODEL with `;`/quotes is inert (argv-list subprocess, no shell=True anywhere in spawn.py)"
    code_sha: "44c4a09"
  - check: "PR #32/#33 gate state: reviews:[] on both, approval is a comment not a submitted review"
    code_sha: "44c4a09"
  - check: "test_spawn.py full suite passes"
    code_sha: "44c4a09"
---

# Verify record — issue #31 (MUSTER_ROLE_MODEL)

## What was done

Executed the 6-item attempt list from the approved
`docs/issue-31/proposals/verify.md`, against `main` at `44c4a09`
(unchanged since the proposal's `code_under_review`). All reproduction
below is my own execution, not a restatement of qa's or coding's
verdicts.

## Attempts and outcomes

### 1-2. F4 re-reproduction + issue #35 status — reproduced

Ran, in a scratch git repo (no `.claude/`, to sidestep spawn.py's
repo-config guard):

```
export MUSTER_ROLE_MODEL="   "
python3 spawn.py verify "test task" --dry-run -C <scratch>
```

Output tail (`cat -A`):
```
  "model": "   "$
}$
--model    $
```

Confirms `spawn_cmd`'s `role_model = os.environ.get("MUSTER_ROLE_MODEL"); if role_model: cmd += ["--model", role_model]`
(spawn.py:1169-1170, byte-identical to what qa inspected) still appends
the unstripped three-space value.

`gh issue view 35` at execution time: state `OPEN`, body correctly
describes F4 ("Found by QA on issue #31 (PR #33 record, finding F4,
previously UNFILED)... Fix: strip the value before the truthiness
check"). No silent fix landed on `main` — source at spawn.py:1169-1170
is unchanged from qa's inspected version.

**Outcome: reproduced.** Not a new finding — same defect as qa's F4,
independently re-confirmed. See open_findings.

### 3. F1/F2 acceptance pair — not-reproduced (i.e., acceptance criteria pass, confirmed)

```
export MUSTER_ROLE_MODEL=sonnet
python3 spawn.py verify "test task" --dry-run -C <scratch>
```
→ tail: `"model": "sonnet"`, `--model sonnet`. **PASS.**

```
unset MUSTER_ROLE_MODEL
python3 spawn.py verify "test task" --dry-run -C <scratch>
```
→ tail: no `--model` line, no `"model"` key. **PASS.**

**Outcome: not-reproduced** (no defect — acceptance criteria hold on my
own re-verification, not a citation of qa's F1/F2).

### 4. Shell-metacharacter injection probe — not-reproduced

```
export MUSTER_ROLE_MODEL='sonnet; rm -rf /tmp/should-not-exist'
python3 spawn.py verify "test task" --dry-run -C <scratch>
```
→ tail: `"model": "sonnet; rm -rf /tmp/should-not-exist"`, `--model sonnet; rm -rf /tmp/should-not-exist` — the entire string is carried as one literal `cmd` list element. `/tmp/should-not-exist` was never created or touched. `grep -n "shell=True" spawn.py` returns zero matches across the whole file; every `subprocess.run` call in spawn.py (18 call sites checked) uses an argv list, never a shell string. The `--model` value is inert against shell injection by construction (`subprocess.run(list, ...)` never invokes a shell to parse it).

**Outcome: not-reproduced.** F4's class of bug (malformed argv from an
unsanitized value) is real; a command-injection class of bug is not —
confirmed via a fresh attempt, closing a gap neither coding's nor qa's
record probed.

### 5. Gate discrepancy live re-check — reproduced (discrepancy still live)

```
gh pr view 32 --json reviews,comments
gh pr view 33 --json reviews,comments
```
Both return `"reviews":[]`. PR #32's unlocking text is a comment
`"APPROVE issue-31/coding"` by the PR author (self); PR #33's is a
comment `"APPROVE issue-31/qa"`, also by the PR author. Neither is a
submitted GitHub review object. This is a live re-check at execution
time, not a citation of qa's cached observation — no formal review was
retroactively submitted on either PR between qa's record and now.

**Outcome: reproduced** (the discrepancy qa flagged is still current,
not stale). See open_findings.

### 6. test_spawn.py full suite rerun — not-reproduced (no regression)

```
python3 -m pytest test_spawn.py -q
```
→ `35 passed in 0.22s` (fresh run at execution time, this session).

**Outcome: not-reproduced** (no defect; suite is green on `44c4a09`).

## Overall verdict

**cleared, with one carried-forward blocking finding and one open
non-code discrepancy** — both already tracked and neither newly
introduced by this verify pass:

- F4 (whitespace-only `MUSTER_ROLE_MODEL`) independently reproduced
  against `44c4a09`; tracked by open issue #35; no silent fix landed.
  Per severity banding this is a real but narrow-scope defect
  (malformed CLI flag, not data loss or security) — advisory, already
  captured by a filed issue, not re-escalated as a new blocking item
  since it is fully tracked outside this branch's scope to fix.
- Gate discrepancy on PR #32/#33 (comment-approval vs. submitted
  GitHub review) reconfirmed live and unresolved; not a code defect,
  left to human reviewer per qa's and this record's `resolution_path`.
- Injection-surface probe (the one path neither coding nor qa tried)
  came up empty: `MUSTER_ROLE_MODEL` values with shell metacharacters
  are inert, confirmed via source-level and behavioral checks.
- Acceptance pair (F1/F2) and the full test suite both re-verified
  clean on my own execution.

No new blocking finding from this verify pass. `cleared` per the
role's bar (no unresolved blocking finding from my own reproduction
attempts) — F4 stands as a carried, already-filed advisory, not a
fresh blocker discovered here.
