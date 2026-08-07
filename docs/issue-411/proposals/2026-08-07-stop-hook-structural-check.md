---
status: proposed
files:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/stop-gate.sh
  - tests/test_stop_gate.sh
  - docs/issue-411/decisions/2026-08-07-stop-hook-enforcement-scope.md
---

References #411.

## Request

Six prior requirements (#318, #320, #341, #371, #373, #379) were designed
assuming some hook inspects what the orchestrator says to the operator.
None does — `hooks.json` declares no `Stop` entry, and none of the
`check()`/`*-check.sh`/`*-guard.sh` functions those six proposals planned
were ever built. The operator's standard: mechanism doesn't matter, only
that the requirements are actually kept. Decide whether/how to inspect
`last_assistant_message`, what such a check can structurally reach versus
not, block-vs-soft-correction on violation, and — per #310 — record which
of the six remain genuinely unenforceable rather than implying full
coverage.

## Constraints

- Follow `deliverable-guard.sh`'s house style: bash wrapper, fail-closed
  `trap`, `CLAUDE_ROLE` pass-through, cheap prefilter before embedded
  Python, no new dependency.
- Stay inside #298's boundary: #298 scopes itself to `gh pr merge` /
  `gh issue comment ... APPROVE` (two Bash-command acts), not
  conversational-text checks. #411 does not fold into #298 and does not
  touch #298's files.
- Do not claim substance-level enforcement anywhere a check can only
  reach structure — the line drawn below is stated in the proposal text,
  not left implicit.
- Ship exactly one real, wired, tested check this proposal — not five
  heuristics of uneven quality. The other five get an honest coverage
  verdict, not a build.

## Rationale

**Chosen approach**: declare `Stop` in `hooks.json`, wire one new script
`stop-gate.sh` that runs a single structural check derived from #318 (does
an approval-shaped reply name its issue with `#<n>`, state what changes,
state a risk/tradeoff), and on violation emit
`hookSpecificOutput.additionalContext` — a correction requirement injected
into the same turn — rather than `decision: "block"`.

**Alternative considered and rejected**: build all three of #318's,
#320's, and #379's planned checks in this pass, since all three sketch a
Stop-hook handler already. Rejected: #320 and #379 are honesty/framing
judgments (did the report explain *effect* not enumerate; did the
orchestrator *actually* re-check a constraint) that a substring/regex
heuristic cannot reliably tell apart from the reverse case — shipping them
now would repeat exactly the failure #411 names, a check that verifies
the wrong thing while implying real coverage. #318's requirement
(issue-number present, a change clause present, a risk clause present) is
the one item structurally checkable with low false-positive risk, so it
is the one built; the rest are recorded as open per #310, not built badly.

**Alternative considered and rejected (blocking)**: use
`decision: "block"` on violation, matching `deliverable-guard.sh`'s
deny-and-exit-2 shape. Rejected: a structural heuristic will misfire on
a legitimately-shaped reply that phrases things unusually, and discarding
the whole turn on a soft/heuristic violation is disruptive out of
proportion to what the check can actually prove.
`hookSpecificOutput.additionalContext` requires a correction in the same
turn without destroying already-produced work — the better fit for a
check whose ceiling is structural, not substantive.

## What will be done

1. `on-the-record/hooks/stop-gate.sh` — Stop hook, orchestrator-only
   (`CLAUDE_ROLE` set → pass-through, matching `deliverable-guard.sh`).
   Reads `last_assistant_message` from the hook payload. Only fires when
   the message looks approval-shaped (contains an approval-request
   trigger phrase, e.g. "승인" / "approve" / "APPROVE issue-"). When it
   fires: checks for (a) an issue reference `#\d+`, (b) a change-statement
   clause, (c) a risk/tradeoff clause. Missing any → emits
   `hookSpecificOutput.additionalContext` naming exactly which clause is
   missing. All three present → exit 0, no output. Non-approval-shaped
   messages → exit 0 immediately (no false-positive risk on ordinary
   turns). Fails closed (`trap` remaps non-0/2 exit to 2) but a Stop hook
   exit 2 blocks the stop, not the tool — tested explicitly.
2. `hooks.json` gains a `Stop` entry pointing at `stop-gate.sh`.
3. `tests/test_stop_gate.sh` — behavioral: feeds a synthetic
   `last_assistant_message` that is approval-shaped but omits the risk
   clause through `stop-gate.sh` via stdin JSON, asserts
   `additionalContext` names the missing clause (the check fires, not
   merely exists); a second fixture with all three clauses asserts
   silent exit 0; a third, non-approval-shaped message asserts pass-through.
4. `docs/issue-411/decisions/2026-08-07-stop-hook-enforcement-scope.md` —
   the line-drawing record: which of the six get real coverage from this
   Stop hook and which don't, with reasons, so an unchecked rule is never
   read as an enforced one:
   - **#318** — structural subset (issue ref / change clause / risk
     clause) enforced by `stop-gate.sh`. The six-item full shape and
     whether the *stated* risk is the *real* risk remain unenforced —
     substance, not structure.
   - **#320** — unenforced. Distinguishing "explains effect" from
     "enumerates changes" is a judgment call a heuristic cannot make
     reliably; recorded open, not built.
   - **#341** — unenforced by this proposal, but its own "not
     mechanically enforceable" premise is now stale (a Stop hook does
     reach the conversational turn it assumed was unreachable);
     flagged for #341 to reopen against, not resolved here (scope
     discipline — this proposal's write set does not include #341's
     record).
   - **#371** — unenforced by a Stop hook and cannot be: it is a
     status-computation defect inside `spawn.py`, not a claim made in
     chat text. Wrong mechanism; no Stop-hook check applies.
   - **#373** — unenforced. Same shape as #320 (delta-stated-or-not is a
     judgment call); recorded open.
   - **#379** — unenforced. Whether the orchestrator *actually*
     re-checked a constraint before offering a choice is not observable
     from the reply text alone; recorded open.

   Net: 1 of 6 gets real, firing, tested coverage (#318, structural
   subset only). 5 of 6 remain open, each with its specific reason, per
   #310.

## Out of scope

- Building #320's, #341's, #371's, #373's, or #379's checks.
- Touching #298's files or scope.
- Rewriting `commands/run.md`'s six-item text (that is #318's own file
  once #318 itself lands).
- Any change to `deliverable-guard.sh` or existing `PreToolUse` gates.

## How you'll know it worked

`tests/test_stop_gate.sh` passes and demonstrates all three cases: (1) an
approval-shaped reply missing the risk clause is caught —
`additionalContext` names it; (2) a compliant approval-shaped reply
passes silently; (3) a non-approval-shaped reply is untouched. This is
the behavioral proof the issue asks for: a reply that violates one of the
six, shown caught by a firing hook, not a test asserting the hook is
merely declared.
