---
code_under_review: 611c0c0
loop_state: phase-2-complete
closed_checks:
  - name: pytest-full-suite
    code_sha: 611c0c0
  - name: pre-fix-regression-repro
    code_sha: 611c0c0
  - name: hunt-assume-broken
    code_sha: 611c0c0
---

# Implementation record — issue #235

Phase 2, executing the approved proposal
(`docs/issue-235/proposals/refusal-classifier-corroboration.md`, approved
via issue-level comment `APPROVE issue-235/implementation`,
single-account mode, role-handoff contract v3 s19, PR author and
approver both jjongkwann).

## What was done

Landed exactly the proposal's write set (`611c0c0`):

1. **`spawn.py`**
   - `_GATE_HOOK_RE` gained a `^` start anchor
     (`r"^PreToolUse:\S+ hook error: \[([^\]]*)\]"`) — a marker
     quoted/embedded anywhere but the start of the `tool_result` text no
     longer matches.
   - `_classify_refusal_text`'s layer-1 branch now takes `detail.gate`
     from the hook path stem unconditionally; `_GATE_DENY_RE`'s token
     (when present) is used only to compute where the reason text
     starts, never as the gate identity.
   - `_spawn_one`'s per-line loop: the `type:"user"` branch no longer
     calls `_append_event` directly. It buffers each classified
     `(ev_type, key, detail)` into a `pending_refusals` dict (first
     classification per key wins, matching the prior per-session dedup
     intent). The `type:"result"` branch — reached once, at the
     terminal line, per Claude Code's stream-json contract — now gates
     everything on `denials` (the same `permission_denials` read
     already there): non-empty flushes `pending_refusals` into real
     events via `_append_event`, then falls back to
     `unclassified-refusal` only if nothing flushed; empty flushes
     nothing and buffered candidates are silently dropped, never
     written to `.events.jsonl`.
