---
code_under_review:
  - test/test_latency_report.py
  - docs/issue-505/reports/implementation.md
loop_state: landed
---

# Implementation — #505 slow-session attribution mining

## What was done

Mined the 9 slowest sessions from today's `runs/ledger.jsonl` (per
`docs/issue-505/reports/implementation/survey.md`'s ranking and
substitution rationale), read each session's `.log` file directly with
`grep -n '"is_error":true'` / `non_execution_kind`, and attributed each
session's wall-clock time to one of: (a) gate-refusal/workaround loop,
(b) harness permission wall / retry loop, (c) network/tooling stall, (d)
genuine task size. Extended `test/test_latency_report.py` with
`parse_slow_session_table` + a regression test asserting row count and
citation shape. Bug candidates are cross-referenced below.

## Attribution table

| issue | repo | duration_s | cause_class | log_citation | finding |
|---|---|---|---|---|---|
| 474 | on-the-record | 1278.2 | a | on-the-record-issue-474-implementation.session.20260808T185416.615087.log:L219-L600 | board-gate.sh refused 25 times against a self-generated `docs/issue-416/` path while the session's own branch is `issue-474/implementation`; the path was never corrected between retries. |
| 147 | tokenmaxxxer-core | 945.0 | a | tokenmaxxxer-core-issue-147-implementation.session.20260808T180551.278899.log:L24-L563 | Same board-gate shape as 474: 22 refusals against a wrong-branch/nonexistent-issue write path, retried identically rather than corrected. |
| 473 | on-the-record | 879.3 | b | on-the-record-issue-473-implementation.session.20260808T185414.614822.log:L46-L358 | 5 `user-rejected` denials: a compound multi-statement Bash command requiring approval (L86 area) plus a self-inflicted `InputValidationError` from malformed JSON tool-call input; distinct from the gate-refusal-loop shape — sandbox/approval friction, not a repeated self-generated bad path. |
| 444 | on-the-record | 786.6 | b | on-the-record-issue-444-conformance-review.session.20260808T171525.81566.log:L68-L405 | A `general-purpose` subagent's Bash calls denied 11 consecutive times over roughly a minute of wall-clock (permission-rule hit at L400, `severity-gate.sh` refusing a Bash-authored edit to the record file); matches #187's scratchpad/permission-wall retry shape. |
| 466 | on-the-record | 774.2 | b | on-the-record-issue-466-implementation.session.20260808T182125.376806.log:L29-L363 | 16 denials, 11 `user-rejected` + 1 `permission-rule` (L97, `record-fields-gate.sh` refusing a Write for missing required fields); session ultimately errored (rc=1). Same #187 friction class as 444/171. |
| 180 | tokenmaxxxer-core | 748.8 | b | tokenmaxxxer-core-issue-180-implementation.session.20260808T205402.1314513.log:L65-L418 | 15 denials including repeated sandbox rejections and a "File has not been read yet" retry (L180) — approval-wall shape at lower multiplicity than 474/147/171. |
| 457 | on-the-record | 730.3 | b | on-the-record-issue-457-implementation.session.20260808T173352.189778.log:L27-L464 | 9 denials: a `find -exec` auto-allow-prefix rejection (L164) and a `board-gate.sh` refusal for writing into another role's report path (L364) — approval-wall shape, not the wrong-branch loop seen in 474/147. |
| 171 | tokenmaxxxer-core | 727.6 | b | tokenmaxxxer-core-issue-171-implementation.session.20260808T214140.1624298.log:L76-L882 | 52 denials in one session, the outlier of this cohort — the identical scratchpad path denied repeatedly with no adaptation between retries; the clearest #187 match in the mined set. |
| 497 | on-the-record | 723.3 | d | on-the-record-issue-497-defect-verification.session.20260808T204508.1271715.log:L49-L287 | 25 `is_error` hits, but the `permission-rule` one (L282) is `record-fields-gate.sh` correctively refusing an incomplete record and getting fixed — iterative record-writing diligence, not a stuck retry loop; classified as genuine task size, not system friction. |

## Bug candidates

### #187 (cross-reference, no new issue needed)

Confirmed present today in issues 444, 466, and — most severely — 171
(52 identical scratchpad-path denials in one 727.6s session). The
friction shape #187 already names — repeated retries into a
sandbox-denied path with no adaptation between attempts — is unchanged;
this mining pass adds three fresh log citations as evidence the pattern
is still live, not a new bug.

### New: `board-gate.sh` loops against self-generated wrong-branch/nonexistent-issue paths

**Title**: board-gate refusal loop retries an unchanged wrong-branch
write path instead of correcting it

**Where seen**: issue-474 (25 refusals, `on-the-record-issue-474-implementation.session.20260808T185416.615087.log:L219-L600`)
and issue-147 (22 refusals, `tokenmaxxxer-core-issue-147-implementation.session.20260808T180551.278899.log:L24-L563`).

**Description**: In both sessions, `board-gate.sh` correctly refuses a
`Write` targeting a `docs/issue-<n>/` path that does not match the
session's own branch (e.g. writing `docs/issue-416/` from a session on
`issue-474/implementation`). The gate's refusal message names the
mismatch plainly. But the worker retries the identical wrong path
repeatedly — 25 and 22 times respectively — rather than adapting to the
gate's own branch name after the first refusal. This is a distinct
failure shape from #187 (which is a sandbox/scratchpad permission wall);
here the gate is functioning correctly and the loop is entirely
self-inflicted by the worker not reading its own refusal message. Fixing
this is out of scope for #505 (measurement-only); candidate fix
direction: have the worker parse the gate's stated "current: issue-<n>"
branch out of the refusal text before retrying, or cap identical-path
retries and surface the mismatch instead of looping silently.

**Repro**: any session whose write path's issue number diverges from its
branch name and that retries a denied Write without adjusting the path;
issue-474's session log line 219 and issue-147's line 24 are concrete
first occurrences to start from.

## What did not work

None. The mining pass matched the survey's ranking and substitution
rationale; the only refinement made during phase 2 was re-verifying
each cited line range directly against the on-disk `.log` files (rather
than reusing survey.md's rougher per-session line pointers), which
turned up more precise `L<first>-L<last>` ranges than the survey draft
had sketched.

## Why

Per the approved proposal
(`docs/issue-505/proposals/2026-08-08-slow-session-attribution.md`): a
markdown table read by a small regex parser mirrors `compute_idle_gaps`'s
style from #501 and avoids a JSON sidecar duplicating the same content
for no reader benefit (see the proposal's Rationale section for the
full alternative-and-reason).

## Upstream

Based on `docs/issue-505/reports/implementation/survey.md` and
`docs/issue-505/proposals/2026-08-08-slow-session-attribution.md`
(commit 9865be5).

## Open findings

None outstanding.
