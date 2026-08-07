# Survey — issue #379

## Scope of the survey

#379 has three sub-questions. This survey covers the write surfaces for
each and marks which are actually buildable per the issue's own honesty
requirement ("did this actor check before asking" is not computable from
question text alone).

## Existing mechanisms this builds on

- **Stop hook exists but is undeclared.** `on-the-record/hooks/hooks.json`
  declares only `SessionStart`, `UserPromptSubmit`, `PreToolUse`. Per the
  2026-08-07 comment on #298, Claude Code's `Stop` hook fires on the
  assistant's final turn text (`last_assistant_message`) and can `block`
  with a `reason`, or inject `additionalContext` without blocking. This is
  the only surface that sees an orchestrator's outbound prose before the
  operator does — exactly what item 3 needs.
- **PreToolUse gate pattern**: `on-the-record/hooks/deliverable-guard.sh`
  is the template for a fail-closed hook — bash prefilter, Python payload
  parse via heredoc, `trap` fail-closed on non-0/2, `ORCHESTRATE_OFF`-style
  kill switch, deny-only (never blocks silently, always names the reason).
- **"Report evidence judged on" precedent**: #312 requires a gate refusal
  to state what it searched for and what it found, not just its verdict
  ("no approval for issue-304/implementation; approvals present on this
  issue: architecture"). #287 requires "could not check" to be a distinct,
  named outcome from "checked and clean". Both are refusal-shaped (a gate
  denies a tool call). #379 item 3 asks for the same shape applied to a
  *question* the orchestrator puts to the operator, not a verdict a gate
  returns to a role session.
- **Mechanical open-issue/open-PR lookup**: `spawn.py` already shells out
  to `gh pr list` / `gh issue list` / `gh pr view` in several places
  (`_pr_for_branch`, `_issue_comments`, closure_sweep's `_issue_view`).
  There is no shared, reusable "does an open issue or PR already address
  this keyword/limitation" query — each caller re-implements its own `gh`
  call for its own narrow purpose. `gates/` has no equivalent.
- **`gates/gates.py:check`** is the dispatcher pattern other gates plug
  into (`check(names, d, cfg)` — pure functions over a work dir + config,
  no hook-specific IO). A new mechanical lookup fits better as a plain
  function other things call (a hook, a test, `spawn.py`) than as another
  entry in that specific dispatcher, since it needs live `gh` access, not
  a diff/worktree.

## Write set this proposal will actually touch

- `gates/open_work.py` (new) — the mechanical open-issue/open-PR lookup
  (item 1's "at minimum: is there an open issue, and is there an open PR,
  for this limitation").
- `gates/test_open_work.py` (new) — tests, `gh` calls mocked.
- `on-the-record/hooks/choice-framing-guard.sh` (new) — the `Stop` hook.
  Heuristically detects constraint-framed-choice language in the
  orchestrator's own final message (Korean/English keyword patterns:
  "정해주셔야", "선택", "…거나", "cannot"/"can't" + "or", "would you
  prefer"), and when matched, requires the message to already state what
  was checked (an open-issue/PR mention, per #312/#287's shape) — else
  blocks with a reason naming what's missing, same as
  `deliverable-guard.sh`'s pattern.
- `on-the-record/hooks/hooks.json` — declare the `Stop` event.
- `docs/decisions/` — one ADR for the scope decision on item 2 (below),
  since it is a design choice with a rejected alternative, not an
  implementation detail.

## Item 2 (role-session visibility of unmerged work) — surveyed, not built

The interaction protocol reminder present in this very session states the
existing invariant in plain words: *"The board is what is MERGED to main.
An open PR is not yet on the board; read other roles' state from main,
not from open PRs."* That line is not incidental — role sessions are
scoped to one issue's branch and tree specifically so their state is
reproducible from git history; letting a role session's picture of
"what's possible" depend on which PRs happen to be open at spawn time
would make that picture non-reproducible and race-prone (a PR merges or
closes mid-session). The orchestrator, by contrast, already queries
`gh pr list`/`gh issue list` live in multiple places (`spawn.py`) — it is
the one actor already designed to see in-flight state.

This asymmetry is the survey's finding, and it is what the proposal's
Rationale will argue from: the fix for item 2 belongs at the orchestrator
boundary (mechanical lookup + Stop hook), not at the role-session
visibility boundary. Changing what role sessions see is out of scope for
this proposal; the proposal states why, as the issue asks, rather than
silently omitting it.

## Skip-condition check (scout-directive)

This is not a pure bugfix (item 2 is an open design question) and the
spec does not leave zero design decisions open, so scouting applies in
principle. In practice the only prior art that matters is internal
(#287, #312, #298's Stop-hook comment, `deliverable-guard.sh`) — this is
an internal process-integrity mechanism with no external product category
to benchmark against, and the external claim it rests on (Stop hook
capabilities) is already sourced in #298's comment to the official Claude
Code hooks reference. No additional web sweep was run; stage count: 0
external stages, reason: no comparable external product exists for
"does an orchestrator hedge its own claims to a human operator" — this is
process design internal to this repo, not a product surface with
industry exemplars to benchmark against.
