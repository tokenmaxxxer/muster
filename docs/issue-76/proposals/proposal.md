# Issue #76 — Reflect Proposal (Phase 1)

Status: proposal only, nothing here is implemented. Findings are severity:advisory throughout — reflect never blocks. Follow-ups on any item below are the user's call. Derived from `docs/issue-76/reports/reflect/survey.md`; see that document for full evidence and citations.

Items are numbered by priority, highest risk/value first, using the risk framing established in the survey.

## 1. Single-source contract-rule policy (highest priority — zero-cite restatement in production)

**1a. Add section cites to muster's uncited restatements — highest priority.**
`orchestrate/hooks/directive.sh:73` restates the approval string verbatim ("approval -> a comment that is EXACTLY `APPROVE issue-<n>/<role>`") with no pointer to the contract at all (survey §2). `run.md:185-187` similarly restates the exact `gh pr comment` string with a mechanism explanation but no section number (survey §2; cf. `run.md:11`'s generic `(contract v3)` header cite with no section number). Propose both sites add `(contract v3 sNN)` citations, matching the safe pattern already used in `core/hooks/approval-gate.sh:159,172,187,213,238,251,253` and `core/hooks/board-gate.sh:195,227,232,244,266,283`. This is the top-priority item because these two sites currently have zero drift signal — a future section renumber in the contract leaves no trace here to prompt a re-check.

**1b. Treat citation-plus-prose as an insufficient pattern, not just a missing-cite problem.**
`core/hooks/directive.sh:82-93` DID cite `(contract v3 s19)` alongside its full restated prose, and it still drifted during the core#14 amendment (survey §2, incident narrative). The incident proves a citation next to restated prose does not, by itself, prevent staleness — the prose has to be kept in sync independently, and issue #14's phase-1 survey did not catch that this file needed updating. Propose that informing-hooks (directive.sh in core, scout, and muster) either (i) generate their approval-text block from the contract file directly at build/install time so there is one physical source, or (ii) reduce to a bare section pointer with no restated rule prose at all, on the reasoning that prose-plus-citation was tested by a real incident and failed.

**1c. Make muster's absence of a local contract copy an explicit, documented choice.**
No canonical contract v3 text exists under muster's `docs/specs/` — only `approvers.md` (survey §2). Every muster-side restatement is therefore an implicit cross-repo copy with no local source to diff against. Propose one of: (i) mirror `docs/specs/` with an explicit "generated, do not hand-edit" copy of the relevant contract sections, refreshed from tokenmaxxxer-core on a defined trigger, or (ii) keep pointing cross-repo as today, but add an explicit note in `docs/specs/` (or wherever a reader would look first) stating that no local copy exists and directing to the core repo, so the absence is a documented decision rather than a silent gap.

## 2. run.md consolidation (accreted obligations, no obligation weakened)

Propose consolidating without removing any existing obligation (survey §1):

- Extract the two duplicated meta-rules — empty-state suppression (`run.md:181-182` and `run.md:144-145`) and silence-is-not-consent (`run.md:158-160` and `run.md:191-193`) — into one shared subsection stated once, with step 6 and the mission board section each referencing it instead of restating it in independent prose. This removes the "6번 스텝과 동일" style cross-reference-plus-restatement pattern the survey identifies as the root cause (issue-44/54/68 proposals each promising not to touch other sections' existing text, per survey §1 root-cause note).
- Relocate the mission-board trigger tied to step 5 completion (`run.md:101-103`) into step 5 itself, since the obligation fires at the same moment step 5 completes but currently sits 25+ lines away in a structurally separate `##` block that reads as optional reference (survey §1, item 3 — flagged as the clearest slippage risk).
- Consider renumbering the mission board as an explicit step inside the main numbered sequence (e.g. "5-bis" or step "5.5"), matching issue-68's own original proposal language (`docs/issue-68/proposals/board-proposal.md:45-47`) rather than the landed `##`-level break that interrupts the document's only numbered list (run.md's 1→6 sequence, survey §1 item 4).
- Also fix the scattered "never repeat the classification line" instruction (`run.md:66-69` pointing back to `run.md:20-24`, three sections apart) as part of the same consolidation pass, since it is the same scattering symptom at lower severity (survey §1, item 1).

## 3. Process lessons to encode

**3a. Informing-hooks must be in the write-set of any future contract-amendment survey.**
Generalized from the core#14/#18 incident (survey §2): a phase-1 survey for a contract amendment covered only enforcing hooks (`approval-gate.sh`, `gh-guard.sh`) and missed the informing hook (`directive.sh`), causing a live session refusal on an authorized action. Propose that any future contract-amendment phase-1 survey checklist explicitly requires enumerating both categories before scoping the change.

**3b. Survey completeness should separate "informing surfaces" from "enforcing surfaces" as a named step.**
Informing surfaces are docs/prompts/hooks that describe rules for humans or agents to read (e.g. `directive.sh`, `run.md` prose); enforcing surfaces are hooks that gate actions (e.g. `approval-gate.sh`, `board-gate.sh`). Issue #14's survey covered only the latter category (survey §2). Propose that contract-amendment proposals include an explicit two-column inventory of both surface types before implementation, so a category is not silently dropped.

**3c. Reflect-role should exist as a periodic checkpoint before obligation-adding issues land, not only after.**
This is the weakest-evidenced lesson here and is offered as an advisory suggestion, not a proven fix — there is no prior reflect record to demonstrate it would have worked (survey §3a: this is the first reflect invocation ever). The motivating observation is that issue #68 (mission board) landed directly after #34/#44/#54 had already stacked three obligations onto run.md's loop with no reflect-role checkpoint ever having run (survey §3b). Propose considering a periodic or pre-merge reflect trigger for issues that add new standing obligations to run.md or the contract, while explicitly flagging that this proposal itself is unverified by any track record.

**3d. All four existing run.md obligations are currently unverified ritual, not outcome-proven procedure.**
Every coding report for issues #34/#44/#54/#68 verifies only "diff matches the approved proposal text" — none shows the mechanism being exercised in a live session and changing orchestrator behavior (survey §3d). This is not itself an action item, but is noted as context for any future decision about which run.md obligations to prioritize, simplify, or instrument with real usage evidence.
