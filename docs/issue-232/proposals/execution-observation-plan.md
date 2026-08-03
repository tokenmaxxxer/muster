---
subject: issue-232
role: execution-observation
phase: 1
---

# Execution-observation plan — issue-232, PR #233

files:
- `docs/issue-232/reports/execution-observation.md` (phase-2 output; this
  role's record, written as the first act of phase 2)

## Request

Judge, independently and from artifacts only, whether the `implementation`
role's merged PR #233 (commits `2dc6ba6` phase 1, `a670098` phase-2
delivery, `af92fce` phase-2 record; merged 2026-08-03T04:48:59Z as
`70f867f`) executed issue #232 soundly. The invoking prompt names four
items — (a) whether `test_spawn.py`'s new layer fixtures genuinely fail
against the pre-change code rather than being written to pass either way,
(b) whether the classification patterns rest only on the issue's own cited
real-session samples with no arbitrary extension, (c) whether the dedup-key
change (single boolean → per-layer/per-gate set) preserves the "보고 한 번"
contract, (d) whether `watch`'s block-then-report cycle is unchanged — and
instructs that the builder's own claims are not to be taken at face value,
and that nothing is to be fixed.

The current-state survey for this observation is
`docs/issue-232/reports/execution-observation/survey.md` (same branch, this
session); it records what was read, the pre-change baseline, the delivered
diff's contents, and the process-state facts, without evaluating any of
them.

## Which verdict levels will be checked, and against what evidence

All three levels required by this role's directive will be addressed. Where
a level does not apply, the record will say so explicitly with its reason
rather than omit it.

**1. Outcome — did PR #233 land what issue #232 asked.** Acceptance
criteria are the issue's own 요구사항 1-4 and its two 제약, each mapped to
named evidence:

| Issue clause | Evidence to be cited |
| --- | --- |
| 요구사항 1 (three-way layer split on reported refusals) | `a670098`'s `spawn.py` hunk `@@ -2559,7 +2617,11 @@` — the emitted event-type strings and the branch that selects them; `docs/issue-232/decisions/event-layer-taxonomy.md:15-30` |
| 요구사항 2 (gate identity + reason on a gate refusal) | `_classify_refusal_text`'s layer-1 return in the same hunk; `_GATE_HOOK_RE`/`_GATE_DENY_RE` in hunk `@@ -1482,6 +1482,64 @@`; `gate-lib.sh:78` (read directly this session) as the source of the `<gate>: refused — <reason>` shape |
| 요구사항 3 (reuse existing log evidence before adding instrumentation) | `docs/issue-232/reports/implementation/survey.md:89-149` (its evidence search, including the preserved-log check) against the delivered diff's actual inputs — whether anything added is in fact new instrumentation |
| 요구사항 4 (per-layer fixture regression test) | `a670098`'s `test_spawn.py` diff, case by case, against the issue body's literal sample strings |
| 제약 1 (`watch` block-then-report cycle untouched) | judgment item (d) below |
| 제약 2 (layer-2/3 *policy* out of scope) | the delivered diff's write set (`git show a670098 --stat`: `spawn.py`, `test_spawn.py`, one decision record) |

**2. Trajectory — was the phase-1 → phase-2 path sound.** Evidence: the
phase-1 artifacts committed in `2dc6ba6` before any code
(`docs/issue-232/reports/implementation/survey.md`,
`docs/issue-232/proposals/implementation.md`) and whether the survey
preceded and fed the proposal; the scout skip record at
`docs/issue-232/reports/implementation/survey.md:9-23` against the
scout-directive's two skip conditions; the approval path — issue comment
`APPROVE issue-232/implementation` by `jjongkwann` (MEMBER, listed in
`docs/specs/approvers.md`) at 2026-08-03T03:54:44Z, single-account mode
under contract v3 s19 — checked as a string-equality match and against the
authored timestamp of the first phase-2 commit `a670098`
(2026-08-03T04:11:50Z); and whether the delivered write set matches the
approved proposal's declared `files:`
(`docs/issue-232/proposals/implementation.md:9-12`) with no silent
additions or omissions.

**3. Step — which specific artifact, if any, is deficient.** The four named
items are the step-level docket; each is checked against the evidence named
here, and any finding carries the blameless four-part shape (impact,
timeline, root cause, action item), scaled to the single finding.

