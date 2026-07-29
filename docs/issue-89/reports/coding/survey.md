# Issue #89 — phase 1 current-state survey

## Issue intent (paraphrased)

A headless role session (`claude -p`, single turn) can delegate work to a
`run_in_background` worker and then end its turn. The backgrounded process
dies with the parent when the turn ends — this is a platform-level fact,
reproduced independently (2026-07-29): a backgrounded `sleep 20 && echo
SURVIVED > bgtest.txt` did not survive turn end. The session nonetheless
self-reports "progressed" / "delegated to background worker, will own
commit and push". `spawn.py` currently relays that self-report largely
as-is, so a run that produced zero commits and zero deliverables can still
be recorded as `progressed`.

The issue asks for two independent fixes:

1. **Preamble warning** — the task text assembled for the role session in
   `_spawn_one` must explicitly say the turn is headless/single-turn and
   that anything pushed to background execution dies at turn end; all work
   must complete inside the turn.
2. **Fail-closed post-exit verification** — after the session exits, if it
   self-reported (or was classified as) `progressed` but the workspace has
   no new commits and/or has a dirty tree, spawn must report the run as
   `FAILED` rather than `progressed`. An honest `blocked` self-report is a
   different, non-failure outcome and must not be swept into `FAILED`.

## Affected code paths

All in `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-89-coding/spawn.py`.

### Preamble assembly — `_spawn_one`, spawn.py:1608-1628

`_spawn_one(cwd, role, task, unattended, issue=None)` builds the effective
task text for isolated (`issue is not None`) runs at spawn.py:1620-1628:

```python
cwd = issue_workspace(cwd, issue, role)
br = checkout_issue_branch(cwd, issue, role)
...
task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
        f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n"
        f"완료의 정의: 변경이 이 브랜치에 **커밋**되고 push 되어 PR 로\n"
        f"제출된 상태다. 미커밋 변경은 존재하지 않는 것과 같다 —\n"
        f"세션을 끝내기 전에 반드시 커밋하라. push/PR 이 네트워크로\n"
        f"막히면 커밋까지는 해 둬라: on-the-record 가 밖에서 릴레이한다.\n\n") + task
```

This block already states "commit before ending the session" but says
nothing about headless/single-turn semantics or that backgrounded work
dies at turn end. This is the insertion point for requirement 1: the new
warning sentence(s) should be appended to (or interleaved with) this
f-string, ahead of `task`.

Note: this block only runs when `issue is not None` (the isolated
issue-workspace path). Ad-hoc (`issue is None`) spawns pass `task`
through unmodified — worth flagging in the proposal, since the incident
was on an issue-workspace run, but the preamble mechanism as it exists
today does not cover the ad-hoc path.

### Self-reported status capture

- `result = {}` is populated by parsing the `stream-json` output for the
  final `type == "result"` event, spawn.py:1674, 1690-1699.
- `session_result(stdout)` (spawn.py:941-948) is a helper for parsing a
  full JSON blob into `dict`, used elsewhere for the non-streaming path.
- `result.get("result")` (the session's final free-text answer, e.g. the
  literal string containing "progressed"/"blocked") is printed for the
  user at spawn.py:1704-1705, but is **not** itself parsed/matched against
  keywords anywhere in this file — "self-reported status" as a machine
  fact is really the `outcome` computed by `classify()`, not free text.

### Classification — `classify()`, spawn.py:951-974

```python
def classify(rc: int, result: dict, delta: list, blocked: list) -> str:
    if rc != 0 or result.get("is_error"):
        return "errored"
    if delta:
        return "progressed"
    if blocked:
        return "waiting-on-human"
    if result.get("permission_denials"):
        return "refused"
    return "silent-failure"
```

`delta` is the board-file diff (see below), not a git-commit check. So a
session that touched wake-board files but produced no git commit already
satisfies `outcome == "progressed"` today — this is the exact gap
requirement 2 targets. `classify()` has no `blocked`-as-self-report
concept currently; `blocked` here means "wake rows blocked pending a
human gate" (from `wakes.evaluate`), a different meaning than an honest
"I am blocked" self-report from the session. The proposal must not
conflate the two.

### Post-exit handling — `_spawn_one`, spawn.py:1710-1770

Sequence after `proc.wait()` (spawn.py:1700):

- `before`/`after` = `board_snapshot(cwd)` calls (spawn.py:1659, 1710);
  `delta` = sorted list of paths whose board snapshot changed
  (spawn.py:1711-1712).
- `blocked` = `wakes.evaluate(cwd)[2]` (spawn.py:1713-1716), wrapped in
  `try/except` so evaluation failure never masks the outcome.
- **Git status check already exists**, but only for logging/push, not for
  classification: spawn.py:1718-1729 —
  ```python
  uncommitted = []
  if issue is not None:
      st = subprocess.run(["git", "-C", cwd, "status", "--porcelain"],
                          capture_output=True, text=True)
      uncommitted = [l for l in st.stdout.splitlines() if l.strip()]
      if uncommitted:
          print(... "미커밋 변경 ... " ...)
      ensure_pushed(cwd, issue, role)
  ```
  This computes `git status --porcelain` (dirty-tree check) but there is
  **no `git rev-parse HEAD` / commit-count comparison** anywhere in
  `_spawn_one` today — no "before" HEAD is captured, so spawn currently
  has no way to tell "0 commits happened this run" from "commits happened
  but tree is now dirty again." This is a second gap requirement 2 must
  close (comparing HEAD before/after the session, in addition to the
  existing dirty-tree check).
