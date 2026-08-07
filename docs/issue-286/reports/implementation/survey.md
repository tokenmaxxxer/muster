# issue-286 current-state survey

## Scope of the complaint

Ten defects (E1-E10 in the issue body, plus one added in a 2026-08-07 comment,
call it E11) in how `spawn.py` reconstructs a session's state from
`.events.jsonl`, `.events.offset`, `runs/active.json` and
`runs/workspaces.json`. All feed the orchestrator's routing decisions, so a
silent lie here propagates everywhere downstream.

## What exists today, per defect (reproduced by reading, not just re-quoting the issue)

- **E1 (lost cursor replays from 0)** — `_read_offset` (spawn.py:1973)
  returns `0` on `OSError`/`ValueError`. Still true. `_watch`'s bounded path
  (`_await_bounded`, :2019) calls `_read_offset` once per invocation with no
  spawn-time reset guard of its own — that guard (mentioned in the issue,
  ":2941"-era) lives only in the one-shot spawn path, not standalone
  `spawn.py watch`.
- **E2 (torn JSON line wedges watch forever)** — `_await_bounded` line 2039:
  `ev = json.loads(lines[seen])` has no try/except. A truncated line raises,
  the process dies before `_write_offset` runs, so the *next* invocation
  reads the same `seen` index and hits the same line. Still true.
- **E3 (torn session-end line -> crashed)** — `session_end_verdict`
  (:1339) parses every event line with `try/except ValueError: continue`
  (:1360-1364) — a malformed line is dropped silently, not counted. If the
  dropped line was the terminal `session-end`, `any(... session-end ...)`
  (:1374) is `False` and the function falls through to the `alive_fn`/mtime
  branch, which can return `crashed` for a session that in fact finished
  mid-write of its own last line. Still true — no warning, no count.
- **E4 (`progressed` false positive on stale PR)** — `classify` (:1313)
  returns `progressed` on any board hash delta, `blocked` is checked before
  git state, matching the issue. `fail_closed_downgrade` (:1387) already
  downgrades a `progressed` run with no new commit unless
  `already_delivered` is true. `already_delivered` (:3415-3420) is set from
  `_pr_for_branch(...) is not None`, and `_pr_for_branch` (:955) calls
  `gh pr list --head <branch> --state all --json number -q .[0].number` —
  `--state all` includes **closed** PRs. So a branch carrying a closed PR
  from an earlier phase (or an abandoned attempt) still marks the current
  no-commit, clean-tree run as `already_delivered` and lets `progressed`
  stand. Reproducible exactly as described.
- **E5 (`pr-opened` silently dropped)** — :3274-3293: `pr_number` is
  memoized once per session (`if pr_number is None: pr_number =
  _pr_for_branch(...)`). A transient `gh` failure makes `_pr_for_branch`
  return `None` (its own `except`-free `returncode != 0` check, :960), so
  `pr_number` stays `None` and the candidate URL is silently skipped with no
  event, no log line. Because `pr_number is None` is re-checked per
  candidate line, a *second* PR-URL line in the same session would retry —
  but if `gh pr create`'s output line is the only candidate (the normal
  case), there is exactly one attempt and no second chance. Still true, and
  nothing today distinguishes "no PR was opened" from "a PR was opened and
  the check to confirm it failed."
- **E6 (refusals batched, delivered only at session end)** — :3235-3350:
  refusal candidates are buffered into `pending_refusals` as they stream by,
  but only ever flushed (`_flush_correlated_refusals` / `_flush_unverified`)
  when the terminal `type: "result"` line is parsed (:3309-3324), which
  Claude Code's stream places last. So refusal events land in
  `.events.jsonl` only once the session is over — exactly the issue's
  complaint that a live watcher sees zero gate friction until then. This is
  a deliberate design from issue #235 (see the comment at :3242-3248): the
  terminal `permission_denials` list is the only place a denial is
  *confirmed*, so provisional emission was rejected earlier to avoid a
  false-positive layer label. E6 as filed is still an accurate description
  of current behavior.
- **E7 (refusals deduped by key, not by incident)** — :3336:
  `if key not in pending_refusals: pending_refusals[key] = ...`. `key` is
  `(layer, gate/detail, normalized-reason)` (finer than the issue's "message
  text" but still content-keyed, not incident-keyed) — a second refusal at
  the same gate with the same normalized reason text within one session
  never enters `pending_refusals` a second time, so it can never be flushed
  a second time. The repeat-refusal signal the issue calls "the single best
  signal a message failed to teach" is still erased.
- **E8 (truncation destroys the payload)** — :1734:
  `_append_event(events_path, "unclassified-refusal", str(denials)[:200])`
  — `str(denials)` on a list-of-dicts produces a Python `repr()`, sliced at
  200 chars with no regard for structure. Still exactly as filed.
- **E9 (unlocked cursor write)** — `_write_offset` (:2001) is a bare
  `offset_path.write_text(str(n))` — no lock, no compare-and-swap, in
  contrast to `ROSTER`'s `_roster_locked()` (:1426, flock-based). A second
  concurrent `watch` process can race this write. Still true.
- **E10 (roster keys are repo-blind)** — every roster/index key is built as
  `f"issue-{issue}/{role}"` with no repo qualifier:
  `_workspace_index_put` (:2015), `_watch` (:2083, :2086), `spawn.py`'s
  spawn-claim path (:2148), `_auto_respawn_check`'s caller (:3151: `f"issue-{issue}/{role}"`
  falling back to `f"adhoc/{role}/{os.getpid()}"` only when `issue is
  None`). `ROSTER`/`WORKSPACE_INDEX` are both single global files under
  `runs/` (`ROOT / "runs" / "active.json"`, `ROOT / "runs" /
  "workspaces.json"`) with no per-repo namespace in the path either. Two
  repos with the same issue number and role collide. Still true.
