# Survey: #414 — stated-intention-not-executed pattern

## Current state

- `on-the-record/hooks/hooks.json` declares `SessionStart`, `UserPromptSubmit`,
  `PreToolUse` only. **No `Stop` key exists on main** — #411 (PR #413,
  merged) landed phase-1 (survey + proposal) only; its planned
  `stop-gate.sh` and the `Stop` hooks.json entry were never built. There
  is currently zero code that reads `last_assistant_message`.
- `tests/run-orchestrate-tests.sh` is the one test runner; it drives
  `hooks.json`, `directive.sh`, `deliverable-guard.sh`. No `Stop`-hook
  test exists yet (`tests/test_stop_gate.sh` from #411's proposal was
  never created).
- `gates/` (repo root, separate from `on-the-record/`) covers
  issue-bundling, acceptance, skip, spawn-coverage, closure-sweep, etc.
  — all `PreToolUse`/CI-time gates over commits/PRs, none over
  conversational turn text. Per #398, `gates/` cannot collect standalone
  under pytest module-name collisions; ignored below, not fixed here
  (out of scope for #414).
- Five prior open issues (#320, #373, #374, #376, #379) already analyzed
  `Stop`/`last_assistant_message` for *other* judgments (semantic-effect
  reporting, choice framing, decision-queue nudge) — none merged code
  either. #411's decision record (never written, since #411 stalled at
  phase 1) was meant to be the single place tracking which of #318/#320/
  #341/#371/#373/#379 get real coverage. #414 is explicitly a *seventh*
  instance in that family per the issue body, told to build on #411
  "rather than inventing a parallel mechanism" — but #411 shipped no
  mechanism to build on. This survey treats #411's unbuilt proposal as
  design precedent (file layout, fail-closed trap style, `CLAUDE_ROLE`
  pass-through, `additionalContext`-not-`block` posture) without
  depending on any of its code existing.

## What #414 needs that #411's design does not cover

#411's structural check only fires on *approval-shaped* replies and only
checks for issue-ref/change-clause/risk-clause presence. #414's pattern
is different: a reply anywhere states a **future intention** ("~하겠습니다",
"will do X next", "지금부터 ~ 뚫겠습니다") and the *next* turn's actions must be
checked against it. This requires **cross-turn state** — #411's check is
single-turn structural matching; #414 needs the last turn's stated
intention persisted somewhere a later turn (or its own Stop hook) can
compare against.

Grep of `on-the-record/hooks/` confirms no existing mechanism persists
anything across turns — `SessionStart`/`UserPromptSubmit`/`PreToolUse`
hooks are all stateless. Nothing to reuse; a persistence file is new
surface.

## Write set this implies

- `on-the-record/hooks/stop-gate.sh` (new) — Stop hook: (a) detect an
  "I will do X" / "지금부터 ~하겠습니다" style stated-intention clause in
  `last_assistant_message`; on detection, write it to a durable
  per-session marker file; (b) on every Stop firing, check whether a
  marker from the *previous* Stop exists and was not cleared, and if so
  require the current message to either report the promised action
  done, or explicitly say it was dropped and why (per issue's ask #3).
- `on-the-record/hooks/hooks.json` — add `Stop` entry.
- `tests/test_stop_gate.sh` (new) — behavioral fixtures.
- `docs/issue-414/decisions/` — record of which of the four "what needs
  deciding" items get real coverage and which do not (per #310), plus
  the phrasing-coverage disclosure the issue explicitly demands
  ("state plainly what phrasings it misses").

## Constraints found in repo

- House style (`deliverable-guard.sh`): bash wrapper, `trap` fail-closed,
  `CLAUDE_ROLE` pass-through (skip on role sessions — orchestrator-only
  concern), cheap prefilter before embedded Python, no new dependency.
- #298 boundary: scoped to `gh pr merge`/`gh issue comment ... APPROVE`
  acts, not general conversational-text checks — #414 does not touch
  #298's files.
- #411's own alternative-rejected reasoning applies directly here too:
  a regex/substring heuristic cannot tell "stated but will drop
  legitimately" from "silently dropped" — so blocking (`decision:
  "block"`) on a bare intention statement is disproportionate; the
  correction path is `additionalContext`, matching #411's precedent.

## Scout brief

See `docs/issue-414/reports/implementation/scout-brief.md`.
