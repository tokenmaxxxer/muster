---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: landed
---

# Implementation record — issue #246

Phase 2, executing the approved proposal
(`docs/issue-246/proposals/refusal-classifier-residual-fixes.md`,
approved via issue-level comment `APPROVE issue-246/implementation`,
single-account mode, role-handoff contract v3, PR author and approver
both jjongkwann).

Rebased onto latest `origin/main` before building — issue #224 landed
`wrapper_pid`/`WATCH_CRASH_RC`/`_issue_comments` pagination changes to
`spawn.py` ahead of this branch, shifting the classifier region's line
numbers (~+40-56 lines) from the proposal's line references. Rebase was
clean (no conflicts — the branch had only touched `docs/issue-246/*` in
phase 1).

## What was done

All edits in `spawn.py`'s `_spawn_one()` buffer-then-flush region
(`_classify_refusal_text` ~line 1530, the loop body ~line 2790-2980) and
`test_spawn.py`'s `EventReporting` class, per the proposal's "What will
be done" items 1-7:

1. `_classify_refusal_text` (`spawn.py:1530-1564`): gate `reason` and
   harness/sandbox `detail` now go through
   `" ".join(text[...].strip().split())[:300]` (collapse whitespace
   runs, including embedded `\n` from multi-block `tool_result` content,
   then truncate) instead of bare `.strip()[:300]`. Case is untouched.
2. Dedup keys widened: layer 1 keys on the gate hook's full path (not
   `Path(...).stem` — `stem` stays only in the display field
   `detail["gate"]`) plus the normalized `reason`
   (`("gate", hook_path, reason)`); layers 2/3 fold in the normalized
   `detail` (`("harness", detail)` / `("sandbox", detail)`) instead of
   being layer-wide (`("harness",)` / `("sandbox",)`).
3. Two new module-level helpers, `_flush_correlated_refusals()` and
   `_flush_unverified()` (`spawn.py:1567-1602`), replace the inline
   flush logic and the single session-wide `if not refusals_seen:` gate.
4. Three-way `permission_denials` read in the `type=="result"` branch
   (`spawn.py:2918-2946`): an actual `list` (empty or not) goes through
   `_flush_correlated_refusals` (Counter-based per-`tool_name`
   correlation); anything else (`None`, absent, truthy non-list) goes
   through `_flush_unverified` instead — defect 1's `isinstance` guard,
   expressed as the three-way split the proposal specified.
5. EOF/crash flush (`spawn.py:2977-2982`): a `result_seen` flag, set
   only once a `type=="result"` line is actually processed; if the
   `for line in proc.stdout:` loop exits with `result_seen` still False
   and `pending_refusals` non-empty, flushes those entries via
   `_flush_unverified` — covers S1 (crash/kill/truncation) and S3
   (malformed terminal JSON, already caught by the existing
   `except ValueError: continue`).
6. Per-candidate correlation (`spawn.py:2855-2977`): a new session-local
   `tool_use_names: dict[str, str]` records every `tool_use` block's
   `id`→`name` in the `type=="assistant"` branch (not just
   `Write`/`Edit`/`Bash`, since correlation needs every tool). The
   `type=="user"` branch resolves each classified candidate's
   `tool_result.tool_use_id` through that dict and stores the resolved
   `tool_name` (or `None`) as a third tuple element in
   `pending_refusals`. `_flush_correlated_refusals` builds
   `Counter(tool_name for denial in denials)` and only emits a
   candidate's real layer-type event (decrementing the matching count)
   if its stored `tool_name` is set and the counter still has a
   remaining count for it — non-matching/unresolved candidates are
   dropped rather than emitted as their real layer type. This replaces
   the session-wide `refusals_seen` boolean that let one classified
   candidate suppress the fallback for every other, uncorrelated denial
   in the same session.
7. `test_spawn.py`: added a `_tool_use_line()` helper on
   `EventReporting`; added 7 new fixture groups per item 6 (EOF/crash
   flush, malformed-`permission_denials`-shape flush with 3 subtests,
   two-distinct-same-layer-denials, two-identical-still-collapse,
   hook-stem-collision, whitespace-normalization-collision); replaced
   `test_spurious_marker_match_does_not_suppress_real_denial_fallback`
   with two fixtures per item 7 (`test_spurious_candidate_tool_name_
   mismatch_does_not_suppress_real_denial_fallback` and its companion
   `..._match_correlates_and_fires_as_real_layer`), since the old
   fixture's spurious text never classified at all (survey's own
   finding) and so never exercised the suppression path it claimed to
   guard.

Verification: `python3 -m pytest test_spawn.py -q` — 196 passed, 0
failures, run in full after all fixes below (this is the authoritative
confirmation run; `python3 -m unittest test_spawn -q` reproduces the
same pre-existing, environment-only `rulebook_checkout` git-template-copy
failure documented in `docs/issue-224/reports/implementation.md` —
confirmed against the pre-change baseline via `git stash`: 41 errors at
baseline vs 50 after, fully accounted for by the net +9 new
`EventReporting`-based tests each independently hitting the same
environment gap, not a code regression).

