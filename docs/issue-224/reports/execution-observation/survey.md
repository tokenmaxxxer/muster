---
subject: issue-224
role: execution-observation
observed_role: implementation
observed_pr: 255
code_under_review: c71faba05224f06cb3a10341c5ae3a8c720d487b
loop_state: phase-1-survey
---

# Current-state survey — issue #224, PR #255 (`implementation` role)

Phase 1. This document records only what exists and what was read this
session, plus what is not yet known. It renders no verdict: the three
verdict levels are declared in the accompanying proposal
(`docs/issue-224/proposals/execution-observation-plan.md`) and rendered
only in phase 2, after approval.

## Scope under observation

- **Issue**: #224 — "조회·감시 신뢰성 3건 — 승인 코멘트 30개 한계, `gh
  pr list --limit` 부재, watch 크래시 세션 무한 루프", OPEN, author
  `jjongkwann`. Its `## 실행 계획` has exactly two steps: step 1
  `implementation`, step 2 `execution-observation` (this role).
- **Observed role**: `implementation`, branch `issue-224/implementation`.
- **Observed session's PR**: **#255** — "issue-224: phase 1 --
  query/watch reliability fixes (proposal)", authored by `jjongkwann`,
  created 2026-08-03T11:09:40Z, MERGED 2026-08-04T01:29:43Z as merge
  commit `d14d44da36aee4f2144c32e5929271eeaed34132`.
- **Observed commits** (both read this session):
  - `9eb1f71fa3f5e24f2bad9be96ed5fbb9c85bb242`, committed
    2026-08-03T11:09:18Z — phase 1: survey + scout brief + proposal,
    3 files / +523 lines, no code.
  - `c71faba05224f06cb3a10341c5ae3a8c720d487b`, committed
    2026-08-03T12:35:25Z — phase 2 delivery, 6 files:
    `docs/issue-224/decisions/watch-crash-exit-code.md` (+56),
    `docs/issue-224/reports/implementation.md` (+274),
    `gates/flows.py` (+7/-2), `spawn.py` (+55/-3),
    `test_flows.py` (+14), `test_spawn.py` (+132).
- **Session that is NOT under observation**: this one. Nothing this
  session produces touches the observed role's write set.

## What was read this session

Admissible evidence only — the observed role's produced artifacts, the
issue/PR record, and this repo's own standing specs. No test suite was
run, `spawn.py` was never invoked, and no part of the observed task was
re-executed.

1. Issue #224 body and its `## 실행 계획` (`gh issue view 224`).
2. Issue #224's only comment:
   https://github.com/tokenmaxxxer/on-the-record/issues/224#issuecomment-5166077886
   — author `jjongkwann`, 2026-08-03T12:05:12Z, body exactly `APPROVE
   issue-224/implementation`.
3. PR #255 body and metadata (`gh pr view 255`), including its
   `reviews` array, which is **empty** — PR #255 carries no PR-review
   Approve.
4. PR #255's only comment:
   https://github.com/tokenmaxxxer/on-the-record/pull/255#issuecomment-5166078117
   — author `jjongkwann`, 2026-08-03T12:05:14Z, three numbered
   phase-2 feedback items, explicitly labelled "승인과 별도 피드백".
5. `docs/specs/approvers.md` — two entries, `JiwonJung94` and
   `jjongkwann` (line 2).
6. Full diff of both observed commits (`git show 9eb1f71fa --stat`,
   `git show c71faba05 -- spawn.py`, `-- gates/flows.py test_flows.py`,
   `-- test_spawn.py`).
7. The observed role's own phase-1 artifacts at `9eb1f71fa`:
   `docs/issue-224/proposals/query-watch-reliability.md`,
   `docs/issue-224/reports/implementation/scout-brief.md` (head +
   `Sources:` block).
8. The observed role's own phase-2 record,
   `docs/issue-224/reports/implementation.md` (274 lines, read in
   full), and `docs/issue-224/decisions/watch-crash-exit-code.md`
   (56 lines, read in full).
9. The tree of `spawn.py` **as committed at `c71faba05`** (not the
   working-tree file), for call-site context around the changed
   hunks — addressed by commit SHA throughout this document.
10. `docs/issue-223/reports/implementation.md:81-85` — an
    independently-committed, prior record used as a documentary
    cross-check of the "41 pre-existing sandbox errors" baseline.

## Timeline as recorded

| When (UTC) | Event | Source |
|---|---|---|
| 2026-08-03T11:09:18Z | phase-1 commit `9eb1f71fa` | commit metadata |
| 2026-08-03T11:09:40Z | PR #255 opened | `gh pr view 255` |
| 2026-08-03T12:05:12Z | `APPROVE issue-224/implementation` | issue comment 5166077886 |
| 2026-08-03T12:05:14Z | 3 phase-2 feedback items | PR comment 5166078117 |
| 2026-08-03T12:35:25Z | phase-2 commit `c71faba05` | commit metadata |
| 2026-08-04T01:29:43Z | PR #255 merged as `d14d44da` | `gh pr view 255` |

