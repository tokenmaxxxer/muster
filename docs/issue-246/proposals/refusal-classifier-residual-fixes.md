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
against `permission_denials`. This revision incorporates the
scope-expansion comment the orchestrator relayed onto the issue after
PR #253's original proposal: (1) the suppression Defect 3 exposed —
a classified candidate in a session silently swallowing the
`unclassified-refusal` fallback that an unrelated, genuinely
uncorrelated denial in the same session should have gotten — is now
in-scope to *fix*, not just to pin as an accepted, documented
limitation; the fix must include a per-candidate correlation design;
(2) the `unverified-refusal` event-type reading (new label on an
already-observed signal, not new instrumentation — same precedent as
#235's `unclassified-refusal`) is confirmed, unchanged; (3) the
dedup key's text component gets an explicit normalization/truncation
rule instead of an unspecified "detail or a normalized/truncated form
of it."

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
   and the fallback is reached trivially. Worse, the suppression it
   claims to guard against is real: `spawn.py:2805`'s
   `if not refusals_seen:` gate is a single session-wide boolean — the
   moment *any* candidate classifies (spurious or not, correlated or
   not), the `unclassified-refusal` fallback is permanently skipped for
   the rest of that session, silently losing any other, genuinely
   uncorrelated denial. The scope-expansion comment asks to fix this
   suppression itself (per-candidate correlation, not a session-wide
   boolean), and to replace the fixture with one that pins the
   corrected, non-suppressing behavior.

## Constraints

- No new instrumentation (issue #232 constraint 3 / #235 constraint 5,
  carried forward by #246's own `## 제약`): every fix reads only text
  already present in the stream-json lines (`tool_result` content, the
  terminal `result` line's `permission_denials`) — no new log line, CLI
  flag, or hook output. A new internal *event type* string written to
  the existing `events.jsonl` (as `unclassified-refusal` already was by
  #235, and as `unverified-refusal` reuses the same precedent) is not
  new instrumentation under this reading — it labels a signal already
  derivable from existing stream content, the same precedent #235
  itself relied on. Reading `tool_use_id` off `tool_result` blocks and
  `id`/`name` off `tool_use` blocks for the per-candidate correlation
  design (Rationale, Defect 3) is the same category: both fields are
  already present on lines `_spawn_one` already parses with
  `json.loads` for other purposes on the same line — no new stream, no
  new field emitted anywhere, only two previously-unread fields of an
  already-parsed object.
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
feature. The fix folds the classified text (normalized and truncated per the
rule below) into the dedup key for all three layers, and keys layer 1 on
the full hook path rather than `Path(...).stem` alone (stem is kept only
for the human-facing `detail["gate"]` field) — so two different hook
scripts sharing a filename stem, and two different same-layer refusal
texts, both correlate as distinct candidates instead of collapsing. The
existing "same detail → one event" intent
(`spawn.py:2619-2622`'s comment, quoted in
`docs/issue-235/reports/execution-observation.md:394-420`) is preserved
because identical detail still produces the identical key.

**Dedup key text — normalization/truncation rule (scope item 3),
rejecting a second, independent truncation length.** The alternative
considered — add a new max-length constant for the key, separate from
the `[:300]` already applied to `detail` — is rejected: it would create
two independently-tunable truncation points for what is conceptually
the same text, the kind of new parameter issue #246's own `## 제약`
(no arbitrary expansion) argues against. The rule instead reuses the
*same* string already computed for `detail` (survey.md's Defect 2
addendum): `_classify_refusal_text`'s existing
`text[deny_m.end():].strip()[:300]` (gate `reason`) and
`text.strip()[:300]` (harness/sandbox `detail`) become
`" ".join(text[...].strip().split())[:300]` — collapse all internal
whitespace runs (including the `\n` `_tool_result_text`'s
`"\n".join(parts)` introduces when a `tool_result`'s content arrives as
multiple text blocks) to single ASCII spaces, *then* truncate to the
existing 300-char limit, so the budget is spent on content rather than
whitespace. Case is deliberately left untouched (no `.lower()`): folding
case risks collapsing two genuinely distinct reason strings that differ
only in case, a correctness cost normalization should not buy. This one
change updates the display `detail`/`reason` string and the key's text
component identically — they were already meant to be the same string;
the key had simply never inherited detail's existing normalization.

**Defect 3 — fix the suppression with per-candidate correlation by
`tool_use_id`/`tool_name`, rejecting both "pin it as an accepted
limitation" and "keep the session-wide `refusals_seen` boolean."**
PR #253's original proposal treated Finding 1's suppression as outside
this issue's boundary and proposed only pinning it via a renamed
fixture; the orchestrator's scope-expansion comment explicitly rejects
that alternative — it is not an accepted limitation, it is a fixable
bug within #246's own constraint set (no new instrumentation, buffer-
then-flush preserved), because the fields needed to fix it are already
in the stream (survey.md's mechanism check; Correlation Identifier
idiom, `docs/issue-246/reports/implementation/scout-brief.md` Angle 3).
The second alternative considered — keep `refusals_seen`/
`pending_refusals` exactly as-is and only special-case "exactly one
spurious candidate + one real denial" in the new fixture — is also
rejected: it would fix the one shape the fixture exercises while leaving
the root cause (a single session-wide boolean standing in for N
independent per-candidate confirmations) in place for every other
N-candidates-vs-M-denials combination, which is precisely the failure
mode Angle 3's "multiple in-flight conversations" premise names. The
chosen fix: tag every `pending_refusals` entry with the `tool_name` of
the `tool_use` block it correlates to (via `tool_use_id`, already on
each `tool_result` block and already matched against each `tool_use`
block's `id` — both fields the stream already carries, per the
Constraints section); at flush time, build a `Counter` of `tool_name`
over `permission_denials` and, for each pending candidate, only emit its
real layer type and decrement the counter if its `tool_name` has a
remaining count — otherwise the candidate does not consume a denial
slot. Any `permission_denials` count left over after all pending
candidates are checked (including the zero-candidates case) flushes as
`unclassified-refusal`/`unverified-refusal`, replacing the single
`if not refusals_seen:` gate. This is what stops the suppression: a
spurious candidate whose `tool_name` doesn't match any denial no longer
"uses up" the session's one reportable-event slot, because there no
longer is one shared slot — each candidate and each denial is checked
independently. A candidate with no resolvable `tool_use_id` (e.g. lost
to a partial stream, composing with Defect 1) is treated the same as a
non-matching `tool_name` — conservatively never confirmed, per Defect
1's own "don't fabricate confidence" stance — so it likewise cannot mask
a real, uncorrelated denial. The replacement fixture (scope item 1's own
instruction) now asserts the corrected, **non-suppressing** property:
a spurious candidate that matches an unanchored layer-2/3 pattern but
whose `tool_name` doesn't match the session's `permission_denials`
coexists with a second, genuinely uncorrelated denial, and the
fallback for that second denial still fires — restoring the original
issue text's non-suppression assertion that PR #253 had walked back.

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
3. **`spawn.py`, `_classify_refusal_text` (`:1520-1540`):** change the
   gate `reason` and harness/sandbox `detail` extraction from
   `....strip()[:300]` to `" ".join(...strip().split())[:300]` (collapse
   internal whitespace/newlines, then truncate) — this string already
   feeds both the display detail and (after step 5) the dedup key, so
   one change covers both.
4. **`spawn.py`, dedup keys (`:1529-1539`, `:2825-2826`):** fold the
   now-normalized classified detail/reason text into the dedup key for
   all three layers; key layer 1 on the hook's full path rather than
   `Path(...).stem` alone, keeping `stem` only for the `detail["gate"]`
   display field.
5. **`spawn.py`, per-candidate correlation (`:2794-2826` region):** (a)
   in the `type=="assistant"` branch, record every `tool_use` block's
   `id`→`name` (not just `Write`/`Edit`/`Bash`) into a session-local
   dict; (b) in the `type=="user"` branch, read each `tool_result`
   block's `tool_use_id`, resolve it through that dict, and store the
   resolved `tool_name` (or `None` if unresolved) alongside
   `(ev_type, detail)` in `pending_refusals`; (c) replace the flush
   loop's `if key in refusals_seen: continue` / `if not refusals_seen:`
   pair with: build `Counter(d.get("tool_name") for d in denials if
   isinstance(d, dict) and d.get("tool_name"))`; for each pending
   candidate, emit its real `ev_type` and decrement the counter only if
   its stored `tool_name` is set and the counter has a remaining count
   for it; leave non-matching/unresolved candidates unflushed as their
   classified layer type; after all candidates are checked, flush one
   `unclassified-refusal`/`unverified-refusal` (per the branch, step 1/2)
   if the counter still has any positive remainder. This replaces the
   single session-wide `if not refusals_seen:` gate.
6. **`test_spawn.py`:** add fixtures for (a) EOF/crash with a pending
   classified candidate and no terminal result line →
   `unverified-refusal`; (b) a terminal result line with
   `permission_denials` as `None`/absent and as a truthy non-list (e.g.
   a string), each with a pending classified candidate → same; (c) two
   distinct same-layer `is_error` texts in one session → two distinct
   events, not one carrying only the first's detail; (d) two identical
   same-layer texts → still collapse to one (regression guard for the
   existing "same detail once" intent); (e) two hook paths with the
   same filename stem in different directories → distinct events, not
   collapsed; (f) two same-layer texts differing only in whitespace/an
   embedded newline (multi-block `tool_result` content) → still collapse
   to one (regression guard for the new normalization rule).
7. **`test_spawn.py`:** replace
   `test_spurious_marker_match_does_not_suppress_real_denial_fallback`
   with a fixture asserting the corrected **non-suppression** property:
   a spurious candidate matching an unanchored layer-2/3 pattern (whose
   `tool_name` does not match the session's `permission_denials`) plus a
   second, genuinely uncorrelated denial in the same session — assert
   the fallback for the second denial **fires** (not suppressed), and
   the spurious candidate's own layer event does **not** fire. Add a
   companion fixture where the spurious candidate's `tool_name` *does*
   match a `permission_denials` entry — assert it correlates and fires
   as its real layer type, confirming the Counter-based match isn't
   vacuously permissive.
8. Run `python3 -m pytest test_spawn.py` (or the project's existing test
   entry point) once, full suite, before considering phase 2 complete.

## Out of scope

- Correlating beyond `tool_name` + count — if a session has two denied
  calls to the *same* tool (e.g. two denied `Write`s) alongside two
  distinct classified candidates for that tool, the Counter-based match
  can confirm both by count but cannot tell *which* candidate maps to
  *which* specific denial entry (`permission_denials` carries no
  per-entry identifier beyond `tool_name`). This is a real residual gap
  in the correlation, not silently swept under "session-level" language
  — it is bounded by what `permission_denials`' existing shape can
  support without adding a new field to it (which would be new
  instrumentation).
- Anchoring `_HARNESS_REFUSAL_PATTERNS`/`_SANDBOX_REFUSAL_PATTERNS`
  themselves, or otherwise changing which text classifies at all — the
  fix changes what happens *after* classification (correlation against
  `permission_denials`), not the classification patterns.
- Any change to `_GATE_HOOK_RE`, `_GATE_DENY_RE`,
  `_HARNESS_REFUSAL_PATTERNS`, `_SANDBOX_REFUSAL_PATTERNS`, or
  `_await_bounded`'s cadence.
- Filing or resolving a further follow-up issue for the out-of-scope
  items above — left for the human to judge, per this repo's existing
  pattern for open findings.

## How you'll know it worked

- The seven new/updated fixture groups in `test_spawn.py` (EOF/crash
  unverified flush, malformed-`permission_denials` shapes, same-layer
  dedup masking, hook-stem-collision, whitespace-normalization dedup,
  the corrected non-suppression fixture, and the correlated-spurious
  companion fixture) each fail against the current, unmodified
  `spawn.py` and pass after the fix — mirroring how issue #235's four
  regression cases were verified pre/post-fix
  (`docs/issue-235/reports/implementation.md:151-161`).
- Specifically for the suppression fix: the replacement for
  `test_spurious_marker_match_does_not_suppress_real_denial_fallback`
  asserts `unclassified-refusal`/`unverified-refusal` **does** fire for
  the second, uncorrelated denial (the property the issue's original
  text asserted and PR #253's version had walked back to asserting
  suppression) — this is the pre/post-fix pin for the suppression bug
  itself, not just a renamed no-op fixture.
- All previously-passing fixtures in `test_spawn.py` — in particular
  `test_denials_with_no_correlating_tool_result_are_unclassified`,
  `test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing`,
  and the five layer-labeling tests at `test_spawn.py:1461-1612` — still
  pass unchanged, confirming the three-way `permission_denials` read,
  the widened/normalized dedup key, and the Counter-based correlation
  don't regress existing corroboration/labeling behavior.
- `python3 -m pytest test_spawn.py` run once, full suite, 0 failures.
