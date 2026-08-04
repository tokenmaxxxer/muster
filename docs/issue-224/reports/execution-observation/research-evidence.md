---
subject: issue-224
role: execution-observation
observed_role: implementation
observed_pr: 255
code_under_review: c71faba05224f06cb3a10341c5ae3a8c720d487b
loop_state: phase-1-research
---

# Research evidence — issue #224, PR #255

Phase 1. Raw evidence pinned verbatim so phase-2 verdicts cite this
file's quotes rather than re-fetching. No verdict appears here.

## E1 — approval (issue-level, single-account mode)

https://github.com/tokenmaxxxer/on-the-record/issues/224#issuecomment-5166077886
— author `jjongkwann`, 2026-08-03T12:05:12Z. Entire body:

```
APPROVE issue-224/implementation
```

`gh pr view 255 --json reviews` returns an empty array — no PR-review
Approve exists on #255. PR #255's author is `jjongkwann`.
`docs/specs/approvers.md` lists exactly:

```
- JiwonJung94
- jjongkwann
```

## E2 — requester's three phase-2 feedback items

https://github.com/tokenmaxxxer/on-the-record/pull/255#issuecomment-5166078117
— author `jjongkwann`, 2026-08-03T12:05:14Z, verbatim:

> phase 2 반영 요청 (승인과 별도 피드백, 발주자 결정):
>
> 1. **pid 생존 확인의 정상-종료 오판 레이스.** 세션이 정상 종료해
>    session-end 를 이미 기록했는데 미소비 이벤트가 남아 있는 경우,
>    루프가 pid 사망을 먼저 판정하면 session-end 를 읽기 전에 비정상
>    종료로 잘못 보고할 수 있다. 이 레포의 선례 `session_end_verdict()`
>    (spawn.py:1190-1226) 가 정확히 이 레이스를 막기 위해 session-end
>    도착 여부를 `_alive()` 보다 먼저 본다 — 같은 순서(잔여 이벤트/
>    session-end 소진 → 그 다음 생존 판정)를 따르거나, 다른 설계라면
>    기록에 사유를 남겨라.
> 2. **비정상 종료 시 리턴할 종료 코드의 구체 값을 정하고 기록에
>    명시하라.** `_watch` 의 rc 는 CLI 종료 코드로 그대로 나간다
>    (spawn.py:2194) — 소비자(오케스트레이터) 해석에 영향이 있다.
> 3. 테스트 파일 위치(`test_flows.py` vs `test_spawn.py::FlowsPayload`)
>    를 확정해 기록에 남겨라.

## E3 — commits and PR metadata

| Item | Value | How obtained |
|---|---|---|
| PR | #255, `issue-224/implementation`, MERGED | `gh pr view 255` |
| PR opened | 2026-08-03T11:09:40Z | `gh pr list --state all` |
| PR merged | 2026-08-04T01:29:43Z, merge `d14d44da36aee4f2144c32e5929271eeaed34132` | `gh pr view 255 --json mergedAt,mergeCommit` |
| Phase-1 commit | `9eb1f71fa3f5e24f2bad9be96ed5fbb9c85bb242`, 2026-08-03T11:09:18Z, 3 files +523 | `gh pr view 255 --json commits`, `git show --stat` |
| Phase-2 commit | `c71faba05224f06cb3a10341c5ae3a8c720d487b`, 2026-08-03T12:35:25Z, 6 files | same |

`c71faba05 --numstat`:

```
56	0	docs/issue-224/decisions/watch-crash-exit-code.md
274	0	docs/issue-224/reports/implementation.md
7	2	gates/flows.py
55	3	spawn.py
14	0	test_flows.py
132	0	test_spawn.py
```

## E4 — the `--follow` crash predicate as committed

`c71faba05:spawn.py:1818-1848`, verbatim (comments elided where marked):

