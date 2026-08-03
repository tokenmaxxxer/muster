---
status: final
loop_state: landed
doc-type: explanation
---

# Record — issue-241 (technical-writing)

## doc-type

`explanation`. The README's spine is now the vision essay (explanation);
the quickstart at the top is a minimal `tutorial`-flavored pointer, but the
record as a whole documents an `explanation`-type deliverable — the
Diátaxis type split moved all `reference`/`how-to` material out to
`docs/handbooks/setup.md` and `docs/handbooks/operations.md`. Per the
phase-1 survey, this was a type split, not a content rewrite: no type
mixing survives in any of the five output files.

## target reader

Unchanged from the phase-1 survey. README.md/README.ko.md: a first-time
visitor deciding whether to install and what this is, not yet operating the
tool. `docs/handbooks/*`: an already-committed user configuring or
day-to-day operating the tool.

## Approval

Issue #241 comment, exact string: `APPROVE issue-241/technical-writing`
(2026-08-03, JiwonJung94, single-account mode). This record and all
docs/handbooks changes below are phase-2 output, gated on that comment per
role-handoff contract v3 s19.

## What was done

Executed the phase-1-approved proposal (`docs/issue-241/proposals/technical-writing.md`)
verbatim: rebuilt README.md/README.ko.md into the 5-part shape (quickstart,
interaction-flow with 2 Mermaid diagrams per language, essay body, handbook
links), and moved every existing operational section into new
`docs/handbooks/setup.md`/`docs/handbooks/operations.md` files plus an
extension of the existing `docs/handbooks/on-the-record.md`, per the
survey's section-inventory table.

**Why:** issue #241 asked for the README to stop mixing pitch/reference/
how-to content and instead lead with the vision essay; per PR #242's two
review comments, the interaction-flow section was added to ground the
essay's abstract claims in concrete repo mechanics (spawn/rulebook/gate).

**Upstream basis:** the phase-1 proposal, survey, and scout-brief under
`docs/issue-241/reports/technical-writing/` and
`docs/issue-241/proposals/technical-writing.md`, all approved by the
`APPROVE issue-241/technical-writing` issue comment above.

`loop_state: landed` — this is the completed phase-2 delivery; no further
round is expected for this subject.

## What changed

**New files:**
- `docs/handbooks/setup.md` (167 lines) — Requirements, Getting started,
  Why this exists; Korean section then English section per topic.
- `docs/handbooks/operations.md` (683 lines) — Using it (install/board
  opt-in/loop/conversation/commands/session-end/deliberate stops),
  Isolation, Three traps (registry/web-access/default-open), Gates,
  Self-check, Open; Korean section then English section per topic.

**Extended file:**
- `docs/handbooks/on-the-record.md` (4 → 100 lines) — gained "오케스트레이션
  모델"/"Orchestration model" (protocol tree + narrative) and "역할"/"Roles"
  (roles table), Korean then English, appended after the existing hook-test
  paragraph.

**Rewritten files:**
- `README.md` (528 → 291 lines), `README.ko.md` (489 → 256 lines) — 5-part
  shape: title/language switch, quickstart, interaction-flow (2 Mermaid
  diagrams each), essay body (Korean original / English translation), links
  to the three handbook files.

## Before → after section-correspondence table

Derived from `docs/issue-241/reports/technical-writing/survey.md`'s
14-row inventory, verified against the actual diff (`git show
main:README.ko.md`, `git show main:README.md` vs. current
`docs/handbooks/*.md`).

