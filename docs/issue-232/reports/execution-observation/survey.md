# Survey — issue #232: execution-observation of PR #233 (`implementation` role)

## Scope

Observed: role `implementation`, subject `issue-232`, one PR — **PR #233**
(`issue-232/implementation` → `main`, state MERGED, merged
2026-08-03T04:48:59Z, merge commit `70f867f`, author `jjongkwann`, per
`gh pr view 233 --json number,title,headRefName,state,mergedAt,mergeCommit,author,commits,files`).
That PR carries all three of the observed role's commits:

- `2dc6ba6` — phase 1, survey + proposal (authored 2026-08-03T03:34:36Z).
- `a670098` — phase 2 delivery, `spawn.py` +87/-4, `test_spawn.py` +91/-6,
  `docs/issue-232/decisions/event-layer-taxonomy.md` +78 (authored
  2026-08-03T04:11:50Z).
- `af92fce` — phase 2 record, `docs/issue-232/reports/implementation.md`
  +171 (authored 2026-08-03T04:12:32Z).

Observing role: `execution-observation`, subject `issue-232`, branch
`issue-232/execution-observation`, this session, **phase 1**. The invoking
prompt names four judgment items, carried through this survey as (a)-(d):

- (a) whether `test_spawn.py`'s new layer fixtures actually fail against the
  pre-change code (i.e. whether all of them really collapsed into
  `gate-refusal`);
- (b) whether the classification patterns rest only on the issue's own cited
  real-session samples, with no arbitrary extension;
- (c) whether the dedup-key change (boolean → per-layer/per-gate set)
  preserves the "report once" contract;
- (d) whether `watch`'s block-then-report cycle is unchanged.

## Scout skip record (scout-directive)

