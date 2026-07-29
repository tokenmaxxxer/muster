# issue-44 — proposal: role-selection guide for orchestrate/commands/run.md

Phase 1 (research + survey + proposal) under role-handoff contract v3. **No implementation in
this PR** — `orchestrate/commands/run.md` is not edited here. Phase 2 (editing run.md with exactly
the text below, or an approver-revised version of it) is gated on a human `APPROVE
issue-44/coding` review comment per `docs/specs/approvers.md`, in a later session.

## files

Frozen write set for phase 2:

- `orchestrate/commands/run.md` — edited in place (insert the section under "What will be done"
  below; no other file needs to change to satisfy issue #44's acceptance criteria).

No new doc/board file is proposed — see "Constraints" below on why (feasibility report condition
1's generalized principle: no new mutable state competing with
`docs/issue-<n>/reports/<role>.md`).

## Request

Paraphrased from issue #44 ("orchestrate: role-selection guide — stop defaulting every request to
coding"): a real orchestration session routed nearly every request straight to `coding` (6x, vs.
`qa` 2x, `verify` 1x), never proposed `product`/`review`/`ux-design`/`reflect`/`ops`, and skipped
research-first work until the user manually asked "shouldn't we survey prior art first?" (which is
the origin of issue #43). The orchestrator's job is to *propose* that upstream judgment, not
shortcut it to request → issue → coding. The issue asks for four additions to the orchestrate
procedure:

(a) a classification obligation stated in conversation before drafting an issue — which role
leads (feasibility / product / ux-design / coding) and one line of reasoning;
(b) a request-type → leading-role mapping table, covering at least three named cases;
(c) an explicit rule that defaulting to coding without stating the classification is a procedure
violation;
(d) an obligation that wake's human-judgment lines (product/ops, "cannot be measured") be answered
with an explicit proposal each time they appear, not silently passed over.

## Constraints

- **Scope discipline**: implement exactly the four elements above; no additional scope (e.g. no
  new automation, no new role, no new file format for the classification record — it is stated in
  conversation, matching how run.md already handles other judgment calls).
- **No new ground truth / mutable state** (generalizing feasibility report condition 1, which
  required the issue-43 mission board to stay a read view over existing files, not compete with
  `docs/issue-<n>/reports/<role>.md`): the classification is spoken in the conversation each time,
  the same way step 2 of the current loop already requires the wake proposal to be one paragraph
  in conversation — it is not written to a new tracked file.
- **Integrate, not overwrite issue-43's eventual edit to the same file** (issue #44's own
  alignment note): issue-43's design issue (mission board / decision-queue batching / parking
  lot) has not yet landed in run.md as of this survey (`git log` shows the last edit is
  issue-34's `2253f9d`), so there is no live conflict, but the insertion point and numbering below
  are chosen to be a self-contained new step that a later mission-board/batching edit to the same
  "당신의 루프" section will not have to unwind.
- **Keep run.md's existing voice and language**: run.md is written in Korean with the established
  "절차 위반" (procedure violation) framing already used by issue-34's gate; the proposed insertion
  matches that voice/register rather than switching to English mid-document, for reviewability by
  the same procedure and consistency with issue-34's adjacent step 4 language.
- **Don't touch issue-34's step 4 gate or the preconditions section's "역할이 맞는가" check** —
  those already exist and are functioning; the new obligation is additive at loop steps 1-2, not a
  replacement.

## What will be done

Proposed replacement of loop steps 1-2 in `orchestrate/commands/run.md` (currently lines 17-23),
inserting a new classification step between issue-drafting and role-waking. Exact text to insert,
in the file's existing voice:

```markdown
1. **요구사항 → 이슈.** 사용자의 요구를 이슈 초안으로 정리해 보여주고,
   확인받은 것만 `gh issue create` 로 등록한다. 당신은 대필자다 — 사용자가
   말하지 않은 요구를 발명해 백로그에 넣지 않는다.
2. **이슈를 등록하기 전에 분류한다.** 어떤 역할이 이끄는지 — feasibility(조사
   먼저) / product(요구사항·수용기준 먼저) / ux-design(UX 판단) / coding(바로
   구현 정당) — 한 줄 근거와 함께 대화에서 명시적으로 말한다. 아래 표를
   참고하되, 표에 없는 요청은 표를 확장하지 말고 근거를 대화로 설명한다.
   **분류를 말하지 않고 coding 으로 기본값 처리하는 것은 절차 위반이다.**

   | 요청 유형 | 리드 역할 | 근거 |
   | --- | --- | --- |
   | "X 를 개선/최적화해줘" (원인·해결책 불명, 결함 위치 미확정) | feasibility | 손대기 전 조사 필요 — 이슈-43 이 이 케이스에서 나왔다 |
   | "정책/행동을 바꿔야 한다" (새 규칙, 새 계약 조항) | product | 요구사항·수용기준부터 확정 필요 |
   | 상호작용/화면·문구 등 사용자 경험 판단이 걸린 요청 | ux-design | 구현보다 UX 판단이 먼저 |
   | "이 위치의 결함을 고쳐줘" (위치·원인이 이미 특정됨) | coding | 바로 구현 정당 |

   product·ops 관련 요청인데 wake 가 "못 잰다"로 표시하는 판단 줄(아래 3번)이
   걸려 있다면, 이 분류도 그 판단에 근거해 명시적으로 제안한다 — 침묵 통과는
   허용되지 않는다.
3. **누구를 깨울지.** `python3 $MUSTER/spawn.py wake -C <레포>` 로 보드를
   읽고, WAKES-ON 이 지목하는 역할을 한 문단으로 제안한다. 기계로 판정
   불가한 줄(product·ops 의 내용 판단)은 "못 잰다"로 말한다 — "안 깨어났다"
   로 옮기지 마라. **이런 판단 줄이 나타날 때마다, 매번 구체적인 제안(어느
   역할을 왜 깨울지)을 함께 내야 한다 — "못 잰다"로 끝내고 넘어가는 것은
   절차 위반이다.**
```

(Steps 3 onward — "띄운다", "PR 을 설명한다", "사용자의 결정을 중계한다" — are renumbered +1 but
otherwise unchanged; not reproduced here since their text is untouched.)

Notes on the wording choices, for the approver:

- (a) is satisfied by new step 2's first paragraph + bold violation sentence.
- (b) is satisfied by the table; three rows directly reuse issue #44's own named examples
  ("improve/optimize X", "policy/behavior change", "fix this located defect"); a fourth row for
  `ux-design` is added since issue #44 names it explicitly as one of the four possible leads in
  (a) and a table with only 3 of the 4 possible leads would be incomplete. The table is
  deliberately small/open-ended ("표에 없는 요청은... 근거를 대화로 설명한다") rather than
  exhaustive, matching run.md's existing style of guiding judgment rather than fully mechanizing
  it (mirrors the "기계로 판정 불가한 줄" distinction already in the file).
- (c) is the bolded sentence in new step 2, mirroring issue-34's existing "절차 위반" sentence
  style in current step 4 for voice consistency.
- (d) is satisfied by the bolded addition to (renumbered) step 3, extending the existing "못 잰다"
  sentence so it can no longer be the end of the turn — a proposal must follow it every time.

## Out of scope

- Editing `orchestrate/commands/run.md` itself (phase 2, gated on approval).
- Any change to issue-34's step-4 approval-summary gate.
- Any change related to issue-43's mission board / decision-queue batching / parking lot — that
  design issue has not been filed yet and is explicitly a different mechanism (wait-time /
  drift-guarding / status-visibility), not role selection.
- Expanding the mapping table beyond the four rows above, or trying to enumerate every possible
  request type — run.md's existing style leaves genuine judgment calls to conversation, not to an
  exhaustive lookup table.
- Any new file, board, or automation to record the classification — it is spoken in conversation
  each time, per the "no new mutable state" constraint above.

## How we'll know it worked (review checklist)

- [ ] The approved run.md text contains, verbatim or as approver-revised, a step requiring the
  orchestrator to state which of feasibility/product/ux-design/coding leads, with one line of
  reasoning, before `gh issue create`.
- [ ] The approved text contains a request-type → leading-role table with at least the three rows
  issue #44 names by example ("improve/optimize X", "policy/behavior change",
  "fix this located defect").
- [ ] The approved text contains an explicit statement that defaulting to coding without stating
  the classification is a procedure violation.
- [ ] The approved text requires an explicit proposal every time wake's "cannot be measured"
  product/ops lines appear, not just a label.
- [ ] No new file, board, or mutable state is introduced — the change is confined to
  `orchestrate/commands/run.md`.
- [ ] The diff does not touch issue-34's existing step-4 gate text or the "역할이 맞는가"
  precondition check, and is structured so a future issue-43 design-issue edit to the same loop
  section can be integrated without unwinding this insertion.