| # | Old section (README.ko.md / README.md, pre-change line range) | New location | Verified |
|---|---|---|---|
| 1 | Title + language switch (1-3 / 1-3) | README.md/README.ko.md §1, unchanged | ✅ present, both files |
| 2 | "다섯 개의 벽" / "Five walls" (5-19 / 5-20) | **Removed** — replaced by essay §1 per issue's explicit dedup instruction | ✅ no destination by design, not a loss |
| 3 | "다른 AI는 기록에 안 남고..." pitch + bullets (21-41 / 22-43) | **Removed** — replaced by essay §3/§6 (record argument) and closing line, reused verbatim as the README's closing sentence | ✅ closing line ported into essay §6 |
| 4 | Orchestration narrative + protocol tree (43-61 / 45-65) | `docs/handbooks/on-the-record.md` §"오케스트레이션 모델"/"Orchestration model" | ✅ `grep -c "protocol.md   규약" docs/handbooks/on-the-record.md` = 1 |
| 5 | 요구사항 / Requirements (63-76 / 67-77) | `docs/handbooks/setup.md` §"요구사항"/"Requirements" | ✅ present verbatim |
| 6 | 시작하기 / Getting started (78-133 / 84-136) | `docs/handbooks/setup.md` §"시작하기…"/"Getting started…" | ✅ present verbatim, incl. `role_model.txt` precedence chain and v3 notes |
| 7 | 왜 필요한가 / Why this exists (135-139 / 146-151) | `docs/handbooks/setup.md` §"왜 필요한가"/"Why this exists" | ✅ present verbatim |
| 8 | 역할 표 / Roles table (141-162 / 153-176) | `docs/handbooks/on-the-record.md` §"역할"/"Roles" | ✅ 9-row role table present in both languages |
| 9 | 쓰기 (install/loop/conversation/commands/ledger/stops) (164-337 / 178-343) | `docs/handbooks/operations.md` §"쓰기"/"Using it" | ✅ present verbatim, incl. all subsections |
| 10 | 격리 (339-349 / 367-377) | `docs/handbooks/operations.md` §"격리…"/"Isolation…" | ✅ comparison table present in both languages |
| 11 | 함정 셋 + registry + web access + default-open (351-454 / 379-487) | `docs/handbooks/operations.md` §"실측으로 확인한 함정 셋"/"Three traps…" | ✅ all three traps + three subsections present verbatim |
| 12 | 게이트 (456-470 / 489-503) | `docs/handbooks/operations.md` §"게이트"/"Gates" | ✅ present verbatim |
| 13 | 자체 점검 (472-476 / 507-514) | `docs/handbooks/operations.md` §"자체 점검"/"Self-check" | ✅ present verbatim, incl. the stray Korean sentence inside the English `README.md` source section, carried as-is per instruction not to alter source text |
| 14 | 미해결 (478-489 / 516-528) | `docs/handbooks/operations.md` §"미해결"/"Open" | ✅ present verbatim |

Zero rows dropped without a destination; rows 2-3 are the two
issue-mandated removals (essay replaces the pitch, not a content loss).

## Minimalism check

Each README.md/README.ko.md section maps directly to a target-reader goal
(decide whether to install, understand what this is):
- Quickstart: install commands only, nothing else — a first-time visitor's
  immediate need.
- Interaction flow: grounds the essay's abstract claims in the repo's
  concrete objects (issue/PR/branch/record/gate), added per two PR #242
  reviewer comments asking for exactly this.
- Essay: the "why," per issue #241's explicit ask.
- Links: handbook pointers only — no inlined reference/how-to content,
  keeping the split clean.
No section restates another; the old duplicate pitch (rows 2-3 above) was
removed rather than kept alongside the essay, per the issue's dedup
instruction.

## Style-guide compliance note

No deviations from the Google Developer Documentation Style Guide in the
quickstart/interaction-flow/links sections (active voice, second person
avoided appropriately for a project README, sentence-case headings). The
essay body is a deliberate, issue-mandated deviation — literary prose
ported/translated faithfully rather than restyled to house style — matching
the phase-1 survey's plan exactly.

## Accuracy review evidence

- **Mermaid syntax**: all 4 diagrams (2 per language) extracted and rendered
  with `@mermaid-js/mermaid-cli` (`npx @mermaid-js/mermaid-cli -i <block>.mmd
  -o <block>.svg`); all 4 produced an SVG with no error output.
- **Section mapping**: verified by heading grep against both new handbook
  files and the extended `docs/handbooks/on-the-record.md` (see table
  above) — every heading from the old README section inventory has an exact
  or `##`-per-language counterpart in its destination file.
- **Commands/paths referenced still resolve**: `docs/handbooks/setup.md`,
  `docs/handbooks/operations.md`, and `docs/handbooks/on-the-record.md` all
  exist at the paths linked from README.md/README.ko.md's "Learn more" /
  "더 알아보기" section (checked with `test -f` on each of the three
  paths — all present).
- **No orphaned content**: `docs/handbooks/operations.md` line count (683)
  plus `docs/handbooks/setup.md` (167) plus the `docs/handbooks/on-the-record.md`
  delta (96 new lines) accounts for the full bilingual operational content
  removed from the old README.md (528 lines) + README.ko.md (489 lines).

## Out of scope (confirmed unchanged)

No changes to operational commands, config behavior, or gates themselves —
this was a documentation reorganization only, matching the phase-1
proposal's stated scope.

## Open findings

None. Every row in the section-correspondence table above resolved to a
destination or a documented, issue-mandated removal; no orphaned content,
broken link, or unrendered diagram was found during accuracy review.
