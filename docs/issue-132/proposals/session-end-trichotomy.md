# proposal: session-end 3분법 + crashed 한정 최대 2회 자동 재스폰 (issue #132)

files: (frozen write set for phase 2)
- `spawn.py` — new judgment (`session_end_verdict`), new `session-start`
  event emission, new persistent respawn-counter state, new
  `--auto-respawn` watchdog action, new issue-comment-on-cap helper.
- `runs/` (gitignored, no repo diff) — new `runs/respawn_state.json`
  alongside existing `runs/active.json`/`runs/watchdog_state.json`.
- test/ — unit tests for `session_end_verdict()` and the respawn-cap/comment
  logic (pure functions, fixture-driven — same style as existing
  `classify()`/`fail_closed_downgrade()` tests already in this repo).
- No new dependency, no new env var, no schema/migration.

## Request (paraphrased)

Silent-failure sessions (no result record) are currently indistinguishable
from a hung-but-alive session, and both require a human to open the log by
hand to decide what happened — 4 such incidents were manually triaged and
manually respawned. Replace ad-hoc triage with: a mechanical 3-way verdict
(normal / crashed / stalled), and a bounded, self-limiting auto-respawn that
only fires for `crashed`, caps at 2 attempts, and always leaves a visible
trail (issue comment) when it gives up.

## Constraints

- Auto-respawn must never bypass the approval gate — it only re-runs the
  *same* issue/role/prompt on the *same* branch a human already authorized
  by spawning it the first time; it creates no new authorization.
- Must not duplicate PRs/commits on respawn — must reuse issue-129's
  idempotent `pr-opened`/`_pr_for_branch` machinery rather than re-deriving
  it (see side-effects below).
