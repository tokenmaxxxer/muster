---
kind: decision
date: 2026-08-03
status: landed
subject: issue-232
---

# `.events.jsonl` tool-refusal event taxonomy

`spawn.py watch`'s single `gate-refusal` event type is replaced by four
distinct event types for a denied-tool `tool_result`, classified inline in
`_spawn_one`'s per-line stream-json loop (spawn.py:2676-2690) from text
already present in the session log — no new instrumentation.

## Event types

- **`gate-refusal`** — the tokenmaxxxer gate plane (this project's own
  `PreToolUse` hooks, via `gate-lib.sh`'s `gate_deny`). Fires only on a
  confirmed match of `PreToolUse:\S+ hook error: \[...\]`, optionally
  followed by `gate_deny`'s own `<gate>: refused — <reason>` text.
- **`harness-refusal`** — Claude Code's own permission layer (missing
  approval, unparseable shell syntax, etc).
- **`sandbox-refusal`** — the OS/sandbox layer (filesystem permission
  denials, ungranted write paths).
- **`unclassified-refusal`** — fallback: the terminal `result` line's
  `permission_denials` is non-empty but no per-line `tool_result` in this
  session classified into any of the three layers above (e.g. a
  truncated/dropped stream line broke the correlation). Exists so a real
  denial is never silently dropped, and so a correlation miss cannot
  masquerade as a confirmed layer finding.

## `detail` shape

- `gate-refusal`: `{"gate": "<gate-name>", "reason": "<text, capped 300 chars>"}`.
  `gate` is read first from `gate_deny`'s own `<gate>: refused —` message
  token (present whenever a rulebook gate uses `gate-lib.sh`, which is
  the house standard per `core/hooks/lib/gate-lib.sh`); if that token is
  absent, `gate` falls back to the hook script's basename (path stem)
  from the `PreToolUse` wrapper text.
- `harness-refusal` / `sandbox-refusal`: the matched `tool_result` text,
  capped 300 chars (plain string, not a dict).
- `unclassified-refusal`: `str(permission_denials)[:200]` — same shape as
  the event this type replaces for the correlation-miss case.

## Layer-signature patterns

Built verbatim from issue #232's own cited real-session sample strings —
see `spawn.py`'s `_GATE_HOOK_RE`, `_GATE_DENY_RE`,
`_HARNESS_REFUSAL_PATTERNS`, `_SANDBOX_REFUSAL_PATTERNS` (spawn.py, just
above `_tool_result_text`). Extending these to a new sample requires
citing the issue/incident the sample came from, per the same standard
this set was built to — no speculative pattern additions.

## Per-session dedup

Replaces the old single `gate_refusal_seen: bool` with `refusals_seen: set`
keyed by `("gate", <gate-name>)` / `("harness",)` / `("sandbox",)` /
`("unclassified",)` — each distinct layer (and, for gate refusals, each
distinct gate) reports at most once per session, preserving the existing
"report once, not once per denial" behavior while no longer collapsing
distinct gates/layers into one flag.

## Consumers

`_watch`/`_await_bounded` already print `f"[watch] {ev['type']}:
{ev['detail']}"` type-agnostically (spawn.py:1691 pre-change numbering) —
no change needed there; the four type strings surface as-is.
`test_spawn.py`'s `EventReporting`/`ProgressEvents` classes assert on the
new type strings directly (issue #232 fixtures, built from the issue's own
literal sample text for all three refusing layers).

## Not touched

`classify()`/`fail_closed_downgrade()`'s session-outcome contract reads
`result.get("permission_denials")`'s non-emptiness only — unaffected by
how per-line `.events.jsonl` entries are labeled. `watchdog_check_one`'s
separate `_DENIAL_RE` raw-text anomaly count (issue #90) is a different
signal for a different purpose, untouched.
