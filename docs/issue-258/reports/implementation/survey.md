---
role: implementation
subject: issue-258
loop_state: survey
---

# Current-state survey — orchestrator skill invocation (issue #258)

## What exists today

- The orchestrator procedure lives in exactly one file this repo owns:
  `on-the-record/commands/run.md` (the `/orchestrate:run` slash command source,
  shipped by this repo's `on-the-record` plugin). It is read by the
  orchestrator session itself, never by role sessions.
- Step 1 of "당신의 루프" (`on-the-record/commands/run.md:17-19`) is where
  requirements become an issue draft: "사용자의 요구를 이슈 초안으로 정리해
  보여주고, 확인받은 것만 `gh issue create` 로 등록한다." Nothing in this
  step, or anywhere else in the file, invokes the Skill tool or any user
  skill. The word "skill" does not appear anywhere in the file
  (`grep -n "skill\|Skill" on-the-record/commands/run.md` → no hits).
- Step 2 (`run.md:20-34`) classifies the issue by lead role (feasibility /
  product / ux-design / coding) via a fixed table with one-line
  justification, spoken in the conversation before `gh issue create`. This
  is the closest existing "judgment + fold into the issue" precedent in the
  file — issue #258's skill-assessment step is structurally the same shape
  (assess → state judgment in conversation → before registering the issue)
  but for a different axis (which skills apply, not which role leads).
- `docs/proposals/2026-07-27-remote-github-marketplace.md` and this repo's
  own `README.md`/`README.ko.md` describe the orchestrator's plugin set at
  a high level but do not touch the issue-drafting step's internal
  procedure — they are not in the write set.
- **The role-handoff contract (v3) is out of reach.** `protocol.md:46-47`
  states plainly: "It lives only in `core/contract/role-handoff-contract.md`
  in `tokenmaxxxer-core` — repos carry no copy." Confirmed on disk: no
  `role-handoff-contract.md` exists anywhere under this repo
  (`find . -iname "role-handoff-contract*"` → no hits); the only copy found
  on the machine is under a *different* repo's plugin cache
  (`~/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/contract/role-handoff-contract.md`),
  which is not this issue's subject repo, not on my `issue-258/implementation`
  branch, and not something this session has a mandate or a PR path to edit
  — role-handoff contract changes are `tokenmaxxxer-core`'s own subject, a
  different repo entirely. Issue #258's scope line "wherever issue drafting
  is specified" therefore resolves, on this repo, to exactly one file:
  `on-the-record/commands/run.md`. The proposal below is scoped to that file
  and notes the contract as a cross-repo follow-up rather than claiming to
  amend it.
- **Skill availability at the orchestrator session**: confirmed directly in
  this session's own system context — a `<system-reminder>` lists 40+
  available skills (market-recon, fmea, requirements-quality,
  decision-brief, tech-feasibility, etc.), invocable via the `Skill` tool
  by exact name. This matches issue #258's premise ("43 personal skills")
  and confirms the mechanism issue #258 asks the orchestrator to use
  (`Skill` tool, not reading skill files as text) is already available to
  orchestrator sessions today — no new plumbing is needed, only a
  procedural instruction to use it.
- **Role sessions have no skills, and issue #258 keeps it that way (decision
  1).** `spawn.py`'s per-role settings-merge (`spawn.py:1-20` docstring)
  isolates each role to its own plugin set; skills are a personal/user-level
  surface, never listed in `roles/<role>.json`. Confirmed no role JSON file
  under `roles/` references skills (`grep -rl "skill" roles/` → no hits).
  This survey found no code path that would need to change to preserve that
  isolation — the write set is documentation-only.

## Write set (confirmed)

- `on-the-record/commands/run.md` — amend step 1 ("요구사항 → 이슈") to add a
  skill-assessment sub-step between "요구를 이슈 초안으로 정리" and
  `gh issue create`, following the same in-conversation-judgment shape step 2
  already uses for role classification.

No other file in this repo specifies the issue-drafting procedure. No
`spawn.py`, `roles/*.json`, or gate script changes are implicated — issue
#258 explicitly rules those out (decision 1, out-of-scope: spawn.py
changes, per-rulebook skill declarations, which skills exist).

## Alternatives visible from this survey (for the proposal's Rationale)

- **A: amend `run.md` step 1 only** (the file this repo actually owns for
  issue drafting) — vs. **B: also attempt to amend the role-handoff
  contract's language on issue drafting** — B is not reachable from this
  repo or this session's mandate (contract lives in `tokenmaxxxer-core`,
  confirmed above); attempting it here would mean editing a file this
  repo does not control and cannot merge into its own board.
- **C: a separate new step** (a "step 1.5") for skill assessment — vs.
  **D: fold skill assessment into existing step 1** as a sub-step — the
  existing step 2 already demonstrates the file's convention of doing
  judgment-with-stated-rationale inline within a step rather than adding a
  new top-level numbered step for every new judgment axis; the proposal
  picks D for consistency with that existing pattern, keeping the loop's
  step count stable (still 6 top-level steps).
