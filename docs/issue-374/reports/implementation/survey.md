# Survey — issue #374

## Scope skip record

Scouting (external best-in-class sweep) is skipped: this is an internal
orchestration-harness fix with no external product category to compare
against — the comparable prior art is this repo's own sibling issues
(#325, #333, #341, #298's 2026-08-07 comment) and its own hook
infrastructure (`on-the-record/hooks/`). That internal survey is done
below in place of an external sweep.

## Where `decision_queue` is actually computed

`gates/flows.py:257` `flows_payload()` builds `decision_queue` (line
306-326) by walking every open PR whose branch matches
`issue-<n>/<role>` and keeping the ones `_pr_approved()` (line 130)
finds no approval for — either an exact `APPROVE issue-<n>/<role>`
comment from a `docs/specs/approvers.md` login, or a PR review
`APPROVED` from one. `spawn.py flows --json` exposes this as-is;
`spawn.py flows` (no `--json`) prints it as prose (line 428-431).

Ran it against the live repo state today (2026-08-07, ~06:22 UTC):

```
decision_queue entries: 10
  issue-298  pr-299  age 4.7h (oldest, matches the issue text)
  issue-303  pr-306  age 1.9h
  issue-304  pr-307  age 1.8h
  issue-318  pr-338  age 1.2h
  issue-320  pr-342  age 1.1h
  issue-324  pr-339  age 1.2h
  issue-358  pr-359  age 0.9h
  issue-362  pr-365  age 0.7h
  issue-363  pr-366  age 0.6h
  issue-371  pr-372  age 0.1h
```

All ten are real, live, unapproved open PRs — confirms the issue's
claim still holds at the moment of this survey, not just when the
issue was filed.

## Resolving the #289/#290/#301 discrepancy (issue's explicit precondition)

Traced each of the three PRs (`#300`→#289, `#295`→#290, `#302`→#301)
through `_pr_approved()` directly against live `gh` data:

| issue | PR | comments found | `_pr_approved()` |
|---|---|---|---|
| #289 | #300 | `APPROVE issue-289/implementation` (from `JiwonJung94`, a listed approver) present | `True` |
| #301 | #302 | `APPROVE issue-301/implementation` present | `True` |
| #290 | #295 | `APPROVE issue-290/implementation` present, **followed by** a later "Not accepted yet — ..." rejection comment | `True` |

All three carry a valid `APPROVE issue-<n>/implementation` comment from
an approvers.md account. `decision_queue` only lists PRs where
`_pr_approved()` returns `False` — i.e., items still *awaiting* the
approve-scope/approve-full decision. These three already received that
decision; they are not awaiting one. Their absence from the queue is
correct, not under-reporting.

`#290` is the interesting case: the approval comment exists, but a
later comment on the same thread says "Not accepted yet" with a failing
check. `_pr_approved()` treats approval as a one-way gate — once a
matching `APPROVE` comment is found, later commentary cannot revoke it
(the function does no comment-ordering or negation logic; role-handoff
contract v3 s19's approval mechanism is deliberately a single
string-equality event, not a running consensus). So #290 is correctly
out of `decision_queue` (no *scope* decision pending) but is stuck for a
different reason — post-approval rework not yet resubmitted — which is
outside `decision_queue`'s definition (`awaiting: approve-scope /
approve-full`) and outside this issue's boundary (closer to #371's
"degrees of doneness" concern). Not fixing that here; noting it so the
proposal doesn't quietly assume `decision_queue` covers all stuck work.

**Conclusion: the queue does not under-report. Item 1 of "What needs
deciding" and everything downstream can be built directly on this data
without first fixing the queue itself.**

## Where the orchestrator's reply text is reachable

`on-the-record/hooks/hooks.json` declares `SessionStart`,
`UserPromptSubmit`, `PreToolUse` — no `Stop`. Per the 2026-08-07 comment
on #298 (Claude Code hooks reference, checked that date), a `Stop` hook
fires when the assistant finishes a turn, receives `last_assistant_message`
(the turn's final text) and `session_id`/`transcript_path`, and can
return `decision: "block"` + `reason` to force another turn, or
`hookSpecificOutput.additionalContext` to inject text without blocking.
This closes the "orchestrator cannot be reached mechanically" gap the
issue explicitly rules out as an answer.

`on-the-record/hooks/directive.sh` (`UserPromptSubmit`) is the existing
precedent for "inject fresh guidance every turn so it can't drift out of
context" — it already tells the orchestrator, in prose, to open every
reply by re-anchoring "what is currently waiting on the user's
decision." That instruction is exactly this issue's ask, already
written down, and — per the issue — provably not read: the orchestrator
drove twenty new issues without once surfacing the ten-item queue. Prose
guidance inside a system prompt is not a mechanism; nothing enforces it.
`directive.sh` also establishes the kill-switch and role-detection
conventions (`ORCHESTRATE_OFF`, `CLAUDE_ROLE` early-exit) any new hook
in this plugin should reuse rather than reinvent.

## Adjacent issues actually checked (not just cited)

- `#325` — covers a spawned session that never runs or stalls silently.
  Confirmed distinct: all ten queue items here have a running-to-completion
  phase-1 session behind them (PR exists, checks green). #325's coverage
  check would mark all ten as covered; that's the gap this issue names.
- `#371` — status-report shape. The queue items are real PRs in real
  `OPEN` state; #371 is about a report collapsing states that already
  differ, not about items missing from the report's input entirely. This
  issue is upstream of that: the items need to *reach* a report first.
- `#319` — batches/risk-classifies approval requests once they reach the
  operator. Assumes arrival; this issue is about arrival itself.
- `#327` — idle time as a defect. Checked whether its measurement window
  distinguishes "idle waiting on a human" from "idle and forgotten": no
  such distinction exists in `gates/flows.py`'s `sessions` block (session
  liveness only, `roster`/`ledger`-based) — a decision-queue item has no
  running session at all by the time it's waiting, so #327's idle-session
  measurement doesn't see it either way. Confirms the boundary the issue
  draws: this is a genuinely uncovered state, not a duplicate of #327.

## Write surface this proposal will need

- `on-the-record/hooks/hooks.json` — register a `Stop` hook.
- `on-the-record/hooks/decision-queue-nudge.sh` (new) — the hook script:
  shells out to `spawn.py flows --json`, reads `decision_queue`, decides
  whether/how to surface it.
- A test exercising the hook against a fixture (and, per the issue's own
  instruction, against today's live repo state) — likely
  `test_decision_queue_nudge.py` at repo root, matching the existing
  `test_flows.py` / `test_spawn.py` sibling convention (flat files, not
  `test/`).
- `protocol.md` / `protocol.ko.md` — if the nudge changes what the
  orchestrator is contractually expected to do each turn, that
  expectation belongs in the protocol text next to the existing
  `directive.sh`-sourced instruction, not only in the hook's behavior.

No new dependency, no new env var beyond the existing `ORCHESTRATE_OFF`
kill-switch convention (reused, not added), no schema change to
`decision_queue` itself — `opened_at`/`age_hours` already exist per the
issue's own framing ("this need not be tracked separately").