- **(a) Fixture strength.** Method: static composition, not execution. The
  pre-change baseline's only refusal-emitting branch is
  `2dc6ba6:spawn.py:2602-2607` (`type == "result"` → non-empty
  `permission_denials` → one `gate-refusal`), with no `type == "user"` /
  `tool_result` branch in that loop. Each new or changed case's fixture
  lines (read from `a670098`'s `test_spawn.py` diff) will be traced through
  that baseline branch to derive what the old code would have emitted, and
  compared with each case's assertions — including the one case that feeds
  no `result` line
  (`test_non_error_tool_result_matching_refusal_text_fires_nothing`). The
  record's own claim of "5 failed, 1 passed"
  (`docs/issue-232/reports/implementation.md:140-151`) will be treated as
  the observed role's assertion and checked against that derivation, never
  adopted as this role's evidence. Re-running the observed role's tests is
  prohibited for this role, and the record will state that limit where the
  derivation rests on reading rather than execution.
- **(b) Pattern provenance.** Each regex in `_HARNESS_REFUSAL_PATTERNS` and
  `_SANDBOX_REFUSAL_PATTERNS`, plus `_GATE_HOOK_RE`/`_GATE_DENY_RE`, will be
  matched one-to-one against the issue body's cited strings (§배경 items
  1-3), noting any pattern with no corresponding sample, any sample with no
  covering pattern, and any pattern broader than the sample it derives from
  (e.g. one regex spanning two distinct samples). The `refused —` half's
  non-issue source (`gate-lib.sh:78`) will be named as such.
- **(c) Dedup contract.** The delivered `refusals_seen` set, its four key
  shapes, the classification branch's skip-if-seen check, and the terminal
  `result` branch's `denials and not refusals_seen` guard will be compared
  against the contract as stated in
  `docs/issue-232/proposals/implementation.md:118-122` and
  `docs/issue-232/decisions/event-layer-taxonomy.md:54-61`, in both
  directions: whether a single cause can now report more than once, and
  whether a real denial can now go unreported (the case the record's hunt
  finding 1 dispositions at
  `docs/issue-232/reports/implementation.md:99-113`).
- **(d) `watch` cycle invariance.** `git show a670098 -- spawn.py`'s two
  hunk headers (`@@ -1482,6 +1482,64 @@`, `@@ -2559,7 +2617,11 @@`) will be
  checked against the line spans of `_await_bounded`
  (`2dc6ba6:spawn.py:1670-1713`) and `_watch`
  (`2dc6ba6:spawn.py:1716-1745`), together with whether those functions'
  read of `ev["type"]`/`ev["detail"]` is in fact type-agnostic for the four
  new type strings.

## Constraints on this observation

- No re-execution of the observed role's code — no `pytest`, no `spawn.py`
  invocation. Admissible evidence is the PR, its commits' diffs, the
  pre-change baseline they landed on, the observed role's own record, and
  externally-owned files read directly (`gate-lib.sh`). Where a check can
  only be settled by running something, the record will say so and state
  what the reading does and does not establish.
- No edit to any `implementation`-role path (`spawn.py`, `test_spawn.py`,
  `docs/issue-232/proposals/implementation.md`,
  `docs/issue-232/reports/implementation*`,
  `docs/issue-232/decisions/event-layer-taxonomy.md`). Findings return only
  through this role's own record on this role's own PR.
- No issue is filed by this role; a confirmed deficiency lands in the record
  with its evidence, for the human to judge.
- Every verdict-bearing sentence in the record names its source (commit SHA,
  `file:line`, or comment URL) directly adjacent to it, and the
  independence statement precedes any verdict language in the document.

## Out of scope

- Re-doing issue #232's implementation work, or proposing a fix for anything
  found — the invoking prompt states judgment only.
- The `watchdog_check_one` `_DENIAL_RE` anomaly signal (issue #90), which
  the observed role's proposal placed out of scope
  (`docs/issue-232/proposals/implementation.md:153-156`) and which the
  delivered diff does not touch.
- Issue #232's own process state (auto-close on PR #233's merge, human
  reopen 11 seconds later, the `## 실행 계획` checklist's missing step-2
  line) — recorded as facts in the survey; the issue itself attributes the
  auto-close defect to issue #228, a different subject.
- Any other role's or issue's PRs.

## How you'll know it worked

- `docs/issue-232/reports/execution-observation.md` exists on this branch,
  committed, written as the first act of phase 2, with `loop_state` updated
  at each transition.
- It addresses all three verdict levels explicitly — including any level
  that does not apply, stated as "not applicable, because X".
- Every verdict-bearing sentence carries an adjacent citation, and the
  independence statement appears before the first of them.
- Each of the four named items (a)-(d) is answered against the evidence
  named above, with the observed role's own claims checked rather than
  relayed, and each deficiency (if any) carries impact, timeline, root
  cause, and action item.
