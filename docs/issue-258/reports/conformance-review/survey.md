---
role: conformance-review
subject: issue-258
loop_state: survey
---

# Current-state survey — conformance review of issue #258 implementation

## Target artifact and spec

- Target: `on-the-record/commands/run.md` step 1, as merged via PR #259
  (commits a224712, 564503f, merge 74353e5 on `main`).
- Spec: issue #258 (title "Orchestrator applies user skills and folds their
  demands into issue requirements") plus the approved phase-1 proposal
  `docs/issue-258/proposals/implementation.md` (approved by `APPROVE
  issue-258/implementation` issue comment).
- Diff actually merged to `main` (`git diff 3c27dc9 74353e5 --stat`):
  `on-the-record/commands/run.md` (+13 lines) plus three doc files under
  `docs/issue-258/`. No other file changed.

## Requirement list (falsifiable, extracted from issue text + proposal, no builder intent)

1. Amend the orchestration procedure so that, before drafting an issue, the
   orchestrator assesses which user skills apply to the request (issue body,
   decision 3/4).
2. Skill invocation must go through the **real `Skill` tool** (loading the
   skill's instructions into the orchestrator's own session) — never by
   reading a skill's file as plain text and paraphrasing it (issue decision
   2, proposal constraint 2).
3. The skill's procedural demands (required steps, evidence standards,
   stopping criteria, deliverable structure) must be folded into the
   **issue's requirements/acceptance criteria** (issue decision 3).
4. Skill invocation must **not itself produce the deliverable** — it only
   shapes requirements; the deliverable stays role work (issue "Scope"
   clarification, proposal constraint 3).
5. **No skill injection into role sessions** — `spawn.py`'s skill surface
   and each `roles/<role>.json` catalog stay untouched (issue decision 1,
   out-of-scope list; proposal constraint 1).
6. Which skills apply is the **orchestrator's per-task judgment** over the
   full pool — no fixed request-type → skill mapping table (issue decision
   4, proposal constraint 4).
7. Out of scope, must NOT be touched: `spawn.py`, any `roles/<role>.json`,
   which skills exist, the Execution Plan syntax, Mission Board rendering,
   or steps 3-6 of the orchestrator loop (issue "Out of scope"; proposal
   "Out of scope").
8. Scope note (from proposal, carried from issue's "wherever issue drafting
   is specified"): the role-handoff contract in `tokenmaxxxer-core` is a
   separate repo out of this repo's reach — proposal explicitly does not
   attempt to amend it, only `run.md`. This is a proposal-level scope
   decision, not itself a spec requirement to verify against code, but is
   checked for consistency (no stray attempt to edit contract files).
9. (Implicit, from proposal's own "How you'll know it worked" — used as
   supplementary acceptance signal since proposal was user-approved via
   phase-1 gate, not as a substitute for 1-7): inserted text explicitly
   names the `Skill` tool and states plain-text reading does not satisfy
   the step; explicitly states no deliverable production and no role-skill
   injection; positioned before role classification (step 2) and before any
   `gh issue create` instruction; no file outside `run.md` changes code.

## Sampling / evidence plan

Small, fully-enumerable diff (13 lines in one file, plus 3 doc files) — no
sampling needed. Every line of the diff will be read directly against
requirements 1-7 above. Requirement 5 (spawn.py / roles/*.json untouched)
and requirement 7 (out-of-scope surfaces untouched) verified by diff stat
already showing only `run.md` + docs changed, cross-checked with a targeted
grep over `roles/` and `spawn.py` for any stray reference.

## Skip records

- Scouting (scout-directive): SKIPPED. Reason: this is conformance review of
  a merged code change against a fixed, already-approved spec (issue text +
  approved proposal) — the spec leaves no open design decision for this
  role to make; conformance review only classifies existing artifact vs.
  existing spec. Second skip condition applies verbatim ("spec literally
  leaves no design decision open").
