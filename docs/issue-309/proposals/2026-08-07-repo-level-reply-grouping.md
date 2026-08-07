---
status: proposed
files:
  - on-the-record/commands/run.md
---

## Request

`run.md`'s per-item flow/stage/next anchoring (이슈-54) has no layer above
it: when a turn's report spans more than one repository, the reader must
mentally group correctly-anchored items by repo and infer each repo's
direction themselves. Add that repo-level layer — group by repository,
lead each group with one line on that repo's current direction — and
state plainly whether/how this new rule is checked.

## Constraints

- Adds a layer above the existing per-item flow/stage/next format; does
  not replace or restructure it (issue's own fix direction #1).
- Applies only to step 5's per-turn PR/decision report — not to the
  separately-triggered Mission Board section, which already groups by
  state and is out of scope here.
- Only fires when a turn's items span more than one repository — a
  single-repo turn keeps today's flat flow-grouped format unchanged.
- Must state enforcement status honestly: no hook in `on-the-record/hooks/`
  inspects reply text (confirmed by survey — `deliverable-guard.sh`,
  `directive.sh`, `self-update.sh` are the only three, none check reply
  shape), so this rule is unchecked and the doc must say so rather than
  imply a gate exists.

## Rationale

Considered adding a mechanical check (a hook that parses the
orchestrator's own reply for repo-header presence) instead of a
prose-only rule. Rejected: `directive.sh` is the only hook that touches
orchestrator prose today, and it runs at prompt-submit (before the reply
is written), not after — there is no PostToolUse-equivalent hook point
for an orchestrator's own conversational text (the orchestrator has no
tool call that emits its reply for a hook to intercept). Building that
capability is exactly the gap #298 already tracks as its own fix
(orchestrator self-enforcement gates); duplicating that inside #309 would
widen this issue's scope into #298's. So this proposal records the
absence explicitly instead, satisfying #309's acceptance criterion #2
("or record explicitly that it is not [checked]") without building #298.

## What will be done

Insert a new subsection into `run.md` step 5, between the existing
flow/stage/next spec (ends at line ~104, "항목이 여럿인 턴") and the
link-obligation spec, titled `**저장소 계층 — 둘 이상 저장소에 걸친
턴.**`:

- Trigger: the turn's items span more than one repository (repo is
  already known — each item's flow lives in a specific project clone).
- Format: one header per repo, each opening with one direction line
  (what is changing about that repo overall — not a restatement of the
  items under it), followed by the existing flow-grouped item blocks
  (issue's fix direction #2 — "not a restatement of the items beneath
  it").
- Single-repo turns are explicitly exempted: today's flat format stays
  the default when everything is in one repo.
- A closing line stating this grouping rule is prose-only, matching
  #309's acceptance criterion #2 and citing why (no reply-inspecting
  hook exists; cross-reference #298 as the tracked gap, without adopting
  #298's scope here).

## Out of scope

- Building a hook/gate that mechanically checks reply shape (belongs to
  #298).
- Changing the Mission Board's grouping (state-based, separately
  triggered, not this issue's target).
- Any change to the per-item flow/stage/next format itself (이슈-54)
  beyond nesting it under the new repo header.

## How you'll know it worked

- `run.md` contains the new repo-level grouping subsection, with a
  concrete definition of "direction line" and the single-repo exemption.
- The subsection states plainly that the rule is unchecked and why,
  cross-referencing #298.
- No orchestrator needs a private memory note to reproduce this format
  (issue's own acceptance criterion #3) — the rule and its example live
  in `run.md` alone.
