# Issue #99 — Phase 1 Proposal: define conditional -> go resolution in wake-routing.md

## files: (frozen write set)

- `docs/specs/wake-routing.md`: one new section, "Conditional verdict
  resolution", placed after "Human-only edges" (it is the same shape
  of edge: a human-gated field transition, not a mechanically-judged
  row). Covers: who re-raises `conditional` to `go`, on what evidence,
  and that condition narrative belongs in the record body, never in
  the `verdict` field.
- `wakes.py`: comment-only — a one-line pointer next to the exact-
  match `verdict == "go"` check in `wake_coding`'s feasibility branch,
  noting that non-"go" strings (including compound text) are refused
  by design and the resolution path lives in the new doc section. No
  branch logic changes.

**Explicitly excluded from this write set:** `roles/feasibility.json`
(the `go|no-go|conditional` enum is already correct and unchanged),
any change to `_rows()`'s conditions, `test_gates.py`, `test_spawn.py`,
and the external feasibility rulebook (lives outside this repo, per
its `path` pointer in `roles/feasibility.json` — out of scope).

## Request (paraphrased)

`roles/feasibility.json` allows a `conditional` verdict, but nothing
defines what happens once the condition is settled. Live incident: a
feasibility record wrote `"go (조건부 → confirmed by human on PR)"`
into the `verdict` field; `wakes.py`'s exact-match `go` check correctly
refused it (by design — not a bug), and the subject went dark because
no defined path existed for turning a settled condition into a valid
`go`. Define that path in `docs/specs/wake-routing.md`.

## Constraints

- Zero behavior change to `_rows()`: the exact-match check is already
  correct and stays untouched. This is a documentation gap, not a
  routing-logic gap.
- The `verdict` field must only ever hold `go`, `no-go`, or
  `conditional` (matching `roles/feasibility.json`'s enum) — never a
  compound or annotated string.
- The resolution path must anchor its "evidence" requirement to this
  repo's existing human-decision mechanics already defined in
  `docs/specs/approvers.md` (PR Approve from a different approvers.md
  account, or an `APPROVE issue-<n>/<role>` comment in single-account
  mode) rather than invent a new evidence channel.
- Model the new section on the existing "Human-only edges" section's
  shape (named edge, who triggers it, what it does) — the section is
  additive to `docs/specs/wake-routing.md`, not a rewrite of its
  existing content.

## What will be done (phase 2, after approval)

1. Add "Conditional verdict resolution" section to
   `docs/specs/wake-routing.md`:
   - **Who re-raises**: feasibility itself re-raises the verdict — the
     role that owns the `verdict` field is the only one that edits it,
     consistent with "you write only your own record area" (contract
     v3). Feasibility is woken to do this the same way it wakes on any
     stale-record edge already in the doc (a change upstream of its
     record — here, the human decision — makes its existing record
     stale).
   - **On what evidence**: a human decision already expressed through
     this repo's defined channels (`docs/specs/approvers.md`): a PR
     review Approve or an `APPROVE` comment addressing the condition.
     The record body must cite which PR/comment settled it (path +
     reference), so the resolution is traceable, not asserted.
   - **Where the narrative lives**: the condition text (what was
     conditional, what settled it, and the citation) lives in the
     record body only. The `verdict` field itself is rewritten to the
     literal string `go` — nothing appended, nothing parenthesized —
     so the existing exact-match check in `wakes.py` wakes coding
     without needing to parse free text.
2. Add a one-line comment in `wakes.py` next to the feasibility
   `verdict == "go"` check pointing at the new doc section as the
   source for why non-exact strings are refused and where the
   resolution path is defined.
3. Read through both edits once for internal consistency with the
   rest of `docs/specs/wake-routing.md` (terminology, table style) —
   no test suite covers doc prose, so this is a manual read, not an
   automated check.

## Out of scope

- Any change to the external feasibility rulebook.
- New machine-judged routing rows in `_rows()` (the resolution stays a
  human/role act producing a normal record commit; the existing
  exact-match wake already fires on it).
- Automating the re-raise itself (mirrors the existing human-only
  edges' explicit "never automated" stance).

## How we'll know it worked (test plan)

- Manual read-through: the new section names a role, an evidence
  source already defined elsewhere in this repo, and a field-vs-body
  rule, with no new undefined terms.
- Existing `test_gates.py` `t_wake_*` cases and `test_spawn.py` pass
  unmodified (no logic touched) — run once as confirmation, not as a
  new obligation.
- Re-reading `roles/feasibility.json`'s enum against the new section
  confirms the field-vs-body rule doesn't require widening the enum.
