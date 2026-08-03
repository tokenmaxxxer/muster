---
subject: issue-232
role: implementation
phase: 1
---

# Current-state survey — issue-232

## Scout skip record

Skipped — pure bugfix. The issue is an event-*labeling* correctness bug
inside `spawn.py`'s own orchestrator-facing instrumentation (`watch`
mislabels every tool refusal as `gate-refusal` regardless of which layer
actually refused). There is no external product category to benchmark a
labeling fix against; the field is this repo's own event pipeline, its
preserved code history, and the literal message samples the issue author
already grepped from real session logs. The issue's own constraints
underline this: harness-permission policy and sandbox policy are
explicitly out of scope ("정책 자체는 이 이슈 범위가 아니다 — 정확히
보고만"), leaving nothing but a classification/labeling fix. This mirrors
the precedent set by issue-129 (`docs/issue-129/reports/coding/survey.md`
§Scout skip note), the direct ancestor of this same event pipeline, which
made the identical call for the identical reason.

## Where the event pipeline lives

Single file: `spawn.py` (2736 lines). No separate "watch" module exists.

- `.events.jsonl` / `.events.offset` sidecar files, one pair per
  workspace — `_append_event`/`_read_offset`/`_write_offset`
  (spawn.py:1494-1497, 1624-1628, 1652-1653).
- `_await_bounded` (spawn.py:1670-1713) — blocks until one new
  `.events.jsonl` line appears or a stall timeout elapses, then returns.
  This is the "block-after-first-material-event" cycle the issue says
  must not change. It reads whatever line is next; it has no opinion on
  event *type* or *shape* — untouched by anything this issue could do.
- `_watch`/`roster_watchdog` (spawn.py:1716-1751, 1439-1472) — CLI entry
  points. Not implicated: `_watch` only looks up the workspace and calls
  `_await_bounded`.
- The actual event *producer* — the part responsible for the mislabeling
  — is `_spawn_one`'s per-stdout-line scan loop (spawn.py:2581-2629) and
  its exit-time block (spawn.py:2634-2705).

## Current gate-refusal detection (spawn.py:2596-2607)

```python
try:
    obj = json.loads(line)
except ValueError:
    continue
...
if obj.get("type") == "result":
    result = obj
    denials = result.get("permission_denials") or []
    if issue is not None and not gate_refusal_seen and denials:
        gate_refusal_seen = True
        _append_event(events_path, "gate-refusal", str(denials)[:200])
```

Three structural facts follow directly from this code:

1. **Single source, single label.** The only signal considered is the
   terminal `result`-type line's `permission_denials` list — the Claude
   Code CLI's own `--output-format json` summary field. Every non-empty
   `permission_denials` becomes one `gate-refusal` event, appended exactly
   once per session (`gate_refusal_seen` dedup). There is no branching on
   *why* the denial happened — layer 1 (tokenmaxxxer gate), layer 2
   (harness permission), and layer 3 (sandbox) all produce a non-empty
   `permission_denials` and are indistinguishable at this call site. This
   is exactly the bug in the issue: the watching orchestrator reads
   `[watch] gate-refusal: ...` and — reasonably, given the label — assumes
   layer 1.
2. **`permission_denials` entries carry no reason text.** Existing
   fixtures (`test_spawn.py:731,737,742,1255,1414`) construct denial
   entries as `{"tool_name": "Write"}` only — this is the actual shape the
   CLI emits (also documented independently at
   `docs/decisions/2026-07-29-headless-cli-measured-facts.md:16-23`,
   "the denial only shows up in `--output-format json`'s
   `permission_denials` field"). Neither the hook path, the gate name, nor
   the human-readable refusal message live in this structure — confirming
   requirement 2's observation ("tool_input 만 실려오고 거부 사유 문자열이
   잘려나간다") literally: there is no reason field to truncate, because
   the summary object never carried one, and the enrichment must come from
   elsewhere.
3. **The `str(denials)[:200]` truncation compounds this**, but is a minor
   second-order issue — even an untruncated `permission_denials` list
   would still lack a reason string, per point 2.

## Where the classification evidence actually lives (requirement 3)

`_spawn_one`'s same per-line loop already parses every stream-json line
from the session (spawn.py:2596-2629) — it just doesn't look at `"user"`-
type lines carrying `tool_result` content. Those lines are where a denied
tool call's actual message text appears. The existing test suite already
has the shape on record
(`test_spawn.py:1246-1247`, from the issue-126 survey fixture):

```python
'{"type":"user","message":{"content":[{"type":"tool_result",'
 '"content":"..."}]}}'
```

Real `tool_result` blocks for a denial additionally carry `is_error:
true` — issue-129's fix (`docs/issue-129/reports/coding/survey.md`
§Confirmed root cause 2/3) exists *because* an earlier version of this
code scanned raw stdout text for the substring "denied" with no
structural check at all, and matched echoed source code and JSON key
names. Any new classification logic must gate on `is_error: true` (not
bare substring matching) or it re-opens that exact false-positive class.

Cross-checking against the three layers the issue names:

- **Layer 1 (tokenmaxxxer gate).** Traced `gate_deny()` in
  `tokenmaxxxer-core`'s `core/hooks/lib/gate-lib.sh:77-79` (installed at
  `~/.claude/plugins/marketplaces/tokenmaxxxer-core/core/hooks/lib/gate-lib.sh`,
  the plugin this project's role sessions load): `gate_deny "<gate>"
  "<message>"` writes `"<gate>: refused — <message>"` to stderr and exits
  2. Claude Code's own PreToolUse-hook-error wrapping is what produces the
  issue's cited sample, `PreToolUse:Bash hook error:
  [.../board-gate.sh] ...` — the hook's own file path appears in brackets
  *before* the gate's own `<gate>: refused — <message>` text. This means
  the gate name is recoverable **twice over** from text already in the
  tool_result: the bracketed hook path's basename (e.g. `board-gate.sh`)
  and, redundantly, the `gate_deny` message's own leading `<gate>:` token.
  No new instrumentation is needed to name the gate.
- **Layer 2 (harness permission)** and **layer 3 (sandbox)** — the issue
  supplies five and two literal message samples respectively. No
  structured field distinguishes them from each other or from layer 1
  beyond the message text itself; classification for these two layers is
  necessarily text-pattern matching against the sample strings the issue
  already grepped from real logs. No further source was found (or
  expected — these are Claude Code harness/OS strings, outside this
  repo's control per the issue's own scope constraint).

## Preserved-log check (requirement 3, continued)

Searched this checkout, sibling issue worktrees under
`/Users/jk/.tokenmaxxxer/work/*/runs/`, and `~/.claude/` for any
preserved `.log`/`.jsonl` session files containing the sample denial
strings from the issue — none exist on this machine (`runs/` is
gitignored and ephemeral per workspace; sibling worktrees' `runs/`
directories hold only `respawn_state.json`, no session logs). The
issue's own 2026-08-03 measurement (11 denials across 3 sessions, 8 at
layer 2/3, 3 at layer 1, cited in the issue body) is the only empirical
evidence available, and it is sufficient: it supplies literal sample
strings for all three layers, which is exactly what a fixture-based
regression test (requirement 4) needs. No new instrumentation, and no
access to a live session to capture fresh samples, is required before
proposing a fix.

## Consumers of the `gate-refusal` event name

- Live code: `_watch`/`_await_bounded` print `f"[watch] {ev['type']}:
  {ev['detail']}"` (spawn.py:1691) — type-agnostic, does not special-case
  the string `"gate-refusal"`.
- Live tests: `test_spawn.py:844,1240,1251,1257,1417,2568,2583` assert on
  the literal event type string `"gate-refusal"` — these will need
  updating for whatever shape phase 2 lands on.
- Historical docs only (`docs/issue-114`, `issue-129`, `issue-132`,
  `issue-180` reports/proposals): reference `gate-refusal` as prose/design
  record, not executable — no live parsing contract to preserve.
- Searched `tokenmaxxxer-core`'s plugin tree and `on-the-record`'s own
  plugin tree for any other reader of the literal string `"gate-refusal"`
  (hooks, directive prompts, docs) — none found. The only place that ever
  "reads" this label is a human or an orchestrating Claude session
  visually scanning `watch`'s stdout — exactly the failure mode the issue
  reports. There is no wire contract with another program to preserve
  beyond this repo's own tests.

## Separate, unrelated denial-counting code (out of scope)

`watchdog_check_one`'s anomaly signal 3 (spawn.py:1352-1354, 1419-1422)
uses its own `_DENIAL_RE = re.compile(r"permission_denial|denied", ...)`
raw-text scan over a log window, for a *different* purpose (issue #90's
observe-only watchdog anomaly count, not event labeling). It is not part
of `watch`'s reported-event pipeline this issue is about, and the issue's
requirements name `watch` and its `gate-refusal` label specifically —
this survey treats `watchdog_check_one` as out of scope, noted here so
phase 2 does not conflate the two.

## Write set implied

- `spawn.py` — the per-line scan loop (spawn.py:2581-2629) and its
  `gate_refusal_seen`/`_append_event("gate-refusal", ...)` call
  (spawn.py:2562, 2605-2607): classify each denial by layer using the
  tool_result stream, not just the terminal `permission_denials` summary.
- `test_spawn.py` — regression fixtures built from the issue's own
  literal sample strings, one per layer, plus a guard that non-`is_error`
  echoed/JSON-key text (issue-129's already-fixed false-positive class)
  still does not fire any refusal event.
- `docs/issue-232/decisions/` — the new three-layer event taxonomy is a
  wire-format change to `.events.jsonl` (new event type name(s)/detail
  shape); per this role's doc-placement ladder a changed wire format gets
  a decision record, written in phase 2 alongside the code.

No `.env`, dependency, or schema/migration surface is touched.
