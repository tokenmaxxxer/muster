---
subject: issue-246
role: implementation
phase: 1
---

# Build proposal — issue-246

files:
- `spawn.py`
- `test_spawn.py`

## Request

Issue #246 collects the three residual gaps left open by
`docs/issue-235/reports/execution-observation.md` (Findings 1, 2, 3)
after issue #235/PR #237 fixed the refusal classifier's corroboration
against `permission_denials`:

1. Three input shapes all currently produce "zero refusal events",
   indistinguishable from "no denial happened": **S1** the child
   crashes/is killed/truncates after a genuine `tool_result` line but
   before the terminal `result` line (already named in
   `docs/issue-235/reports/implementation.md:94-115` as Hunt finding 1,
   left open); **S2** the terminal line arrives but
   `permission_denials` is absent, `None`, or a truthy non-list
   (`spawn.py:2796`'s `or []` and the missing `isinstance` check
   collapse all three to "no denial"); **S3** the terminal line itself
   is malformed JSON, silently skipped by `except ValueError: continue`
   (`spawn.py:2789-2791`). The issue asks to either distinguish/handle
   S1–S3 (e.g. flush the buffer as an `unverified-refusal`-like type on
   crash/abnormal end) or explicitly document a decision to drop them,
   plus add an `isinstance` guard on `denials`.
2. Per-layer dedup masking: `pending_refusals`' key space
   (`spawn.py:1533,1536,1539`) is layer-wide for layers 2/3 and
   hook-stem-wide for layer 1, and the buffer write is first-write-wins
   (`:2825-2826`). Two same-layer `is_error` texts in one session
   collapse to one event carrying the first text's detail — if the
   first is textually coincidental and the second is the genuine
   denial, the real detail is discarded before the flush ever runs, and
   no fixture exists for this. `Path(hook_m.group(1)).stem` (`:1529`)
   additionally drops the directory, colliding two different hook
   scripts that share a filename stem. The issue asks to decide the
   dedup granularity (move to per-detail, or explicitly document
   keeping per-layer) and add a masking fixture.
3. `test_spurious_marker_match_does_not_suppress_real_denial_fallback`
   (`test_spawn.py:1576-1593`) does not pin the property its name
   claims: its spurious text never classifies at all (the anchored
   `_GATE_HOOK_RE` at `spawn.py:1491` doesn't match mid-text, and no
   harness/sandbox pattern matches either), so nothing is ever buffered
   and the fallback is reached trivially. The issue asks to replace or
   augment this fixture with a spurious candidate that bypasses the
   anchor (matches an unanchored layer-2/3 pattern) and actually
   exercises the suppression path at `spawn.py:2805`.

## Constraints

