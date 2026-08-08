# Issue #507 — Phase 1 Proposal (implementation)

files:
- `on-the-record/hooks/retry-loop-bound.sh` (new PreToolUse+PostToolUse
  hook: session-scoped identical-denial counter, K-th corrective
  `additionalContext` injection, 2K-th loud abort of the action class)
- `on-the-record/hooks/hooks.json` (register the new hook for
  `Write|Edit|MultiEdit|Bash` on both `PreToolUse` and `PostToolUse`)
- `on-the-record/hooks/test_retry_loop_bound.py` (new: red-green K/2K
  test using a synthesized issue-474 log-shape fixture, per
  `docs/issue-505/reports/implementation.md:26` and
  `board-gate.sh:512`'s exact message template)
- `docs/issue-507/reports/implementation/survey.md` (this phase's survey,
  already committed)

## Request (paraphrased intent)

#505's slow-session mining found sessions burning 10+ minutes retrying an
*identical* denied write 22-52 times with no adaptation, even when the
gate's own message named the mismatch (board-gate wrong-branch path,
issue-474/147; a sandbox-denied scratchpad path, issue-171/#187). #507
asks for two things: (1) a mechanical bound — after K identical denials
of the same `(tool, target, reason)` in one session, inject a corrective
message quoting the deny reason and the expected-correct value; after 2K,
abort that action class loudly instead of letting it retry forever; (2)
board-gate's own deny message should state the session's exact writable
path, not just name the mismatch.

## Constraints

- Repo boundary (survey, "Repo boundary"): `board-gate.sh` is owned by
  `tokenmaxxxer-core`, a separate repository — not in this write set. No
  file under `tokenmaxxxer-core` is touched by this proposal, matching
  the boundary this repo already drew in
  `docs/issue-100/proposals/coding.md:11,54` for the same gate.
- The hook must persist a counter *across* separate hook-process
  invocations within one session (each `PreToolUse` call is a fresh
  process) — no existing hook here does this; state goes to a
  per-session JSON file keyed by the payload's `session_id`.
- Must follow this directory's existing hook contract: `ORCHESTRATE_OFF`
  kill switch, `CLAUDE_ROLE` early-exit for spawned role sessions
  (mirroring `decision-queue-stopgate.sh`), fail-closed trap, and the
  `{"decision":"block"}` vocabulary already used by
  `decision-queue-stopgate.sh` for the 2K abort. Note (warrant-hunt
  finding, after-proposal transition, `docs/reports/2026-08-08-hunt-retry-loop-bound.md`):
  every existing `additionalContext` emitter in this repo
  (`decision-queue-stopgate.sh`, `stop-gate.sh`, `role-test-claim-guard.sh`)
  is a `Stop`-event hook, not `PreToolUse` — the K-th allow-with-context
  nudge is a new usage of `hookSpecificOutput.additionalContext` on
  `PreToolUse` for this repo, not a copy of an existing PreToolUse
  precedent. Phase 2 must verify against the Claude Code hook schema
  (Claude Code docs, `PreToolUse` supports `hookSpecificOutput` with
  `permissionDecision`/`permissionDecisionReason` as well as
  `additionalContext`) rather than assuming `decision-queue-stopgate.sh`'s
  shape transfers unmodified.
- K and 2K must be visible/tunable, not magic numbers buried in the
  script (an env var default, so a consumer repo can adjust without
  editing the hook).
- The state file is per-session and must not leak across sessions or
  grow unbounded — cleared/ignored once stale (no session_id match).

## Rationale

Considered tracking identical-denial counts **post-hoc in `spawn.py`**,
reusing `_classify_refusal_text`/`_GATE_HOOK_RE` (`spawn.py:1990`,
already parses this exact wire shape per
`docs/issue-235/reports/implementation/survey.md`). Rejected: `spawn.py`
only sees a session's transcript after the session has already run (or
via log tailing it does not currently do live) — it cannot inject a
mid-session `additionalContext` message or abort an in-flight tool call,
which is the actual requirement ("the hook layer escalates... after 2K
abort the action class **for the session**"). Post-hoc mining answers "how
much time did this cost," which is #505's job and already done; #507
needs to act *while* the loop is happening, which only a live
PreToolUse/PostToolUse hook pair can do. Chose the hook-pair design
instead: a `PostToolUse` observer classifies a denial (reusing the same
`PreToolUse:<tool> hook error: [...]`/`<gate>: refused —` wire shape
`_GATE_HOOK_RE`/`_GATE_DENY_RE` already parse) and bumps a per-session
counter keyed by `sha256(tool_name, normalized target, gate/reason)`; a
`PreToolUse` gate on the same matchers checks that counter before the
*next* identical attempt — at K it allows through but adds
`additionalContext` quoting the deny reason and, when the message text
contains an extractable expected value (e.g. board-gate's own `(current:
issue-<n>)` / `requires branch issue-<n>/<role>` text), that value; at 2K
it denies outright (fail loud) with a record-worthy message naming the
signature and count, independent of what the underlying gate would have
said.

## What will be done

- Add `retry-loop-bound.sh`, registered twice in `hooks.json`:
  - `PostToolUse` (`Write|Edit|MultiEdit|Bash`): on a matched deny-shaped
    `tool_response` (anchored `PreToolUse:\S+ hook error: \[...\]`
    prefix, per issue-235's Point-2 anchoring lesson — no unanchored
    `.search()`), compute the signature and increment
    `<state-dir>/<session_id>.json[signature].count`.
  - `PreToolUse` (`Write|Edit|MultiEdit|Bash`): look up the *incoming*
    request's signature in the same state file before the underlying
    gates run. `count == K` → allow (exit 0) plus
    `hookSpecificOutput.additionalContext` quoting the last deny reason
    and any extracted expected-value substring. `count >= 2K` → deny
    (exit 2) with a message stating the signature, the count, and that
    the action class is aborted for this session (loud record entry, per
    #507's wording) — the underlying gate is never consulted again for
    that exact signature.
- State file: `${TMPDIR:-/tmp}/otr-retry-bound/<session_id>.json` (or
  `ORCHESTRATE_OFF`-style env override for tests), a flat `{signature:
  {count, last_reason, first_seen}}` map; missing/unparseable state
  treated as empty (fail open on the *counter*, never silently fail open
  on the surrounding gate's own deny — this hook only adds behavior on
  top of, never instead of, the existing gates).
- `test_retry_loop_bound.py`: red-green pair per Acceptance — a fixture
  built from #505's issue-474 citation and `board-gate.sh:512`'s exact
  message template (25 identical `docs/issue-416/...` writes from an
  `issue-474/implementation` session): red = pre-hook behavior (nothing
  bounds the 25th identical retry), green = with the hook, the K-th call
  carries `additionalContext`, the 2K-th is denied with the abort
  message. A second fixture covers a *non*-identical sequence (denials
  differ by target) to assert the counter does not falsely trip.

## Out of scope

- Editing `board-gate.sh` itself (the "board-gate deny names the
  session's writable path" half of #507's Acceptance) — that file is
  owned by `tokenmaxxxer-core`, outside this repo's write set (see
  Constraints). This proposal's corrective-injection message already
  extracts and surfaces board-gate's *existing* `(current: issue-<n>)` /
  `requires branch issue-<n>/<role>` text as part of the K-th nudge, which
  covers #507's live-loop-breaking goal without editing the gate — but
  the acceptance line "board-gate test asserts the corrected-path string
  in the deny output" needs its own issue against `tokenmaxxxer-core`,
  same pattern as `docs/issue-100/proposals/coding.md`'s equivalent
  carve-out.
- Any gate other than the ones already wired through
  `PreToolUse:Write|Edit|MultiEdit|Bash` in `hooks.json` (e.g. no new
  coverage for `NotebookEdit`-only deny paths).
- Cross-session persistence or reporting (the counter is per-session and
  local to the hook; no aggregation into `spawn.py`'s mining).

## How you'll know it worked

- `on-the-record/hooks/test_retry_loop_bound.py` passes: the K-th
  identical denial in the fixture produces `additionalContext` quoting
  the deny reason and the extracted expected-branch text; the 2K-th
  produces a deny (exit 2) whose stderr states the signature was aborted
  for the session; a non-identical denial sequence never trips either
  threshold (red case demonstrated failing against pre-change `main`
  first, per contract's red-green requirement).
- `pytest on-the-record/hooks/` green alongside the existing suite
  (`test_contract_guard.py`, `test_decision_queue_stopgate.py`, etc. —
  no regression).
