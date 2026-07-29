# Issue #90 phase-1 survey: observable surfaces of an in-flight role session

Scope: read-only research into what an in-flight (still-running) role session
exposes today, so a future watchdog knows what it can poll. Sources:
`spawn.py` and `on-the-record/commands/run.md`. No behavior changed.

Prior-art framing carried from the issue: systemd `WatchdogSec` (process must
ping within a deadline or is presumed dead), CI no-output stall timeouts
(kill/report after N minutes of silent stdout), k8s liveness probes (repeated
per-signal checks, independent thresholds per signal type). All three are
multi-signal with per-signal thresholds, not one global timer — the same
shape this survey's "Signals visible today" section assumes.

## Surfaces

Every surface a spawned session touches while it is still running:

- **Live log file.** Path is `<workspace>.session.log` for issue-scoped spawns,
  or `runs/last-session.log` for ad-hoc ones (`spawn.py:1729-1730`). It is
  opened once per session (`spawn.py:1749`, `"w"` mode) and each stream-json
  line from the child's stdout is written and flushed immediately
  (`spawn.py:1750-1752`), so `mtime` and file size grow monotonically while
  the session is alive and freeze the instant it goes silent. `run.md:222-223`
  already tells the orchestrator this file's path and that it's the thing to
  tail "when the user asks."
- **Workspace / worktree layout.** `issue_workspace()` clones the target repo
  into an on-the-record-owned clone per (issue, role) pair
  (`spawn.py:1518-1527`); reused across respawns via fetch. The clone's
  filesystem path is exactly `log_path` minus the `.session.log` suffix
  (`spawn.py:1729`), so log and workspace are co-located and both known before
  the child process starts.
- **Role branch.** `checkout_issue_branch()` creates/checks out
  `issue-<n>/<role>` before the child ever starts (`spawn.py:1592-1612`), off
  the remote default branch. This branch is the git-state surface: `git log`,
  `git status --porcelain`, and `git rev-parse HEAD` against the workspace
  path all read live state on this specific branch while the session runs.
- **Ledger entries.** `runs/ledger.jsonl` (`spawn.py:1107-1115`) is
  **write-once per session, at exit only** — `ledger_write()` is called a
  single time, after `proc.wait()` returns (`spawn.py:1759-1820`). There is no
  ledger row, partial or otherwise, while a session is in flight; it has no
  in-flight analog.
- **PID / process handle.** `roster_register()` writes `runs/active.json`
  keyed by `issue-<n>/<role>` with `pid`, `role`, `issue`, a spawn-time `ts`
  epoch, `work` (workspace path) and `log` (log path) — written right after
  `Popen()`, before the task is even piped to stdin (`spawn.py:1735-1743`).
  It is removed on exit (`spawn.py:1760`, `roster_remove`). `_alive(pid)`
  (`spawn.py:1046-1051`) does a signal-0 kill check. `spawn.py ps`
  (`roster_ps`, `spawn.py:1066-1086`) surfaces `RUNNING`/`DEAD` state, elapsed
  minutes (`(now - ts) // 60`), pid, log path, and work path for every roster
  entry — this is the one command that already aggregates PID + elapsed time
  + log path + workspace path for a live session, and `run.md:221-223`
  already tells the orchestrator to check `spawn.py ps` instead of trusting
  "background task memory."
- **Board snapshot (file-hash diff).** `board_snapshot()` hashes every file
  under `docs/issue-*/` in the workspace (`spawn.py:951-968`); it is taken
  once before spawn and once after exit (`spawn.py:1717`, `1769`) to compute
  `delta`. It is a two-point diff, not a live poll target — no per-file
  timestamp is recorded, so re-running `board_snapshot()` mid-session would
  only show file-level cumulative diff, not *when* the last board write
  happened.
- **The task prompt's own warning text.** For issue-scoped spawns, the prompt
  handed to the child explicitly warns against background delegation:
  "이 턴은 headless 이고 단발이다 … run_in_background 로 넘긴 작업은 부모 턴이
  끝나는 순간 함께 죽는다" (`spawn.py:1683-1686`). This is a prevention
  instruction baked into the prompt, not a monitor — it does not detect the
  anomaly if the role session ignores it; it only lowers the prior probability.

### In-flight analogs of the issue-89 post-exit checks

Issue-89/PR-91 added post-exit fail-closed verification. Their in-flight
analogs, all computable against the *same* workspace path while the process
is still alive:

| post-exit check (spawn.py) | in-flight analog available today |
| --- | --- |
| `_git_head()` before/after (`spawn.py:921-926`) | `git -C <work> rev-parse HEAD` any time mid-run — same command, just polled early |
| `_is_new_commit()` ancestry check (`spawn.py:929-948`) | same `merge-base --is-ancestor` call, computable against the branch mid-run instead of only at exit |
| uncommitted-diff check via `git status --porcelain` (`spawn.py:1781-1783`) | identical command works mid-run; only its *meaning* differs (mid-run dirt is expected, not yet a violation) |
| `fail_closed_downgrade()`'s "no new commit" verdict (`spawn.py:1007-1028`) | cannot be replicated mid-run as a verdict — it depends on the session having *exited*; the in-flight analog is only the raw ingredient ("no new commit **yet**"), not the classification |
| `result.get("permission_denials")` from the final `result` stream-json event (`spawn.py:1002`, `1806`) | **not available mid-run** — see Gaps |

