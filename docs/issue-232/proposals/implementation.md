---
subject: issue-232
role: implementation
phase: 1
---

# Build proposal — issue-232

files:
- `spawn.py`
- `test_spawn.py`
- `docs/issue-232/decisions/event-layer-taxonomy.md`

## Request

`spawn.py watch` is the orchestrator's only observation window into a role
session — it reports every tool refusal it sees as a single `gate-refusal`
event, regardless of which of (at minimum) three distinct layers actually
refused: the tokenmaxxxer gate plane this project owns, the Claude Code
harness's own permission layer, or the OS sandbox. A real 2026-08-03
incident: an orchestrating session read a `gate-refusal` report whose
actual cause message was `Permission to use Bash has been denied` (harness
layer, on a pure read command) and told the user "board-gate keeps
false-positiving" — a report with no basis, that the user then asked to be
filed as an issue, caught only because someone read the raw session log
by hand. A same-day audit of three session logs found 11 total refusals,
8 of them layer 2/3 and only 3 actually the tokenmaxxxer gate — meaning
most `gate-refusal` labels issued that day were wrong. Requirements: (1)
report which of the three layers actually refused; (2) when it is the
tokenmaxxxer gate, report which gate (board-gate, trailer-gate, ...) and
its refusal reason, not just a truncated `tool_input`; (3) do this from
evidence already present in the session log rather than adding new
instrumentation, if that evidence already suffices; (4) leave a regression
test with real fixture samples from all three layers so the label cannot
silently collapse back into one bucket.

## Constraints

- `_await_bounded`'s block-until-first-new-event-line-or-stall cycle
  (spawn.py:1670-1713) is not touched — it is type-agnostic already
  (reads whatever line is next) and the issue explicitly preserves it.
- Harness-permission policy and sandbox policy themselves are out of
  scope — this only makes their *refusals* reportable accurately, never
  changes when/whether they refuse.
- `classify()`'s existing precedence contract (spawn.py:1165-1189) and
  its passing tests are untouched — this proposal only changes what gets
  written to `.events.jsonl`'s refusal-shaped entries, not session-level
  outcome classification (`errored`/`progressed`/`refused`/...), which
  reads `result.permission_denials`' non-emptiness only, unaffected by
  how the per-line `.events.jsonl` entries are labeled.
- `.events.jsonl` is append-only; already-written history is not
  retrofitted, matching the same constraint issue-129 already established
  for this file.
- Must not regress issue-129's structural-detection fix: any new
  tool_result-text classification gates on `is_error: true`, never bare
  substring matching over arbitrary stdout — the exact bug class
  issue-129 fixed (echoed source text, JSON key names matching
  "denied").

## Rationale

**Chosen approach:** classify each denial inline, in `_spawn_one`'s
existing per-line stream-json loop, by matching a denied tool_result's
message text (`type: "user"`, `content[].type: "tool_result"`,
`is_error: true`) against a small set of layer-signature patterns built
from the issue's own cited sample strings; for a tokenmaxxxer-gate match,
additionally extract the gate name from the hook path already present in
that same message text. Replace the single, now-inaccurate `gate-refusal`
label with three distinct event *type* strings — `gate-refusal` (kept,
but now fired only for confirmed layer-1 matches), `harness-refusal`, and
`sandbox-refusal` — so the label itself, not just its `detail` payload,
tells the truth.

**Alternative 1 — keep one event type, add a `layer` field to `detail`.**
Rejected: the measured failure was the orchestrator trusting the *label*
`gate-refusal` without reading into `detail` at all. A single generic
type name reproduces exactly that failure surface for the next
orchestrator session that skims `watch`'s output; making the type string
itself layer-specific removes the failure mode at its actual point of
occurrence instead of hoping the reader inspects a nested field.

