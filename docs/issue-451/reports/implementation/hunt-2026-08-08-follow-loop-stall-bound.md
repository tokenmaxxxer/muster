---
proposal: docs/issue-451/proposals/2026-08-08-follow-loop-stall-bound.md
note: board-gate blocked write to docs/issue-451/reports/2026-08-08-hunt-follow-loop-stall-bound.md
      ("belongs to another role" — implementation role writes only implementation.md,
      implementation/**), so this record is filed here instead.
---

# Hunt record — follow-loop-stall-bound

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the outer cumulative stall tracker never gets a chance to run when the log keeps changing without ever producing an offset-advancing event, because `_await_bounded()`'s own internal micro-stall loop resets its `last_change` on any log-size change and only returns to the caller once *its own* stall_limit_s has elapsed with *zero* log growth — so a single `_await_bounded()` call blocks forever (never returning) whenever the underlying process keeps writing non-event noise to the log at least once per stall interval, and the new outer `last_progress`/`stall_limit_s` check added in this diff is only ever evaluated between calls to `_await_bounded()`, i.e. it is dead code in exactly the "roster entry never appears, no session-end ever comes" scenario the diff's own comment and commit message target.
Kind: design-error
Seed: spawn.py new stall-tracking block in `_watch()` (spawn.py:2199-2251) plus rewritten test/test_silent_failure_repros.py::test_attempt_2_follow_loop_unbounded_on_absent_roster_entry
cap_seconds: 120
tier: default
diff_stat_lines: ~35
started_at: 2026-08-08T08:31:00Z
ended_at: 2026-08-08T08:33:45Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-451-implementation
python3 - <<'PY'
import sys, time, threading, pathlib
sys.path.insert(0, ".")
import spawn

tmp_path = pathlib.Path("/tmp/repro-stall")
tmp_path.mkdir(exist_ok=True)
spawn.WORKSPACE_INDEX = tmp_path / "workspaces.json"

work = tmp_path / "work"
log_path = tmp_path / "session.log"
log_path.write_text("hello\n")
spawn._workspace_index_put(99999, "probe", str(work), str(log_path))

spawn._roster_load = lambda: {}  # no roster entry ever, matching the diff's target scenario

stop = threading.Event()
def grower():
    i = 0
    while not stop.is_set():
        with open(log_path, "a") as f:
            f.write(f"noise {i}\n")
        i += 1
        time.sleep(0.02)  # faster than the stall bound below
t = threading.Thread(target=grower, daemon=True)
t.start()

STALL_S = 0.3
start = time.monotonic()
rc = spawn._watch(99999, "probe", STALL_S / 60, follow=True)
elapsed = time.monotonic() - start
stop.set()
print("rc=", rc, "elapsed=", elapsed)
PY
```

### Observed
Process runs past a 20-second `timeout` wrapper without ever returning (`EXIT:124`) even though the configured stall bound is 0.3 seconds — the new outer stall check (spawn.py:2244-2249) is never reached because control stays inside a single `_await_bounded()` call, whose own internal stall timer (spawn.py:2147-2149) keeps resetting on the log's continued growth.

### Expected
Per the diff's own comment ("반복에 걸친 무진전 누적 시간을 직접 잰다") and the proposal's stated goal, `_watch(follow=True)` should return within roughly `stall_timeout_min` of no *event* progress, regardless of unrelated log churn. Instead, any log activity that isn't an offset-advancing event (e.g. periodic non-event log lines from a hung wrapper) keeps `_await_bounded()` from ever returning, so the newly-added cumulative-stall safeguard is unreachable in that case — the loop is still effectively unbounded for the scenario the fix targets. The added regression test only covers a *static* log (no growth at all), so it does not catch this.