- `stalled` is observation-only, matching the existing `roster_watchdog`
  contract (spawn.py:1348-1350 docstring: "아무 것도 고치거나 죽이지
  않는다") — the issue text scopes auto-action to `crashed` only ("crashed
  에 한해"); see scout-brief.md adopt/skip.
- The verdict must not depend on the transient `runs/active.json` roster
  surviving the crash (it is a fully-rewritten JSON file — `_roster_save`
  at spawn.py:1209 — not append-only, so it can itself be lost/corrupted by
  the same crash it's supposed to help diagnose).

## What will be done

1. **`session-start` event** — at the top of `_spawn_one`'s detached-child
   branch (spawn.py:2139, right after `roster_register`), append
   `{"type": "session-start", "detail": {"pid": proc.pid, "ts": ...}}` to
   `<work>.events.jsonl`. This is the durable, append-only record of "a
   process for this workspace existed" that survives even if the process
   dies before `roster_remove`/the terminal `session-end` event — the gap
   the current code has (confirmed in survey.md incident #2: two crashed
   runs left *zero* trace in events.jsonl because the crash landed between
   `roster_remove` and the terminal event append).
2. **`session_end_verdict(work) -> "normal" | "crashed" | "stalled" |
   "in-progress"`** (new pure function, next to `classify()`): read
   `events.jsonl` for the latest `session-start` not yet matched by a
   following `session-end`.
   - no unmatched `session-start` → `normal` (whatever `classify()` last
     said stands; nothing to auto-act on).
   - unmatched, and `_alive(pid)` is false → `crashed` — case (b).
   - unmatched, `_alive(pid)` true, log mtime silent past a threshold
     (reuse `WATCHDOG_SILENCE_MIN`, already 90min, already the repo's
     considered threshold for "too quiet") → `stalled` — case (c).
   - unmatched, alive, log not stale → `in-progress` (still legitimately
     working; not a verdict, just "too soon to tell").
3. **`--auto-respawn` flag on `spawn.py watchdog`** (default off — plain
   `watchdog` stays observe-only, per existing contract): for every
   workspace scanned, compute the verdict.
   - `crashed`: read/init the per-`issue-<n>/<role>` counter in
     `runs/respawn_state.json`. If attempts < 2: **claim first** — append a
     `respawn-attempt` event with `detail: {"session_start_ts": ...,
     "attempt": n}` to `events.jsonl` and bump-and-save the counter *before*
     spawning the child (single-writer race guard: re-read events.jsonl
     right before claiming via `_prior_event_details`-style check; if
     another `respawn-attempt` already exists for this same
     `session_start_ts`, skip — another watchdog process already claimed
     it). Then re-invoke `_spawn_one` with the **same** cwd/role/issue and
     the **original task text**, which must therefore also be persisted —
     write it once to `<work>.task.txt` at first spawn (spawn.py:2069-2070
     area) so a respawn (possibly from a different `spawn.py` process/host)
     can read it back verbatim.
   - `crashed` with attempts already at 2: **do not respawn.** Post exactly
     one issue comment (idempotency: check existing comments for a fixed
     marker string `[on-the-record] issue-<n>/<role>: crashed, 재스폰 상한(2) 도달`
     before posting, same pattern `_issue_comments`/idempotent-comment
     already used by `approve_scope`) describing the crash, the log path,
     and that a human must intervene. Then stop touching that workspace.
   - `stalled`: report only (existing `roster_watchdog` anomaly-print
     behavior), never auto-act — matches scout-brief's "skip" call.
4. Unit tests for `session_end_verdict` (fixture events.jsonl + fake
   `_alive`) and for the counter/claim/comment-idempotency logic
   (fixture `respawn_state.json` + fake `gh api` comment list), mirroring
   the existing test style for `classify`/`fail_closed_downgrade`.

## Out of scope

- Active heartbeat/liveness pings from inside the Claude session
  (WatchdogSec-style) — see scout-brief skip.
- Auto-respawning `stalled` sessions, or killing them automatically.
- Changing `classify()`'s own five outcomes, or `fail_closed_downgrade` —
  this proposal adds a parallel, orchestrator-level judgment layered on top
  of (not replacing) the existing per-session outcome.
- Cross-repo/cross-issue respawn scheduling policy (how often the
  orchestrator calls `watchdog --auto-respawn`) — that cadence is an
  operator/orchestrator decision, same as today's 10-15분 watchdog loop.

## Side effects: duplicate PR/commit risk from a misjudged respawn

- **Same workspace, same branch, reused**: `issue_workspace()`
  (spawn.py:1901) already fetches into the existing clone if the directory
  exists rather than re-cloning — a crashed-then-respawned session resumes
  on the exact branch the crashed one was building, including any
  uncommitted work it left behind (spawn.py:2200-2205 already prints this
  as an intended recovery path). Nothing new needed here.
- **Duplicate PR**: if the crashed session had already opened a PR before
  dying, the respawned session's own `pr-opened` detection re-scans the
  same branch/log space; issue-129's idempotent `pr-opened`
  (`_prior_event_details(events_path, "pr-opened")`, spawn.py:2154) and
  `_pr_for_branch` lookup already prevent a second PR for the same branch —
  this proposal deliberately reuses that machinery instead of re-deriving
  it, so the guarantee issue-129 landed keeps holding under auto-respawn.
- **Duplicate respawn from a race**: two concurrent `watchdog
  --auto-respawn` invocations (e.g. operator running it manually while a
  cron/loop also runs it) both observe the same `crashed` verdict before
  either claims it. Mitigated by the claim-before-spawn ordering in step 3
  above (append `respawn-attempt` event, re-read to detect a concurrent
  claim for the same `session_start_ts`, skip if found) — same
  append-and-recheck idempotency pattern issue-129 used for `pr-opened` and
  `gate-refusal`.
- **False-positive crash** (pid reported dead but the session actually
  finished normally in the split second between the scan's `_alive()` check
  and its `events.jsonl` read): mitigated by verdict order — check for an
  unmatched `session-start` *first*; if a matching `session-end` already
  landed, verdict is `normal` regardless of what `_alive()` says, so a
  benign race resolves to "no action," never a spurious respawn.
- **Cap-exceeded comment spam**: idempotency check against existing issue
  comments (marker string match, same read path as `_issue_comments`)
  before posting — a repeated watchdog scan after the cap is hit will not
  repost.

## How you'll know it worked

- Unit tests pass for `session_end_verdict` against fixture event logs
  reproducing all 3 survey incidents (silent-failure/normal,
  crashed/no-session-end, stalled/synthetic alive+stale-log case).
- A manual dry run: kill a spawned detached child mid-session (`kill -9` on
  its pid) and confirm `spawn.py watchdog --auto-respawn` classifies it
  `crashed`, respawns once, and on a second forced kill respawns a second
  time, and on a third forced kill posts exactly one issue comment and
  stops (no third respawn).
- Re-running `watchdog --auto-respawn` on an already-cap-exceeded workspace
  posts no second comment.
