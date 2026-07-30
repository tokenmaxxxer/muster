---
subject: issue-129
role: coding
phase: 1
---

# Build proposal — issue-129

files:
- `spawn.py`
- `test_spawn.py`

## Request (paraphrased intent)

Over half of watch's reported events during a 12-issue run were false
positives, in four confirmed shapes (see
`docs/issue-129/reports/coding/survey.md`): (1) an already-open/merged PR
re-reported as `pr-opened` on later spawns, (2) a normal `end_turn` result
misreported as `gate-refusal` because the detector regex-matches the JSON
key name `permission_denials` rather than its content, (3) unrelated
mid-session tool output (echoed source/file text containing "denied")
misreported as `gate-refusal` for the same reason, (4) a session with an
existing commit+PR from an earlier phase on the same branch labeled
`session-end: failed-no-commit` because the downgrade only checks *this*
session's own before→after HEAD delta. Fix each root cause; keep reporting
idempotent, gate-refusal accurate, and end labels honest, without
reintroducing unbounded blocking in `_await_bounded`.

## Constraints

- `classify()`'s precedence order and existing contract (rc/result/
  delta/blocked) stay untouched — `test_spawn.py`'s existing
  `classify()` cases must keep passing unmodified. Only
  `fail_closed_downgrade()` and its call site gain a new check.
- `_await_bounded` (already bounded per issue #114) is not touched —
  requirement (d), "watch returns within finite time," is already met by
  the existing stall-timeout design; this proposal only changes what
  gets written to `.events.jsonl`, not how `watch` reads it.
- No new dependency, no schema/migration, no `.env` surface.
- Events already appended to a workspace's existing `.events.jsonl` from
  before this fix ships are not retrofitted — only new appends are
  affected. `.events.jsonl` is append-only; this proposal doesn't rewrite
  history.

## What will be done

1. **Idempotent `pr-opened`** (fixes root cause 1): before appending a
   `pr-opened` event for a matched URL, load prior `pr-opened` details for
   this workspace from its own `.events.jsonl` (in addition to the
   in-process `pr_seen` set) and skip the append if that URL was already
   recorded. This makes dedup durable across process restarts within the
   same workspace, at zero network cost — no `gh pr view` call is added,
   since the *event itself* only needs to fire once per PR URL ever seen
   for this workspace, regardless of the PR's later merge state.
2. **Structural `gate-refusal` detection** (fixes root causes 2 and 3):
   move the check from a raw-text regex scan over every stdout line
   (spawn.py:2135-2137, before `json.loads`) to after the existing
   `json.loads(line)` parse (spawn.py:2138-2141). Only classify a line as
   a gate refusal when the parsed object is a `stream-json` entry whose
   *structure* indicates an actual tool-permission denial (e.g. a
   `tool_result`/`user`-type entry whose `is_error`/content shape matches
   Claude Code's own denial shape), never by substring-matching arbitrary
   text content (echoed file contents, JSON key names, OS-level
   filesystem messages). The terminal `result` event's own
   `permission_denials` list (already parsed at spawn.py:2142-2143)
   becomes the authoritative source for whether *any* denial occurred in
   the session — `gate_refusal_seen` is set from that list's non-emptiness
   at exit time instead of (or in addition to) an in-flight regex, so a
   session with zero real denials can never end up flagged.
3. **Honest `failed-no-commit`** (fixes root cause 4): before
   `fail_closed_downgrade()` downgrades a `progressed` outcome, check
   whether the branch already carries a commit ahead of the point this
   *specific* session started from — reuse `_is_new_commit` against the
   branch's most recent known-good state (not just this session's own
   `before_head`) and/or consult `_pr_for_branch` (spawn.py:796, already
   used for scope-approval, not yet threaded here) to see if a PR already
   exists for this branch. If either already holds, the outcome is not
   downgraded to `failed-no-commit` — a session that made no *new* changes
   on top of prior, already-delivered work is not a failure.
4. `test_spawn.py`: four new cases, one per root cause, built from literal
   fixtures drawn from the preserved `.events.jsonl`/`.session.log`
   evidence cited in the survey (issue-123's repeated PR #124 URL,
   issue-46/49's `end_turn` result misfire, issue-126's echoed-`spawn.py`-
   source misfire, issue-126's existing-PR-then-`failed-no-commit`
   sequence) — each asserting the fixed behavior no longer reproduces the
   false positive.

## Side-effect analysis (required)

- **Branch reuse (phase 1 then phase 2 on the same branch)** — this is the
  exact scenario that produced 3 of the 4 confirmed false positives. After
  the fix: `pr-opened` fires once for the branch's PR regardless of how
  many phase-2 spawns later echo its URL; `failed-no-commit` no longer
  fires for a phase-2 session that only reads/verifies without adding a
  new commit, because it can see the phase-1 commit/PR already on the
  branch. A genuine phase-2 regression (an actual missing commit despite
  real edits) still downgrades correctly, since the check is "does a
  known-good prior state already carry the required commit/PR," not "did
  this session try."
- **Concurrent flows (multiple issues/roles running at once)** — each
  workspace has its own `.events.jsonl`/`.events.offset` pair (keyed by
  workspace path, spawn.py:1372-1373), so the durable `pr_seen` lookup and
  the branch-state check are both scoped per-workspace; no cross-workspace
  interference. `_pr_for_branch`/prior-`pr-opened` reads are local file/
  git reads, not shared mutable state, so no new lock or race is
  introduced between concurrently running sessions.
- **GitHub API latency** — item 1 (idempotent `pr-opened`) makes zero new
  network calls (reads only the local `.events.jsonl`). Item 3's
  `_pr_for_branch` call is a `gh pr view`/API call already used elsewhere
  in this file for scope-approval, so it has the same latency/failure
  profile as existing code; if it fails or times out, the downgrade check
  falls back to today's before/after-HEAD-only comparison (fail toward
  the existing, already-shipped behavior, never toward a new blocking
  wait) — this keeps requirement (d) intact, since nothing in this
  proposal adds a network call inside `_await_bounded`'s wait loop itself.

## Out of scope

- `_await_bounded`/`_watch` themselves — already bounded (issue #114); no
  change proposed.
- The mid-run watchdog design in `docs/issue-90/proposals/coding-watchdog.md`
  (a separate, still-unimplemented observe-only feature) — this proposal
  only fixes the exit-time/per-line event producers in `_spawn_one`.
- Retrofitting already-written `.events.jsonl` history — append-only, not
  rewritten.
- Any change to `classify()`'s precedence order or its existing contract.

## How it'll be known to work

- `python3 -m pytest test_spawn.py` (or however the suite is invoked),
  new cases green, shown once before the phase-2 PR.
- Each new case reproduces one of the four preserved-log false positives
  verbatim as a fixture and asserts the fixed code path no longer
  misclassifies it — not a synthetic input invented independent of the
  evidence in the survey.
