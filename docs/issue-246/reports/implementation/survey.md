---
subject: issue-246
role: implementation
phase: 1
---

# Current-state survey — issue-246

## Scope update (발주자 확장, phase-1 재작업)

PR #253의 최초 제안 이후 이슈에 발주자 코멘트로 범위가 확장됐다: (1)
Defect 3이 노출한 억제(같은 세션의 한 후보가 분류되면, 상관관계 안 되는
다른 진짜 거부의 `unclassified-refusal` 폴백이 억제되는 현상)를 "수용된
한계"로 문서화하는 대신 이 이슈 범위에서 고친다 — 건별(per-candidate)
상관관계 설계 포함; (2) `unverified-refusal` 이벤트 타입 해석(새 계측
아님, #235의 `unclassified-refusal` 선례와 동일)은 추인 — 변경 없음; (3)
dedup 키에 포함되는 텍스트의 정규화·절삭 규칙을 명시적으로 기록한다. 이
문서와 제안서는 이 세 항목 기준으로 갱신됐다. Defect 1의 설계(EOF/형태
불량 시 `unverified-refusal` flush)는 영향받지 않는다.

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

**Dedup key text — normalization/truncation rule (issue's scope item 3).**
`_classify_refusal_text` (`spawn.py:1520-1540`) already computes the exact
string that would become the key's text component: the gate layer's
`reason = text[deny_m.end():].strip()[:300]` (or `text.strip()[:300]` if
no `_GATE_DENY_RE` match), and the harness/sandbox layers'
`text.strip()[:300]`. Two properties of this existing string are
undocumented and both cause spurious dedup misses today: (1)
`_tool_result_text` (`spawn.py:1504-1513`) joins multi-block `tool_result`
content with `"\n".join(parts)` — a denial reason that happens to arrive
split across two content blocks carries an internal `\n` that a
logically-identical reason arriving as one block would not, so
`.strip()[:300]` alone leaves two otherwise-identical reasons keyed
differently; (2) `.strip()` only removes leading/trailing whitespace, not
internal whitespace-run variance (e.g. a reason logged with a
double-space vs. single-space after a colon). Neither is hypothetical —
both are properties of the *existing* `.strip()[:300]` call, not a new
input class. No fixture currently exercises either.

## Defect 3 — the suppression itself (issue's 결함 3, now in scope)

`test_spurious_marker_match_does_not_suppress_real_denial_fallback`
(`test_spawn.py:1576-1593`) uses spurious text that opens with
`"Some unrelated tool output happened to mention PreToolUse:Bash hook
error: [...] some-other-gate: refused — 무관한 내용"`. Traced against the
live code: `_GATE_HOOK_RE` is anchored (`^`, no `re.MULTILINE`,
`spawn.py:1491`) so it does not match (the marker is not at index 0);
none of `_HARNESS_REFUSAL_PATTERNS`/`_SANDBOX_REFUSAL_PATTERNS`
(`:1493-1502`) match this text either (no "requires approval", no
"Operation not permitted", etc.). `_classify_refusal_text` therefore
returns `None` (`:1540`) and the current fixture never even reaches the
suppression path — the test passes trivially, not because a spurious
*classified* candidate failed to suppress the fallback.

**The actual suppression mechanism** lives at `spawn.py:2798-2804`: the
`type=="result"` branch flushes every key in `pending_refusals` that
isn't yet in `refusals_seen`, then at `:2805` gates the
`unclassified-refusal` fallback on `if not refusals_seen:` — a single
session-wide boolean. If a session buffers even one classified candidate
(any layer, any correlation status), that boolean flips true and the
fallback never fires — including for a *second*, genuinely uncorrelated
denial in the same session that no candidate ever classified. This is
the "같은 층의 거부 후보가 앞선 이벤트에 가려져 유실되는 억제" the
scope-expansion comment names: the flush loop treats "at least one
classified candidate exists" as "the session's one reportable event is
accounted for," which is only true when there is exactly one denial per
session — false the moment two distinct denials (one classifiable, one
not, or two same-layer ones after Defect 2's key-widening) land in the
same session.

**Per-candidate correlation, mechanism check.** `permission_denials`
entries are dicts carrying `tool_name`
(`test_spawn.py:731,1456,1472,...` — every existing fixture uses
`{"tool_name": "Write"}`/`{"tool_name": "Bash"}` shape; grep confirms no
other key is ever populated in a fixture). Confirmed via
`grep -n "tool_use_id" spawn.py test_spawn.py`: zero hits — the stream's
`tool_result` blocks carry a `tool_use_id` field in the underlying
Claude Code stream-json protocol (linking each `tool_result` back to the
`assistant` message's `tool_use` block that has the same `id` and a
`name`), but `_spawn_one`'s `type=="assistant"` branch
(`spawn.py:2831-2846`) currently reads `block.get("name")` only for
`Write`/`Edit`/`Bash` progress reporting and discards the block's `id`;
the `type=="user"` branch (`:2814-2826`) never reads
`block.get("tool_use_id")` at all. Both fields are already present on
every line already being parsed — reading them is not a new stream, log
line, or hook output (no new instrumentation), only reading two fields
of an object already fully parsed by `json.loads(line)` for other
purposes on the same line.

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
fix shape), issue #246's body (as expanded by the orchestrator's scope
comment) names three decisions rather than a single fix shape: (1) 결함
1 offers "구분해 다루거나 ... 명시적으로 버리는 결정을 문서화" — handle-
and-distinguish vs. explicitly-document-and-discard; (2) 결함 2 asks to
"결정(층당 → detail 당 또는 전체 유지)" — move dedup granularity to
per-detail, or document keeping the current per-layer granularity, plus
(scope item 3) the normalization/truncation rule for the text folded
into that key; (3) the scope-expansion comment adds a third: how to
correlate each buffered candidate against `permission_denials` entries
so a spurious classified candidate can no longer suppress a genuinely
uncorrelated denial's fallback (Defect 3). All three are genuine open
design choices this proposal must resolve before phase 2 can build
against a frozen contract — decisions (1) and (2) are the gap the
original scout sweep (Angles 1-2 below) aimed at; decision (3) is new
and is covered by the re-scout micro-round below.

## Re-scout micro-round — per-candidate correlation (issue's scope item 1)

The scope-expansion comment surfaced a new build decision the original
scout brief did not cover: *how* to correlate a buffered candidate
against `permission_denials` so the Defect 3 suppression is fixed rather
than pinned as accepted. Per the scout directive's re-scout trigger, one
micro-round ran (single `WebSearch` call, judged, no further deepening —
saturates immediately since the matching engineering idiom is
well-established and this repo is not a product-shaped surface, per the
original scout brief's segment judgment). Finding folded into
`docs/issue-246/reports/implementation/scout-brief.md` as Angle 3.
