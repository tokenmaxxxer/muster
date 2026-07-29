# Issue #76 — Reflect Record

loop_state: done

Status: final. Phase 2 opened via single-account APPROVE on PR #79 (contract v3 s19). All findings are `severity: advisory` — reflect informs future issues, it never blocks this one. Follow-up issues are the user's call; nothing below is self-authorizing.

Inputs: `docs/issue-76/reports/reflect/survey.md` (evidence, file:line citations), `docs/issue-76/proposals/proposal.md` (approved phase-1 proposal). This record restates the approved proposal as the delivered retrospective; no new evidence was gathered in phase 2.

Scope: merged history of issues #34, #43/#64, #44, #54, #68, #38/#51/#58/#65/#72, core#12/#14/#18.

## What was done, and why

What was done: phase 1 (survey + proposal, this issue's earlier commits) audited run.md's accreted obligations, audited contract-rule duplication across muster and tokenmaxxxer-core (including the core#14→#18 directive.sh incident), and checked this repo's reflect-role track record for the first time ever. Phase 2 (this record) restates that approved proposal as the final retrospective — no new evidence-gathering was done, because the proposal was already evidence-cited against the survey and approved verbatim by a human approver.

Why this shape: the role directive requires the record be "built from records, with each conclusion citing the record path it rests on." Every finding below traces to `survey.md` by section, which in turn traces to file:line citations in run.md, the hook files, and prior issues' proposals/reports. The alternative considered was re-running the phase-1 investigation live in phase 2 (re-reading run.md and the hooks directly). That was rejected: contract v3 s19 scopes reflect's evidence to other roles' records, not the running system, and the proposal had already cleared the human approval gate — redoing the analysis would not change the conclusions, only duplicate the paper trail phase 1 already produced.

## 1. Single-source contract-rule policy (highest priority)

The audit found a live incident, not just a style nit: core#14 amended contract v3 s19 (single-account approval path) and updated the enforcing hooks (`approval-gate.sh`, `gh-guard.sh`) but missed the informing hook `core/hooks/directive.sh:82-93`, which kept stating the pre-amendment rule. A role session refused an authorized single-account APPROVE because the stale informing text told it comments never approve anything. Fixed in core#18 (survey §2, incident narrative).

**1a. Zero-cite restatements are the top risk.** `orchestrate/hooks/directive.sh:73` and `run.md:185-187` (muster) restate the approval string verbatim with no `(contract v3 sNN)` cite at all — a future section renumber leaves no trace to prompt a re-check. Proposal: add section cites, matching the safe pattern already in `core/hooks/approval-gate.sh` and `core/hooks/board-gate.sh` (cite-only, no restated prose).

**1b. Citation next to restated prose is not sufficient by itself.** `core/hooks/directive.sh:82-93` DID carry a `(contract v3 s19)` cite next to full restated prose, and it still drifted — the incident is direct proof that a citation alone doesn't keep prose in sync. Proposal: informing hooks should either generate their approval-text block from the contract file at build/install time, or drop to a bare section pointer with no restated rule prose.

**1c. Muster has no local contract copy at all.** No canonical contract v3 text exists under muster's `docs/specs/`; only `approvers.md`. Every muster-side restatement is an implicit cross-repo copy with no local source to diff against. Proposal: either mirror the relevant contract sections as an explicit "generated, do not hand-edit" copy, or document the absence explicitly so it reads as a decision rather than a silent gap.

## 2. run.md obligation-accretion audit

Four issues (#34, #44, #54, #68) each added a standing obligation to `run.md`, and each explicitly promised, in its own proposal, not to touch the others' existing text — safe for review, but the reason the file now carries restated cross-references ("6번 스텝과 동일") instead of shared definitions (survey §1, root-cause note).

Concrete findings: two "don't render empty state" rules stated as three copies (`run.md:181-182`, `run.md:144-145`); two "silence ≠ consent" principles cross-referenced but not merged (`run.md:158-160`, `run.md:191-193`); a "never repeat the classification line" instruction scattered three sections from what it protects (`run.md:66-69` → `run.md:20-24`); and the clearest slippage risk — the mission-board trigger tied to step 5's completion sits 25+ lines away in a separate `##` block that an orchestrator reading step 5 top-to-bottom will finish past before reaching (`run.md:101-103`), breaking the document's only numbered sequence (1→6) with an ~80-line unnumbered insertion, contrary to issue-68's own proposal language of a "5-bis" step (survey §1, items 2–5).

Proposal: consolidate without weakening any existing obligation — factor the two duplicated meta-rules into one shared subsection cited by both sites, relocate the mission-board trigger into step 5 itself, and consider renumbering the mission board as an explicit step (e.g. "5.5") rather than an interrupting `##` break.

## 3. Process lessons

**3a/3b. Informing surfaces must be in the write-set of contract-amendment surveys.** The core#14 incident happened because phase-1 scoping covered only enforcing hooks. Proposal: future contract-amendment surveys should explicitly enumerate both "informing surfaces" (docs/prompts/hooks read by humans or agents) and "enforcing surfaces" (hooks that gate actions) as a two-column inventory before implementation, so a category isn't silently dropped.

**3c. A periodic reflect checkpoint, offered with low confidence.** Issue #68 landed directly after #34/#44/#54 had already stacked three obligations onto run.md, with no reflect-role checkpoint ever having run — this is the first reflect invocation in this repo's history (survey §3a), so there is no track record to confirm an earlier checkpoint would have caught the accretion. Proposal offered as advisory only: consider a periodic or pre-merge reflect trigger for issues that add standing obligations to run.md or the contract.

**3d. Unverified-ritual observation.** All four run.md mechanisms accreted by #34/#44/#54/#68 (explain-before-ask, role-selection classification, flow/stage/next reporting, mission board) are verified in their coding reports only by "diff matches the approved proposal text" (survey §3d, citing each report). None has a report showing the mechanism was exercised in a live session and changed orchestrator behavior. Applying this issue's own round-end value gate (procedure-value: a mechanism must cite evidence it changed an outcome, or be marked `ritual`): **all four are currently `ritual`** by that standard — proposal-conformance-checked, not outcome-proven. This is not itself an action item; it is context for any future decision about which run.md obligations to prioritize, simplify, or instrument with real usage evidence. This reflect record is subject to the same gate: it too has no track record yet and should be judged as ritual until a future issue can cite it changing a decision.

## Blind-onboarding check

Assessed on the four accreted-obligation issues' phase-1/phase-2 record pairs (survey §3c): three of four (`#34`, `#44`, `#68`) are fully reconstructable from records alone — origin request, exact edit location, checkable verification criterion, no code inspection needed. `#54`'s coding report is the weakest: it cites the triggering complaint and upstream PRs but not inline why flow/stage/next was the chosen schema, forcing a reader to chase two other PRs for "why this shape." No record among the four is a genuine defect by the blind-onboarding bar, but `#54` is the one worth tightening if it is ever revised.

## What this issue's own history teaches

This is the first reflect invocation ever run in this repo. The recurred-prediction check the role directive calls for (did an earlier reflect record predict a failure that recurred here) is not assessable — there was nothing to predict against. The gap itself is the finding: obligation accretion on run.md and the directive.sh drift both ran their full course, unflagged, before any reflect-shaped review existed. Whether a periodic checkpoint (§3c) would have caught either is unverified and should stay unverified in anyone's mind until a future issue can cite this record changing a decision.

## Next-steps backlog (user's call — none of this is self-authorizing)

1. File follow-up issue(s) to add contract-section cites to `orchestrate/hooks/directive.sh:73` and `run.md:185-187` (§1a).
2. Decide the informing-hook drift-prevention mechanism: generate-from-contract vs. bare-pointer-only (§1b), and whether to mirror or explicitly document muster's missing local contract copy (§1c).
3. Decide whether to commission a run.md consolidation pass (§2) — extracting the duplicated meta-rules, relocating the mission-board trigger into step 5, and considering a "5.5" renumbering.
4. Decide whether future contract-amendment surveys should mandate the informing/enforcing two-column inventory (§3a/3b) as a standing checklist item.
5. Decide whether to adopt a periodic reflect checkpoint for obligation-adding issues (§3c) — flagged as the weakest-evidenced proposal here.
6. Decide whether any of the four `ritual`-flagged run.md mechanisms (§3d) should be instrumented with real usage evidence, simplified, or left as-is.

## Open-finding resolution path

Every finding in this record is `severity: advisory` and none blocks issue #76's own completion. Resolution path: the user reviews the backlog above and, for any item they want acted on, files a new GitHub issue naming this record (`docs/issue-76/reports/reflect.md`) as its origin — per contract v3, reflect never files issues itself and never re-litigates another role's verdict. Items not picked up simply remain advisory record for the next reflect invocation to re-surface if the same pattern recurs (per §3c's recurred-prediction check, which this record itself now makes possible for the first time).
