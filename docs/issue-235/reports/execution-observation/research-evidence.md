---
subject: issue-235
role: execution-observation
observed_role: implementation
observed_pr: 237
phase: 1
---

# Research — evidence inventory for PR #237

Phase-1 research material. This file records **facts and coordinates
only**: what the blobs say and what the code paths structurally do. It
renders no verdict; judgment belongs to phase 2 and to the record. Every
entry addresses a blob through its SHA — no working-tree path is cited
as evidence, and nothing here was produced by running the observed
role's code. Line numbers in the `611c0c0:spawn.py:2615-2705` region were
re-derived directly from `git show 611c0c0:spawn.py` in this session.

## Trajectory evidence

- Approval for the observed role: issue comment whose entire body is
  `APPROVE issue-235/implementation`, author `jjongkwann`, association
  `MEMBER` (listed in `docs/specs/approvers.md`), created
  **2026-08-03T05:52:52Z**
  (https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162801451).
- Observed phase-1 commit `bf5f71f`, authored 2026-08-03 14:46:02 +0900
  (= 05:46:02Z), file set exactly two paths:
  `docs/issue-235/proposals/refusal-classifier-corroboration.md` (+214)
  and `docs/issue-235/reports/implementation/survey.md` (+257). No code
  file.
- Observed phase-2 delivery commit `611c0c0`, authored 2026-08-03
  15:03:13 +0900 (= 06:03:13Z), `spawn.py` +57/-23, `test_spawn.py`
  +75/-0.
- Observed phase-2 record commit `e7a13db`, authored 2026-08-03 15:12:37
  +0900, adding `docs/issue-235/reports/implementation.md` (+187).