## Why

Executing the phase-1 proposal at
`docs/issue-246/proposals/refusal-classifier-residual-fixes.md`: three
residual gaps left open by `docs/issue-235/reports/execution-observation.md`
(Findings 1-3) on the `permission_denials` refusal classifier in
`spawn.py`, with issue #246's own scope-expansion comment additionally
requiring Defect 3's session-wide suppression (a classified candidate
silently swallowing another, genuinely uncorrelated denial's
`unclassified-refusal` fallback) to be *fixed* via per-candidate
correlation, not pinned as an accepted limitation.

## Upstream basis

`docs/issue-246/proposals/refusal-classifier-residual-fixes.md`, approved
via issue #246's `APPROVE issue-246/implementation` comment.

## What did not work

- First cut of `_flush_correlated_refusals` built `remaining` (the
  Counter) only from `permission_denials` entries with a truthy
  `tool_name` — matching the proposal's literal Counter description.
  Expected: entries that don't carry a usable `tool_name` simply can't
  correlate with any candidate, so they'd be dropped from matching only.
  Actual: the mandatory hunt found they were dropped from the *leftover
  count* too, so a denial entry shaped differently from
  `{"tool_name": "..."}` (the shape `docs/decisions/2026-07-29-headless-
  cli-measured-facts.md` documents as the actual CLI output, but not
  contractually guaranteed) vanished with zero events — reopening
  Defect 1's exact "0 events, indistinguishable from no denial" failure
  through a new door. Fixed by adding a separate `unattributable` count
  (denials lacking a usable `tool_name`) folded into the leftover check,
  so any denial that can't be attributed to a specific candidate still
  triggers the `unclassified-refusal` fallback instead of disappearing.
