# Current-state survey — issue #247

Scope of this survey: what exists today in this repo (`on-the-record`) around
session-end classification and auto-respawn, and where the write set for a
phase-2 fix would actually land. Scout ran inside this survey (survey-first
order); see `scout-brief.md` in this same directory.

## The reported incident, replayed against this repo's current code

Issue #247's incident (repo-status-board issue #29 phase 2, 2026-08-03): a
headless coding-role session split work across two `Agent` calls, ended its
own turn narrating "I'll pick this up when the workers finish," and the
headless process then had nothing left in its main loop and exited — `rc=0`,
`result.is_error=False`. One worker's edit landed on disk uncommitted; the
other was mid-flight. No crash, no gate refusal — the process finished
normally in the sense `spawn.py` measures.

Tracing this repo's HEAD (`spawn.py`) through that exact sequence:

1. `classify(rc, result, delta, blocked)` (spawn.py:1165-1188): `rc=0`,
   `is_error` false, `delta` (git-tracked "board" file changes,
   `board_snapshot()` diff at spawn.py:2861-2863) empty since nothing in
   `docs/issue-*/reports/**` moved, `blocked` empty, no `permission_denials`
   → falls through to `"silent-failure"`.
2. spawn.py:2868-2874 separately computes `uncommitted` via
   `git status --porcelain` on the workspace — the worker's uncommitted edit
   shows up here even though `delta` (a different, git-tracked-content diff)
   missed it.
3. spawn.py:2884-2885: `if outcome == "silent-failure" and uncommitted:
   outcome = "uncommitted-work"` — this reclassification already exists and
   already correctly names the incident's shape. (If `delta` had been
   non-empty instead — e.g. a docs/record file *was* touched — the path
   would go through `fail_closed_downgrade()`, spawn.py:1239-1272, and land
   on `"failed-no-commit"` instead; both outcome strings describe the same
   underlying "abandoned mid-flight, no commit" condition, just reached via
   different branches depending on whether `delta` fired.)
4. spawn.py:2876-2880 already prints an operator-facing hint: respawning the
   *same issue* will resume into the *same workspace/branch*
   (`issue_workspace()`, which fetches into an existing clone rather than
   re-cloning) and can finish the commit from there. This is the "이어받기"
   (resume) path acceptance criterion 3 asks to be documented — it already
   exists in code, today, just not written down anywhere a human would read
   it up front, and not automatic.
5. spawn.py:2951: for a `bounded` + `issue is not None` run, a `session-end`
   event is unconditionally appended to `<work>.events.jsonl` right before
   the process exits, whatever the outcome was.

## Where the existing crashed/stalled/auto-respawn machinery sits, and why it doesn't reach this case

`session_end_verdict()` (spawn.py:1191-1236, issue #132) answers `normal` /
`crashed` / `stalled` / `in-progress` by reading `<work>.events.jsonl` for an
unmatched `session-start`. Because step 5 above *always* appends a matching
`session-end` for exactly this incident (the process didn't crash — it exited
through its own normal control flow), `session_end_verdict` returns `normal`
for this case. `_auto_respawn_check()` (spawn.py:1611-1678) only acts when
the verdict is `crashed` (checked at spawn.py:1624) and is only ever invoked
by `roster_watchdog()` for roster entries that are *still registered* despite
being dead (spawn.py:1456-1460, `if not _alive(...): _auto_respawn_check(...)`).

But `roster_remove(roster_key)` (spawn.py:2849) runs synchronously, inside
the same process, immediately after `proc.wait()` returns — for *this*
incident's normal exit, the roster entry is already gone by the time any
future `spawn.py watchdog` tick could run. There is no "dead-but-registered"
entry for the watchdog to ever find. The trichotomy and its auto-respawn
wiring are built entirely around *external* observation of a process the
caller lost track of (crashed, or gone quiet while nominally alive); this
incident's signal is the opposite — it is fully known *in-process*, in the
same function, in the same moments where `outcome` is computed
(spawn.py:2883-2912) — one call frame away from where
`_auto_respawn_check`'s reusable respawn logic (claim, attempt counter, cap
comment, spawn.py:1611-1678) already lives, but that logic is currently only
reachable from the watchdog's roster scan, not from `_spawn_one()` itself.

Separately, `watchdog_check_one()` (spawn.py:1369-1436, issue #90) already
has a live-session anomaly signal for exactly the delegate-then-wait
*phrasing* (`_DELEGATION_RE`, spawn.py:1352-1353, matching
`run_in_background|백그라운드|delegate|background worker` in newly-appended
log text) — but this only fires for roster entries the watchdog scans while
still `_alive()` (spawn.py:1461, called from the `for key, e in
sorted(d.items())` loop at spawn.py:1456 only on the *alive* branch). A
headless session that delegates and then has nothing left to do typically
exits within the same turn, before any 10-15 minute watchdog cadence
(protocol.md §7, `on-the-record/hooks/directive.sh:74-77`) would catch it
still alive and logging.

## Prior related work already merged to this branch's history (confirmed via `git show main:<path>` / `git log --all`)

- Issue #90: `watchdog_check_one` anomaly signals (log-silence,
  delegation-phrasing, denied-tool-calls, no-commits-late) — observe-only.
