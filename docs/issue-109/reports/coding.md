---
kind: coding-record
loop_state: landed
---

# Issue #109 — Phase 2 record (coding)

code_under_review: gates/gates.py, test_gates.py (this branch, phase-2 commit)

## Why

`record_enums` (#100) resolved `roles/<role>.json` relative to the checked
work repo. Role definitions only ever live in the `on-the-record` repo
itself, so every board that isn't `on-the-record` had no `roles/` and the
gate blocked with "역할 정의를 읽을 수 없어 enum 을 검사할 수 없다" on
otherwise-fine records (observed twice: feasibility-agent-rulebook issue-26
phase 2, product-agent-rulebook issue-29 phase 2). Fix per the approved
proposal (`docs/issue-109/proposals/coding.md`): resolve role definitions
from the on-the-record checkout via self-location (`Path(__file__)`,
mirroring `spawn.py`'s `ROOT`), so a board without `roles/` is never a
violation, while a genuinely broken on-the-record install (missing its own
role file) still fails closed.

## Anomaly note

The phase-1 PR (#111) body contained a literal `Closes #109`, in violation of
the phase-1 issue-reference rule (plain `#109` only). GitHub auto-closed
issue #109 on merge (2026-07-30T00:35:20Z), one second after the human
approver's `APPROVE issue-109/coding` comment (2026-07-30T00:34:39Z) and PR
merge (00:35:19Z). Approval was validly obtained via the single-account
`APPROVE issue-109/coding` string match before the auto-close fired, so phase
2 proceeded per that approval rather than treating the closed state as "no
delivery intended." Flagging per the anomaly-reporting instruction; no other
action taken on the issue itself (closing/reopening is a human act).

## What was done

Implemented the approved proposal exactly:

- `gates/gates.py`: added `ON_THE_RECORD_ROOT = Path(__file__).resolve().parent.parent`
  and switched `record_enums`'s `role_file` lookup from `root / "roles" /
  f"{role}.json"` (work-repo-relative) to `ON_THE_RECORD_ROOT / "roles" /
  f"{role}.json"`. The missing-role-file block message now names the
  on-the-record-relative path checked, distinguishing a broken on-the-record
  install from a board's normal (roles-less) state.
- `test_gates.py`: `_record_repo` now writes `roles/<role>.json` into a
  fabricated on-the-record checkout (`Path(td)/"otr"`) and points
  `gates.ON_THE_RECORD_ROOT` at it, instead of writing into the work repo.
  Every test using it now implicitly exercises "board has no roles/" (since
  the fixture never creates one there). Added
  `t_record_enums_no_roles_in_work_repo_passes` (explicit repro: no `roles/`
  in the work repo, valid on-the-record role file → passes, no warning
  anywhere in the result) and updated `t_record_enums_missing_role_file_blocks`
  to point at a missing on-the-record-checkout role file and assert the
  block message contains the on-the-record path.

## Verification run (this session, once)

`python3 test_gates.py` — all `t_record_enums_*` tests pass (6/6, including
the new one). One unrelated pre-existing failure
(`t_repo_local_claude_config_stops_the_spawn`, `OSError: Read-only file
system: /home/jwjung/.tokenmaxxxer/trusted-repo-config.json`) reproduces
identically on `main` before this change (verified via `git stash` + rerun)
— it's a sandbox filesystem-permission artifact unrelated to this fix, out
of this write set.

## closed_checks

- check: record_enums resolves roles/ from ON_THE_RECORD_ROOT, never from
  the work repo — code_sha: this commit; verified by
  t_record_enums_no_roles_in_work_repo_passes and t_record_enums_out_of_enum_blocks
  / t_record_enums_in_enum_passes / t_record_enums_undeclared_field_passes
  / t_record_enums_loop_state_out_of_set_blocks (none of which create a work-repo
  `roles/` dir).
- check: on-the-record checkout itself missing the role file still fails
  closed, with an on-the-record-relative path in the message —
  code_sha: this commit; verified by t_record_enums_missing_role_file_blocks.

## What did not work

- Initial `_record_repo` rewrite committed the record file and re-pointed
  `origin/main` at that same commit, collapsing the diff to empty —
  `changed_files()` returned `[]` and every record_enums test passed
  vacuously. Expected: fixture diff shows the record as changed; actual:
  no diff. Fixed by leaving the record file uncommitted against the
  existing `origin/main` marker `_repo()` already sets, matching the
  pattern every other fixture in this file uses.

## Hunt

warrant-hunter dispatched at phase-2 completion (stance: rotated —
"ON_THE_RECORD_ROOT resolution for record_enums"). Verdict: NO FINDING.
Traced spawn.py's existing `ROOT` role-resolution pattern (spawn.py:32) and
confirmed gates.py's new `ON_THE_RECORD_ROOT` mirrors it one directory up,
that the plugin/marketplace deployment and `directive.sh`'s checkout
resolution keep `gates.py` inside the same resolved checkout, that symlinked
entry points still resolve correctly, and that fail-closed behavior on a
missing role file is preserved. Full record:
docs/reports/2026-07-30-hunt-issue-109-record-enums-root.md.

## Open findings

None open. No blocking finding has been addressed to this record.
