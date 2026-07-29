# wake-routing — WAKES-ON table

This is this repo's own record of the WAKES-ON routing table `wakes.py`
implements. It replaces the external contract's §3 table as the cited
source: `wakes.py`'s comments point here, not at contract section
numbers, because the routing decisions below already live entirely in
`wakes.py`'s code — this doc documents what is already true, it does
not define new behavior.

Nine rows. Seven are judged mechanically by `wakes.py._rows()`; two are
judgment calls a human makes; two edges outside the row table are
human-only by design (automation is disallowed for them, not merely
unimplemented).

## Mechanically-judged rows (7)

| role | trigger (board vocabulary) |
| --- | --- |
| feasibility | a hypothesis proposal appears under `docs/issue-*/proposals/*.md` (`kind: hypothesis`) that feasibility's record hasn't acknowledged, or has acknowledged at a stale `sha` |
| coding | four wake-branches — new/changed proposal upstream, a `verdict: go`, a `loop_state` transition it must react to, an `addressed_to: coding` finding — all funneled through the shared first-build approval guard below |
| ux-design | a design-relevant upstream record changes (`loop_state`/`sha` drift analogous to the coding branches) |
| verify | a record reaches the `loop_state` that means "ready for verification" |
| reflect | a verified/landed record needs the reflect pass |
| qa | any commit under `src/` since qa's record last acknowledged |
| review | `loop_state: landed` persists without a matching review record |

Each row's `sig` (see `Row` in `wakes.py`) is the content hash of the
files it based its wake on; when the same evidence recurs, the row
does not re-fire (see `consume()`/`fresh()`), it doesn't just get
suppressed silently. All seven are governed by the same rule: a row
that CAN be judged from repo state alone is never left to a human.

## Judgment-only rows (2)

These two rows are not evaluated mechanically — `wakes.py` reports
them separately (see `JUDGEMENT` in `wakes.py`) precisely because they
require substantive judgment, not because nobody built the check yet.

| role | why it's judgment |
| --- | --- |
| product | whether qa/review's findings shake the agreed acceptance criteria is a content question |
| ops | whether a merged change is "ready to roll out" is a judgment call |

## Human-only edges (2, outside the row table)

Automation is explicitly disallowed for these — not merely
unimplemented (see `HUMAN_ONLY` in `wakes.py`):

- **findings-resolved re-verify**: the role that raised a blocking
  finding wakes again once it is addressed. Only a human triggers this
  re-verify.
- **round-done value gate**: `candidate-round-done` wakes a human to
  run the round's value gates. Never automated.

## First-build approval guard

`coding`'s first entry into build on any subject is gated: it does not
wake on its own funnels until the subject's front record reaches
`scope-approved` (the sole path there is a human reading the
`scope-proposed` state and approving it — no role, including coding
itself, can self-approve). This guard applies uniformly across all
four of coding's wake-branches, including the finding-return edge
below, so none of them can bypass it individually.

## Finding-return edge

A finding recorded in any role's report body (`addressed_to: <role>`)
wakes that role — not just coding. `wakes.py` resolves this as this
repo's own decided behavior: earlier drafts of the routing table only
wrote the finding trigger explicitly on coding's row, but every role
wakes on findings addressed to it. The first-build approval guard
above applies equally to the finding-return branch.

## Board vocabulary this doc uses

- `loop_state`: the phase marker a role's report carries (e.g.
  `scope-proposed`, `scope-approved`, `landed`).
- `verdict`: a `go`/`no-go`-shaped call recorded by a role.
- `addressed_to`: the role a finding in a report body targets.
- `upstream`: the `path`/`sha` pairs a record cites as what it read;
  staleness is judged by comparing the recorded `sha` to the path's
  current head.