- `outcome = classify(rc, result, delta, blocked)` at spawn.py:1731.
- `if outcome == "silent-failure" and uncommitted: outcome =
  "uncommitted-work"` at spawn.py:1732-1733 — the **only** existing place
  where the git-dirty signal feeds back into `outcome`, and it only fires
  when the board also showed no delta. It does not touch the
  `outcome == "progressed"` case, which is exactly the incident's shape
  (self-reported/classified progressed, board maybe touched, but no
  commit landed).
- `outcome == "progressed"` gates `wakes.consume(cwd, answering)`
  (spawn.py:1735-1738) — consuming the wake row. If `progressed` gets
  downgraded to a new `FAILED` outcome, this consume call must not fire
  for the downgraded case (otherwise the wake row is silently marked
  answered despite no real deliverable).
- `ledger_write(...)` (spawn.py:1739-1748) records `outcome` into the
  JSONL ledger — this is the durable record consumers (drivers, reports)
  read; the downgrade must happen **before** this call so the ledger
  reflects `FAILED`, not `progressed`.
- Terminal stderr messaging exists per-outcome for `refused` (1762-1765)
  and `silent-failure` (1766-1769) but not yet for any downgraded
  fail-closed outcome — requirement 2's implementation will need an
  analogous message.

### Workspace/commit info available at this point

- `cwd` — resolved workspace path (issue-isolated clone when `issue is
  not None`, via `issue_workspace()`/`checkout_issue_branch()`,
  spawn.py:1620-1621).
- `git -C {cwd} status --porcelain` — already run (spawn.py:1720-1721),
  reusable for the dirty-tree half of the check.
- No existing HEAD capture; would need a `git -C {cwd} rev-parse HEAD`
  (or `git -C {cwd} rev-list --count <before>..HEAD`) taken once before
  `subprocess.Popen(cmd, ...)` (near spawn.py:1659, alongside `before =
  board_snapshot(cwd)`) and once after `proc.wait()` (near spawn.py:1710,
  alongside `after = board_snapshot(cwd)`), for symmetry with the
  existing board-snapshot pattern.
- `issue is not None` gate: the git-based checks are only meaningful (and
  only currently run) for issue-isolated workspaces; ad-hoc spawns have
  no dedicated branch/workspace to check commits against.

## Status flow today (summary)

```
_spawn_one
  -> before = board_snapshot(cwd)                         [no HEAD capture]
  -> subprocess.Popen(...) runs the role session, streams stream-json
  -> result = last {"type": "result"} event                (free-text "result" field, is_error, permission_denials, ...)
  -> after = board_snapshot(cwd)
  -> delta = board diff (before vs after)
  -> blocked = wakes.evaluate(cwd)[2]                      (wake-gate blocks, not self-report "blocked")
  -> uncommitted = git status --porcelain (issue-workspaces only)  [dirty tree only, no commit-count check]
  -> outcome = classify(rc, result, delta, blocked)         ["progressed" whenever delta non-empty, regardless of commits]
  -> if outcome == "silent-failure" and uncommitted: outcome = "uncommitted-work"   [only path where git signal changes outcome, and it never touches "progressed"]
  -> if outcome == "progressed": wakes.consume(...)
  -> ledger_write({..., "outcome": outcome, ...})
```

The incident's failure mode — self-report/classification says
`progressed`, workspace has no real commit — passes straight through this
pipeline unmodified today.

## Honestly-projected write set for phase 2

Implementation:
- `spawn.py` — `_spawn_one` (preamble text, spawn.py:1620-1628; HEAD
  capture near 1659/1710; fail-closed downgrade logic near
  1731-1738/1739 before `ledger_write`).

Tests (existing coverage found in `test_spawn.py`, which already has a
`classify()`-focused test class — see spawn.py:459-524 in survey terms,
i.e. `test_spawn.py` tests named `test_progressed_on_delta`,
`test_waiting_on_human`, `test_refused_is_not_silent_failure`,
`test_progress_outranks_refusal`, `test_human_gate_outranks_refusal`,
`test_silent_failure_is_loud`, plus board-delta tests
`test_delta_shows_changed_and_new`, `test_no_board_is_empty`):
- `test_spawn.py` — new test(s) for the fail-closed downgrade (either as
  a `classify()`-level unit test if the downgrade is implemented as a
  pure function taking `(outcome, commits_happened, dirty)`, or as an
  integration-style test around `_spawn_one` if the downgrade is inlined
  — implementation phase decides which, per `## What will be done` below)
  and for the preamble-text addition (asserting the warning string is
  present in the assembled `task` for `issue is not None` calls).

No other files are expected to need changes; `wakes.py`, `ledger`
helpers, and CLI entry points (`main()`, `drive()`) are unaffected by
either requirement as scoped.
