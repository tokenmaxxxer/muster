# Issue #507 — current-state survey

## Repo boundary (load-bearing)

This session's write set is `on-the-record` (`tokenmaxxxer/on-the-record`,
this checkout). `board-gate.sh` — the gate issue #507 names directly for
the deny-message change — lives in `core/hooks/board-gate.sh` in the
**separate** `tokenmaxxxer-core` repository
(`/home/jwjung/tokenmaxxxer-core/core/hooks/board-gate.sh`, confirmed by
direct read this session). This repo's own prior proposal for a related
gate change stated the same boundary explicitly and left `board-gate.sh`
untouched (`docs/issue-100/proposals/coding.md:11,54`: "No file under
`tokenmaxxxer-core` (the repo that owns `board-gate.sh`) is touched...
that would need its own issue in that repo"). #507's phase 1 in *this*
repo inherits that boundary; the board-gate message change is scoped
accordingly (see proposal Out of scope).

Read `board-gate.sh:494-515` directly (R4, the branch-mismatch check the
#505 mining hit): the current deny text is

```
writing docs/%s/ requires branch %s (current: %s). Every role writes
its own board only from its own issue branch — never a direct write
from another branch. (contract v3 s10)
```

— it names the *expected branch* and the *current (wrong) branch*, but
never spells out the corrected **file path** the session should retry
with (e.g. `docs/issue-474/...` instead of the `docs/issue-416/...` it
kept retrying in the #505-mined log). That gap is exactly what #507's
half 2 asks to close, and it is a `tokenmaxxxer-core` file — out of this
write set.

## What #505 already measured (the fixture source)

`docs/issue-505/reports/implementation.md:26-27,47-70` (landed, this
repo) is #507's direct upstream. Two concrete log citations for the
identical-retry shape:

- issue-474 session (this repo):
  `on-the-record-issue-474-implementation.session.20260808T185416.615087.log:L219-L600`
  — 25 identical `board-gate.sh` R4 refusals against a self-generated
  `docs/issue-416/...` path while the session's own branch was
  `issue-474/implementation`; path never corrected between retries.
- issue-147 session (`tokenmaxxxer-core`):
  `tokenmaxxxer-core-issue-147-implementation.session.20260808T180551.278899.log:L24-L563`
  — same shape, 22 refusals.

Neither raw `.log` file is present in this checkout (they live under
each session's own `runs/` tree, not this repo) — the fixture for the
K/2K test must therefore reconstruct the *shape* (repeated
`PreToolUse:Write hook error: [.../board-gate.sh] board-gate: refused —
writing docs/issue-416/... requires branch issue-474/implementation
(current: issue-474/implementation)...`-style payload) from #505's
citation and `board-gate.sh:512`'s exact message template, not replay a
literal log file. This matches how existing fixtures in this repo's hook
tests are built (e.g. `on-the-record/hooks/test_contract_guard.py`'s
`FAKE_GH` fixture — synthesized payloads shaped like the real thing, not
raw captures).

## Existing hook composition pattern in this repo

`on-the-record/hooks/hooks.json` registers per-matcher `PreToolUse` and
`Stop` hook chains; scripts read a JSON payload from stdin (`tool_name`,
`tool_input`, plus harness-supplied `session_id`/`transcript_path`,
observed via other hooks' payload handling) and either exit 0 (allow),
exit 2 with stderr text (deny), or emit `{"hookSpecificOutput": {...,
"additionalContext": "..."}}` on stdout for a non-blocking nudge — the
exact vocabulary #507 asks for (corrective injection vs. loud abort):

- `decision-queue-stopgate.sh` (`on-the-record/hooks/decision-queue-stopgate.sh`)
  is the closest existing precedent for #507's two-tier escalation: tier 1
  (`age_hours >= 1`) emits a non-blocking `additionalContext` reminder;
  tier 2 (`>= 4`) emits `{"decision": "block", "reason": ...}`, a stronger
  in-band nudge. #507's K/2K is the same two-tier shape (K = soft
  correction, 2K = loud/blocking), on a different signal (identical-denial
  count vs. queue age).
- `deliverable-guard.sh` / `contract-guard.sh` show the deny-only,
  fail-closed style (`trap ... EXIT`, `ORCHESTRATE_OFF` kill switch,
  `CLAUDE_ROLE` early-exit for spawned role sessions) every hook in this
  directory follows.
- No existing hook here tracks state *across* invocations within one
  session — every current hook is stateless per call (reads the current
  payload only). #507's mechanism is new: it needs a session-scoped
  counter keyed by `(tool, target, reason)`, persisted between PreToolUse
  invocations for the same `session_id`.

## `_classify_refusal_text` (spawn.py) — a second, non-live precedent

`spawn.py:1990` (`_classify_refusal_text`) and its supporting regexes
(`_GATE_HOOK_RE`, `_GATE_DENY_RE`, documented further in
`docs/issue-235/reports/implementation/survey.md`) already parse the
*same* `PreToolUse:<tool> hook error: [<path>]` / `<gate>: refused — ...`
shape this issue's fixture needs, but only **post-hoc**, off a finished
session's log — it is #505's mining tool, not a live hook, and it has no
notion of "identical denial count within a session" (issue-235's survey
documents its known correlation gaps). It confirms the wire shape to
build the K/2K fixture against, but is not itself a mechanism #507 can
extend for live intervention (wrong layer: batch analysis vs. per-call
hook).

## Where a new hook would need to persist counts

No existing hook in this repo writes session-scoped state to disk today.
`decision-queue-stopgate.sh` recomputes its answer fresh every call from
`spawn.py flows --json` (no local state). A K/2K counter must persist
between separate hook process invocations (each `PreToolUse` call is a
fresh `bash`/`python3` process) — needs a small per-session JSON file,
keyed by the payload's `session_id` (present in the standard Claude Code
hook payload; not yet read by any hook in this directory, confirmed by
`grep -rn session_id on-the-record/hooks/*.sh` returning nothing).

## Alternatives visible from this survey (for the proposal's Rationale)

1. Track identical-denial counts in **spawn.py** (post-hoc, reusing
   `_classify_refusal_text`) and have it inject correction on the *next*
   spawned turn. Rejected direction to weigh: spawn.py only sees a
   session after it ends (or via log tailing it does not currently do
   live) — it cannot inject a mid-session `additionalContext` or abort an
   in-flight tool call, which is exactly what #507 requires ("after K...
   the hook layer escalates... after 2K abort the action class").
2. Track identical-denial counts in a **new PreToolUse/PostToolUse hook
   pair** in `on-the-record/hooks/`, persisting a per-session counter file
   — live, in-band, matches the `hookSpecificOutput`/`decision:"block"`
   vocabulary already used by `decision-queue-stopgate.sh`. This is the
   only option that can act *during* the session the #505 mining
   measured minutes lost in.

## Skip conditions checked

Neither scout-directive skip condition applies (this is not a pure
bugfix — the persistence mechanism and signature/thresholds are open
design choices; the spec does not pin an implementation). A scout pass
was run: internal precedent only (this repo's own hook directory and
`spawn.py`/`docs/issue-235`, `docs/issue-100` prior art), no external web
sweep — the deliverable is an internal session-harness safety hook, not a
product-shaped surface with an external best-in-class category to
benchmark against; scout-brief.md is therefore not written per the
scout-directive's product-shaped-only external-sweep expectation, and the
"considered/rejected" alternatives above are drawn from this internal
survey instead.