## Signals visible today

For each anomaly class named in the issue, where it would show up and with
what concrete check:

- **Log silent for N minutes.** `stat` on `<workspace>.session.log` /
  `runs/last-session.log` (path per `spawn.py:1729-1730`); compare `mtime` to
  `time.time()`. Because every stream-json line is flushed on arrival
  (`spawn.py:1750-1752`), `mtime` truly reflects "last tool-call/text event
  emitted," not a buffering artifact. Concrete check: `now - mtime(log_path) >
  N_minutes`. This is the direct analog of a CI no-output stall timeout.
- **"Delegating to background worker" phrasing.** Only visible by grepping
  the *content* of the live log for stream-json `text`/tool_use content
  blocks matching phrases like `run_in_background`, "백그라운드", "delegate",
  "background worker" — there is no structured field for this; it is a
  string-match over the same log file already being tailed for silence. The
  log already accumulates exactly the content that would contain this
  phrasing, since it is a full stream-json transcript, not a truncated tail.
- **Denied tool calls.** Two different granularities exist:
  - Per-event: individual `permission_denial`-shaped events appear inline in
    the stream-json transcript as they happen — visible today by scanning the
    live log for such lines as they're appended, same file as above.
  - Aggregate: `result.get("permission_denials")` (`spawn.py:1002`, `1806`,
    `1830-1833`) — the count used for the post-exit `refused` classification —
    is only populated on the final `result`-type event
    (`spawn.py:1757-1758`), i.e. **only after exit**. Concretely: `obj.get("type")
    == "result"` never fires mid-run, so this aggregate count cannot be
    reproduced live; only the raw per-event denials in the log can be counted
    by tailing.
- **No commits late in the run.** `git -C <workspace> log --oneline
  <base>..<branch>` (mirrors the `ensure_pushed` ahead-check pattern at
  `spawn.py:1628`) or `git rev-parse HEAD` compared against `before_head`
  (same value already captured at `spawn.py:1718` before the child starts).
  Concrete check: `elapsed_minutes > threshold AND git rev-list --count
  <before_head>..HEAD == 0` on the workspace path from the roster's `work`
  field. `elapsed_minutes` itself is already computed by `roster_ps()` as
  `(int(time.time()) - e["ts"]) // 60` (`spawn.py:1076`).

## Gaps

What is not observable today, and why:

- **No per-step or per-turn timestamps.** The log has one timestamp
  implicitly (file `mtime`, updated on every flushed line) but no timestamp
  *inside* each stream-json record — there's no way to say "the last tool
  call was 4 minutes ago vs. the last text token was 4 minutes ago" without
  external `stat` polling, and no way to distinguish "slow single tool call"
  from "actually stuck" from log content alone.
- **No structured progress markers.** The issue explicitly scopes this out
  ("structured heartbeat convention... a follow-up"), and the survey confirms
  why it would help: today's only sub-exit signal is raw stream-json content,
  which requires string/regex heuristics (for phrasing detection) rather than
  a typed field a watchdog could check directly.
- **`permission_denials` aggregate is exit-only.** As shown above, the count
  used by `classify()`/`fail_closed_downgrade()` lives solely in the final
  `result` event (`spawn.py:1757-1758`, `1806`); an in-flight watchdog can at
  best approximate it by counting denial-shaped lines itself, with no
  guarantee its counting logic matches what the final `result` event would
  report.
- **No mid-run classification hook.** `classify()` (`spawn.py:981-1004`) and
  `fail_closed_downgrade()` (`spawn.py:1007-1028`) are pure functions called
  exactly once, after `proc.wait()` (`spawn.py:1792`, `1796`). There is no
  seam today where a watchdog could invoke the same logic against
  in-progress state — it would need a parallel, weaker implementation, not a
  call into existing code.
- **`board_snapshot()` diffing is two-point, not continuous.** It hashes
  whole files before and after (`spawn.py:951-968`); polling it mid-run would
  show cumulative change since spawn, not "changed in the last N minutes" —
  useful for "board moved at all" but not for freshness.
- **The roster (`runs/active.json`) is best-effort, not authoritative for
  liveness beyond pid existence.** `_alive()` (`spawn.py:1046-1051`) only
  confirms the OS pid still exists; it cannot distinguish "actively working"
  from "hung waiting on a permission prompt that will never be answered in
  headless mode" — both look identically alive by signal-0.
- **No cross-process notification.** Nothing pushes state; every surface above
  requires the orchestrator to poll (log mtime, git state, roster file) —
  there is no equivalent of a systemd watchdog ping or k8s probe callback
  where the session itself reports "I'm alive."