## Write surfaces the observed change touched

### S1 — comment pagination (`spawn.py::_issue_comments`)

At `c71faba05:spawn.py:830-857` the `gh api
repos/<slug>/issues/<n>/comments` call gains `--paginate --slurp`, and
a flatten step `data = [c for page in data for c in page]` is inserted
after `json.loads` and before the existing login/body dict conversion.
The `except ValueError: return []` fallback is unchanged. The
phase-1 proposal's item 1
(`docs/issue-224/proposals/query-watch-reliability.md:117-120`)
prescribes exactly this.

Tests: `test_spawn.py::IssueComments`, 2 new tests —
`test_flattens_multi_page_slurp_response` (asserts the flattened
2-element result and `--paginate`/`--slurp` in the constructed
command) and `test_empty_slurp_response_yields_empty_list` (`[[]]` →
`[]`).

Known unknown: both tests stub `subprocess.run`; the shape assumption
(`--paginate --slurp` yields a list-of-lists, and `[[]]` for zero
comments) is asserted by the record
(`docs/issue-224/reports/implementation.md:228-230`, hunt finding 4) as
verified against real `gh` output on an external repo, but that
verification is not itself in the diff.

### S2 — PR list limit (`gates/flows.py::_pr_list_all`)

At `c71faba05:gates/flows.py:44-58` the `gh pr list` argv gains
`"--limit", "1000"` after the `--json` argument, matching the sibling
`_issue_list_all()` idiom, with a docstring note naming issue #224.
Test: `test_flows.py::PrListAllLimit::test_gh_pr_list_call_includes_limit_1000`,
which mocks `flows.subprocess.run` and asserts `--limit` is present and
its following element is `"1000"`.

### S3 — `--follow` dead-session detection (`spawn.py::_watch`)

At `c71faba05:spawn.py`:

- `:1783` — new module constant `WATCH_CRASH_RC = 2`.
- `:1789-1800` — the no-`--role` multi-match branch now retains the
  resolved workspace-index key in a local `key`.
- `:1832-1836` — drain check: if any unconsumed line past the current
  offset is a `session-end`, `continue` (skip the liveness check this
  iteration).
- `:1843-1848` — liveness check:
  `roster_entry = _roster_load().get(key) if key else None`;
  `pid = roster_entry.get("wrapper_pid") if roster_entry else None`;
  `if roster_entry is None or not pid or not _alive(pid): ... return
  WATCH_CRASH_RC`.
- `:2781` — `_spawn_one()`'s `roster_register()` payload gains
  `"wrapper_pid": os.getpid()`. `"pid"` (the `claude` subprocess pid at
  `:2767`) is unchanged.

Tests: `test_spawn.py::WatchFollow` `setUp` now registers a roster entry
with `wrapper_pid: os.getpid()`, plus 3 new tests —
`test_follow_detects_dead_session_and_returns_crash_rc`,
`test_follow_prioritizes_pending_session_end_over_pid_check`,
`test_follow_tolerates_post_processing_tail_before_session_end`.

## Neutral observations recorded for phase 2

These are statements of what the artifacts contain. None of them is a
verdict; each is listed with the citation a phase-2 verdict would have
to address.

- **O1 — approval path.** Issue #224 comment 5166077886's entire body is
  the exact string `APPROVE issue-224/implementation`, author
  `jjongkwann`, who is listed at `docs/specs/approvers.md:2`. PR #255's
  author is the same account and its `reviews` array is empty. The
  phase-2 commit `c71faba05` is dated 30 minutes after that comment.
- **O2 — feedback item 2 (exit code).** `WATCH_CRASH_RC = 2` exists at
  `c71faba05:spawn.py:1783`, and
  `docs/issue-224/decisions/watch-crash-exit-code.md:10-56` records the
  value, the meanings of `0`/`1`/`2`, and two rejected alternatives.
- **O3 — feedback item 3 (test placement).** The new `_pr_list_all`
  test lands in `test_flows.py::PrListAllLimit`
  (`c71faba05:test_flows.py:58-69`), and
  `docs/issue-224/reports/implementation.md:73-83` states the choice and
  its reasoning against `test_spawn.py::FlowsPayload`.
- **O4 — feedback item 1 (drain before liveness).** The drain check at
  `c71faba05:spawn.py:1832-1836` textually precedes the liveness check
  at `:1843-1848`, and the inline comment at `:1826-1831` cites PR #255
  feedback 1 and `session_end_verdict()`.
- **O5 — where `wrapper_pid` is written.** `os.fork()` is at
  `c71faba05:spawn.py:2744`; the parent returns at `:2745-2748` and the
  child continues. `roster_register(...)` at `:2766-2782` — including
  `"wrapper_pid": os.getpid()` at `:2781` — therefore executes in the
  fork-child on the bounded+issue path.
