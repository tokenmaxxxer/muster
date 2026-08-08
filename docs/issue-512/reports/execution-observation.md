---
code_under_review: dbb5162451057bd4486b49f2227ad7b4e7c903ad
loop_state: phase-2-complete
---

# Execution observation record: issue #512

Subject: #512

## Independence statement

This role did not author or edit the observed artifact this session. No
file under `on-the-record/hooks/`, `gates/`, `test/`, or any
`docs/issue-512/` path other than this record was modified in this
session. All verdicts below are drawn from (a) files read on
`dbb5162` (the merged implementation, PR #514), and (b) this session's
own fixture runs against those unmodified, already-shipped scripts —
never from re-executing the implementation session's task.

## What was done

Independently reproduced the three runtime claims made in
`docs/issue-512/reports/implementation.md` (implementation record,
"Acceptance verification" section, roughly lines 128-145), by invoking
the already-shipped hook scripts and `closure_sweep.py` function against
fixture repos built from scratch in `$TMPDIR`, outside this repo's tree,
per the approved proposal
(`docs/issue-512/proposals/2026-08-09-execution-observation-fixture-run.md`):

1. `on-the-record/hooks/call-shape-guard.sh` (payload contract read at
   that file, lines 28 and 216: `CSG_PAYLOAD` env var,
   `tool_name`/`tool_input`/`cwd` JSON fields) against a fresh git
   fixture with a baseline `a.py` containing `subprocess.run(["gh",
   "api", "-X", "POST"])`:
   - synthetic divergent write (`b.py`,
     `subprocess.run(["gh", "api"])`) — rc=2, stderr: `call-shape-guard:
     명령 'gh api' 의 호출부들이 flag 모양이 다르다 (a.py:2, b.py:2)
     ...`.
   - matching/clean write (`c.py`, identical call shape) — rc=0, no
     stderr.
2. `on-the-record/hooks/accumulation-claim-guard.sh` (payload contract
   read at that file, lines 27 and 183: `ACG_PAYLOAD` env var, same JSON
   shape) against a fresh git fixture on branch `issue-999/implementation`
   with a committed proposal file (fixture-only path, not part of this
   repo's tree — docs/issue-999/proposals/x.md) carrying an empty "##
   Accumulation" body:
   - shape-1 write (`foo.py`, three inline `subprocess.run` calls,
     matching the `_SHAPE_1_CONTENT` fixture in
     `on-the-record/hooks/test_accumulation_claim_guard.py`, roughly
     lines 40-44) — rc=2, stderr: `accumulation-claim-guard: 변경이
     축적-비용 모양 ... 을 건드리지만, proposal 본문에 내용이 채워진
     '## Accumulation' 필드가 없다 (issue #424/#512) ...`.
   - non-shape-touching write (`clean.py`, `x = 1`) — rc=0, no stderr.
3. `gates.closure_sweep.accumulation_trend(root)` (defined in
   `gates/closure_sweep.py`, roughly lines 174-198) called directly
   (Python import, not subprocess) against a fresh git fixture with a
   committed `a.py` (one inline `subprocess.run` call) and no
   `runs/accumulation_trend.json` present before the call — returned
   `{'current': {'shape1_sites': 1, 'shape5_files': 0}, 'has_prior':
   False}`, no exception raised.
   `gates.closure_sweep.format_accumulation_trend(trend)` on that same
   result returned `"accumulation-trend: no prior tick data (first run)
   — shape1_sites=1 shape5_files=0"`. After the call,
   `runs/accumulation_trend.json` existed in the fixture (the function's
   documented persistence side effect, same lines above).

All three fixture drivers and their raw stdout are scratch-only
(`$TMPDIR`, outside this repo); the observed rc/stderr values above are
transcribed from this session's actual command output, not predicted.

## Why

The approved proposal
(`docs/issue-512/proposals/2026-08-09-execution-observation-fixture-run.md`)
asked for independent reproduction of the implementation session's own
"Acceptance verification" claims, on a fixture this session built itself,
as the acceptance criterion the issue names (`provenance:
executed-unit`) — distinct from re-running the implementation task
itself, which this session never did.

## Upstream

Based on:
`docs/issue-512/proposals/2026-08-09-execution-observation-fixture-run.md`,
approved via issue comment `APPROVE issue-512/execution-observation`
(single-account mode, author `JiwonJung94`, an account listed in
`docs/specs/approvers.md`).

## Verdict

### Outcome

The implementation PR (#514, merged as `dbb5162`) landed what issue #512
asked: two new PreToolUse hooks
(`on-the-record/hooks/call-shape-guard.sh`,
`on-the-record/hooks/accumulation-claim-guard.sh`), the field-presence
strengthening in `gates/accumulation.py`, and the watchdog-tick
`accumulation_trend()`/`format_accumulation_trend()` pair in
`gates/closure_sweep.py`. All three runtime claims in
`docs/issue-512/reports/implementation.md` (Acceptance verification
section) reproduce independently on this session's own fixtures,
matching the reported rc/stderr values exactly (see "What was done"
above) — outcome: met.

### Trajectory

The implementation session's own record shows it followed the phase
gate: survey (`docs/issue-512/reports/implementation/survey.md`,
present in the merged tree), proposal
(`docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md`),
and phase 2 opened only after a real human approval — the issue comment
`APPROVE issue-512/implementation`, author `JiwonJung94` (listed in
`docs/specs/approvers.md`), read this session via `gh issue view 512
--comments`. This session's own trajectory to this point (survey ->
proposal -> approval-gated phase 2) mirrors the same shape, per this
record's own "Upstream" section above — trajectory: sound.

### Step

No deficient artifact found in what this session's fixtures actually
exercised: both hooks and `accumulation_trend()` behave exactly as
`docs/issue-512/reports/implementation.md` claims. One pre-existing open
finding from the implementation session's own pre-landing warrant hunt
is worth re-citing here rather than re-investigating, since
re-litigating it is explicitly out of this role's scope per the approved
proposal's "Out of scope" section: both new hooks (and pre-existing
`record-claim-guard.sh`) fire only on PreToolUse+Write|Edit|MultiEdit,
so an identical file write routed through the Bash tool bypasses both
guards — recorded in `docs/issue-512/reports/implementation.md`'s "Open
findings" section, full repro in
`docs/reports/2026-08-09-hunt-authoring-time-maintainability-hooks.md`.
This session did not re-verify that finding (out of scope per the
proposal); it is cited, not re-confirmed, here — step: no new deficiency
found in the fixture-observed surface; the one known open finding is the
implementation session's own bypass gap, already tracked, not a defect
in this session's own observation work.

## What did not work

None — no reverted attempts this session; all three fixture drivers
matched their expected exit codes on the first run.

## Open findings

None new. The Bash-routed bypass gap (recorded in
`docs/issue-512/reports/implementation.md`'s "Open findings" section) is
the implementation session's own recorded open finding, cited above, not
reopened or re-investigated by this session.

## Next steps

None for this issue's approved scope — phase 2 complete.

## Resolution path

Not applicable — no new open finding raised by this session.
