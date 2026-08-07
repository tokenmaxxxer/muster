---
status: proposed
files:
  - gates/open_work.py
  - gates/test_open_work.py
  - on-the-record/hooks/choice-framing-guard.sh
  - on-the-record/hooks/hooks.json
  - docs/decisions/2026-08-07-choice-framing-scope.md
---

## Request

An orchestrator can put a constraint-framed choice to the operator ("run
tests manually, or wait for X") without checking whether the constraint
still holds. The observed instance: a session offered two workarounds for
a Playwright limitation that PR #307 had already fixed, and misattributed
the cause besides. #379 asks for three things: (1) what must be checked
before framing such a choice, (2) whether/how a session can learn about
delivered-but-unmerged work without breaking the "board is merged main"
invariant, (3) applying #287/#312's "report the evidence you judged on"
principle to questions, not just gate verdicts.

## Constraints

- Per #379's own honesty requirement: "did this actor check before
  asking" is not computable from question text alone. Any mechanism here
  is a heuristic on the orchestrator's *output text*, not a proof of
  intent.
- Per #310: prose does not discharge acceptance; the artifact must be
  something that runs and fails on regression.
- Role sessions read board state from merged `main` only, by design (this
  session's own protocol reminder states it verbatim). That invariant is
  not this proposal's to break.
- The `Stop` hook is undeclared but real (2026-08-07 comment on #298);
  declaring it is additive to `hooks.json`, not a new mechanism.
- `gates/gates.py:is_protected` puts `gates/` in `PROTECTED_ROOT_DIRS`, so
  any diff touching `gates/open_work.py` or `gates/test_open_work.py`
  will be flagged `보호 경로 변경` by the `writeset` check — by design
  ("변경되면 무조건 사람에게"), not a defect: this proposal genuinely adds
  gate-shaped infrastructure, and that class of change is supposed to
  force human eyes regardless of role write_scope. Phase 2 must expect
  and accept that escalation rather than route around it (e.g. by hiding
  the new module outside `gates/`, which would only obscure that it is
  gate logic).

## Rationale

**Alternative considered and rejected: expose open PRs/issues to role
sessions directly** (e.g. inject an "in-flight work" summary into every
role session's context at spawn time, so a role session could itself
notice PR #307 exists). Rejected because it directly breaks the
deliberate invariant surveyed above: role-session state would then depend
on which PRs happen to be open at spawn time, which is neither
reproducible from git history nor stable across a session's lifetime (a
referenced PR can merge or close mid-session). The orchestrator already
queries `gh pr list`/`gh issue list` live in several places in
`spawn.py`; it is the actor already designed to see in-flight state, so
correcting a false dilemma belongs at the point where in-flight state is
already visible, not by extending visibility to an actor deliberately
scoped away from it.

**Alternative considered and rejected: try to detect "did the actor check
before asking" from the message text.** #379 itself states this is not
obviously computable, and a heuristic classifier for actor *intent*
(rather than actor *output*) would produce exactly the "checked clean"-
style false confidence #287 warns against — a passing heuristic would be
read as "the actor verified," which it cannot establish. This proposal
instead checks a narrower, mechanical thing: when the orchestrator's
final message contains constraint-framed-choice language, does that
message itself name what was checked (an issue/PR reference)? That is a
property of the text, not a claim about the actor's process.

## What will be done

1. `gates/open_work.py`: `open_work_for(keywords: list[str]) -> dict` —
   shells out to `gh issue list --search` and `gh pr list --search` (open
   state only), returns matched issue/PR numbers and titles. Pure
   function, `gh` calls isolated behind a thin wrapper so tests can mock
   it. This is item 1's mechanical query, reusable by hooks, gates, and
   `spawn.py` alike (not duplicated per-caller as it is today).
2. `on-the-record/hooks/choice-framing-guard.sh`: new `Stop` hook,
   modeled on `deliverable-guard.sh`'s fail-closed/kill-switch shape.
   Reads `last_assistant_message`; if it matches a constraint-framed-
   choice pattern (keyword list, documented as heuristic and
   deliberately over-inclusive — false positives cost one hook rerun,
   false negatives cost a repeat of the #304 incident) AND the message
   text contains no issue/PR reference (`#\d+`) near the constraint
   language, block with a reason naming exactly that gap — same shape as
   #312's fix: name what was searched for (issue/PR mention) and what
   was found (none), not just "blocked." Kill switch `ORCHESTRATE_OFF=1`
   matching the existing convention.
3. `hooks.json`: declare the `Stop` event pointing at the new script.
4. `docs/decisions/2026-08-07-choice-framing-scope.md`: record the item-2
   scope decision (orchestrator boundary, not role-session visibility)
   as an ADR, since it's a hard-to-reverse design choice with a named
   rejected alternative — the doctrine ladder's trigger for `decisions/`.
5. Tests for `open_work.py` (`gh` mocked) and a reproduction test for the
   guard script against the literal #304 transcript shape (message
   offering two workarounds, no issue/PR reference present) asserting it
   blocks, and against a message that does cite `#307` asserting it does
   not.

## Out of scope

- Exposing in-flight/unmerged work to role sessions (item 2's harder
  half) — argued above as a deliberate non-fix, not deferred for lack of
  time.
- Any attempt to classify actor *intent* rather than message *text*.
- Retrofitting `spawn.py`'s existing ad hoc `gh` calls to use
  `open_work.py` — worth doing, not required for #379's acceptance, and
  would widen the write set beyond what this proposal covers.

## How you'll know it worked

- `pytest gates/test_open_work.py` passes with `gh` mocked to return
  both a hit and a miss.
- A reproduction test feeds `choice-framing-guard.sh` a message shaped
  like the actual #304 incident text (workaround-or-wait framing, no
  `#`-reference) and asserts exit code 2 (block) with a reason string
  naming the missing check; feeds it the same message with `#307` cited
  and asserts exit 0.
- `hooks.json` after the change still validates as JSON and declares
  exactly one more event (`Stop`) than before.
