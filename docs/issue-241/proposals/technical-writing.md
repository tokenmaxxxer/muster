---
status: final
---

# Proposal — issue-241 README overhaul

## Background

Issue #241 asks for README.md/README.ko.md to be rebuilt around a vision essay
("믿음이 필요 없는 협업"): an install quickstart at the top, the essay as the body
(Korean original in README.ko.md, English translation in README.md), and a link
list to operational docs at the tail. Existing operational content must not be
deleted — it moves to docs/. The current "Five walls" pitch section is replaced by
the essay (dedup). The full current-state section inventory and disposition is in
`docs/issue-241/reports/technical-writing/survey.md`; scouting on README
best-practice (essay-as-README precedent, quickstart-first ordering) is in
`docs/issue-241/reports/technical-writing/scout-brief.md`.

## Target reader

README readers: a first-time visitor deciding whether to install and understanding
what the project is — not yet operating the tool (Diátaxis: quickstart is
tutorial-flavored, essay is explanation). Handbook readers: already-committed users
configuring or operating the tool day-to-day (Diátaxis: reference/how-to).

## Proposed structure

**README.md / README.ko.md**, same 3-part shape in both:

1. Title + language switch (unchanged).
2. **Quickstart** (one screen): `gh auth login`, `claude plugin marketplace add
   tokenmaxxxer/on-the-record`, `claude plugin install on-the-record@tokenmaxxxer`,
   `/on-the-record:run`. Pulled from current 시작하기 §1-2 only; deeper config knobs
   (env vars, `role_model.txt`, project init) move to the handbook.
3. **Essay body**: full text verbatim in README.ko.md; README.md carries a faithful
   English translation (own voice, not machine pass-through — matching the
   existing bilingual-maintenance convention).
4. **Operational docs links** (tail): pointers to `docs/handbooks/setup.md`,
   `docs/handbooks/operations.md`, `docs/handbooks/on-the-record.md`.

**New/changed docs/ files:**

- `docs/handbooks/setup.md` (new): Requirements, Windows/WSL structural rationale,
  full 시작하기 setup flow, "왜 필요한가" (settings.json scoping rationale).
- `docs/handbooks/operations.md` (new): install command reference, the loop,
  conversation usage, full command table, ledger/session-end behavior, deliberate
  stop points, isolation model, the three measured traps, package-registry/web-access
  sections, default-open posture, gates, self-check, open items.
- `docs/handbooks/on-the-record.md` (existing): gains the orchestration
  narrative/protocol-tree section and the roles table as new sections.

Full old-line-range → new-file mapping: `survey.md`'s section-inventory table. Every
existing section maps to exactly one destination (Keep or Move); none are dropped.
The two removed pitch sections ("Five walls", "Other AI works off the record") have
no destination — the essay is their replacement per the issue's explicit dedup
instruction, not a content loss.

## Rationale

Scout brief confirms essay-as-README-spine is a known strong pattern (e.g.
Day8/re-frame), provided the quickstart is hoisted above the essay to defuse
"manifesto bloat" risk — hence quickstart-first ordering. Splitting reference/how-to
material into docs/handbooks/ instead of leaving it in the README follows Diátaxis:
mixing tutorial, explanation, and reference in one file was the original structural
problem, not merely a length problem. Grouping by "how do I get running"
(setup.md) vs. "how do I operate this day-to-day" (operations.md) matches how a
committed user actually returns to the docs, rather than mirroring the old README's
section order for its own sake.

## Plan for phase 2

1. Draft `docs/handbooks/setup.md` and `docs/handbooks/operations.md`; extend
   `docs/handbooks/on-the-record.md`, carrying content verbatim per the survey
   table (no rewriting of operational prose beyond re-flowing headings/anchors).
2. Rewrite README.md and README.ko.md to the 4-part shape, including the essay
   translation.
3. Produce the phase-2 record with a before/after section-correspondence table
   (derived from survey.md, verified against the actual diff), a minimalism check,
   a style-guide compliance note, and accuracy-review evidence (grep/diff proof that
   every moved section landed somewhere and every command/path referenced still
   resolves).

## Out of scope

- No changes to the actual operational commands, config behavior, or gates
  themselves — this is a documentation reorganization only.
- No English translation quality review beyond faithful-meaning check (a full
  copyedit pass on the essay's English prose is not this issue's ask).
- No changes to non-README/non-handbook docs (proposals/, decisions/, other issues'
  reports).

**Scope-gate statement**: this PR contains only phase-1 material (survey,
scout-brief, this proposal) under `docs/issue-241/reports/technical-writing/` and
`docs/issue-241/proposals/`. No README.md, README.ko.md, or docs/handbooks/ changes
are included in this PR; those are phase-2 work, gated on the Approve below, and out
of scope for this PR.

## Approval

Per role-handoff contract v3 s19, phase 2 (the actual rewrite) opens only on a human
Approve — a PR review Approve from an approvers.md account distinct from this PR's
author, or an issue comment whose entire body is `APPROVE issue-241/technical-writing`
from an approvers.md account. This proposal and the survey/scout-brief are the only
phase-1 output; no README/docs edits are made before that Approve.
