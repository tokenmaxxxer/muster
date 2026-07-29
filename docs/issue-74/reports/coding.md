---
subject: issue-74
role: coding
kind: record
loop_state: executing
code_under_review: 36ae122a943d73060416d8d580b0e99fb62f9ec5
---

# issue-74 — record: revive the self-check suite

## What was done

(in progress — updated per item as landed; see items 1-7 below as they complete)

### Item 1 — `_board()` / `_wake_repo()` rebuilt to v3 shape

`_board()` (test_gates.py:20-27) now builds `docs/<subject>/reports/<role>.md`
and its two direct callers pass an `issue-<n>`-shaped subject
(`"issue-26"`, `"issue-1"`). `_wake_repo()`'s board-dir construction
(test_gates.py:68) now creates `docs/issue-5/reports/` instead of
`docs/s/`, and the 5 direct record-path sites (feasibility.md x3,
coding.md, review.md) now build `docs/issue-5/reports/<role>.md`.

RED (isolated `t_board_reads_loop_state`, pre-edit):
```
AssertionError: {}
  test_gates.py:44 in t_board_reads_loop_state
```
(exact reproduction of the AssertionError captured in the proposal/issue.)

GREEN (post-edit, each run individually):
- `t_board_reads_loop_state` -> no output, exits 0 ("OK t_board_reads_loop_state")
- `t_board_tolerates_trailing_comment` -> "OK t_board_tolerates_trailing_comment"
- `t_wake_first_build_needs_scope_approval` -> "OK"
- `t_wake_rebuild_is_not_gated` -> "OK"
- `t_wake_finding_wakes_the_addressed_role` -> "OK"
- `t_wake_answered_row_does_not_fire_again` -> "OK"
- `t_wake_refires_when_its_evidence_changes` -> "OK"
- `t_wake_report_never_hides_a_suppressed_row` -> "OK"
- `t_wake_never_reports_judgement_rows_as_unwoken` -> "OK"

(`t_wake_hypothesis_wakes_feasibility` and
`t_wake_acknowledged_hypothesis_goes_quiet` are covered under item 2 below,
since they also depend on the hypothesis-fixture path.)

### Item 2 — hypothesis fixture moved under `docs/issue-<n>/proposals/`

`_wake_repo()` now writes the hypothesis fixture at
`docs/issue-5/proposals/h.md` (was `docs/proposals/h.md`), matching
`wakes._hypotheses()`'s glob of `docs/issue-*/proposals/*.md`. The two
references inside `t_wake_acknowledged_hypothesis_goes_quiet`
(sha lookup + recorded `upstream:` path) were updated to the same path.

RED (isolated `t_wake_hypothesis_wakes_feasibility`, after item 1 landed
but before item 2):
```
AssertionError: {}
  test_gates.py:91 in t_wake_hypothesis_wakes_feasibility
```

GREEN: `t_wake_hypothesis_wakes_feasibility` -> "OK".

**Mandatory round-trip on `t_wake_acknowledged_hypothesis_goes_quiet`:**
- (a) Deliberately corrupted the recorded sha in the `upstream:` block at
  test_gates.py:103, appending the literal string `CORRUPT` to the real
  sha, so the recorded acknowledgement no longer matches the hypothesis
  file's actual head sha.
- (b) Ran the test in isolation. Observed output (verbatim):
  ```
  Traceback (most recent call last):
    File "<string>", line 1, in <module>
    File "/Users/jk/.tokenmaxxxer/work/muster-issue-74-coding/test_gates.py", line 104, in t_wake_acknowledged_hypothesis_goes_quiet
      assert "feasibility" not in _woken(root), _woken(root)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  AssertionError: {'feasibility': 'hypothesis docs/issue-5/proposals/h.md 가 기록된 sha 이후 바뀜'}
  ```
  This proves `"feasibility"` DOES appear in `_woken(root)` once the
  acknowledged sha no longer matches — the test now exercises the
  suppress-on-matching-evidence path instead of passing vacuously.
- (c) Reverted the corruption exactly (removed the appended `CORRUPT`
  suffix, restoring `f"...sha: {sha}\n---\n"`).
- (d) Re-ran the test in isolation. Observed output (verbatim):
  ```
  OK - green after revert
  ```

## Why

Upstream basis: issue #74 ("the self-check suite is dead: test_gates.py
crashes on its first test") + the approved proposal
`docs/issue-74/proposals/coding.md` (approver: jjongkwann, per
`docs/specs/approvers.md`). This is phase-2 execution of that frozen
proposal: rebuild the v2-shaped test fixtures to the v3 board/hypothesis
layout, retire two tests that call symbols v3 already removed, replace one
of them with `require_board()` coverage that did not exist, and make
`tests/run-orchestrate-tests.sh` safe to run in this sandbox before running
it.

## What did not work

(none yet)

## Scope decision recorded

(pending — will record the approver's choice of option (b) for wakes.py:335)

## Verification

(pending)

## closed_checks

(pending)

## Open findings

None yet — items 1-7 are still being worked through in order per the
proposal's sequencing.

## Next steps

Work through items 1-7 of `docs/issue-74/proposals/coding.md` in order,
isolating each test red before fixing it, committing per the prescribed
sequence, then set `loop_state: phase2-complete` once
`python3 test_gates.py`, `python3 test_spawn.py` (or its blocker), and
`bash tests/run-orchestrate-tests.sh` have all been observed with their
final verbatim output recorded here.

## Open-finding resolution path

No open findings block this record. The out-of-scope `wakes.py:335` defect
raised during phase-1 survey is being routed to a separate issue (#82) per
the approver's choice of option (b) in the proposal's "Scope decision
requested" section — it is not an open finding against this record, it is a
deliberately deferred, separately tracked item.
