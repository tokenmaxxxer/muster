---
status: proposed
files:
  - on-the-record/hooks/stop-gate.sh
  - on-the-record/hooks/hooks.json
  - tests/test_stop_gate.sh
  - docs/issue-414/decisions/2026-08-07-intention-followthrough-coverage.md
---

References #414.

## Request

Orchestrator replies sometimes end by stating a next action ("지금부터
남은 14건을 차례로 뚫겠습니다") that then does not happen — the next turn opens
with a fresh assessment instead, and the stated intention is gone with
no record. The operator wants this made durable and checkable rather
than left to the model's own attention. Per #310, the acceptance
criterion is an executable artifact that fails when this regresses, and
the mechanism must state, against the four transcript instances in the
issue, how many it would have caught and which phrasings it misses.

## Constraints

- House style: bash wrapper, fail-closed `trap`, `CLAUDE_ROLE`
  pass-through (orchestrator-only concern, matching `deliverable-guard.sh`
  and #411's precedent).
- Stay inside #298's boundary (`gh pr merge`/`APPROVE` acts only) —
  #414 does not touch #298's files.
- Do not build #411's own unbuilt approval-shape check as part of this
  proposal — #414 is a distinct pattern (cross-turn intention
  follow-through, not same-turn structural shape) and gets its own
  script; conflating the two would silently make #414's coverage claim
  about a different check's behavior.
- No new dependency; no DB/daemon for cross-turn state — a marker file
  under a session-scoped tmp path is the only persistence primitive
  available to a stateless bash hook.
- Per #310: name which of the issue's four "what needs deciding" items
  get real coverage and which stay open, in the decision record, not
  implied by silence.

## Rationale

**Chosen approach**: a new `Stop` hook (`stop-gate.sh`) that (a) scans
`last_assistant_message` for a stated-future-intention phrase against a
fixed pattern list (Korean commitment endings: "겠습니다"/"하겠다"/"할게요"
combined with a forward-looking marker, and English "I will "/"I'll "/
"next I will"/"going to now"), and when matched, writes the matched
clause plus a timestamp-free session-scoped marker to
`${CLAUDE_STATE_DIR:-/tmp}/on-the-record-intent-<session-hash>`; (b) on
every firing, first checks for an existing marker from a *prior* Stop
call in the same session and, if present, requires the current
`last_assistant_message` to contain either a completion signal for that
same clause (a tool-call/action reference correlating to it — approximated
by requiring the new message to be substantively different in a way that
isn't itself another bare "will" statement re-issuing the same promise)
or an explicit drop statement; violation emits
`hookSpecificOutput.additionalContext` naming the undischarged clause,
never `decision: "block"`.

**Alternative considered and rejected**: extend #411's planned
`stop-gate.sh` (approval-shape check) to also cover intention
follow-through in the same script. Rejected: #411's check is same-turn
structural (does this one reply contain three clauses); #414's check is
inherently cross-turn (does *this* reply discharge what the *previous*
reply promised) — different state model, different failure mode
(false-negative here means silence propagates across two turns, not
one). Merging them means one script's fail-closed trap taking down both
checks together, and a coverage claim for #414 would be entangled with
whatever #411 eventually builds. Keeping them separate scripts (both
registered under the same `Stop` array in `hooks.json`, which supports
multiple entries) keeps each one's coverage independently statable, per
#310.

**Alternative considered and rejected**: `decision: "block"` on an
undischarged intention. Rejected for the same reason #411's proposal
rejected blocking on its structural check — the detector is a phrase
heuristic, not a semantic judge of whether the drop was legitimate
(the issue's own item #3 says a dropped intention is sometimes correct,
and only needs to be *visible*, not forbidden). Blocking would punish
legitimate priority changes exactly as hard as silent drops.

## What will be done

1. `on-the-record/hooks/stop-gate.sh` — new Stop hook per Rationale
   above. Orchestrator-only (`CLAUDE_ROLE` set → pass-through). Cheap
   grep-style prefilter (does the message contain any commitment marker
   at all) before the embedded Python does clause extraction and marker
   file read/write. Marker cleared once discharged or explicitly dropped
   (write-then-delete, not append-only, so state doesn't leak across
   unrelated future turns).
2. `on-the-record/hooks/hooks.json` — add a `Stop` array with one entry
   pointing at `stop-gate.sh`.
3. `tests/test_stop_gate.sh` — behavioral, run via
   `tests/run-orchestrate-tests.sh`-compatible pattern (own script,
   invoked the same way `run-orchestrate-tests.sh` invokes the other
   hook tests): (a) turn N states an intention ("지금부터 남은 14건을 차례로
   뚫겠습니다") → marker written, exit 0 (nothing to check against yet);
   (b) turn N+1 opens with a fresh status report and no action taken →
   `additionalContext` names the undischarged clause; (c) turn N+1
   explicitly states the intention was dropped and why → exit 0, marker
   cleared; (d) turn N+1 re-states another bare "will" clause without
   discharging the first → still flagged (re-promising isn't
   discharging); (e) a message with no commitment phrasing at all →
   pass-through, exit 0, no marker touched.
4. `docs/issue-414/decisions/2026-08-07-intention-followthrough-coverage.md`
   — records, against the issue's four "what needs deciding" items and
   the four transcript instances quoted in the issue body:
   - Item 1 (must become durable or not stated) — partially addressed:
     the marker file makes a stated intention durable *after the fact*,
     for one Stop-to-Stop cycle; it does not prevent the sentence from
     being written in the first place (that would require a
     pre-generation constraint this mechanism cannot enforce from a
     Stop hook).
   - Item 2 (reconcile against what happened) — addressed by the
     marker-and-check design above.
   - Item 3 (dropped-deliberately must be visible) — addressed: an
     explicit drop statement clears the marker silently-to-the-check
     but is only "silent" to the hook, not to the operator, since it's
     the orchestrator's own visible sentence that clears it.
   - Item 4 (doing X should be preferred to saying X) — not
     enforceable by a Stop hook; recorded open, same as #411's #371
     line (behavior-shaping, not a text-observable property).
   - Against the 4 quoted instances: state which the phrase-list would
     have caught (the "지금부터", "뚫겠습니다", "확인하겠습니다" style ones —
     estimate 3 of 4 catchable by the Korean commitment-ending pattern;
     the "#307을 승인해서 처리할까요?" instance is a *question*, not a stated
     intention, and is explicitly named as **not caught** by this
     mechanism — a different pattern, tracked as a gap, not silently
     folded in).
   - Explicit phrasing-miss disclosure per the issue's own demand:
     misses any intention phrased as a plan without a commitment verb
     ("다음은 X 순서로 처리"), any intention embedded mid-message rather
     than at the reply's end, and any intention split across multiple
     sentences with no single matching clause.

## Out of scope

- Building #411's approval-shape check (separate, already-proposed,
  unbuilt work).
- Any pre-generation mechanism that would stop the orchestrator from
  writing an unbacked "I will" sentence in the first place.
- #371 (status-computation defect in `spawn.py`) and #341 (stale
  premise, flagged for #341 itself to reopen against) — named in scope
  boundary by the issue, not rebuilt here.
- `gates/` module-collision fix (#398) — unrelated tree, not touched.

## How you'll know it worked

`tests/test_stop_gate.sh` passes, demonstrating all five fixtures in
"What will be done" item 3 — in particular fixture (b), an
undischarged-intention turn caught by a firing hook (not merely a script
that exists), and fixture (e), an ordinary turn passing through
untouched. The decision record states the 3-of-4 transcript-instance
coverage count and the explicit phrasing-miss list, so the PR does not
imply full coverage anywhere.
