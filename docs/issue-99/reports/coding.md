# Issue #99 — coding record

loop_state: landed

## upstream-basis

- `docs/issue-99/proposals/coding.md` @ this branch (phase-1 proposal,
  approved via PR #101 merge — approvers.md account APPROVE
  issue-99/coding).
- `docs/issue-99/reports/coding/survey.md` @ this branch (current-state
  survey: write set = `docs/specs/wake-routing.md` +
  `wakes.py` comment only).
- `docs/specs/wake-routing.md` @ this branch, pre-edit (existing
  "Human-only edges" section used as the shape model).
- `docs/specs/approvers.md` (cited as the evidence channel the new
  section anchors to, per proposal constraint — not modified).
- `roles/feasibility.json` (verdict enum `go|no-go|conditional`,
  unchanged — read to confirm the field-vs-body rule doesn't require
  widening it).
- `wakes.py:277` pre-edit (`verdict == "go"` exact-match check, the
  live incident's refusal point per issue #99's body).

## why

Issue #99: `roles/feasibility.json` allows a `conditional` verdict but
no spec defined how a settled condition legally becomes `go`. Live
incident: a record wrote `"go (조건부 → confirmed by human on PR)"`,
the exact-match check correctly refused it, and the subject went dark
with no recovery path. The approved proposal scopes this to a pure
documentation gap — the exact-match check itself is correct behavior,
not a bug — so the fix is defining the resolution path, not changing
routing logic.

## What was done

1. `docs/specs/wake-routing.md`: added "Conditional verdict
   resolution" section (placed after "Human-only edges", before
   "Board vocabulary this doc uses"), modeled on "Human-only edges"'s
   shape (named edge, who triggers it, what it does). States:
   feasibility alone re-raises its own `verdict` field (no other role
   may edit it); evidence is a human decision through
   `docs/specs/approvers.md`'s existing channels (PR Approve or
   `APPROVE issue-<n>/<role>` comment), cited by path+reference in the
   record body; condition narrative (what was conditional, what
   settled it, the citation) lives in the record body only; the
   `verdict` field itself is rewritten to the literal string `go` —
   never a compound/annotated string; the re-raise is never automated.
2. `wakes.py`: two-line comment above the feasibility
   `verdict == "go"` exact-match check (`wake_coding`'s feasibility
   branch, ~line 277) pointing at the new doc section as the source
   for why non-exact strings are refused and where resolution lives.
   No branch logic changed.

## What did not work

(none — doc-only change plus a comment, no iteration needed)

## Test plan / confirmation run

- `python3 -m pytest test_gates.py test_spawn.py -q` → 83 passed,
  unmodified (confirms zero behavior change to `_rows()`/routing
  logic, per the proposal's constraint).
- Manual read-through of the new section against
  `roles/feasibility.json`'s `go|no-go|conditional` enum: the
  field-vs-body rule does not require widening the enum.
- Manual read-through of the new section against the rest of
  `docs/specs/wake-routing.md` for terminology/table-style
  consistency (no automated check covers doc prose).

## closed_checks

- check: "conditional->go resolution path is documented and matches
  the approved proposal's three requirements (who/evidence/narrative
  placement)"
  code_sha: (docs-only change; see git log for this commit's SHA on
  `docs/specs/wake-routing.md` and `wakes.py`)
  result: closed — all three requirements present in the new section,
  cross-checked against `docs/issue-99/proposals/coding.md` §"What
  will be done" item 1.

## Hunt

warrant-hunter dispatched at phase-2 completion per cadence; this is a
docs-only change with no new branch logic, so the probe's surface is
narrow (spec-vs-code consistency, not runtime behavior).

## Open findings

None open. No `addressed_to: coding` findings existed for this
subject prior to this record.

## Out of scope (per approved proposal)

- External feasibility rulebook (lives outside this repo).
- New mechanically-judged row in `_rows()` — the resolution stays a
  human/role act producing a normal record commit; the existing
  exact-match wake already fires on it.
- Automating the re-raise itself.
