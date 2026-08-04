---
role: conformance-review
subject: issue-258
loop_state: landed
---

Survey: [[survey.md]](reports/conformance-review/survey.md).

# Conformance review — issue #258 implementation (PR #259)

## What was done

Audited `on-the-record/commands/run.md` step 1 as merged in PR #259 (diff
`3c27dc9..74353e5`, +13 lines, one code file) against the 7 falsifiable
requirements extracted in the survey plus supplementary acceptance signal
9, producing a per-requirement verdict below (Present | Surface | Absent |
Incorrect | Unverifiable), each citing exact `run.md` line ranges as
evidence.

## Why

Issue #258 phase-2 conformance review: this role's own phase-1 proposal
(PR #260, `docs/issue-258/proposals/conformance-review.md`) was Approved,
opening phase 2 — the actual audit against the merged artifact. This role
classifies spec-vs-artifact conformance only; it does not fix the target
artifact, and does not judge code quality or design merit, only whether
what was specified is present in what was built.

Target: `on-the-record/commands/run.md` step 1, diff `3c27dc9..74353e5`
(+13 lines, one file; `git diff 3c27dc9 74353e5 --stat` confirms no other
code file changed). Spec: issue #258 body + approved
`docs/issue-258/proposals/implementation.md`. Verdicts classify the merged
artifact against the spec only, independent of builder intent.

## Verdicts

| # | Requirement | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Amend orchestration procedure so orchestrator assesses applicable user skills before drafting an issue | **Present** | `run.md:21-32` inserts a new "스킬 평가 — 이슈 등록 전" sub-step inside step 1, positioned before the "이슈 초안으로 정리해 보여주고" draft-and-confirm flow completes and before step 2's role classification. |
| 2 | Skill invocation must go through the real `Skill` tool, never plain-text reading/paraphrase | **Present** | `run.md:24-26`: "적용된다고 판단한 스킬은 반드시 `Skill` 도구로 **실제로 호출**한다 — 스킬 파일을 텍스트로 읽고 패러프레이즈하는 것은 이 절차를 만족하지 않는다." Names the `Skill` tool explicitly and explicitly negates the plain-text-read path. |
| 3 | Skill's procedural demands (steps, evidence standards, stopping criteria, deliverable structure) folded into the issue's requirements/acceptance criteria | **Present** | `run.md:26-29`: "호출한 스킬이 요구하는 절차적 조건(필수 단계, 근거 기준, 중단 조건, 산출물 형식)을 이슈 초안의 요구사항/수용 기준 문장으로 접어 넣는다." Enumerates the same four demand categories from the spec (steps, evidence standards, stopping criteria, deliverable structure) and names the target as the issue draft's requirements/acceptance-criteria text. |
| 4 | Skill invocation must not itself produce the deliverable — deliverable stays role work | **Present** | `run.md:28-30`: "**스킬 호출이 산출물을 만들지는 않는다** — 이슈에 요구사항으로만 반영되고, 실제 산출물은 여전히 역할 세션의 몫이다." Explicit boundary statement matching the spec's clarification. |
| 5 | No skill injection into role sessions — `spawn.py` skill surface and `roles/<role>.json` catalogs untouched | **Present** | `git diff 3c27dc9 74353e5 --stat` shows only `on-the-record/commands/run.md` (+13) and three `docs/issue-258/` files changed — `spawn.py` and `roles/` absent from the diff. `grep -rni skill on-the-record/spawn.py on-the-record/roles/` returns no matches. The inserted text itself states the invariant: `run.md:29-30` "(역할 세션에는 스킬이 주입되지 않는다 — 격리는 그대로 유지된다)". |
| 6 | Which skills apply is the orchestrator's per-task judgment over the full pool — no fixed request-type → skill mapping table | **Present** | `run.md:21-23`: "판단은 매 이슈마다 하는 것이지, 정해진 매핑표를 찾는 것이 아니다 — 어떤 스킬이 적용되는지는 오케스트레이터의 그때그때 판단이다." No table follows the inserted paragraph (unlike step 2's role-classification table at `run.md:39-44`) — confirmed by reading the full inserted block, `run.md:21-32`, which is prose only. |
| 7 | Out-of-scope surfaces untouched: `spawn.py`, `roles/<role>.json`, which skills exist, Execution Plan syntax, Mission Board rendering, steps 3-6 of the orchestrator loop | **Present** | Diff stat confirms only `run.md` changed among code files. Within `run.md`, `git diff 3c27dc9 74353e5 -- on-the-record/commands/run.md` is a pure insertion of lines 21-32 into step 1's body; steps 2-6 (`run.md:33` onward) and the `## 실행 계획` / Mission Board sections are unchanged (no `-` lines in the diff outside the insertion point). |
| 9 | (Supplementary, proposal §"How you'll know it worked") Insertion positioned before role classification (step 2) and before any `gh issue create` instruction; no file outside `run.md` changes code | **Present** | Position confirmed at `run.md:21-32`, ending immediately before step 2's heading at `run.md:33`. The sub-step's own text (`run.md:21`, "이슈 초안을 보여주기 전에") places the judgment before the draft is shown, i.e. before the confirm-then-`gh issue create` action closes step 1. Diff stat confirms the only non-doc file changed is `run.md`. |

## Notes

- Requirement 8 (survey item 8) is a proposal-level scope decision about the
  out-of-reach `tokenmaxxxer-core` contract repo, not itself a verifiable
  spec claim against this repo's artifact — survey explicitly flags it as
  "not itself a spec requirement to verify against code, but checked for
  consistency." Consistency check: no file under a `contract/` path or
  named `role-handoff-contract.md` appears in the diff — no stray attempt
  to edit contract files. No independent verdict row assigned; folded into
  requirement 7's out-of-scope check.
- All 7 falsifiable requirements plus supplementary signal 9 verdict
  **Present**. No Surface, Absent, Incorrect, or Unverifiable findings —
  the diff is small (13 lines, one file) and fully enumerable, so no
  sampling gap exists that would force an Unverifiable classification.

## Open findings

None. All requirements verified Present against `run.md` as merged; no gap
to address back to the `implementation` role. Review is complete — no
further action pending in this subject.
