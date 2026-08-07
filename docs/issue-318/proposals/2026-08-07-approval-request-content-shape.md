---
status: proposed
files:
  - on-the-record/commands/run.md
  - test_run_md_shape.py
  - on-the-record/hooks/approval_request_check.py
  - test_approval_request_check.py
---

## Revision note (rework after rejection)

PR #338 was rejected: its Rationale rejected a runtime check on the
grounds that "this plugin has no hook point that observes the
orchestrator's own conversational text." That is false — Claude Code's
`Stop` hook fires at the end of every assistant turn, receives
`last_assistant_message` (the turn's full final message text), and can
return `decision: "block"` + `reason` to block that response, or
`hookSpecificOutput.additionalContext` to inject a requirement without
blocking. Source: https://code.claude.com/docs/en/hooks.md, checked
2026-08-07. See `docs/issue-318/reports/implementation/survey.md`,
"Constraint check (corrected)" and "Root cause," for the corrected fact
and how the wrong premise got written as "confirmed" in the first place
(same failure class as #287).

This revision keeps the run.md six-item rewrite and its regression test
(the rejection said to keep them, as a floor even runtime checks need),
and adds what the corrected fact makes reachable: a pure, hook-free
function that checks whether a given approval-request message contains
all six required items. Declaring the `Stop` hook itself and wiring it
to call that function is left to #298, with the reasoning for that
boundary below — not because a hook is unreachable, but because
*declaring* it is general orchestrator-output enforcement, which is
#298's stated subject.

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
- No *hook declaration* in `on-the-record/hooks/hooks.json` — that step
  is general orchestrator-output enforcement infrastructure and belongs
  to #298 (see Rationale). The content-check logic itself is in scope;
  only wiring it to a live hook is not.

## Rationale

**Alternative considered: declare the `Stop` hook in this PR and wire it
to block/annotate approval-request messages missing required items at
runtime.** This is now known reachable (the corrected fact above) and is
the mechanism #310 ultimately wants — it checks the live message, not
just the spec that should produce it. Rejected for *this* PR's write
set, not as impossible: `on-the-record/hooks/hooks.json` currently
declares only `SessionStart`, `UserPromptSubmit`, `PreToolUse`, all
scoped to role-session enforcement; adding `Stop` is the first hook that
constrains the orchestrator's own output, which is precisely what #298
already exists to build ("orchestrator is the only unenforced actor...
building that surface is the entire subject of the already-open #298").
Declaring it here would fold #298's subject into #318 through the back
door — the operator's own item-7 principle (unrelated problems merged
into one issue destroy parallelism) argues against that, and #298 is
still open and unassigned, not stalled on this decision. #318 instead
ships the part #298 will need regardless of how it wires the hook: the
checking logic itself, decoupled from any hook.

**Chosen approach, two parts:**

1. Keep `run.md` as the executable spec and its regression test
   (unchanged from the rejected proposal) — a `Stop`-hook-based runtime
   check tells you a *specific message* was non-compliant; it says
   nothing about whether the *instruction* that should produce compliant
   messages is still intact. Both checks catch different regressions and
   neither substitutes for the other.
2. Add `on-the-record/hooks/approval_request_check.py`: a pure function
   `check(message: str) -> CheckResult` that scans a candidate
   approval-request message for the six required items' marker phrases
   and returns which are present/missing. It takes a string in, returns
   structured data out — no hook registration, no I/O, no dependency on
   `hooks.json`. This is the part #310 asks for that a text-only run.md
   test cannot give: a check against what a message actually says, not
   just what the spec says it should say. It is fully unit-testable
   today with string fixtures, the same pattern `gates/flows.py`'s
   markdown-as-data parsing already uses in this repo, and it is the
   exact function #298 (or any future hook wiring) would call from
   inside a `Stop` handler — building it here means #298 does not have
   to invent the check, only the wiring.

Alternative considered and rejected for part 2: embed the six-item check
directly inside a new `Stop` hook script (bash calling into Python)
rather than as a standalone importable function. Rejected because it
would force the hook declaration (out of #318's write set per the
Constraints) just to get the checking logic under test — a pure function
gets the same test coverage without touching `hooks.json`, and hands
#298 a ready-made dependency instead of a design question.

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
3. Add `on-the-record/hooks/approval_request_check.py`: given a message
   string, detect each of the six items via marker-phrase/section
   matching (mirroring the six markers used in run.md) and return a
   structured result (`missing: list[str]`) usable by a `decision:
   "block"` reason or an `additionalContext` nudge.
4. Add `test_approval_request_check.py`: fixtures covering a
   fully-compliant message, a message missing each item individually,
   and the literal rejected baseline ("Approve PR #N?") to lock in that
   it is flagged as missing all six.
5. Record, in this proposal, the boundary with #298 (hook declaration
   deferred there) so it is a stated decision, not a silent gap.

## Out of scope

- Declaring the `Stop` hook in `on-the-record/hooks/hooks.json` and
  wiring it to call `approval_request_check.py` at runtime — #298.
- Any change to how many approval requests are raised, or when.
- The flow/stage/next and link-obligation bullets already in step 5
  (touched only insofar as the six-item list sits alongside them, not
  the reverse).

## How you'll know it worked

`python3 -m pytest test_run_md_shape.py test_approval_request_check.py -q`
passes now. `test_run_md_shape.py` fails the moment
`on-the-record/commands/run.md` loses any of the six required marker
phrases from its approval-request instructions.
`test_approval_request_check.py` fails if `approval_request_check.py`
stops correctly flagging a message missing any one of the six items,
including the literal "Approve PR #N?" baseline the issue opens with.
Both are executable artifacts per #310; neither claims to be the runtime
`Stop`-hook enforcement itself — that remains #298's to wire, using this
PR's checker as its dependency, and this record says so rather than
implying the gap is closed.