- **O6 — roster lifetime vs `session-end` lifetime.** In the same
  function, `rc = proc.wait()` is at `c71faba05:spawn.py:2900` and
  `roster_remove(roster_key)` at `:2901`; `_append_event(events_path,
  "session-end", outcome)` is at `:3003`, after `board_snapshot`,
  `git status --porcelain`, gate/ownership reporting, `classify` and
  `ledger_write`. Between `:2901` and `:3003` the roster entry for
  `roster_key` is absent while the fork-child recorded in
  `wrapper_pid` is still running.
- **O7 — what the liveness predicate reads first.** The predicate at
  `c71faba05:spawn.py:1845` is a three-term disjunction whose first
  term, `roster_entry is None`, is evaluated without reference to
  `wrapper_pid`.
- **O8 — what the tail-window regression test sets up.**
  `test_follow_tolerates_post_processing_tail_before_session_end`
  (`c71faba05:test_spawn.py`, added block) begins by calling
  `spawn.roster_register("issue-180/implementation", {..., "wrapper_pid":
  os.getpid(), ...})` — i.e. it exercises the window with the roster
  entry **present**.
- **O9 — deviation and its recorded justification.** `wrapper_pid` is
  not in the approved proposal; the proposal's item 3
  (`docs/issue-224/proposals/query-watch-reliability.md:79-85`,
  `:124-132`) prescribes re-reading "로스터에서 같은 키의 현재 pid".
  `docs/issue-224/reports/implementation.md:254-274` ("Rationale for
  deviations") states the deviation, its trigger (the mandatory
  pre-completion hunt), its scope containment (same frozen file,
  additive field, `roster_kill()`/`flows_payload()` untouched), and
  `:127-147` ("What did not work") states the first cut and its
  reproduction.
- **O10 — record's own test count.**
  `docs/issue-224/reports/implementation.md:89` says "4 new tests" for
  `WatchFollow` and then names three; the diff of
  `c71faba05:test_spawn.py` adds exactly three `WatchFollow` tests plus
  two `IssueComments` tests (5 total), consistent with the record's
  reported suite growth from issue-223's 179
  (`docs/issue-223/reports/implementation.md:81`) to 184
  (`docs/issue-224/reports/implementation.md:99`).
- **O11 — verification claim not re-executable here.**
  `docs/issue-224/reports/implementation.md:99-105` reports "184 tests,
  41 errors" for `test_spawn` and "10 passed" for `test_flows`. The 41
  sandbox-baseline errors are corroborated documentarily by
  `docs/issue-223/reports/implementation.md:81-85`. Re-running is
  prohibited for this role, so the claim is treated as documentary.
- **O12 — self-declared open findings.**
  `docs/issue-224/reports/implementation.md:149-177` records two
  findings left unfixed (unguarded `json.loads` in the new drain check;
  unlocked `_roster_load()`), each mapped to the phase-1 proposal's
  Rationale alternative 5 as out of the frozen write set.
- **O13 — scope judgments carried from phase 1.** The proposal
  (`docs/issue-224/proposals/query-watch-reliability.md:87-113`,
  `:150-163`) rejects the issue's two "same-family" candidates and the
  "watch returns on every event" observation, which issue #224 itself
  delegates to the proposal ("제안이 판단", "제안이 비용을 보고 판단").

## Unknowns entering phase 2

1. Whether O6 + O7 + O8 taken together mean the tail window is closed,
   partially closed, or unchanged by the `wrapper_pid` design — this
   requires reading the disjunction's first term against the roster's
   actual lifetime, and is the single largest open question. **Not
   answered in this document.**
2. Whether the drain check at `:1832-1836` covers the same window, i.e.
   whether a `session-end` is on disk at any point between `:2901` and
   `:3003`.
3. Whether any consumer of `_watch`'s exit code exists in-repo today
   that would observe `WATCH_CRASH_RC`, and what it does with `2`.
4. Whether the phase-1 proposal's "How you'll know it worked" manual
   check (`:180-184`, a real >30-comment thread) was performed or
   explicitly waived.

## Scout gaps this survey hands to the sweep

The survey found the following surfaces thin or contested, and the
scout sweep aims at exactly these:

- G1 — prior art on **liveness registries whose entry is removed before
  the final "done" record is written**: how do supervisors and job
  runners avoid reading "registry entry gone" as "crashed"?
- G2 — what strong reviews of watchdog / follow-mode termination changes
  check, specifically the failure mode "the regression test constructs a
  state the production code cannot reach".
- G3 — `gh api --paginate --slurp` semantics and known pitfalls, to know
  what an audit of S1 should look at beyond the mock.
- G4 — exit-code conventions for follow/watch CLIs, against which O2's
  choice of `2` can be situated.
