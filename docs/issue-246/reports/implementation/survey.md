---
subject: issue-246
role: implementation
phase: 1
---

# Current-state survey — issue-246

## Where the classifier lives

Single file, unchanged in shape since issue #235/PR #237 (`d187559`):
`spawn.py`. Three regions matter, all inside `_spawn_one`:

- **Layer classification** — `_GATE_HOOK_RE`/`_GATE_DENY_RE`
  (`spawn.py:1491-1492`), `_HARNESS_REFUSAL_PATTERNS`/
  `_SANDBOX_REFUSAL_PATTERNS` (`:1493-1502`), `_classify_refusal_text`
  (`:1520-1540`) — returns `(event_type, dedup_key, detail)` or `None`.
- **Buffer-then-flush loop** (`:2748-2826`, inside
  `for line in proc.stdout:`): `refusals_seen: set` (`:2748`) and
  `pending_refusals: dict` (`:2754`) are session-local. The `type=="user"`
  branch (`:2814-2826`) classifies each `is_error` tool_result and writes
  it into `pending_refusals` **first-write-wins**
  (`:2825-2826`, `if key not in pending_refusals: pending_refusals[key]
  = (ev_type, detail)`). The `type=="result"` branch (`:2794-2813`) reads
  `denials = result.get("permission_denials") or []` (`:2796`) and, only
  if `denials` is truthy, flushes every unseen key in `pending_refusals`
  (`:2800-2804`) then emits `unclassified-refusal` as a fallback if
  nothing was classified (`:2805-2813`, gated on `if not refusals_seen`).
- **JSON-parse guard** for every stream line: `except ValueError:
  continue` (`:2789-2791`) — a malformed line (including a malformed
  terminal line) is silently skipped, not specially handled.

Test harness: `EventReporting._run` (`test_spawn.py`, shared by all
refusal-classifier fixtures) streams fixture lines through the same
`_spawn_one` code path with `issue=<int>` fixed, so `issue is not None`
holds throughout every existing fixture.

## Defect 1 — S1–S3 report-loss inputs (issue's 결함 1)

Three input shapes all end in "zero refusal events", indistinguishable
from "no denial happened":

- **S1** (already named in `docs/issue-235/reports/implementation.md:94-115`,
  Hunt finding 1, left open): the child crashes/is killed/truncates after
  a genuine `tool_result` line but before the terminal `result` line. The
  `for line in proc.stdout:` loop ends at EOF with `pending_refusals`
  populated only in memory (`:2754`) — never flushed, because the flush
  only happens inside the `type=="result"` branch (`:2794`).
- **S2**: the terminal `result` line arrives but `permission_denials` is
  absent, `None`, or a truthy non-list (e.g. a string) — `or []` at
  `:2796` collapses all three to `[]` with no `isinstance` check, so
  `:2797`'s `if issue is not None and denials:` is false and nothing
  flushes. Not named in `docs/issue-235/reports/implementation.md`'s Open
  findings (which only names S1).
- **S3**: the terminal line itself is malformed JSON — caught by the
  blanket `except ValueError: continue` (`:2789-2791`), same effective
  outcome as S1 (loop reaches EOF with `pending_refusals` unflushed).
  Also unnamed in the prior record.

No existing fixture exercises any of S1–S3: `grep -n "def test_" test_spawn.py`
shows only correlation/labeling fixtures (`test_denials_with_no_correlating_tool_result_are_unclassified`
at `test_spawn.py:1450-1459` tests the *opposite* shape — denials present,
no correlating tool_result — not denials malformed or absent-with-real-refusal).

## Defect 2 — per-layer dedup masking (issue's 결함 2)

`pending_refusals`' key space (`spawn.py:1533,1536,1539`) is
`("gate", stem)` for layer 1, `("harness",)` for layer 2, `("sandbox",)`
for layer 3 — layer-wide for layers 2/3, hook-stem-wide for layer 1. The
buffer write is first-wins (`:2825-2826`). Two `is_error` texts that key
the same layer in one session collapse to one event carrying the
**first** text's detail; if the first is a textual coincidence and the
second is the genuine denial, the emitted event's `detail` is wrong while
the flush still "succeeds" (one event, looks correct). Separately,
`Path(hook_m.group(1)).stem` (`:1529`) drops the directory, so two
different hook scripts sharing a filename stem collapse to the same
layer-1 key even though they are different gates.

Confirmed no fixture exists for this: `grep -n "def test_" test_spawn.py`
lists no test with two same-layer `is_error` tool_result blocks in one
session (`test_consecutive_writes_to_same_file_are_deduped` at
`test_spawn.py:1714` is unrelated — it dedupes `progress` events by
`file_path`, not refusal-classification keys).

## Defect 3 — regression case (iii) doesn't pin the non-suppression property (issue's 결함 3)

`test_spurious_marker_match_does_not_suppress_real_denial_fallback`
(`test_spawn.py:1576-1593`) uses spurious text that opens with
`"Some unrelated tool output happened to mention PreToolUse:Bash hook
error: [...] some-other-gate: refused — 무관한 내용"`. Traced against the
live code: `_GATE_HOOK_RE` is anchored (`^`, no `re.MULTILINE`,
`spawn.py:1491`) so it does not match (the marker is not at index 0);
none of `_HARNESS_REFUSAL_PATTERNS`/`_SANDBOX_REFUSAL_PATTERNS`
(`:1493-1502`) match this text either (no "requires approval", no
"Operation not permitted", etc.). `_classify_refusal_text` therefore
returns `None` (`:1540`) and **nothing is ever buffered** — the test
passes because the fallback path is reached trivially, not because a
spurious *classified* candidate failed to suppress it. This matches
`docs/issue-235/reports/execution-observation.md`'s Finding 1 exactly
(same fixture, same root cause, carried forward unfixed): a companion
input that classifies to a real layer (e.g. matches an unanchored
layer-2/3 pattern) while remaining uncorrelated with the genuine denial
is needed to actually exercise the suppression path at `:2805`
(`if not refusals_seen:`).

## Constraints carried forward (issue's own `## 제약`)

- No new instrumentation (issue #232 constraint 3 / #235 constraint 5) —
  fixes read only text already in the stream-json lines (`tool_result`
  content, terminal `result`'s `permission_denials`), no new log line,
  CLI flag, or hook output.
- `watch` cadence/interval unchanged — `_await_bounded` untouched.
- No arbitrary pattern-set expansion — `_GATE_HOOK_RE`/`_GATE_DENY_RE`/
  `_HARNESS_REFUSAL_PATTERNS`/`_SANDBOX_REFUSAL_PATTERNS` stay as-is.
- Buffer-then-flush (corroborate-then-emit) structure preserved — issue
  #246 does not reopen whether to corroborate against
  `permission_denials` at all, only how the buffering/dedup/fallback
  paths behave.

## What's still an open decision (why scouting applies)

Unlike issue #235's phase-1 (`docs/issue-235/reports/implementation/survey.md:9-27`,
skipped as pure bugfix because its own `## 요구사항` fixed the exact
fix shape), issue #246's body names two decisions explicitly rather than
a single fix shape: (1) 결함 1 offers "구분해 다루거나 ... 명시적으로
버리는 결정을 문서화" — handle-and-distinguish vs. explicitly-document-
and-discard; (2) 결함 2 asks to "결정(층당 → detail 당 또는 전체 유지)" —
move dedup granularity to per-detail, or document keeping the current
per-layer granularity. Both are genuine open design choices this proposal
must resolve before phase 2 can build against a frozen contract — this is
the gap the scout sweep below aims at.
