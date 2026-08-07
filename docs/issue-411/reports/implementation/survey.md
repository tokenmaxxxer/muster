# Survey — issue #411

## Current state (measured)

`on-the-record/hooks/hooks.json` declares `SessionStart`, `UserPromptSubmit`,
`PreToolUse` only. No `Stop` key. Grep for `last_assistant_message`,
`additionalContext`, `hookSpecificOutput` across `gates/*.py` and
`on-the-record/hooks/*.sh` returns nothing — confirmed.

`on-the-record/hooks/deliverable-guard.sh` is the only hook that inspects
orchestrator *action* (PreToolUse on Write/Edit/MultiEdit/NotebookEdit,
substring-checks the tool payload for `src/|test/|docs/`, denies by exit 2,
fails closed on non-0/2 exit via `trap`). It never sees conversational text.

## The six requirements — what each actually specifies and enforces today

None of the six is merged to `main`; each exists only as
`status: proposed` under `docs/issue-<n>/proposals/` (or, for #341, a
phase-2 `docs/issue-341/reports/implementation.md`).

- **#318** (`docs/issue-318/proposals/2026-08-07-approval-request-content-shape.md`) —
  approval requests must carry six items (requirement link; investigated/
  concluded; structural change; newly possible/impossible; rejected
  alternative + reason; accepted risk/tradeoff). Ships a pure function
  `check(message)` intended for a `Stop` hook, but its own text explicitly
  **defers declaring `hooks.json`'s `Stop` entry to #298** — the function
  exists nowhere in the tree (`find` confirms no `approval_request_check.*`
  file). Enforcement today: a presence test that `run.md` still contains
  the six-item sentence.
- **#320** (`docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md`) —
  reports must state problem solved / prior cost / newly possible / still
  open, not enumerate changed files. Plans a real `report-framing-check.sh`
  Stop handler; also unbuilt (`find` confirms no `report-framing-check.*`).
  Negotiates Stop-hook ownership with #318 ("whichever lands on main first
  declares the entry") — neither has landed it.
- **#341** (`docs/issue-341/reports/implementation.md`) — "every
  orchestrator-stated constraint names its enforcer." Explicitly recorded
  as **not mechanically enforceable**, on the premise that orchestrator
  turns are not a git-tracked artifact. That premise is now stale: a
  `Stop` hook receives exactly the untracked conversational turn this
  record assumed was unreachable. Only a narrow proxy landed
  (`t_spawn_has_no_concurrency_limit` in `test_gates.py`, checks
  `spawn.py` source, not conversation).
- **#371** (`docs/issue-371/proposals/2026-08-07-status-state-vocabulary.md`) —
  `spawn.status()` must distinguish delivered/blocked/merged-unverified/
  rejected from `gh`-backed state, not self-asserted `loop_state`. This is
  a status-computation fix inside `spawn.py`, not a claim the orchestrator
  makes in chat — a `Stop`-hook text check cannot reach it; wrong
  mechanism entirely.
- **#373** (`docs/issue-373/proposals/2026-08-07-delta-declaration-and-remainder-linkage.md`) —
  a proposal delivering less than asked must say so, track the remainder
  as its own issue, and the orchestrator's relay must state the delta.
  The relay-states-the-delta half is a conversational-text claim,
  structurally similar to #318.
- **#379** (`docs/issue-379/proposals/2026-08-07-choice-framing-guard.md`) —
  before offering a constraint-framed choice, check whether the
  constraint still holds. Plans `choice-framing-guard.sh` + `hooks.json`
  Stop wiring; unbuilt. Its own text already states "the `Stop` hook is
  undeclared but real... declaring it is additive, not a new mechanism."

`#310`'s rule, cited by all six: a doc sentence with a presence test is
not an executable check that fails on regression.

## #298 — scope check

`docs/issue-298/proposals/2026-08-07-orchestrator-enforcement.md`
(`status: proposed`, unmerged) scopes itself to exactly two **Bash-command
acts** by the orchestrator: `gh pr merge` and
`gh issue comment ... APPROVE`, gated via a new
`orchestrator-state.sh`/`orchestrator-gate.sh` pair. Its own `files:`
frontmatter lists no `Stop` hook, no conversational-text check. The
Stop-hook linkage exists only in #318/#320/#379's prose *about* #298, never
in #298's own scope. #298 is real and unmerged, but it does not cover
`last_assistant_message` inspection — #411 is a separate, smaller,
prerequisite decision, not a subset of #298.

## Gate house style (from `deliverable-guard.sh`)

Bash wrapper: `trap` remaps non-0/2 exit to 2 (fail closed); kill switch
env var checked first; `CLAUDE_ROLE` set → pass-through (role sessions
exempt, this gate is orchestrator-only); cheap substring prefilter before
invoking embedded Python; Python does the real decision via `deny(msg)` →
stderr + exit 2; exit 0 = allow. A new Stop gate should read
`last_assistant_message` the same way `deliverable-guard.sh` reads
`tool_input`, and should emit `hookSpecificOutput.additionalContext`
rather than `deny`+exit-2 when the violation is a soft/heuristic one (see
Rationale below) — a different output shape than any existing gate here,
so it is new plumbing, not a copy.

## Test house style (`gates/test_gates.py`, repo-root `test_gates.py`)

Functions named `t_<behavior>()`, self-contained assertions, `report()`
harness. Nearest analogues for "feed a payload, assert the decision":
`t_writeset_fail_closed` (malformed payload → fail closed).