**Alternative 2 — add new upstream instrumentation** (a Claude Code CLI
flag, or a `hookSpecificOutput` convention in `tokenmaxxxer-core`'s gate
scripts) so refusal reason/layer arrives as a structured field instead of
being pattern-matched from message text. Rejected per requirement 3: the
survey confirms the session log's `tool_result` stream already carries
everything needed — the hook path (naming the gate), the gate's own
`<gate>: refused — <message>` text (`gate-lib.sh`'s `gate_deny`), and the
harness/sandbox message text verbatim. Pursuing upstream instrumentation
would mean depending on and coordinating changes across two other repos
(`tokenmaxxxer-core`, and Claude Code itself, which this project does not
control) for information already available locally — larger blast radius
for no gain, and violates requirement 3's explicit instruction to check
existing evidence first.

**Alternative 3 — classify only at session end, from the already-written
full log file** (reread `log_path` after `proc.wait()` instead of
classifying inline in the streaming loop). Rejected: it duplicates I/O
the loop already does line-by-line, and it breaks with the existing
established pattern in this same function — `pr-opened` and `progress`
events are already detected inline in the streaming loop, not via a
post-hoc reread. Inline classification also means a real denial is
visible to `watch` as soon as it happens, consistent with how `progress`
events already work, rather than only once the session fully exits.

## What will be done

1. Add layer-signature matching for the three layers, built from the
   issue's literal sample strings (bracketed-hook-path pattern for layer
   1; the five harness-permission phrases for layer 2; the two
   sandbox/OS phrases for layer 3).
2. In `_spawn_one`'s per-line loop (spawn.py:2596 onward), add a branch
   for `obj.get("type") == "user"` tool_result blocks with `is_error:
   true`: match the content text against the layer signatures; for a
   layer-1 match, additionally extract the gate name from the hook path
   in brackets (e.g. `board-gate.sh` → `board-gate`).
3. Replace the single `gate_refusal_seen` boolean with a small
   per-session dedup set keyed by `(layer[, gate])`, so each distinct
   layer (and, for gate refusals, each distinct gate) reports at most
   once per session — preserving today's "report once, not once per
   denial" behavior while no longer collapsing distinct gates/layers
   into the same single flag.
4. Emit `_append_event(events_path, "gate-refusal" | "harness-refusal" |
   "sandbox-refusal", detail)` per classified, not-yet-seen denial, where
   `detail` carries the reason text (a longer, still-bounded cap, not the
   current 200-char cut on a stringified list) and, for `gate-refusal`,
   the extracted gate name.
5. Keep a fallback: if the terminal `result` line's `permission_denials`
   is non-empty but the per-line scan classified nothing for this session
   (correlation miss — e.g. a truncated/dropped stream line), still emit
   one event so a real denial is never silently dropped — labeled
   distinctly (e.g. `unclassified-refusal`) rather than defaulting back
   to `gate-refusal`, so an unclassified case cannot masquerade as a
   confirmed layer-1 finding.
6. `test_spawn.py`: new fixture-based cases, one per layer, built from the
   issue's literal sample message strings, asserting the correct event
   type + gate name (layer 1) is produced; a case asserting issue-129's
   already-fixed false-positive class (non-`is_error` tool_result echoing
   denial-like text) still fires nothing; a case for the
   `unclassified-refusal` fallback.
7. `docs/issue-232/decisions/event-layer-taxonomy.md`: record the new
   event-type names, their `detail` shape, and the layer-signature
   patterns as the wire-format decision for `.events.jsonl` consumers
   (this repo's doctrine ladder: a changed wire format gets a decision
   record).

## Out of scope

- Harness-permission and sandbox *policy* — this proposal only reports
  their refusals accurately, never changes what they allow or deny.
- `_await_bounded`/`_watch`'s blocking cycle — unchanged, per the issue's
  own constraint.
- `watchdog_check_one`'s unrelated `_DENIAL_RE` raw-text anomaly-count
  signal (spawn.py:1352-1354, 1419-1422, issue #90's separate observe-only
  watchdog) — different code path, different purpose, not part of
  `watch`'s reported-event pipeline.
- `classify()`/`fail_closed_downgrade()`'s session-outcome contract —
  unaffected; they read `permission_denials`' non-emptiness only.
- Retrofitting already-written `.events.jsonl` history.

## How you'll know it worked

- `python3 -m pytest test_spawn.py` (or the suite's existing invocation),
  new layer-fixture cases green, run and shown once before the phase-2
  PR — including the issue-129 regression guard staying green.
- Each new case reproduces one of the issue's own cited sample denial
  strings verbatim and asserts the resulting event's type (and, for layer
  1, gate name) matches that layer — not a synthetic input invented
  independent of the issue's own evidence.