Scouting is **skipped**. Skip condition: the spec leaves no design decision
open — this role's own directive fixes the deliverable's shape entirely
(three-level outcome/trajectory/step verdict, citation adjacency, blameless
four-part finding shape, record path
`docs/issue-232/reports/execution-observation.md`), and the invoking prompt
fixes the four judgment items (a)-(d) plus the acceptance criteria they are
judged against (issue #232's 요구사항 1-4 and its two 제약). This is
mechanical evidence-gathering against a fixed spec, not a design choice with
a field to benchmark. Same skip condition and same reason as this role's
precedent surveys `docs/issue-205/reports/execution-observation/survey.md`
§"Scope skip record" and `docs/issue-204/reports/execution-observation/survey.md`.

## What was read this session

- `gh issue view 232` (full body), `gh issue view 232 --json comments`,
  `gh api repos/tokenmaxxxer/on-the-record/issues/232/events` — the issue's
  three-layer requirement list (요구사항 1-4), its two 제약, its `## 실행 계획`
  checklist, both comments, and its close/reopen event pair.
- `gh pr view 233 --json number,title,headRefName,baseRefName,state,mergedAt,mergeCommit,author,commits,files`
  — PR #233's metadata, all three commit oids with their authored dates and
  full messages, and its six-file change set.
- `git show a670098 -- spawn.py` and `git show a670098 -- test_spawn.py` —
  the phase-2 delivery diff in full (both hunks of `spawn.py`, all of
  `test_spawn.py`'s added/changed cases).
- `git show a670098 --stat`, `git show af92fce --stat` — write sets.
- `docs/issue-232/reports/implementation.md` (the observed role's own phase-2
  record, `af92fce`, read in full, 171 lines).
- `docs/issue-232/proposals/implementation.md` (the approved phase-1
  proposal, `2dc6ba6`, read in full, 169 lines).
- `docs/issue-232/reports/implementation/survey.md` (the observed role's
  phase-1 survey, `2dc6ba6`, read in full, 196 lines).
- `docs/issue-232/decisions/event-layer-taxonomy.md` (`a670098`, read in
  full, 78 lines).
- `git show 2dc6ba6:spawn.py` at lines `1670-1713` (`_await_bounded`),
  `1716-1751` (`_watch`), and `2588-2615` (the per-line stream-json loop's
  `result`-branch) — the **pre-change** baseline the delivery landed on.
- `/Users/jk/.claude/plugins/marketplaces/tokenmaxxxer-core/core/hooks/lib/gate-lib.sh:78`
  — `gate_deny`'s literal output format, read directly (external plugin, not
  this repo's source).
- `docs/specs/approvers.md` — approver accounts `JiwonJung94`, `jjongkwann`.
- `gh pr list --state all --limit 12` — no PR exists on
  `issue-232/execution-observation`; `git log --oneline -15` — this branch
  carries no commit of its own beyond `main`'s `70f867f`.
- `docs/issue-205/reports/execution-observation/survey.md` — read for this
  role's established phase-1 format and skip-record precedent only.

## Current-state facts, mapped to the four judgment items

Read statically. No code under observation was executed this session (see
§Prohibitions honored).

**(a) Pre-change behavior of the new fixtures.** The baseline per-line loop
(`2dc6ba6:spawn.py:2602-2607`) has exactly one refusal-emitting branch:

```python
if obj.get("type") == "result":
    result = obj
    denials = result.get("permission_denials") or []
    if issue is not None and not gate_refusal_seen and denials:
        gate_refusal_seen = True
        _append_event(events_path, "gate-refusal", str(denials)[:200])
```

There is no `type == "user"` / `tool_result` branch anywhere in that
baseline loop (the adjacent `elif` at `2dc6ba6:spawn.py:2608` handles
`type == "assistant"` only). The fixture line composition of each new or
changed case is recorded from `git show a670098 -- test_spawn.py`:
`test_gate_hook_denial_is_gate_refusal_with_gate_name`,
`test_harness_permission_denial_is_not_labeled_gate_refusal` (5 subTests),
`test_sandbox_denial_is_not_labeled_gate_refusal` (2 subTests),
`test_denials_with_no_correlating_tool_result_are_unclassified`, and
`ProgressEvents::test_refusal_parsing_still_works_alongside_progress` each
feed a terminal `result` line carrying a non-empty `permission_denials`;
`test_non_error_tool_result_matching_refusal_text_fires_nothing` feeds a
single `tool_result` line and **no** `result` line. The observed role's
record claims a stash-and-rerun repro against the prior code produced
"5 failed, 1 passed"
(`docs/issue-232/reports/implementation.md:140-151`). Phase 2 will decide
this item by static composition of baseline branch × fixture input, since
re-running the observed role's code is prohibited for this role; the
record's own run is treated as the role's claim, not as this role's
evidence.

**(b) Pattern provenance.** The delivered patterns
(`git show a670098 -- spawn.py`, module level, inserted at `spawn.py:1485-1500`
in the new numbering) are:

- `_GATE_HOOK_RE = PreToolUse:\S+ hook error: \[([^\]]*)\]`;
  `_GATE_DENY_RE = (\S+):\s*refused\s*—`.
- `_HARNESS_REFUSAL_PATTERNS`: `Permission to use \S+ has been denied`,
  `requires approval`, `cannot be statically analyzed`, `simple_expansion`
  — four regexes against the issue's five cited layer-2 samples.
- `_SANDBOX_REFUSAL_PATTERNS`: `Operation not permitted`,
  `haven't granted it yet` — two regexes against the issue's two cited
  layer-3 samples.

Issue #232's own layer-2 sample list (issue body, §배경 item 2) is:
`Permission to use Bash has been denied`; `This Bash command contains
multiple operations. The following part requires approval: ...`; `This
command requires approval`; `Contains shell syntax (string) that cannot be
statically analyzed`; `Contains simple_expansion`. Its layer-3 list (item 3)
is: `mkdir: /tmp/...: Operation not permitted`; `Claude requested
permissions to write to ..., but you haven't granted it yet`. Its layer-1
sample (item 1) is `PreToolUse:Bash hook error: [.../board-gate.sh]`. The
`refused —` half of the layer-1 signature is not from the issue body: it
comes from `gate-lib.sh`'s `gate_deny`, cited by the observed role's survey
(`docs/issue-232/reports/implementation/survey.md:113-125`) and confirmed
independently this session by direct read —
`gate-lib.sh:78` is `echo "${1:-gate}: refused — $2" >&2`. Whether one
regex covering two distinct issue samples (`requires approval`) counts as
arbitrary extension or as faithful coverage, and whether the
`gate-lib.sh`-sourced half is within "the issue's real samples," is the
phase-2 judgment this survey does not render.

**(c) Dedup-key change.** Baseline: one `gate_refusal_seen: bool`
(`2dc6ba6:spawn.py:2605-2606`), so at most **one** refusal event per session
regardless of denial count or cause. Delivered (`a670098`): `refusals_seen:
set` keyed `("gate", <gate-name>)` / `("harness",)` / `("sandbox",)` /
`("unclassified",)`, with the classification branch skipping any key already
in the set, and the terminal `result` branch guarded by `denials and not
refusals_seen` (i.e. the `unclassified-refusal` fallback fires only if
nothing at all classified this session). The stated contract is "each
distinct layer (and, for gate refusals, each distinct gate) reports at most
once per session — preserving the existing 'report once, not once per
denial' behavior" (`docs/issue-232/decisions/event-layer-taxonomy.md:54-61`,
identical wording in `docs/issue-232/proposals/implementation.md:118-122`).
A per-session event count therefore moves from ≤1 to ≤(1 per distinct gate +
1 harness + 1 sandbox), or exactly 1 `unclassified-refusal` when nothing
correlates. The observed role's own hunt finding 1
(`docs/issue-232/reports/implementation.md:99-113`) records the converse
case — a second, unmatched denial in a session that already classified one
produces no event at all — and dispositions it as an approved scope boundary
of proposal step 5. Phase 2 will judge both directions against the "보고 한
번" contract as the issue and the approved proposal state it.

**(d) `watch`'s block-then-report cycle.** Baseline `_await_bounded`
(`2dc6ba6:spawn.py:1670-1713`) returns on the first unconsumed
`.events.jsonl` line, printing `f"[watch] {ev['type']}: {ev['detail']}"`
(`2dc6ba6:spawn.py:1691`) and branching on the event type only to
distinguish `session-end`; `_watch` (`2dc6ba6:spawn.py:1716-1745`) looks up
the workspace and delegates to it. `git show a670098 -- spawn.py` contains
exactly two hunks, headed `@@ -1482,6 +1482,64 @@` and `@@ -2559,7 +2617,11 @@`
— neither covers `1670-1751`. The proposal declared the same boundary
(`docs/issue-232/proposals/implementation.md:38-41`, §Out of scope
`:151-153`), and the decision record states consumers need no change
(`docs/issue-232/decisions/event-layer-taxonomy.md:63-67`). Phase 2 will
confirm the hunk boundaries and whether type-agnostic consumption in fact
makes the new type strings surface unchanged.

## Process-state facts (not evaluated here)

- Approval: issue-level comment whose entire body is `APPROVE
  issue-232/implementation`, author `jjongkwann`, association MEMBER, posted
  2026-08-03T03:54:44Z
  (https://github.com/tokenmaxxxer/on-the-record/issues/232#issuecomment-5162113858).
  `docs/specs/approvers.md` lists `jjongkwann`. PR #233's author is also
  `jjongkwann` — single-account mode per contract v3 s19. The phase-2
  delivery commit `a670098` is authored 2026-08-03T04:11:50Z, ~17 minutes
  after that comment.
- PR #233's title reads "issue-232: phase 1 — layer-classify watch's
  tool-refusal events" while the PR carries the phase-2 commits `a670098`
  and `af92fce` (per `gh pr view 233 --json title,commits`).
- Issue #232 was closed 2026-08-03T04:49:00Z (actor `jjongkwann`, no
  `commit_id`) and reopened 11 seconds later at 04:49:11Z with the comment
  "reopen: 실행 계획 step 2(execution-observation)가 미완인 채 PR #233 머지의
  closing 키워드로 자동 종결됐다 — issue #228 이 고치는 결함의 6번째 실물 사례"
  (https://github.com/tokenmaxxxer/on-the-record/issues/232#issuecomment-5162415521).
- The issue body's `## 실행 계획` checklist contains a single line,
  `- [ ] step 1  implementation` — unchecked, and with no step-2 line, while
  the reopen comment above names step 2 as `execution-observation`. Recorded
  as a process-state fact; the invoking prompt is this session's authority
  for its own scope.
- `docs/issue-232/reports/implementation.md`'s frontmatter carries
  `code_under_review: a670098` and `loop_state: phase-2-complete`, with three
  `closed_checks` entries all citing `code_sha: a670098` — the same SHA as
  the delivery commit those checks exercise.

## Candidates surfaced while reading, not evaluated

- The `unclassified-refusal` fallback's guard is `denials and not
  refusals_seen` (session-wide), so its interaction with a partially
  classified session is the observed role's own hunt finding 1, already
  dispositioned in its record (`docs/issue-232/reports/implementation.md:99-113`).
  Noted as read; whether that disposition is sound is a phase-2 step-level
  item.
- `_HARNESS_REFUSAL_PATTERNS`' `requires approval` and
  `_SANDBOX_REFUSAL_PATTERNS`' `Operation not permitted` are generic
  substrings; the record names this as hunt finding 2 and disposes of it as
  an approved tradeoff (`docs/issue-232/reports/implementation.md:114-122`).
  Noted as read, not evaluated here.
- Classification order in `_classify_refusal_text` is gate → harness →
  sandbox, first match wins; a text carrying signatures of two layers would
  resolve to the earlier one. Read from the delivered diff, not evaluated.

## Prohibitions honored

No code under observation was executed this session — `spawn.py` and
`test_spawn.py` were read only as `git show a670098` diff text and as
`git show 2dc6ba6:spawn.py` baseline text, never run, and no test suite was
invoked. Nothing under `spawn.py`, `test_spawn.py`, or
`docs/issue-232/{proposals,reports,decisions}/` belonging to the
`implementation` role was written or edited this session or on this branch;
this session writes only under
`docs/issue-232/reports/execution-observation/` and
`docs/issue-232/proposals/execution-observation-plan.md`.