- **E11 (comment: vanished log reported as stall, not "cannot observe")** —
  partially addressed already. `_await_bounded` (:2058-2064) now checks
  `log_path.exists()` before declaring a stall and prints "cannot observe: 세션
  로그 파일이 없다" instead, returning 0 without reporting `stall`. This
  covers the *watch*-path half of the comment. It does **not** cover the
  ledger/workspaces-index cross-check the comment asks for ("must never
  report (b) [log gone] or (c) [already terminal in the ledger] as a
  stall") for the *watchdog* path: `_auto_respawn_check` /
  `session_end_verdict` still classify purely from `.events.jsonl` +
  `alive_fn`/mtime, with no cross-check against `runs/workspaces.json` or a
  ledger entry recording the session already ended. Given `session_end_verdict`
  itself has no `stalled`-vs-"log deleted" distinction (:1380: `if
  log_path is not None and log_path.exists(): ... elif silent -> stalled`;
  if `log_path` doesn't exist, the branch is skipped entirely and the
  function falls through to `"in-progress"` — not `stalled`, so watchdog's
  case is actually already fail-closed-to-in-progress, not
  fail-closed-to-stall, for a genuinely vanished log). The comment's
  concrete repro (issue-301) was in `watch`'s stall detector, which is
  fixed; no evidence the watchdog path shares the same bug today.

## Boundary with named sibling issues

- **#390** ("a PR's green attests to the state it was verified against, not
  the state it lands in") is about CI/merge-time re-establishment of a
  green check, not about event/cursor integrity. No overlap with #286's
  write set (`spawn.py`'s event/offset/roster machinery).
- **#358** ("role sessions survey a clone that excludes all operational
  state") is about `runs/` being gitignored so a role session's own clone
  cannot see it — a documentation/survey-honesty issue about *what a
  session can observe locally*, not about spawn.py's own internal
  correctness reading its own `runs/` tree at orchestrator time. No
  overlap. Per #358: `runs/` is confirmed gitignored (`.gitignore` in this
  repo lists `runs/`) and is genuinely absent from this session's clone —
  this survey's file/line citations above come from reading `spawn.py`
  itself, not from any `runs/*.json` file, none of which exist in this
  clone.
- **#310** ("acceptance must be an executable artifact") governs how this
  issue's own acceptance criteria get discharged — addressed directly in
  the proposal's "How you'll know it worked" section, not a scope
  boundary.
- **#363** ("a proposal must address the generator, not the symptom") —
  the generator common to E1/E2/E3/E9 is one thing: every read of
  `.events.jsonl`/`.events.offset` in `spawn.py` assumes the file is
  well-formed and fully written, because nothing in this codebase treats a
  killed session's last write as a first-class truncation case. The
  generator for E5/E6/E7/E8 is different: refusal/PR-open confirmation is
  designed around Claude Code's stream-order guarantee (terminal `result`
  line) being the only trustworthy correlation point, and nothing today
  separates "provisional, unconfirmed" from "confirmed" as two distinct
  event types the orchestrator can tell apart. E10's generator is that no
  roster/index key construction anywhere in `spawn.py` includes a repo
  identity. The proposal states explicitly, per defect, whether the fix
  removes that generator or patches the one reported instance.
- **#374/#325** (named in this session's invocation as the reason #286 was
  never spawned) are about spawn *coverage* (an issue filed with no session
  ever spawned for it) — a different mechanism from #286's event/cursor
  correctness. No write-set overlap; #325's own proposal
  (`docs/issue-325/proposals/2026-08-07-spawn-and-stall-coverage-gate.md`)
  already confirms this against #298/#288 and does not touch
  `_read_offset`/`_write_offset`/`classify`/refusal-flushing.

## What #310 requires here

Every acceptance line below must be an executable test against a real
function in `spawn.py`, not a docstring or a comment claiming the behavior
holds. `test_spawn.py` already tests `classify`, `session_end_verdict`,
`fail_closed_downgrade`, and the refusal-classification helpers directly
(see current file) — the fix continues that pattern: pure-function tests
first, subprocess/stream-level tests where the defect only reproduces at
that level (E2, E5, E6).

## Write set this survey supports

- `spawn.py` — the ten functions/call sites cited above:
  `_read_offset`, `_write_offset`, `_await_bounded`, `session_end_verdict`,
  `_pr_for_branch`/its call site building `already_delivered`, the
  pr-opened correlation block (:3274-3293), the refusal buffering/flush
  block (`pending_refusals`, `_flush_correlated_refusals`,
  `_flush_unverified`), `_flush_correlated_refusals`'s `unclassified-refusal`
  fallback, and every `f"issue-{issue}/{role}"` key-construction site plus
  `ROSTER`/`WORKSPACE_INDEX` path definitions.
- `test_spawn.py` — new/extended unit tests pinning each fixed behavior,
  following the existing direct-function-call style already used for
  `classify`/`session_end_verdict`/`fail_closed_downgrade` in this file.