- Issue #132 (`c18b6e5`, `e222e2f`): `session_end_verdict` trichotomy,
  `RESPAWN_MAX_ATTEMPTS=2` capped auto-respawn scoped to `crashed` only,
  idempotent cap-comment (`_post_crash_comment`), `.respawn-claim-{ts}`
  atomic claim, `.task.txt` persistence of the original task text so a
  respawn (possibly a different process) can replay it verbatim.
- Issue #205: `fail_closed_downgrade` check-order fix
  (`progressed-dirty-tree` vs `failed-no-commit`), `.warrant-hunt.*`
  gitignored, `clean`'s sibling-delete directory guard.
- Issue #223: `.spawn-claim` — the same O_EXCL claim family extended to the
  *primary* spawn path (`_spawn_one()` itself), not just the respawn path,
  with fork-then-rewrite-pid handling for the bounded/detached child.

None of these four touch the specific gap above: an outcome computed
in-process, at normal exit, that never reaches any auto-respawn trigger
because the roster-based crashed/stalled detector was never built to look at
it.

## Where a "core"-side fix (role prompt/directive text) would actually live — and why it's not in this repo

The issue's own "추가 맥락" section asks this proposal to judge the split
between otr-side (this repo) and core-side (role prompt/contract) treatment.
`protocol.md:44-50` states plainly: "The role-handoff contract (v3) is the
authority here... It lives only in `core/contract/role-handoff-contract.md`
in `tokenmaxxxer-core` — repos carry no copy." Per-role directive text (the
`freelunch`/`scout`/`no-mock`/etc. hooks this very session was launched
under) ships from each role's own rulebook repo
(`roles/implementation.json:2-4`: `"repo":
"tokenmaxxxer/implementation-rulebook"`) — also not this repo. This repo
(`on-the-record`) contains only `spawn.py`/`protocol.md`/`roles/*.json` (the
orchestrator and its role-selection config) and
`on-the-record/hooks/directive.sh` (the *orchestrator* session's own prompt,
which already tells the orchestrator to always spawn role sessions in the
background and re-arm on `watchdog`/`watch` — a different delegation layer
than the one this issue is about: role-session-internal `Agent`/`Task` use).
Neither `tokenmaxxxer-core` nor `tokenmaxxxer/implementation-rulebook` is
checked out in this working tree, and this issue's branch/write scope
(`roles/implementation.json:18`, `write_scope: ["src/**", "test/**"]`,
matching the precedent of issues #132/#205/#223 which all touched
root-level `spawn.py`/`test_spawn.py` as this same role) has no path into
either external repo. A core-side prompt-text change is a decision for a
different repository's own issue, not something this branch can write.

## Write set this survey actually expects for a phase-2 fix (informs the proposal's frozen `files:` list)

- `spawn.py` — extend `_spawn_one()`'s end-of-run outcome handling
  (spawn.py:2883-2912 area) to trigger the same respawn-claim/attempt-cap/
  cap-comment logic `_auto_respawn_check()` already has, for a defined
  no-human-blocker "abandoned work" outcome set, instead of only printing
  the manual-resume hint.
- `test_spawn.py` — unit tests for the new self-triggered path, fixture-
  driven like the existing `AutoRespawnClaim`/`FailClosedDowngrade` classes.
- `docs/handbooks/operations.md` — currently has no section on
  crashed/stalled verdicts, auto-respawn, or manual workspace resume at all
  (confirmed: no hits for "재스폰"/"resume"/"watchdog"/"crashed" in this
  file before this issue). Acceptance criterion 3 needs this documented
  somewhere a human would read it; this handbook is the existing home for
  operational procedure in this repo (`setup.md` is install-time,
  `on-the-record.md` is the plugin's own description).
- No new dependency, env var, or migration.
- No change in this repo to role-prompt/directive text — that lives outside
  this repo per the section above; the proposal will record this as an
  explicit scope decision rather than leaving it implicit.

## Alternatives this survey found plausible (for the proposal's Rationale)

An alternative a reader could plausibly have picked instead of "self-trigger
inside `_spawn_one()`" genuinely exists in this codebase's own precedent:
extending `session_end_verdict()`'s trichotomy with a 4th value (e.g.
inspecting the `session-end` event's `detail` — which already *is* the
outcome string, spawn.py:2951 — instead of only checking presence/absence of
the event) and wiring `roster_watchdog()`/`_auto_respawn_check()` to act on
it, matching issue #132's existing shape exactly. This is a real fork in the
design space, not a strawman — it is the same file, the same authors' own
established pattern, and would have been the obvious next place to look
before tracing the roster-removal ordering. It is examined and rejected in
the proposal's Rationale.