- First cut of the `type=="result"` branch had no guard against a
  repeated `result` line. Expected: `result` is the stream's terminal
  line, so the branch runs at most once per session (documented
  assumption, e.g. `spawn.py:2762-2764`'s comment). Actual: that
  assumption is explicitly unenforced elsewhere in this repo's own
  research (`docs/issue-235/reports/execution-observation/research-
  evidence.md:160-164`), and the pre-#246 code's session-wide
  `refusals_seen` set made a second `result` line's flush a no-op for
  free; the new design dropped that incidental protection, and the hunt
  reproduced a duplicated `harness-refusal` event from two identical
  `result` lines. Fixed by wrapping the flush in `if not result_seen:`,
  restoring "flush at most once per session."

## Open findings

From the hunt, findings not fixed here, with resolution path:

1. **N-candidates-vs-M-same-`tool_name`-denials, N > M**: the extra
   candidate(s) beyond `M` get no event at all (not even
   `unclassified-refusal`), since the `Counter` reaches exactly 0 and
   there's no way to distinguish "a real (N-M)th denial of this tool"
   from "the (N-M)th candidate was itself a spurious classification."
   This is the same root-cause gap the proposal's own "Out of scope"
   section already names and bounds (`permission_denials` carries no
   per-entry identifier beyond `tool_name`) — not a new gap, just not
   spelled out in that exact N>M wording. Resolution path: would need
   `permission_denials` to carry a `tool_use_id` (new instrumentation,
   out of this issue's constraints) to resolve precisely; left as the
   same accepted residual the proposal already scoped out.
2. **300-char dedup-key truncation collision**: two genuinely different
   same-layer texts sharing a >300-char common prefix now collide into
   one dedup key. Explicitly an accepted trade-off in the proposal's own
   Rationale (rejects a second, independent truncation length for the
   key) — degrades gracefully (first-write-wins, leftover denial count
   still surfaces via `unclassified-refusal`), not a silent total loss.
   No resolution path needed unless the proposal's own accepted
   trade-off is revisited in a future issue.

Both are pre-existing-shape residuals the approved proposal itself
scoped out, not omissions introduced by this session's fixes — no
further action taken here.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step
  introduced -> N/A.
- No library-or-format choice over a named alternative, or changed
  public signature/wire format, beyond what the proposal's own Rationale
  already recorded -> no additional `docs/issue-246/decisions/` entry.
- No benchmark/investigation numbers produced -> no additional
  `docs/issue-246/reports/` entry beyond this record and the existing
  phase-1 survey/scout-brief.

## Hunt

Stance: **adversarial-self** (rotated — the immediately prior
implementation session, issue-224, used assume-incomplete-coverage). No
registered `warrant-hunter` subagent type is available in this harness
(same gap noted in issue-216/218/220/221/223/224/232/235/236's records),
so `general-purpose` was dispatched in its place with an explicit
adversarial-self brief. Dispatched foreground (synchronous) against the
uncommitted diff before delivery, with instructions to actually run the
tests and construct adversarial inputs by hand rather than re-reading
the diff and trusting its own reasoning.

Findings:

1. **NOT-A-BUG.** Whether modifying the 5 pre-existing layer-labeling
   tests (adding a resolving `tool_use` line via the new
   `_tool_use_line()` helper) is a defensible reading of the proposal,
   given the proposal's "How you'll know it worked" section separately
   claimed they'd "pass unchanged." Confirmed defensible: the
   correlation code path is identical for real and synthetic streams: a
   candidate with no resolvable `tool_use_id` never fires as its real
   layer type in either case (item 5(c)'s literal wording), and all 5
   tests' assertions are unchanged — only their input stream gained a
   realistic preceding `tool_use` line establishing what production
   streams always have.
2. **CONFIRMED, fixed.** `permission_denials` entries lacking a
   resolvable `tool_name` caused total, silent event loss (not even
   `unclassified-refusal`) — see "What did not work" above. Fixed with
   the `unattributable` count; regression test
   `test_denial_entry_missing_tool_name_still_fires_unclassified_fallback`
   added.
3. **Test-coverage gap, closed.** Unresolved `tool_use_id` paired with a
   well-shaped `permission_denials` list already degraded correctly to
   `unclassified-refusal` (not dropped) even before the finding-2 fix —
   but no fixture exercised it, which is exactly how finding 2's
   neighbor bug went undetected. Regression test
   `test_unresolved_tool_use_id_with_well_shaped_denials_degrades_to_unclassified`
   added.
4. **NOT-A-BUG, confirmed matches claims.** Full suite run
   (`python3 -m pytest test_spawn.py -q`) — 193 passed at hunt time (196
   after the 3 new regression tests added post-hunt). `unittest`-mode
   errors traced to `conftest.py`'s `os.environ.setdefault(...)` for
   `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` (pytest auto-loads
   `conftest.py`; bare `python3 -m unittest` does not) — confirmed
   pre-existing via `git stash` to the parent commit (41 errors at
   baseline, same signature).
5. **CONFIRMED, fixed.** No guard against a repeated `type=="result"`
   line — see "What did not work" above. Fixed with the `result_seen`
   guard around the flush; regression test
   `test_repeated_result_line_does_not_double_flush` added.
6. **NOT-A-BUG / same accepted residual as the proposal's "Out of
   scope."** N-candidates-vs-M-same-`tool_name`-denials with N > M —
   recorded as Open findings item 1 above.
7. **NOT-A-BUG.** Empty `reason` when `_GATE_DENY_RE` matches at text
   end (`text[deny_m.end():]` is `""`) — normalizes to `""` cleanly, no
   crash, dedup key still separated by `hook_path`. Pre-existing edge
   case in `_classify_refusal_text`, not introduced or worsened here.
8. **NOT-A-BUG.** `pending_refusals`/`tool_use_names`/`result_seen` are
   all `_spawn_one`-call-local, never persisted, never expected to
   survive a respawn — unchanged from the pre-#246 design.
9. **NOT-A-BUG / accepted trade-off.** 300-char dedup-key truncation
   collision — recorded as Open findings item 2 above; explicitly
   rejected as a concern in the proposal's own Rationale (no second,
   independent truncation length for the key).

Disposition: findings 2 and 5 fixed in this session (in-scope, same
files, no consumer's existing contract changed beyond the two new
helper functions' own internal correctness). Findings 1, 4, 6, 7, 8, 9
checked out fine or are already-accepted, documented trade-offs. Finding
3 closed a test-coverage gap without needing a code change.

## Rationale for deviations

Two deviations from the literal `## What will be done`, both driven by
the mandatory phase-2 hunt rather than a scope-exceeded stop or an
alternative-swap:

1. Item 5(c)'s Counter description
   (`Counter(d.get("tool_name") for d in denials if isinstance(d, dict)
   and d.get("tool_name"))`) was implemented verbatim first; the hunt
   found this silently drops malformed/`tool_name`-less
   `permission_denials` entries from the leftover count, not just from
   matching — reintroducing Defect 1's "0 events" failure through a new
   door. Added the `unattributable` count (see "What did not work")
   inside `_flush_correlated_refusals`, purely additive to the function
   item 5(c) already specified — no change to any other function's
   contract, no change to the event schema, no change to the dedup keys
   or the correlation's `tool_name`-matching semantics for well-shaped
   entries.
2. Item 5(c) didn't address a repeated `type=="result"` line (the
   proposal assumed, consistent with an existing but unenforced
   in-repo comment, that `result` is always the stream's single
   terminal line). The hunt reproduced a duplicate-event regression
   versus the pre-#246 code, which had this guard for free via the
   session-wide `refusals_seen` set. Added the `result_seen` guard
   around the in-loop flush — purely additive, restores a robustness
   property the prior code already had, changes no event schema or
   external contract.

Both deviations stay inside the same frozen write set (`spawn.py`,
`test_spawn.py`) the proposal names, touch only the two new helper
functions and the one `if obj.get("type") == "result":` branch item
5(c) already scoped, and add 3 regression tests documenting exactly
what each fix guards against.