- PR #237: author `jjongkwann`, `reviews: []`, merged
  **2026-08-03T06:15:33Z** as `d187559`
  (https://github.com/tokenmaxxxer/on-the-record/pull/237). Single-account
  mode, so the issue-comment approval path is the applicable one.
- Second issue comment, `jjongkwann`, 2026-08-03T06:16:21Z
  (https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162962921):
  a reopen note recording that step 2 was still unrun when PR #237's
  closing keyword auto-closed #235.

## Unit (a) — the four regression cases against the pre-change blob

### The four added tests and their 요구사항 4 mapping

| 요구사항 4 case | Test | Coordinate |
|---|---|---|
| (i) layer-2 message quoting a gate marker | `test_layer2_denial_quoting_gate_marker_is_harness_refusal_not_gate` | `611c0c0:test_spawn.py:1342-1359` |
| (ii) zero-denials session, marker in failure output | `test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing` | `611c0c0:test_spawn.py:1361-1377` |
| (iii) fake match + real refusal compounded | `test_spurious_marker_match_does_not_suppress_real_denial_fallback` | `611c0c0:test_spawn.py:1379-1396` |
| (iv) real `record-fields-gate` text, gate = hook stem | `test_record_fields_gate_denial_reports_hook_stem_not_role_name` | `611c0c0:test_spawn.py:1398-1415` |

Each required case maps to exactly one added test; each test's leading
comment cross-references its case number. Shared harness:
`EventReporting._run` (`611c0c0:test_spawn.py:1187-1223`) calls
`spawn._spawn_one(..., "execution-observation", task, unattended=True,
issue=7)` — `issue` is not `None`, and `role` is the literal
`"execution-observation"` (`611c0c0:test_spawn.py:1223`).

### Pre-change code the cases land on

- `bf5f71f:spawn.py:1491` — `_GATE_HOOK_RE = re.compile(r"PreToolUse:\S+
  hook error: \[([^\]]*)\]")`, no `^`.
- `bf5f71f:spawn.py:1492` — `_GATE_DENY_RE = re.compile(r"(\S+):\s*refused\s*—")`.
- `bf5f71f:spawn.py:1520-1541` — `_classify_refusal_text`: `hook_m =
  _GATE_HOOK_RE.search(text)` (`:1525`); if `hook_m`, `deny_m` is tried
  (`:1527`) and when present `gate = deny_m.group(1)` (`:1529`),
  otherwise `gate = Path(hook_m.group(1)).stem` (`:1532`); returns
  `("gate-refusal", ("gate", gate), {...})` at `:1534`, so the
  `_HARNESS_REFUSAL_PATTERNS` loop (`:1535-1537`) is unreachable once
  the gate marker matched anywhere in the text.
- `bf5f71f:spawn.py:2624` — `refusals_seen: set = set()`, one set for
  the whole session loop.
- `bf5f71f:spawn.py:2664-2674` — `type == "result"` branch: `denials =
  result.get("permission_denials") or []` (`:2666`); appends
  `unclassified-refusal` only under `if issue is not None and denials
  and not refusals_seen` (`:2667`).
- `bf5f71f:spawn.py:2675-2689` — `type == "user"` branch: classifies
  every `is_error` tool_result and calls `_append_event` immediately
  (`:2689`), gated only on `key not in refusals_seen` (`:2686-2688`).
  The two branches are `elif` siblings on `obj.get("type")` — the user
  branch never reads `denials`.

### Per-case static divergence on `bf5f71f:spawn.py`

- **(i)** The marker sits mid-sentence after `"...requires approval: "`
  (`611c0c0:test_spawn.py:1348-1351`). `.search()` at
  `bf5f71f:spawn.py:1525` matches it anyway; `deny_m` yields
  `gate="some-gate"` (`:1529`); the function returns `gate-refusal` at
  `:1534`, so the `requires approval` harness pattern at `:1536` is
  never reached. Both asserts diverge: no `harness-refusal` exists
  (`611c0c0:test_spawn.py:1358`) and a `gate-refusal` does (`:1359`).
- **(ii)** Text begins with the marker; `permission_denials` is `[]`
  (`611c0c0:test_spawn.py:1371`). The user branch appends
  `gate-refusal` at `bf5f71f:spawn.py:2689` before the result line is
  read, and never consults `denials`. The assert at
  `611c0c0:test_spawn.py:1374-1377` (no refusal event of any of the four
  types) diverges.
- **(iii)** Spurious embedded marker names `some-other-gate` / tool
  `Bash`; the real denial on the terminal line names tool `Write`
  (`611c0c0:test_spawn.py:1385-1392`). The spurious text classifies and
  populates `refusals_seen` at `bf5f71f:spawn.py:2688`, which falsifies
  `not refusals_seen` at `:2667`, so no `unclassified-refusal` is
  appended. Both asserts diverge (`611c0c0:test_spawn.py:1395,1396`).
- **(iv)** `_GATE_DENY_RE` matches `"execution-observation: refused —"`,
  so `gate = "execution-observation"` (`bf5f71f:spawn.py:1529`) and the
  stem branch at `:1532` is not taken. The assert at
  `611c0c0:test_spawn.py:1415` (`detail["gate"] == "record-fields-gate"`)
  diverges.

### Non-discriminating assertion

`611c0c0:test_spawn.py:1414` (`assertEqual(len(refusals), 1)`) holds on
`bf5f71f:spawn.py` too: the single user line appends exactly one event
(`:2689`) and the result-line branch is then blocked by `not
refusals_seen` (`:2667`). Only the paired assert at
`611c0c0:test_spawn.py:1415` separates the two blobs. No other assertion
among the four cases was found to hold on the pre-change blob.

## Unit (b) — `permission_denials` buffer-then-flush gate

### Post-change shape

- `611c0c0:spawn.py:1491` — `_GATE_HOOK_RE = re.compile(r"^PreToolUse:\S+
  hook error: \[([^\]]*)\]")`. The `^` is present; no `re.MULTILINE`, so
  it binds to text index 0 only.
- `611c0c0:spawn.py:1493-1498` (`_HARNESS_REFUSAL_PATTERNS`) and
  `:1499-1502` (`_SANDBOX_REFUSAL_PATTERNS`) are **not** anchored and are
  still applied with `.search()` at `:1535` and `:1538`.
- `611c0c0:spawn.py:1527-1533` — `_classify_refusal_text`: `gate =
  Path(hook_m.group(1)).stem` (`:1529`) unconditionally, computed before
  `deny_m` (`:1530`); `deny_m` only sets where `reason` starts
  (`:1531-1532`).
- State locals in `_spawn_one`: `refusals_seen: set = set()`
  (`611c0c0:spawn.py:2623`, comment `:2619-2622`), `pending_refusals:
  dict = {}` (`:2629`, new in this commit, comment `:2624-2628`).
- Line loop: `for line in proc.stdout:` (`:2649`); `json.loads` at
  `:2664` inside `try/except ValueError: continue` (`:2663-2666`);
  `if not isinstance(obj, dict): continue` (`:2667-2668`); `if/elif`
  dispatch on `obj.get("type")` at `:2669` (`result`), `:2689` (`user`),
  `:2702` (`assistant`). No `break`.
- Buffering, `type == "user"` branch — `611c0c0:spawn.py:2689-2701`; the
  write is `if key not in pending_refusals: pending_refusals[key] =
  (ev_type, detail)` (`:2700-2701`). No `_append_event` in this branch.
- Flush, `type == "result"` branch — `611c0c0:spawn.py:2669-2688`:
  `denials = result.get("permission_denials") or []` (`:2671`); `if issue
  is not None and denials:` (`:2672`); flush loop `:2675-2679`
  (`if key in refusals_seen: continue` `:2676-2677`, `refusals_seen.add`
  `:2678`, `_append_event` `:2679`); fallback `if not refusals_seen:`
  (`:2680`) → `refusals_seen.add(("unclassified",))` (`:2686`) and
  `_append_event(events_path, "unclassified-refusal", str(denials)[:200])`
  (`:2687-2688`). The fallback is **nested inside** the `denials` guard
  at `:2672`.
- `session-end` is emitted at `611c0c0:spawn.py:2824`, outside this
  control flow and independent of `refusals_seen`/`pending_refusals`.

### Ordering assumption

"`result` is always the last line" appears only as a comment at
`611c0c0:spawn.py:2624-2626`. No assertion, count check, or post-loop
validation enforces it. Traced outcomes when it does not hold:

- **Terminal `result` line absent** — loop ends at EOF; `:2669` never
  true; `pending_refusals` is discarded with the frame; nothing appended.
- **Terminal line malformed JSON** — `ValueError` caught at `:2665-2666`,
  line skipped; same outcome as absent.
- **`permission_denials` key missing** — `.get(...) or []` at `:2671`
  yields `[]`; `:2672` is false; flush loop (`:2675-2679`) *and* fallback
  (`:2680-2688`) both skipped; buffered candidates discarded.
- **`permission_denials` present but not a list** — no `isinstance` check
  anywhere. Truthy non-list (non-empty str/dict/int) passes `:2672` and
  the flush loop runs normally (`:2675-2679` never inspects `denials`);
  `str(denials)[:200]` at `:2688` accepts any type. Falsy non-list
  (`""`, `0`, `{}`, `False`) collapses to `[]` at `:2671`, same as the
  missing-key case.

### P1 — zero-denials session

`denials = [] or []` → `[]` (`611c0c0:spawn.py:2671`), so `:2672` is
false. `pending_refusals` is read only inside that guard (`:2675`), and
the `unclassified-refusal` fallback (`:2680-2688`) is nested inside it
too. Emitted set is empty, for any number of buffered candidates.

### P2 — spurious candidate alongside a real denial

- The gate correlates at **session level**: only `denials`' truthiness is
  tested (`611c0c0:spawn.py:2672`); no line maps an entry of `denials` to
  a key in `pending_refusals`. When a real denial makes `denials`
  non-empty, the flush loop at `:2675-2679` iterates **every** buffered
  key, including one buffered from unrelated text. The observed role's
  own Hunt finding 2 states the same
  (`e7a13db:docs/issue-235/reports/implementation.md:116-129`).
- The `^` anchor at `:1491` constrains only the gate layer. Layers 2 and
  3 still match by unanchored `.search()` at `:1535` and `:1538`, so a
  quoted harness/sandbox phrase anywhere in an `is_error` text still
  buffers a candidate.
- **Distinct keys**: the real denial's candidate and the spurious one are
  both emitted at `:2679`; neither suppresses the other, and the fallback
  at `:2680` does not fire because `refusals_seen` is non-empty after the
  loop.
- **Same key** (same layer, and for the gate layer the same stem):
  `:2700`'s `if key not in pending_refusals` is first-write-wins, so
  whichever `is_error` block arrived earlier owns the entry. If that is
  the spurious one, the single event emitted for that key at `:2679`
  carries the spurious `detail`; the real denial's `detail` is discarded
  at `:2700` before the flush runs. `ev_type` is unchanged (same key
  implies same branch of `_classify_refusal_text`).
- Test (iii) (`611c0c0:test_spawn.py:1379-1396`) exercises the
  distinct-key/uncorrelated shape only: under the anchored pattern its
  spurious text classifies to `None` (`:1540`), so nothing is buffered at
  all.

### Dedup key and masking shapes

The key is the tuple from `_classify_refusal_text`: `("gate", stem)`
(`611c0c0:spawn.py:1533`), `("harness",)` (`:1536`), `("sandbox",)`
(`:1539`) — layer-wide for layers 2 and 3, per-gate-**stem** for layer 1
— plus the sentinel `("unclassified",)` built at `:2686`. Two collapse
points, both first-wins:

- `611c0c0:spawn.py:2700` — `if key not in pending_refusals`.
- `611c0c0:spawn.py:2676-2678` — `refusals_seen`, same key space,
  checked at flush. Within a single flush pass it is redundant with the
  buffer's own dedup; it becomes load-bearing only if the `result` branch
  is entered more than once (no `break` at `:2669-2688`) or if `user`
  lines arrive after a first `result` line.

Concrete collapse shapes:

- **Two denials of the same layer, different reasons.** Two `is_error`
  texts both keying `("harness",)` (or both `("gate", "board-gate")`):
  the first owns `pending_refusals[key]` at `:2700`, so the emitted event
  at `:2679` carries the first `detail` and the second is never written.
- **Two different gate scripts sharing a filename stem.**
  `Path(hook_m.group(1)).stem` (`:1529`) discards the directory, so
  `/a/hooks/some-gate.sh` and `/b/hooks/some-gate.sh` both key
  `("gate", "some-gate")` and collapse. No admissible sample shows two
  hook scripts with a colliding stem; this is a structural shape.
- Pre-change used the identical key space and the same first-wins
  ordering at `bf5f71f:spawn.py:2686-2688`, so the layer-wide
  granularity is carried over from `a670098`, not introduced by
  `611c0c0`.

### Pre-change counterpart

- `bf5f71f:spawn.py:1520-1541` — classify; gate name from
  `deny_m.group(1)` (`:1529`), stem only as fallback (`:1532`).
- `bf5f71f:spawn.py:2675-2689` — the `user` branch classifies **and**
  emits in the same pass (`_append_event` at `:2689`), gated only on
  `key in refusals_seen` (`:2686-2688`). No buffer exists; `denials`
  plays no part in this path.
- `bf5f71f:spawn.py:2664-2674` — the fallback fires under `denials and
  not refusals_seen` (`:2667`), i.e. suppressed by any earlier per-line
  classification, spurious or not.
- Predecessor `2dc6ba6:spawn.py:2562, 2602-2607` — a single boolean
  `gate_refusal_seen` gating one generic `"gate-refusal"` event with
  `detail = str(denials)[:200]`; no per-line text classification at all.
- `permission_denials` reads outside this gate are byte-identical across
  the two commits: `bf5f71f:spawn.py:1186` / `611c0c0:spawn.py:1186`
  (`classify()` → `"refused"`), and `bf5f71f:spawn.py:2775` /
  `611c0c0:spawn.py:2786` (ledger `"denials": len(denials)`).

## Unit (c) — prescription provenance, coverage delta, dedup

### Provenance of the "four-point prescription"

Searched: `git grep -n -E "153|적대 검증|adversarial" d187559 -- docs`;
`git log --all --oneline -S153 -- docs`; history-wide `git grep` for
`153.fixture|fixture.corpus|153개`, `fallback.*unconditional|무조건.*폴백`,
`검증자|반려했다|adversarial.verification`; `gh issue view 232 --comments`;
`gh issue view 235 --comments`; `gh pr view 237 --comments` (empty);
`gh pr view 234 --comments`; `7685f60`/`417e702`
`:docs/issue-232/reports/execution-observation.md`;
`bf5f71f:docs/issue-235/proposals/refusal-classifier-corroboration.md`;
`bf5f71f:docs/issue-235/reports/implementation/survey.md`;
`e7a13db:docs/issue-235/reports/implementation.md`;
`af92fce:docs/issue-232/reports/implementation.md`.

Findings:

- **No admissible source carries a four-point prescription** of the shape
  "anchor / keep the fallback unconditional / dedup safety / 153-fixture
  corpus". Every `153` hit under `d187559 -- docs` is a pytest count
  (`docs/issue-204/reports/execution-observation.md:99`,
  `docs/issue-205/reports/implementation.md:99`) or an `issue-153` path.
  No occurrence of "fallback unconditional" or a Korean equivalent
  exists in the history.
- The only in-repo text bearing the phrase "adversarial-verification
  experiment that rejected the same code twice" is
  `bf5f71f:docs/issue-235/proposals/refusal-classifier-corroboration.md:15-25`,
  and its enumeration is **three** points: (1) `is_error` classified
  without checking `permission_denials`; (2) `_GATE_HOOK_RE` unanchored;
  (3) `detail.gate` prefers the `gate_deny` token over the hook stem.
- Issue #235's own 배경 paraphrases the same local verifier as rejecting
  twice on one attack angle — "게이트 층을 가장 먼저, 무앵커 부분문자열
  검색으로 판정 — 다른 층 메시지 본문에 마커류 텍스트가 인용되면 오분류".
  That is the anchoring point only.
- A structurally similar but unrelated four-item list does exist:
  `7685f60:docs/issue-232/reports/execution-observation.md:46-49` — "(a)
  fixture strength against the pre-change code, (b) pattern provenance
  …, (c) the dedup contract, (d) `watch` cycle invariance". That is this
  role's own review scope for issue #232/PR #233, authored before #235
  existed; it is not a prescription for this fix and contains neither
  "153" nor "unconditional fallback".
- `test_spawn.py` `def test_` count: 166 at `bf5f71f`, 170 at `611c0c0`
  — a delta of 4, and neither figure is 153.

Consequence for planning: the prescription's "unconditional fallback",
"dedup safety" and "153 fixtures" points enter phase 2 as questions to be
answered from the blobs, not as a citable external standard. The
proposal's check 5 carries that contingency.

### Point-by-point map of the admissible three-point prescription

- Point 1 (corroborate against `permission_denials`) →
  `611c0c0:spawn.py:2619-2629` (buffer introduced) and `:2669-2701`
  (flush-on-`result` restructuring).
- Point 2 (anchor `_GATE_HOOK_RE`) → `611c0c0:spawn.py:1491`, `^` added;
  call site unchanged (`.search(text)` at `:1527`).
- Point 3 (prefer the hook stem) → `611c0c0:spawn.py:1529`, against
  `bf5f71f:spawn.py:1528-1533`.
- "Keep the fallback unconditional" → **no corresponding line**. The
  fallback is conditional at both SHAs: `bf5f71f:spawn.py:2667` guards it
  with `denials and not refusals_seen` in one condition;
  `611c0c0:spawn.py:2672` + `:2680` split the same two tests around the
  flush loop.
- "Dedup safety" → **no corresponding line**. The key shapes and the
  `refusals_seen` mechanism are structurally unchanged between
  `bf5f71f:spawn.py:2624,2686-2688` and `611c0c0:spawn.py:2623,2676-2678`;
  the check merely moved from the per-line branch into the flush loop.
- "153-fixture corpus" → **no corresponding line** in either
  `611c0c0:spawn.py` or `611c0c0:test_spawn.py`.

### Coverage-delta shapes (pre-change emits, post-change does not)

- **S1 — no terminal `result` line.** A genuine denial's `tool_result`
  line streams, then the child crashes / is killed / the stream
  truncates. `bf5f71f:spawn.py:2689` has already appended the event;
  `611c0c0:spawn.py:2700-2701` has only buffered it and the flush at
  `:2675-2679` never runs. Named by the observed role itself at
  `e7a13db:docs/issue-235/reports/implementation.md:94-115`.
- **S2 — terminal line present, `permission_denials` empty, absent, or
  falsy non-list.** `611c0c0:spawn.py:2671`'s `or []` collapses all of
  these to `[]`, so `:2672` is false and both the flush and the fallback
  are skipped. `bf5f71f:spawn.py:2689` would still have appended the
  classified event. This is the shape test (ii) encodes.
- **S3 — terminal line malformed JSON.** `ValueError` at
  `611c0c0:spawn.py:2665-2666` skips it; same outcome as S1.
- **Not a delta: a genuine gate denial whose marker is not at text
  position 0.** `^` at `:1491` fails; if no layer-2/3 pattern matches,
  `_classify_refusal_text` returns `None` (`:1540`) and nothing is
  buffered; at flush, `denials` is non-empty and `refusals_seen` is
  empty, so `:2680-2688` emits `unclassified-refusal`. The event is
  downgraded, not lost. (`_tool_result_text` joining list blocks with
  `"\n"` is the shape Hunt finding 3 names at
  `e7a13db:docs/issue-235/reports/implementation.md:130-139`.)
- **Reverse direction**: no shape was found in which `bf5f71f:spawn.py`
  emits nothing and `611c0c0:spawn.py` emits something, since both
  populate from the same `_classify_refusal_text` return under the same
  `is_error` guard (`611c0c0:spawn.py:2693` / `bf5f71f:spawn.py:2680`).

So the fallback is retained on every path where `denials` is truthy; the
only shapes where post-change reporting is narrower than pre-change are
those in which `denials` is never read or reads falsy (S1-S3).

### Fallback-suppression shape that survives the change

`611c0c0:spawn.py:2680` gates the fallback on `if not refusals_seen`, and
`refusals_seen` is populated at `:2678` by the flush loop in the same
pass. So whenever **any** buffered candidate flushes, the
`unclassified-refusal` fallback does not fire — structurally the same
condition as pre-change `denials and not refusals_seen`
(`bf5f71f:spawn.py:2667`).

The `^` anchor at `:1491` removes the *gate-layer* fake match, which is
why the fixture at `611c0c0:test_spawn.py:1379-1396` reaches the
fallback. The layer-2 and layer-3 patterns (`:1493-1502`) are still
matched by unanchored `.search()` at `:1535` and `:1538`. Input shape: an
`is_error` `tool_result` whose text merely quotes `requires approval` (or
`Operation not permitted`) — for instance the very text used at
`611c0c0:test_spawn.py:1348-1351`, which under `611c0c0` classifies as
`harness-refusal` — buffers a `("harness",)` candidate; if the session's
genuine denial fails to correlate (its own text truncated, absent, or
matching no pattern), the flush at `:2679` emits the quoted-text
candidate, `refusals_seen` becomes non-empty, and `:2680`'s fallback does
not fire. No fixture among the four added cases exercises this shape.