- No new instrumentation (issue #232 constraint 3 / #235 constraint 5,
  carried forward by #246's own `## 제약`): every fix reads only text
  already present in the stream-json lines (`tool_result` content, the
  terminal `result` line's `permission_denials`) — no new log line, CLI
  flag, or hook output. A new internal *event type* string written to
  the existing `events.jsonl` (as `unclassified-refusal` already was by
  #235) is not new instrumentation under this reading — it labels a
  signal already derivable from existing stream content, the same
  precedent #235 itself relied on.
- `watch` cadence/interval unchanged — `_await_bounded` is untouched.
- No arbitrary pattern-set expansion — `_GATE_HOOK_RE`, `_GATE_DENY_RE`,
  `_HARNESS_REFUSAL_PATTERNS`, `_SANDBOX_REFUSAL_PATTERNS` are not
  edited.
- Buffer-then-flush (corroborate-then-emit) structure preserved — #246
  does not reopen whether to corroborate against `permission_denials` at
  all, only how the buffering/dedup/fallback paths behave at the edges.

## Rationale

**Defect 1 — flush unconfirmed candidates as `unverified-refusal` on
EOF/malformed-shape, rather than only documenting the loss.** The
alternative named by the issue itself — explicitly document dropping
S1–S3 and leave the code as-is — was considered and rejected: these are
audit-relevant events (tool refusals), and the write-ahead-logging
principle that crash-safe systems record *before* confirming
(`docs/issue-246/reports/implementation/scout-brief.md`, Angle 1) shows
that "confirm first, log second" — the structure #235 chose and #246
keeps — trades away durability for exactly this class of loss. Since
changing that order is out of this issue's scope (constraint: buffer-
then-flush structure preserved), the available in-scope remedy is
narrowing the *silent* part of the loss: when the stream ends without a
successfully-parsed terminal `result` line, or when `permission_denials`
arrives in a shape that cannot be trusted as an authoritative list,
flush whatever was already classified in `pending_refusals` under a
distinct, honestly-labeled event (`unverified-refusal`) instead of
leaving it in memory. This requires a three-way read of
`result.get("permission_denials")` instead of the current two-way `or
[]`: an actual `list` (empty or not) is treated as authoritative
(existing behavior, unchanged); anything else (`None`/absent, or a
truthy non-list) is treated as an unconfirmed shape and triggers the
same `unverified-refusal` flush as the EOF case — this is the
`isinstance` guard the issue asks for, expressed as a three-way split
rather than a boolean patch, so "confirmed zero" (`[]`) stays
distinguishable from "shape we can't trust" (anything else).

**Defect 2 — move the dedup key from layer-wide to per-detail,
rejecting "keep per-layer granularity as documented, intended
behavior".** The rejected alternative is naming the current per-layer-
once masking as intentional and leaving it alone. Sentry's fingerprint-
grouping guidance is the concrete counter-example
(`docs/issue-246/reports/implementation/scout-brief.md`, Angle 2): a
default grouping key that is too coarse for cases where the same
category (here: same layer) legitimately contains distinct events is a
known failure mode with a known fix — narrow the key to the content that
actually varies. This repo's own first-write-wins buffer already makes
that failure concrete and unfixture-tested (survey.md's Defect 2
section), so "document as intended" would mean codifying a bug as a
feature. The fix folds the classified text (or a normalized/truncated
form of it) into the dedup key for all three layers, and keys layer 1 on
the full hook path rather than `Path(...).stem` alone (stem is kept only
for the human-facing `detail["gate"]` field) — so two different hook
scripts sharing a filename stem, and two different same-layer refusal
texts, both correlate as distinct candidates instead of collapsing. The
existing "same detail → one event" intent
(`spawn.py:2619-2622`'s comment, quoted in
`docs/issue-235/reports/execution-observation.md:394-420`) is preserved
because identical detail still produces the identical key.

**Defect 3 — replace the fixture, and pin the actual (accepted)
suppression behavior rather than a behavior the code doesn't have.**
The alternative considered — leave the existing fixture in place, since
its assertions currently pass — is rejected because a passing assertion
that never reaches the code path it claims to test is worse than no
test: it reads as coverage that is not there
(`docs/issue-235/reports/execution-observation.md`'s Finding 1, and this
proposal's own survey, both independently confirm the fixture's
spurious text classifies to `None`). The replacement fixture uses
spurious text that matches an unanchored `_HARNESS_REFUSAL_PATTERNS`/
`_SANDBOX_REFUSAL_PATTERNS` entry (so it *does* populate
`pending_refusals`/`refusals_seen`) while being textually unrelated to a
second, genuinely-unclassifiable denial in the same session. Per
Finding 1's own root-cause analysis, the correct assertion for that
input is that the fallback **is** suppressed — fixing the suppression
itself would need per-candidate correlation, which Finding 1's own
action item already places outside this issue's boundary (and outside
#246's `## 제약`). The fixture therefore becomes a pin of a documented,
accepted limitation (cross-referenced to Finding 1 in a comment), not a
regression test for behavior this issue is not fixing — and is renamed
so its assertion direction matches its name.

## What will be done

1. **`spawn.py`, result-branch (`:2794-2813` region):** replace
   `denials = result.get("permission_denials") or []` with a three-way
   read — confirmed non-empty/empty `list` keeps the existing
   correlate/flush/`unclassified-refusal`-fallback path; any other shape
   (`None`, missing, truthy non-list) flushes whatever is in
   `pending_refusals` as `unverified-refusal` instead of silently doing
   nothing.
2. **`spawn.py`, after the `for line in proc.stdout:` loop
   (near `:2848`):** track whether a terminal `result` line was ever
   successfully parsed (`result_seen`-style flag); if the loop exits
   without one and `pending_refusals` is non-empty, flush those entries
   as `unverified-refusal` — covering S1 (crash/kill/truncation) and S3
   (malformed terminal JSON) with the same mechanism.
3. **`spawn.py`, dedup keys (`:1529-1539`, `:2825-2826`):** fold the
   classified detail/reason text (or a normalized/truncated form) into
   the dedup key for all three layers; key layer 1 on the hook's full
   path rather than `Path(...).stem` alone, keeping `stem` only for the
   `detail["gate"]` display field.
4. **`test_spawn.py`:** add fixtures for (a) EOF/crash with a pending
   classified candidate and no terminal result line →
   `unverified-refusal`; (b) a terminal result line with
   `permission_denials` as `None`/absent and as a truthy non-list (e.g.
   a string), each with a pending classified candidate → same; (c) two
   distinct same-layer `is_error` texts in one session → two distinct
   events, not one carrying only the first's detail; (d) two identical
   same-layer texts → still collapse to one (regression guard for the
   existing "same detail once" intent); (e) two hook paths with the
   same filename stem in different directories → distinct events, not
   collapsed.
5. **`test_spawn.py`:** replace
   `test_spurious_marker_match_does_not_suppress_real_denial_fallback`
   with a fixture whose spurious text matches an unanchored layer-2/3
   pattern and is uncorrelated with a second, unclassifiable genuine
   denial in the same session; assert the fallback is suppressed
   (matching the real, accepted behavior), with a comment citing
   `docs/issue-235/reports/execution-observation.md` Finding 1 for why
   this is a documented limitation and not a bug this issue fixes.
6. Run `python3 -m pytest test_spawn.py` (or the project's existing test
   entry point) once, full suite, before considering phase 2 complete.

## Out of scope

- Fixing the suppression compounding itself (a spurious classified
  candidate suppressing the generic fallback for an unrelated, unclassifiable
  genuine denial) — Finding 1's own action item ties this to
  per-candidate correlation or an anchored layer-2/3 form, both outside
  #246's constraint set. Defect 3's fixture documents this limitation;
  it does not remove it.
- Session-level (vs. per-candidate) corroboration — a real denial and an
  unrelated classified candidate can still both flush once `denials` is
  non-empty; this is `docs/issue-235/reports/execution-observation.md`
  Finding 2 / `docs/issue-235/reports/implementation.md`'s finding 2, and
  #246 does not name it.
- Any change to `_GATE_HOOK_RE`, `_GATE_DENY_RE`,
  `_HARNESS_REFUSAL_PATTERNS`, `_SANDBOX_REFUSAL_PATTERNS`, or
  `_await_bounded`'s cadence.
- Filing or resolving a further follow-up issue for the out-of-scope
  items above — left for the human to judge, per this repo's existing
  pattern for open findings.

## How you'll know it worked

- The five new/updated fixture groups in `test_spawn.py` (EOF/crash
  unverified flush, malformed-`permission_denials` shapes, same-layer
  dedup masking, hook-stem-collision, and the corrected suppression-path
  fixture) each fail against the current, unmodified `spawn.py` and pass
  after the fix — mirroring how issue #235's four regression cases were
  verified pre/post-fix
  (`docs/issue-235/reports/implementation.md:151-161`).
- All previously-passing fixtures in `test_spawn.py` — in particular
  `test_denials_with_no_correlating_tool_result_are_unclassified`,
  `test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing`,
  and the five layer-labeling tests at `test_spawn.py:1461-1612` — still
  pass unchanged, confirming the three-way `permission_denials` read and
  the widened dedup key don't regress existing corroboration/labeling
  behavior.
- `python3 -m pytest test_spawn.py` run once, full suite, 0 failures.