2. **`test_spawn.py`** — `EventReporting`: four new regression cases,
   each built from the issue's own requirement 4 list and confirmed
   failing against the pre-fix classifier before the fix landed (see
   Verification run below):
   - `test_layer2_denial_quoting_gate_marker_is_harness_refusal_not_gate`
     (requirement 4(i))
   - `test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing`
     (requirement 4(ii))
   - `test_spurious_marker_match_does_not_suppress_real_denial_fallback`
     (requirement 4(iii))
   - `test_record_fields_gate_denial_reports_hook_stem_not_role_name`
     (requirement 4(iv), text built from the issue-232
     execution-observation record's live `record-fields-gate` sample)

## What will be done (from proposal)

Proposal items 1-4 (corroborate the per-line classification against
`permission_denials`, anchor `_GATE_HOOK_RE`, prefer the hook stem for
`detail.gate`, add the four named regression cases) — all delivered as
scoped, no additions or omissions.

## What did not work

None.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step ->
  no handbook entry needed.
- No changed public signature or wire format — event type names and the
  `detail` dict shape are unchanged; only which event fires (or doesn't)
  and what value `detail.gate` holds changed -> no
  `docs/issue-235/decisions/` entry (matches the survey's own call,
  `docs/issue-235/reports/implementation/survey.md` closing section).
- No benchmark/investigation numbers produced beyond this record -> no
  separate `docs/issue-235/reports/` entry.

## Hunt

No `warrant-hunter` agent type is registered in this harness (same gap
issue-232's own record hit). Substituted a `general-purpose` agent with
an adversarial brief against the committed diff (`611c0c0`), stance
**assume-broken** (rotated — issue-232 used assume-incomplete-coverage
most recently on this classifier). Dispatched foreground (synchronous),
report received before this record was finalized.

Findings:

1. **PLAUSIBLE, flagged for follow-up — deferring emission to the
   terminal `result` line trades away crash-survival for the refusal-
   event class specifically.** `pending_refusals` is only flushed
   inside the terminal `type:"result"` branch (`spawn.py:2664-2688`).
   If the child process crashes, is killed, or the stream truncates
   *after* a genuine denial's `tool_result` line streamed but *before*
   the terminal `result` line arrives, the `for line in proc.stdout:`
   loop ends at EOF with `pending_refusals` populated only in memory —
   never flushed — while `_spawn_one` still proceeds to write
   `session-end`. Before this fix, the classified event would already
   have been appended (`.events.jsonl` is append-only specifically so
   it survives a crash, per the comment at `spawn.py:2608-2611`); after
   this fix, a crash in that window loses the refusal event entirely,
   something the pre-fix code did not do. Left open rather than
   redesigned here: the approved proposal's own mechanism is
   corroborate "from the terminal `result` line, which ... always
   follows the per-line stream" — recovering the crash case would mean
   deciding what to do with unconfirmed `pending_refusals` when no
   terminal line ever arrives (flushing unconditionally reopens the
   same gap this issue exists to close), a call outside this issue's
   four named items and this session's write set to make on its own.
   Worth a human decision on a follow-up issue.
2. **PLAUSIBLE, non-blocking — corroboration is session-level, not
   per-candidate.** `spawn.py:2669-2679` flushes every buffered key
   once `denials` is non-empty, with no check that the count or
   content of `denials` matches the number of buffered candidates. Two
   simultaneously-classifiable but unrelated `tool_result` blocks (one
   real, one textually coincidental) alongside a single real denial
   would both fire. Same class of limitation issue-232's own hunt
   already documented for the harness/sandbox patterns being generic
   substrings (`docs/issue-232/reports/implementation.md` Hunt finding
   2) — not new, and strictly better than pre-fix code, which had zero
   corroboration of any kind. Requirement 4's four cases don't exercise
   two simultaneously-plausible candidates against one denial, and
   constraint 5 forbids inventing new correlation instrumentation to
   close this gap.
3. **Unsure, low confidence — `_tool_result_text`'s block-list join
   could in principle shift a real marker off index 0.**
   `_tool_result_text` (`spawn.py:1505-1517`) joins list-content blocks
   with `"\n".join(...)`; a leading empty/whitespace block before the
   real hook-error text (unconfirmed against any real observed sample
   — all cited samples, including execution-observation's, are plain
   strings) would push the marker past position 0, downgrading a
   genuine gate-refusal to `unclassified-refusal` rather than
   misclassifying it. Not chased further — no real sample shows this
   shape.

No exception/crash paths in `Path(hook_m.group(1)).stem` (checked empty
string, a traversal path, embedded NUL, bare `/`, bare `.` — all return
safely), no dict-key or scoping bugs (`pending_refusals` is a fresh
local per `_spawn_one` call; keys are hashable strings/tuples
throughout).

## Verification run

`python3 -m pytest test_spawn.py` — 170 passed, 0 failed.

Pre-fix regression repro (issue requirement 4, and the invoking
instruction): added the four new test methods to `test_spawn.py` while
`spawn.py` was still unmodified (equivalent to `main`/`70f867f`), ran
them — all 4 failed, each showing the exact pre-fix misclassification
requirement 4 names (a quoted marker in a layer-2 message classifying as
`gate-refusal`; a zero-`permission_denials` session still emitting
`gate-refusal`; a spurious match populating `refusals_seen` and
suppressing the real denial's `unclassified-refusal` fallback; `detail.gate`
resolving to the role-name token `execution-observation` instead of the
hook-stem `record-fields-gate`). Applied the fix, reran the same 4 —
all passed. Ran the full suite — 170 passed, 0 failed.

## Open findings

Hunt finding 1 (crash before the terminal `result` line loses buffered
refusal candidates entirely) is a genuine change in failure-mode
behavior relative to pre-fix code and is not one of the four cases the
issue names — it does not block this delivery (the approved proposal's
own corroboration mechanism produces it, and no alternative in the
proposal's Rationale avoids it without inventing a new design outside
this issue's scope), but it is real and worth the human's attention on
a follow-up issue. Hunt findings 2 and 3 are non-blocking: finding 2 is
the same class of pre-existing precision limit issue-232's own hunt
already accepted, and finding 3 is unconfirmed against any real sample.
No open finding requires resolution before this delivery.

## Next steps

Hunt finding 1 (see above) is a candidate for a follow-up issue: decide
whether refusal-candidate buffering should have a crash/EOF fallback
(e.g. flush unconfirmed candidates when the stream ends without a
terminal `result` line) and, if so, what corroboration standard applies
when `permission_denials` was never read. Not proposed or decided here.

## Open-finding resolution path

No open findings require resolution; none outstanding.
