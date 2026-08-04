---
role: implementation
subject: issue-258
loop_state: scope-proposed
---

files: `on-the-record/commands/run.md`

Survey: [[survey.md]](../reports/implementation/survey.md).

## Request

The orchestrator has access to the user's personal skills (43 skills:
market-recon, fmea, requirements-quality, ...) but the orchestration
procedure never invokes them, so tasks reach role sessions as plain prose
that loses the rigor those skills encode. Amend the orchestration procedure
so the orchestrator itself invokes the applicable skills — via the real
`Skill` tool, never by reading skill files as plain text — and folds their
procedural demands (required steps, evidence standards, stopping criteria,
deliverable structure) into the issue's requirements/acceptance criteria
before drafting it. Role sessions keep their rulebook-only isolation
unchanged; which skills apply to a given piece of work is the orchestrator's
own per-task judgment, drawn from the full pool available to the user.

## Constraints

- No skill injection into role sessions — `spawn.py`'s skill surface, and
  each `roles/<role>.json` catalog, stay untouched (issue #258 decision 1,
  confirmed unaffected by survey).
- Skill invocation happens through the real `Skill` tool mechanism (loading
  the skill's instructions into the orchestrator's own session), never by
  the orchestrator reading a skill's `SKILL.md` as plain text and
  paraphrasing it.
- Skill invocation shapes the issue's *requirements*; it must not produce
  the deliverable itself — that stays role work, preserving the existing
  "orchestrator drafts, roles execute" boundary (`run.md`'s "당신은
  대필자다" framing in step 1, and the "하지 않는 것" section's "역할 세션의
  PR 을 대신 고치지 않는다").
- Which skills apply is the orchestrator's per-task judgment (issue #258
  decision 4) — no fixed mapping table from request-type to skill, unlike
  the existing role-classification table in step 2 (deliberately: the
  skill pool is large and open-ended, a request-type role table is
  small and closed).
- The role-handoff contract (`core/contract/role-handoff-contract.md`) is
  out of this repo's reach (confirmed in survey: it lives in
  `tokenmaxxxer-core`, no copy exists here). This proposal is scoped to
  `on-the-record/commands/run.md` only, the one file this repo owns for
  issue drafting.

## Rationale

**Chosen: amend `run.md` step 1 with an inline skill-assessment sub-step,
modeled on step 2's existing classify-and-state-rationale shape.**

- **Rejected alternative — a new standalone step ("step 1.5") dedicated to
  skill assessment.** The file's own step 2 already establishes the
  convention for this shape of judgment: assess against a set (there, the
  four-role table; here, the skill pool), state the judgment explicitly in
  conversation with reasoning, and only then proceed to `gh issue create`.
  Rejected because introducing a new top-level step for every new judgment
  axis makes the loop grow unboundedly as more per-task judgments get added
  over time, and splits a single conceptual unit ("turn the user's request
  into a well-formed issue") across two steps for no procedural benefit —
  step 2's role classification also happens "before registering the issue"
  and lives inside step 1's neighborhood conceptually, not as a separate
  numbered step. Folding into step 1 keeps the loop at its current 6
  top-level steps and matches the file's established pattern.
- **Rejected alternative — also edit the role-handoff contract's
  issue-drafting language, since issue #258 says "wherever issue drafting
  is specified."** Rejected because the contract lives in a different
  repo (`tokenmaxxxer-core`) that this session has no branch, no PR path,
  and no mandate into — role-handoff contract changes are that repo's own
  subject. Confirmed on disk in the survey: no copy of
  `role-handoff-contract.md` exists in this repo or on this branch.
  Attempting the edit here would mean writing to a file this repo cannot
  merge into its own board, and would silently claim contract authority
  this repo's `protocol.md` explicitly disclaims ("It lives only in
  `core/contract/role-handoff-contract.md`... repos carry no copy"). The
  cross-repo change is noted below as a follow-up rather than attempted.
- **Rejected alternative — a fixed request-type → skill mapping table**,
  mirroring step 2's role-classification table. Rejected because issue
  #258 decision 4 states skill applicability is the orchestrator's
  per-task judgment over the full pool ("everything available to the
  user"), not a small closed set like the four leading roles — a fixed
  table would either omit most of the 43 skills or become unmaintainably
  large, and would misrepresent an open-ended judgment call as a lookup.

## What will be done

Insert a new sub-step into `on-the-record/commands/run.md` step 1
("요구사항 → 이슈"), between the existing "이슈 초안으로 정리해 보여주고"
sentence and the "이슈를 등록하기 전에 분류한다" (step-2 role
classification) content, so the ordering inside the loop becomes: draft →
assess & invoke skills → classify lead role → confirm → `gh issue create`.
The inserted text (Korean, matching the file's existing language and
directive style):

> **스킬 평가 — 이슈 등록 전.** 이슈 초안을 보여주기 전에, 그 요청에 적용될
> 사용자 스킬이 있는지 판단한다. 판단은 매 이슈마다 하는 것이지, 정해진
> 매핑표를 찾는 것이 아니다 — 어떤 스킬이 적용되는지는 오케스트레이터의
> 그때그때 판단이다. 적용된다고 판단한 스킬은 반드시 `Skill` 도구로
> **실제로 호출**한다 — 스킬 파일을 텍스트로 읽고 패러프레이즈하는 것은
> 이 절차를 만족하지 않는다. 호출한 스킬이 요구하는 절차적 조건(필수
> 단계, 근거 기준, 중단 조건, 산출물 형식)을 이슈 초안의 요구사항/수용
> 기준 문장으로 접어 넣는다. **스킬 호출이 산출물을 만들지는 않는다** —
> 이슈에 요구사항으로만 반영되고, 실제 산출물은 여전히 역할 세션의 몫이다
> (역할 세션에는 스킬이 주입되지 않는다 — 격리는 그대로 유지된다). 적용될
> 스킬이 없다고 판단했으면 그 판단도 대화에서 한 줄로 말한다 — 침묵 통과는
> 허용되지 않는다.

This mirrors step 2's existing enforcement language ("분류를 말하지 않고
coding 으로 기본값 처리하는 것은 절차 위반이다") with an equivalent line for
skills, keeping both judgment axes symmetric in how strictly they're
enforced in prose.

The document's own numbered step 1 heading and step 2+ numbering are
unchanged — this is prose inserted inside step 1's body, not a renumbering.

## Out of scope

- `spawn.py`, any `roles/<role>.json` file, or any other skill-declaration
  surface for role sessions (issue #258 decision 1 and out-of-scope list).
- The role-handoff contract in `tokenmaxxxer-core` (unreachable from this
  repo; noted as a cross-repo follow-up, not attempted here).
- Adding, removing, or altering which skills exist (issue #258
  out-of-scope list).
- Any change to the Execution Plan (`## 실행 계획`) syntax, the Mission
  Board rendering logic, or steps 3-6 of the orchestrator loop — none of
  those are "issue drafting."

## How you'll know it worked

- `on-the-record/commands/run.md` step 1 contains the skill-assessment
  sub-step text above, positioned before the role-classification content
  (step 2) and before any `gh issue create` instruction.
- The inserted text names the `Skill` tool explicitly and states that
  reading a skill file as plain text does not satisfy the step (matching
  issue #258 decision 2's "never by reading skill files as plain text"
  requirement, verifiable by grepping the file for "Skill" and "패러프레이즈").
- The inserted text states explicitly that skill invocation does not
  produce the deliverable and that role sessions receive no skills
  (matching issue #258's "must not itself produce the deliverable" boundary
  clarification and decision 1).
- No file outside `on-the-record/commands/run.md` changes.
