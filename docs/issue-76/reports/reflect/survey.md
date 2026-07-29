# Issue #76 — Reflect Survey (Phase 1)

Status: phase-1 research artifact. This is not the final reflect record — `docs/issue-76/reports/reflect.md` is phase-2 output, gated behind human Approve per role-handoff contract v3 s19, and is out of scope for this document.

Scope per issue #76: retrospective over merged history of issues #34, #43/#64, #44, #54, #68, #38/#51/#58/#65/#72, core#12/#14/#18. This survey states findings as facts with file:line citations. No recommendations here — see `docs/issue-76/proposals/proposal.md` for the proposal list. All findings are severity:advisory; reflect never blocks.

## 1. run.md obligation-accretion audit

1. The instruction "never repeat the classification line" is asserted three times across files, none of which is a true consolidation point. `run.md:66-69` (issue-54's flow/stage/next preamble) says not to repeat `run.md:20-24`'s (issue-44) classification line, but the instruction lives three sections away from the rule it protects. This is a scattering symptom, assessed as low risk.

2. Two independent "don't render empty state" rules are stated as three separate copies. `run.md:181-182` (step 6, decision queue): "대기 항목이 없으면 이 블록 자체를 만들지 않는다." `run.md:144-145` (mission board render): "그룹에 항목이 없으면 그 헤더 자체를 만들지 않는다... 6번 스텝의 규칙과 동일한 원칙." The mission board section already recognizes it is "the same principle" but restates it in prose anyway — issue-68 added this second copy on top of pre-existing step 6 text.

3. Reporting obligations for the same "per-item report" moment are split across three non-adjacent locations: step 5 (`run.md:51-65`, issue-34's 4-item what/why/what-changed/how-verified), step 5's added bullet (`run.md:66-90`, issue-54's flow/stage/next), and the separate `## 미션 보드` section (`run.md:91-168`, issue-68). The mission board section is triggered partly BY step 5 completing ("역할 세션이 완료 통지를 보낸 직후... 5번 스텝의 PR 요약과 별도로," `run.md:101-103`) but sits 25+ lines away from step 5, after step 5's numbered list has closed. An orchestrator reading step 5 top-to-bottom finishes the obligations and outputs the report before ever reaching the "you may also owe a mission-board render right now" trigger in a section that reads as optional reference rather than a per-turn gate. This is flagged as the clearest slippage risk: the obligation firing at the SAME moment as step 5 completion is not colocated with step 5.

4. Ordering ambiguity exists between the proposal and the landed document. Issue-68's own proposal (`docs/issue-68/proposals/board-proposal.md:45-47`) describes the board as step "5-bis," inserted "between step 5 and step 6." The landed `run.md` instead makes it a `##`-level section (`run.md:91`), breaking the numbered-list flow: steps 1-5 are one list (`run.md:17-90`), the mission board interrupts as an H2, then step 6 (`run.md:170`) resumes the SAME numbered list at "6." The document's only numbered sequence (1→6) has an approximately 80-line unnumbered insertion in the middle, so a step-6-adjacent trigger condition sits outside the enumerated step list a reader is scanning.

5. Two different "silence ≠ consent/promotion" principles are cross-referenced but not merged: `run.md:158-160` (mission board parking-lot promotion: "침묵은 승격이 아니다 — 6번 스텝의 원칙과 동일") and `run.md:191-193` (step 6's closing sentence, same principle, independently phrased: "당신이 먼저 승인을 제안할 수는 있어도, 사용자의 답 없이 실행하는 일은 없다"). Issue-68 again chose citation-plus-restatement over factoring out a shared principle.

Root cause: each of the four issue proposals (`docs/issue-44/proposals/role-selection-guide.md:57`, `docs/issue-54/proposals/coding.md:180-181`, `docs/issue-68/proposals/board-proposal.md:47-48`) explicitly promised not to touch the others' existing text — a scope discipline that is safe for review, but is why the file now carries restated cross-references ("6번 스텝과 동일") instead of shared definitions.

## 2. Contract-rule duplication audit and directive.sh incident

### Incident narrative

Core issue #14 (commit 4bf2910, PR #15) amended `core/contract/role-handoff-contract.md` s19/s10 to add a second approval path: single-account mode, where the PR author and sole approver are the same account, and an issue-level comment whose entire body is exactly `APPROVE issue-<n>/<role>` from an approvers.md account also opens phase 2. This closed a discrepancy first surfaced in muster `docs/issue-31/reports/verify.md`, where PRs #32/#33 were unlocked by author self-comments with `"reviews":[]`.

`core/hooks/directive.sh` (injected into every role session's SessionStart prompt) still carried the pre-amendment sentence "A comment is never an approval, however affirmative it reads." Issue #14's phase-1 survey updated the enforcing hooks (`approval-gate.sh`, `gh-guard.sh`) correctly but missed the informing hook (`directive.sh`).

This caused a live refusal: a role session, told by `directive.sh` that comments never approve anything, refused to start phase-2 on an authorized single-account APPROVE comment. This was reported on muster PR #75 (`core/docs/issue-18/proposals/coding.md`). It was fixed in core issue #18 (commit f4cc6ab) by replacing the stale sentence with the amended two-path text, this time with an inline `(contract v3 s19)` cite.

### Restatement inventory

- `core/hooks/directive.sh:82-93` — restates verbatim, with a section cite alongside: spells out the full two-path approval text rather than only pointing to `s19`. This is the exact site that drifted, demonstrating that a citation alone did not prevent drift; the restated prose itself had to stay in sync too.
- `core/hooks/approval-gate.sh:159,172,187,213,238,251,253` — cites section (safe pattern): messages cite `(contract v3 s19)`/`(s8)`/`(s10)`, quoting only the minimal enforced string ("APPROVE %s"), with no prose paraphrase.
- `core/hooks/board-gate.sh:195,227,232,244,266,283` — cites section (safe): refusals end with `(contract v3 s10)`/`s11`, no restated rule prose.
- `core/hooks/gh-guard.sh:4,77-94` — cites section (safe), mixed with a short paraphrase ("an APPROVE-shaped comment is the single-account approval signal"). This carries low but nonzero drift risk since it names the rule's meaning, not just the section number.
- `scout/hooks/directive.sh` — shares the same drift-risk pattern as `core/hooks/directive.sh` (flagged by issue #18's own survey as "informing-half" text, not independently re-diffed).
- `orchestrate/hooks/directive.sh:73` (muster) — restates verbatim, with no section cite at all: `approval -> a comment that is EXACTLY "APPROVE issue-<n>/<role>"`. There is zero pointer to contract v3, so even a section-number bump elsewhere leaves a silent reader with no signal to re-check. This is assessed as the highest-risk pattern found in either repo.
- `orchestrate/commands/run.md:11` (muster) — cites `(contract v3)` generically, with no section number, header note only.
- `orchestrate/commands/run.md:185-187` (muster, Korean) — restates verbatim, citing the mechanism but no section number: gives the exact `gh pr comment ... "APPROVE issue-<n>/<역할>"` string plus a parenthetical explaining approval-gate's matching behavior.
- No canonical contract v3 copy exists under muster's `docs/specs/` (only `approvers.md`). The canonical text lives solely in tokenmaxxxer-core's `core/contract/role-handoff-contract.md`, so every muster-side restatement is inherently a cross-repo copy with no local source to diff against.

## 3. Prior-reflect-record audit, procedure-value check, blind-onboarding check

### (a) No prior reflect record

No prior `docs/issue-*/reports/reflect.md` exists anywhere in muster — this is the first reflect invocation ever. `roles/reflect.json` exists procedurally but has never produced a report.

### (b) Recurred-prediction check

Not assessable — there is no prior record to check predictions against. Gap noted for the retrospective: issue #68 (mission board) landed directly after #34/#44/#54 had already stacked three obligations onto run.md's loop, with no reflect-role checkpoint ever warning about obligation accretion before it landed.

### (c) Blind-onboarding check

Assessed on `docs/issue-34`, `docs/issue-44`, `docs/issue-54`, `docs/issue-68` (proposals + reports):

- `docs/issue-34/proposals+reports/coding.md`: reconstructable — origin request, exact edit location (run.md step 4), out-of-scope statement, checkable verification criterion cited back in the report. Not thin.
- `docs/issue-44/proposals/role-selection-guide.md` + `reports/coding.md`: strongest of the four — cites the triggering incident (a real session defaulting 6x to coding), a frozen write set, integration constraints with #34/#43, and an explicit review checklist. Fully reconstructable with no code inspection needed.
- `docs/issue-54/reports/coding.md`: reconstructable but thinner — cites the triggering user complaint ("what was #48 again?") and upstream PRs (#55/#56/#57), but does not restate WHY flow/stage/next was the chosen schema inline; that rationale lives only in the product/ux-design reports. A reader of only this file gets the "what" but must chase two other PRs for "why this shape." This is the weakest of the four — citation-by-reference rather than self-contained.
- `docs/issue-68/proposals/board-proposal.md` + `reports/coding.md`: reconstructable, well-cited — explicitly threads #43's conditions, #54's schema, and #64's re-verification. Not thin.

None of the four is a genuine "records defect" — all cite upstream issues/PRs and state before/after states. #54's coding record is the comparatively weak one.

### (d) Procedure-value evidence

For the four accreted run.md mechanisms — explain-before-ask (#34), role-selection classification (#44), flow/stage/next reporting (#54), mission board (#68) — every coding report's verification is identical in kind: "diff matches the approved proposal text."

- `docs/issue-34/reports/coding.md`: "confirmed by inspection."
- `docs/issue-44/reports/coding.md`: "diff-scope-check... confirmed."
- `docs/issue-54/reports/coding.md`: "byte-for-byte match."
- `docs/issue-68/reports/coding.md`: "Re-read the edited run.md... confirmed."

None has a report showing the mechanism was exercised in a live session and changed orchestrator behavior — e.g. a transcript where classification caught a defaulted-to-coding case, or explain-before-ask blocked an unexplained merge. By this repo's own records, all four run.md obligations are currently unverified ritual (proposal-conformance-checked only), not outcome-proven procedure.

The closest thing to outcome evidence is #44's proposal, which cites the pre-existing failure (6x defaulted to coding) that motivated the rule — this is evidence for the problem, not evidence the fix prevented recurrence. No later record cites the classification step being invoked and diverting a session away from coding.
