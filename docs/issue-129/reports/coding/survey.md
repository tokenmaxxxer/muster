---
subject: issue-129
role: coding
phase: 1
---

# Current-state survey — issue-129

## Scout skip record

Skipped. This is an internal event-detection bugfix inside `spawn.py`'s own
orchestrator code — there is no external product category to benchmark
against; the relevant field is this repo's own event pipeline and its
preserved logs, which this survey covers directly.

## Where the event pipeline lives

Single file: `spawn.py`. No separate "watch" binary/module exists anywhere
on the filesystem (checked other issue worktrees, `~/.claude/`, site-packages
— every other "watch*" hit is an unrelated third-party package).

- `.events.jsonl` / `.events.offset` sidecar files, one pair per workspace,
  written by `_append_event`/`_read_offset`/`_write_offset`
  (spawn.py:1380-1394).
- `_await_bounded` (spawn.py:1411-1446) — blocks until one new
  `.events.jsonl` line appears or a stall timeout elapses; already bounded
  (issue #114 fix) and not implicated in the false-positive reports.
- `_watch` (spawn.py:1449-1464) — CLI entry point, looks up the workspace in
  `runs/workspaces.json`, calls `_await_bounded`.
- The actual event *producers* — the part responsible for the false
  positives — live inside `_spawn_one`'s per-stdout-line scan loop
  (spawn.py:2124-2143) and its exit-time block (spawn.py:2149-2227).
- `classify()` (spawn.py:1139-1162) and `fail_closed_downgrade()`
  (spawn.py:1165-1186) decide the `outcome` string recorded as the
  `session-end` event's detail.

## Confirmed root causes (code + preserved-log evidence)

Preserved `.events.jsonl`/`.session.log` pairs checked: issue-120 (PR
#121/#122), issue-123 (PR #124/#125), core issue-46 (PR #47/#48), core
issue-49 (PR #50/#51), issue-126 (PR #127/#128).

**1. `pr-opened` re-reported for an already-open/merged PR.** `pr_seen =
set()` (spawn.py:2124) is local to one `_spawn_one()` call — it dedupes a PR
URL only within a single process's stdout stream, never persisted, never
checked against `.events.jsonl` history, never checked against GitHub's
actual state (no `gh pr view --json state/merged` call anywhere in this
path). `on-the-record-issue-123-coding.events.jsonl` shows PR #124's URL
reported 3 times across 3 separate spawns 148-210s apart; the same pattern
recurs for PR #50 in `tokenmaxxxer-core-issue-49-coding.events.jsonl`. Any
later session that merely echoes the URL (status check, `gh pr view`,
re-reading the PR body) re-fires `pr-opened` because dedup resets every
process.

**2. Normal `end_turn` misreported as `gate-refusal`.**
`_DENIAL_RE = re.compile(r"permission_denial|denied", re.IGNORECASE)`
(spawn.py:1253) is applied at spawn.py:2135-2137 against **raw stdout text**
before any `json.loads`/type check. The terminal `result` event's own JSON
serialization contains the key name `"permission_denials":[]` — the regex
matches that key-name substring regardless of the list being empty.
`on-the-record-issue-123-coding.events.jsonl` ts 1785397053 records a
`gate-refusal` whose `detail` is the full `result` object with
`"stop_reason":"end_turn"`, `"is_error":false`; identical shape recurs in
core issue-46/issue-49 events at ts 1785385555, 1785397062/314/327.

**3. Mid-session tool output misreported as `gate-refusal`.** Same
root cause as #2 — the regex scans every raw line unconditionally, with no
distinction between an actual denial-shaped transcript entry and any other
tool output that happens to contain "denied" as data.
`on-the-record-issue-126-coding.events.jsonl` ts 1785398909 records a
`gate-refusal` whose `detail` is an `Edit` tool_result echoing
`spawn.py`'s own pre-edit source — because that session's task was editing
`spawn.py` itself, and the tool_result payload contains the line
`_DENIAL_RE = re.compile(r"permission_denial|denied", ...)`. (A fourth,
previously unenumerated match kind was also found:
`on-the-record-issue-120-coding.events.jsonl` ts 1785384041 catches an
OS-level `ugrep: ... Permission denied` filesystem message, unrelated to
Claude Code's tool-permission gating — the same over-broad regex conflates
it too.)

**4. `session-end: failed-no-commit` for a session that already has a
commit+PR from an earlier phase on the same branch.**
`fail_closed_downgrade()` (spawn.py:1165-1186) forces
`outcome = "failed-no-commit"` whenever `outcome == "progressed"`,
`blocked` is empty, and `new_commit` is False. `new_commit` comes from
`_is_new_commit(cwd, before_head, after_head)` (spawn.py:1087-1106, called
at spawn.py:2180) where `before_head` is captured fresh at the top of
*this* `_spawn_one()` call (spawn.py:2071) — it only asks "did *this*
session add a commit on top of *its own* start point," with no memory of
commits made by an earlier phase on the same branch and no check of
whether a PR already exists for the branch (`_pr_for_branch`,
spawn.py:796, exists but is only wired into scope-approval, never
consulted here). `on-the-record-issue-126-coding.events.jsonl` shows PR
#127 reported at ts 1785398505, then `session-end: failed-no-commit` at ts
1785398645 (140s later, same workspace) — and again after PR #128 appears
at ts 1785399116, `session-end: failed-no-commit` at ts 1785399121.

## Intended design vs. actual behavior

`docs/issue-90/proposals/coding-watchdog.md` (referenced at spawn.py:1247-
1250) describes a separate, observe-only mid-run watchdog with its own
denial-count signal, explicitly treating the exit-time
`result.get("permission_denials")` aggregate as a different concept from
any in-flight string scan. The shipped `_spawn_one` code conflates the two:
it regex-matches the literal field name `permission_denials`, not a
denial-shaped line. No ADR exists specifically for the
`pr-opened`/`gate-refusal`/`session-end` event contract — the issue-90
proposal is the closest design record, and it does not cover this event
path at all.

`test_spawn.py` (~line 38) already documents a known, opposite-direction
gap: a session can look externally successful while `permission_denials`
silently records failures. The bug found here is the flip side — the
*field name* gets mistaken for a denial regardless of its content.

## Write set implied by the four confirmed root causes

- `spawn.py` — `_spawn_one`'s per-line scan loop (spawn.py:2124-2143):
  replace the raw-text `_DENIAL_RE` scan with a structural check on parsed
  JSON (only classify an actual denial-shaped entry, never a key name or
  echoed source text); make `pr_seen` persistent across a workspace's
  history (read prior `pr-opened` details from `.events.jsonl` before
  emitting) or otherwise dedupe against durably-recorded state.
- `spawn.py` — `fail_closed_downgrade()`/its call site (spawn.py:1165-1186,
  2180-2181): account for a PR/commit already existing on the branch from
  an earlier phase before downgrading to `failed-no-commit`.
- `test_spawn.py` — new cases reproducing each of the four false-positive
  shapes from the preserved logs (fed as literal fixtures), asserting the
  fixed classification.

No `.env`, dependency, or schema/migration surface is touched — pure
event-classification bugfix inside existing `spawn.py` functions.
