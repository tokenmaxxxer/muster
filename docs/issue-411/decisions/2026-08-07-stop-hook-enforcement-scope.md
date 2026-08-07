# Stop-hook enforcement scope for the six requirements named in #411

`stop-gate.sh` is now wired as a `Stop` hook and fires on approval-shaped
`last_assistant_message`. This records which of the six requirements named
in #411 get real, firing coverage from it and which don't — per #310, an
unenforced rule must be recorded as such, not implied to be covered.

- **#318** — structural subset enforced. `stop-gate.sh` checks for an
  issue reference (`#\d+`), a change-statement clause, and a
  risk/tradeoff clause on any approval-shaped reply. The full six-item
  shape `run.md` describes, and whether the *stated* risk is the *real*
  risk, remain unenforced — that is substance, not structure, and a
  regex heuristic cannot reach it.
- **#320** — unenforced. Distinguishing "explains effect" from
  "enumerates changes" is a judgment call a substring/regex heuristic
  cannot reliably make without a high false-positive/false-negative rate
  in both directions; not built this pass.
- **#341** — unenforced by this proposal. Its own premise ("not
  mechanically enforceable") is now stale — a Stop hook does reach the
  conversational turn #341 assumed was unreachable. Flagged for #341 to
  reopen against; not resolved here (out of this proposal's write set).
- **#371** — unenforced by a Stop hook, and cannot be by one: it is a
  status-computation defect inside `spawn.py`, not a claim made in chat
  text. Wrong mechanism for this hook to apply to.
- **#373** — unenforced. Same shape as #320 — whether a delta was stated
  is a judgment call a heuristic cannot reliably make.
- **#379** — unenforced. Whether the orchestrator *actually* re-checked a
  constraint before offering a choice is not observable from the reply
  text alone.

Net: 1 of 6 (#318) gets real, firing, tested coverage — structural subset
only. 5 of 6 remain open, each for its own stated reason.