```python
        before = _read_offset(offset_path)
        rc = _await_bounded(events_path, offset_path, stall_timeout_min, log_path)
        after = _read_offset(offset_path)
        if after > before:
            lines = events_path.read_text(encoding="utf-8").splitlines()
            ev = json.loads(lines[after - 1])
            if ev.get("type") == "session-end":
                return rc
        # ... (PR #255 피드백 1: drain before liveness)
        if events_path.exists():
            lines = events_path.read_text(encoding="utf-8").splitlines()
            if any(json.loads(line).get("type") == "session-end"
                   for line in lines[after:]):
                continue
        # ... (wrapper_pid rationale)
        roster_entry = _roster_load().get(key) if key else None
        pid = roster_entry.get("wrapper_pid") if roster_entry else None
        if roster_entry is None or not pid or not _alive(pid):
            print(f"[watch] 세션 프로세스가 사라졌다(pid {pid}) — session-end "
                  f"없이 끝났다. 크래시로 보고 멈춘다", file=sys.stderr)
            return WATCH_CRASH_RC
```

`c71faba05:spawn.py:1783`:

```python
WATCH_CRASH_RC = 2
```

## E5 — roster and `session-end` lifetimes in `_spawn_one()`

All in the same function, `c71faba05:spawn.py`:

| Line | Statement |
|---|---|
| 2744 | `child_pid = os.fork()` — parent returns via `_await_bounded` at 2745-2748; the child continues |
| 2766 | `roster_register(roster_key, {` |
| 2767 | `"pid": proc.pid, ...` (the `claude` subprocess, `subprocess.Popen` at 2762-2765) |
| 2781 | `"wrapper_pid": os.getpid(),` |
| 2900 | `rc = proc.wait()` |
| 2901 | `roster_remove(roster_key)` |
| 3003 | `_append_event(events_path, "session-end", outcome)` |

Between 2901 and 3003 the function performs `board_snapshot`, `git
status --porcelain`, gate/ownership reporting, `classify` and
`ledger_write` (`c71faba05:spawn.py:2905-3002`).

## E6 — tests added by `c71faba05`

`test_spawn.py` (+132), five new tests in two classes:

```
class IssueComments(unittest.TestCase):
    def test_flattens_multi_page_slurp_response(self)
    def test_empty_slurp_response_yields_empty_list(self)
class WatchFollow(unittest.TestCase):   # existing class, setUp extended
    def test_follow_detects_dead_session_and_returns_crash_rc(self)
    def test_follow_prioritizes_pending_session_end_over_pid_check(self)
    def test_follow_tolerates_post_processing_tail_before_session_end(self)
```

`WatchFollow.setUp` gains, and
`test_follow_tolerates_post_processing_tail_before_session_end` repeats:

```python
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": os.getpid(), "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})
```

`test_flows.py` (+14), one new test:

```python
class PrListAllLimit(unittest.TestCase):
    def test_gh_pr_list_call_includes_limit_1000(self):
```

## E7 — the approved proposal's wording for defect 3

`docs/issue-224/proposals/query-watch-reliability.md:79-82`:

> `--follow` 루프가 매 반복 진입 시(`_await_bounded` 재호출 전) 로스터에서
> 같은 키(`issue-{issue}/{role}`)의 현재 pid 를 다시 조회해
> `_alive(pid)`를 확인 — 죽었으면(엔트리 부재 포함) 루프를 즉시 끝내고
> 0 이 아닌 코드로 리턴

## E8 — the record's own deviation statement

`docs/issue-224/reports/implementation.md:256-269`, abridged:

> One deviation from `## What will be done` … the proposal's item 3
> described the `--follow` pid check as reusing the existing roster
> `pid` field verbatim … Fixed by adding one new, purely additive roster
> field (`wrapper_pid`, set to `os.getpid()` at the same
> `roster_register()` call site) that stays alive for the whole
> `_spawn_one()` invocation, and pointing the liveness check at it
> instead of `pid`.

## E9 — documentary cross-check of the test baseline

`docs/issue-224/reports/implementation.md:99-105` reports `test_spawn`
at 184 tests / 41 errors and `test_flows` at 10 passed.
`docs/issue-223/reports/implementation.md:81-85` independently records
the same sandbox baseline at 179 tests / 41 errors, attributing all 41
to a pre-existing `rulebook_checkout()` git-template-copy failure.
179 + 5 new tests = 184. No suite was run by this session.
