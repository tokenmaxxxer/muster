---
code_under_review: 2808632
loop_state: landed
closed_checks:
  - name: proposal-text-fidelity-diff
    code_sha: 2808632
  - name: hunt-assume-broken
    code_sha: 2808632
---

# Implementation record — issue #236

Phase 2, executing the approved proposal
(`docs/issue-236/proposals/implementation.md`, approved via issue-level
comment `APPROVE issue-236/implementation`, single-account mode,
role-handoff contract v3, PR author and approver both jjongkwann).

## What was done

Added exactly one new bullet to `on-the-record/commands/run.md`, inside
step 5, as a sibling immediately after the existing "구조적 맥락 —
flow/stage/next" bullet (`2808632`):

- **링크 의무 — PR·이슈 언급.** PR/issue mentions in the orchestrator's
  own reply carry a clickable full URL, mandatory whenever the item is
  one the user is being asked to decide on (approve/accept/reject/close
  — explicitly stated to cover step 5's own 1단계/2단계 승인 요청,
  step 6's decision-queue block, and the mission board's
  `waiting-for-human-decision` group). A same-answer repeat mention of
  the same item may use just its number. Notation format is
  unconstrained (markdown link or bare URL, either is fine). Scope is
  the orchestration session's own reply text only — role-session PR
  bodies/records are out of scope.

Nothing else in `run.md` changed: `git show --stat 2808632` shows a
single file, 12 insertions, 0 deletions, one hunk.

## What will be done (from proposal)

Proposal's "What will be done" section specified the exact bullet text
and insertion point (after the "구조적 맥락" bullet's closing two lines,
before the `## 미션 보드 (Mission Board)` heading). Implemented
byte-for-byte identical to the proposal's planned block — confirmed via
`diff` between the proposal's fenced "New" excerpt and the committed
lines, empty. No additions, no omissions, no rewording. This record
implements the plan exactly as approved; there is no gap between what
was proposed and what landed.

## What did not work

None.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step ->
  N/A, none introduced.
- No library-or-format choice beyond what
  `docs/issue-236/proposals/implementation.md` already decided (format
  freedom — "표기 형식은 강제하지 않는다" — was the phase-1 proposal's
  own decision, not a new one made in phase 2) -> no new
  `docs/issue-236/decisions/` entry needed.
- No benchmark/investigation numbers produced in phase 2 -> no
  additional `docs/issue-236/reports/` entry beyond this record and the
  existing phase-1 `docs/issue-236/reports/implementation/survey.md`.

## Hunt

Stance: **assume-broken** (rotated — issue-229 used adversarial-self,
issue-222 composition-regression, issue-220/232 assume-incomplete-coverage,
issue-216/218 assume-broken; this session, like those, has no registered
`warrant-hunter` subagent type available, so `general-purpose` was
dispatched in its place with an explicit adversarial framing, matching
the issue-216/218/220/222/232 precedent). Dispatched in the foreground
against the committed diff (`2808632`) before delivery.

Findings:

1. **Text fidelity — clean.** Proposal's planned "New" block vs. the
   committed bullet: byte-for-byte identical (bold markers, em-dashes,
   line breaks all match).
2. **Diff scope — clean.** Single file, 12 insertions, 0 deletions, one
   hunk; all four pre-existing step-5 bullets untouched by construction
   (insertion-only diff).
3. **Cross-reference phrasing (PLAUSIBLE, not blocking).** The new
   bullet's parenthetical says "6번 스텝의 결정 대기 큐," but step 6
   itself only uses the term "결정 대기 항목," and "결정 큐" is the
   mission board's pre-existing term — the new bullet's phrase is a
   blend that appears nowhere else verbatim. This exact wording was
   already in the phase-1 proposal's planned text and was approved as
   written, so this is carried over from the approved plan rather than
   introduced during this execution. Left as-is.
4. **Indentation/list nesting — clean.** Top bullet `   - `, sub-bullets
   `     - `, matching the existing "구조적 맥락" bullet's pattern
   exactly. No trailing whitespace, no tabs.
5. **No gate coupling — clean.** `grep -rn "run\.md" on-the-record/hooks/*.sh`
   returns no hits, matching the proposal's stated expectation.
6. **Templates don't show a URL slot (PLAUSIBLE, not blocking).** Step
   5's single-item compact line (`[이슈 #<n>] <flow 요약> · <stage> →
   <next>`) and step 6's fixed decision-queue line (`1) [이슈 #<n1>]
   ...`) both keep a bare `[이슈 #<n>]` tag with no explicit URL slot;
   neither template was edited to show where the mandated link goes.
   This is the phase-1 proposal's own explicit, reviewed design choice
   — its "Out of scope" section states step 6's decision-queue bullet
   and the mission board's render-format bullets are deliberately *not*
   edited directly, covered instead by the new step-5 rule's
   cross-reference, specifically to keep the change to the issue's
   "문서 한 곳의 최소 수정" constraint. Editing the templates too would
   fall outside the approved proposal's write set and outside the
   issue's single-bullet/single-file constraint. Left as-is, consistent
   with the approved design.

Disposition: findings 3 and 6 are choices already made and approved in
the phase-1 proposal (its Rationale and Out-of-scope sections), carried
straight through to this execution — not something introduced fresh by
this phase-2 commit, and not fixed here, per the "single file, minimal
edit, do not change any existing rules" instruction governing this
delivery. No crash paths apply (this is a prose/markdown edit with no
execution surface); no gate-script coupling found.

## Verification run

`run.md` is a prompt document with no test harness (same as
issue-54/issue-229 precedent, and as the proposal's own "How you'll
know it worked" section states) — verification is direct text/diff
inspection, matching the proposal's 5-point checklist:

1. New bullet present, appended after "구조적 맥락 — flow/stage/next",
   nowhere else — confirmed (`git show 2808632`).
2. All four pre-existing step-5 bullets byte-for-byte unchanged —
   confirmed (insertion-only diff, 0 deletions).
3. New bullet's text states mandatory link for decision-pending items,
   number-only on same-answer repeat, notation format free, and the
   orchestration-only scope note — confirmed by direct read and by the
   hunt's text-fidelity diff against the proposal.
4. No file other than `run.md` in the diff — confirmed
   (`git show --stat 2808632`).
5. No gate script references `run.md` — confirmed
   (`grep -rn "run\.md" on-the-record/hooks/*.sh`, no hits, same as
   pre-change).

## Open findings

Hunt findings 3 and 6 above are documented, pre-approved scope
boundaries from `docs/issue-236/proposals/implementation.md` (its
Rationale and Out-of-scope sections), not blocking defects. No open
findings require resolution before delivery.

## Next steps

None for this issue. A future issue could resync
`on-the-record/hooks/directive.sh`'s "REPLY STRUCTURE" summary or edit
step 6's/the mission board's literal templates to show an explicit URL
slot, if a real session shows the cross-reference-only approach
under-communicating in practice — not proposed here, since the phase-1
proposal already considered and explicitly excluded both.

## Open-finding resolution path

No open findings require resolution; none outstanding.
