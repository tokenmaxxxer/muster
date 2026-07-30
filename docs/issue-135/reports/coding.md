---
loop_state: landed
---

# Coding record — issue #135

upstream: docs/issue-135/proposals/coding.md (approved via issue comment
`APPROVE issue-135/coding`)

## What was done

- `gates/closure_sweep.py` (new): `classify(issue_state, pr_state, pr_body,
  issue)` — pure classifier, no network. Two invariants:
  `open-pr-on-closed-issue` (issue closed, PR still open and referencing
  it) and `merged-delivery-issue-open` (PR merged with a
  `Closes/Fixes/Resolves #n` body and the issue still open). Reuses
  `pr_reference._CLOSES_REF` / `_PLAIN_REF` for reference classification
  instead of a second regex. A merged PR with only a plain `#n` reference
  (the phase-1 shape) against an open issue is explicitly not a
  violation. `find_violations(root, subjects=None)` walks
  `spawn.board(root)`'s subjects x roles, resolves each branch's PR via
  `spawn._pr_for_branch`, reads issue/PR state via `gh`, and classifies.
  `format_report` and `post_sweep_comments` (marker-guarded via
  `spawn._issue_comments`, marker includes a hash of the sorted violation
  set so a changed set posts fresh instead of going silent) follow the
  `_post_crash_comment` precedent.
- `spawn.py`: new `closure-sweep` subcommand (explicit invoke, parallel to
  `approve-scope` — not wired into `roster_watchdog`'s tick) and a
  `--post` flag to also comment on violating issues.
- `test_gates.py`: five new cases against `closure_sweep.classify`
  covering both violation kinds, the phase-1 negative case, an issue
  closed with an unrelated PR (no violation), and the fully-consistent
  case.

## Why

The approved proposal (`docs/issue-135/proposals/coding.md`) defines, in
code, what "the board's issues and PRs close consistently" means and adds
a report-only sweep — closing stays a human/orchestrator decision per
contract v3.

## What did not work

(nothing — no reverted attempts this phase)

## Confirmation run

`python3 test_gates.py` — all `t_closure_sweep_*` cases pass. One
pre-existing failure (`t_repo_local_claude_config_stops_the_spawn`,
`OSError: Read-only file system: /home/jwjung/.tokenmaxxxer/trusted-repo-config.json`)
is a sandbox/home-write restriction unrelated to this change's write set.

`python3 spawn.py closure-sweep` run for real against this repo's live
board (real `gh` calls, not mocked): output `종결 일관성 스윕: 위반 없음` —
the board is closure-consistent right now.

## Hunt

warrant-hunter dispatched at end of phase 1 (see
`docs/issue-135/reports/coding/scout-brief.md`). No fresh phase-2 probe
was dispatched — the write set is small and mirrors the already-reviewed
`pr_reference.py`/`_post_crash_comment` patterns closely.

closed_checks: none (no findings addressed to this record).

## Open findings

None outstanding for this record.

## Out of scope (unchanged from proposal)

Auto-closing issues/PRs; scheduling the sweep inside the watchdog tick;
sweeping non-`issue-<n>/<role>` branches; cross-repo sweeps.
