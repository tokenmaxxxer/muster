---
status: proposed
files:
  - on-the-record/commands/run.md
  - test_run_md_shape.py
---

## Request

An approval request that says "Approve PR #N?" makes the operator
reassemble the decision themselves. It must instead stand alone,
covering: which requirement it serves, what was investigated and
concluded, what changes structurally in the code, what becomes
possible/impossible afterward, what alternative was considered and
rejected (and why), and what risk/tradeoff is being accepted.

## Constraints

- Content only — the *number* of approval requests is explicitly
  out of scope per the issue's own "Note on scope."
- Per #310: prose alone does not discharge this. The acceptance must
  name an executable artifact that fails on regression, or say plainly
  the requirement is unverifiable and why.
- Must not touch the existing 이슈-54 (flow/stage/next) or 이슈-236
  (link obligation) bullets already in step 5 of run.md.
- No new gate infrastructure — that is #298's scope (orchestrator has
  no PreToolUse-style hook over its own chat output; building one is a
  separate, much larger issue).

## Rationale

**Alternative considered: build a PostToolUse/transcript-inspection
gate that checks the orchestrator's actual approval-request message at
runtime**, the same mechanism role sessions get (board-gate,
approval-gate, trailer-gate). Rejected: this plugin has no hook point
that observes the orchestrator's own conversational text (confirmed in
survey.md) — the orchestrator is the one actor with no PreToolUse
enforcement surface, and building that surface is the entire subject of
the already-open #298. Doing it here would silently widen #318 into
#298's scope, which the operator's own item-7 principle (unrelated
problems merged into one issue) argues against.

**Chosen approach: treat `run.md` itself as the executable spec and add
a regression test over its text**, the same pattern this repo already
uses for `gates/flows.py`'s markdown-as-data parsing
(`test_flows_plan_*` tests parse issue-body markdown and assert
structure). A test that reads `on-the-record/commands/run.md` and
asserts each of the six required items' marker phrases are present in
the 1단계/2단계 approval-request bullets fails the moment a future edit
strips one out — this is the artifact #310 asks for, scoped honestly to
what's checkable: it verifies the spec the orchestrator reads, not a
specific live message the orchestrator produced. The proposal states
this boundary explicitly rather than claiming runtime enforcement it
cannot deliver.

## What will be done

1. Rewrite the "1단계 승인 요청 시" and "2단계 머지 요청 시" bullets in
   `on-the-record/commands/run.md` step 5 to require six items instead
   of the current three/two:
   - 어떤 요구사항을 위한 것인가 (requirement link)
   - 무엇을 조사했고 무엇을 결론지었는가
   - 코드/구조상 무엇이 바뀌는가 (혹은 바뀌었는가, 2단계)
   - 승인 이후 무엇이 가능/불가능해지는가
   - 무엇을 검토했다가 기각했는가, 왜
   - 사용자가 감수하는 리스크/트레이드오프
   Fold the existing "네 항목" closing sentence into this six-item list
   (drop the now-redundant duplicate four-item summary) so there is one
   authoritative list, not two that drift.
2. Add `test_run_md_shape.py`: reads
   `on-the-record/commands/run.md`, isolates the step-5 approval-request
   block, and asserts each of the six marker phrases is present. Fails
   loudly (assertion, not silent) if a future edit drops one.
3. Record, in this proposal's own body (this section), that live-message
   enforcement is unreachable within #318's write set and why — so the
   unverifiable half of the requirement is visible as such rather than
   implied covered.

## Out of scope

- Runtime/transcript-level enforcement that inspects what the
  orchestrator actually said in a given turn (#298).
- Any change to how many approval requests are raised, or when.
- The flow/stage/next and link-obligation bullets already in step 5
  (touched only insofar as the six-item list sits alongside them, not
  the reverse).

## How you'll know it worked

`python3 -m pytest test_run_md_shape.py -q` passes now, and fails the
moment `on-the-record/commands/run.md` loses any of the six required
marker phrases from its approval-request instructions — that is the
executable artifact #310 requires. The record for this issue states
plainly that this artifact checks the spec text, not a specific live
approval message, and names that gap rather than hiding it.
