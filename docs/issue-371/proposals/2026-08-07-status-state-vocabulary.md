---
status: proposed
files:
  - gates/status_vocabulary.py
  - tests/test_status_vocabulary.py
  - spawn.py
  - docs/handbooks/on-the-record.md
  - docs/decisions/2026-08-07-status-state-vocabulary.md
---

## Request

The operator's status report (`spawn.status()`) showed 11/15 requirements as
"delivered" using only the role's own self-asserted `loop_state`/`verdict`
frontmatter fields. None had actually merged; the operator only learned this
by asking an unrelated question. The report was accurate item-by-item and
wrong as a whole because nothing distinguishes "delivered" from "delivered
but blocked at the merge gate" from "merged but never independently
re-checked" from "rejected and being reworked." Requested: a state vocabulary
for these distinctions, computed from merge status / check status / whether
acceptance was independently re-run — not self-asserted — and an honest
statement of what a mechanical check on "scope weakening" (item 3) can and
cannot catch.

## Constraints

- `spawn.status()` must stay read-only (spawn.py:1126-1128 — "상태는
  에이전트의 것이다"): this proposal adds a second, derived field alongside
  the existing asserted `loop_state`/`verdict` line; it must not rewrite or
  patch the role's own record file.
- Derivation must reuse `gh`-backed helpers already in this repo
  (`spawn._pr_for_branch`, `closure_sweep._issue_view`,
  `closure_sweep._pr_view_state_body`, `pr_reference._CLOSES_REF`) rather
  than inventing a second way to query GitHub state.
- Per #310, acceptance must be an artifact that runs — a pytest test module,
  not prose.
- Per the issue's own acceptance section: where the honest ceiling on
  mechanical checking is weaker than a real semantic check (item 3), say
  exactly what it does not catch, rather than presenting a shape check as if
  it verified truth.
- Must not widen into #320 (PR-vs-effect prose) or #318 (approval-request
  content shape) — this proposal touches only the *status report's* state
  field, not those other artifacts' shapes.

## Rationale

Considered building this as a **general "requirement completeness" engine**
that also judges whether a proposal satisfies its issue (fully solving item 3
as a semantic check). Rejected: the issue itself calls this "the hardest to
check... a judgment," and asserting a semantic pass/fail here would repeat the
exact failure this issue reports — a green-looking check standing in for a
question nobody actually verified. Instead this proposal computes only the
mechanically groundable states (item 1+2, merge/check/re-run derived) and, for
item 3, adds one narrow, explicitly-labeled structural heuristic (does the
proposal's frozen write set touch any non-`docs/` path, when the parent
issue's own title/body implies behavior rather than documentation) — flagged
to the operator as a heuristic with a stated blind spot, never as a verified
"scope not weakened."

Considered computing "independently re-run" from CI check status
(`gh pr checks`) alone. Rejected as the sole signal: this repo has no CI
wired for most role branches (`gates/ci.py` checks the local working tree,
not remote CI), so a CI-only signal would report "unverified" for nearly
everything, including cases where a `review` role record already exists with
`Present` verdicts (ledger/collect.py's own re-check proxy). Using the
review-record proxy first, with CI checks as an additional positive signal
when present, avoids that false-negative flood while still being derived, not
asserted.

## What will be done

1. `gates/status_vocabulary.py` — new module, `compute(root, subject, role) -> dict`:
   - Reads issue number from `subject` (`issue-<n>`), issue state via
     `closure_sweep._issue_view`, PR number via `spawn._pr_for_branch`,
     PR state/body via `closure_sweep._pr_view_state_body`, Closes-ref
     presence via `closure_sweep._refs_issue`.
   - Emits one of: `not-started` (no record), `phase1-proposed` (record
     exists, no PR with Closes-ref found), `rejected-reworking` (PR with
     Closes-ref was CLOSED unmerged, and a newer commit/record exists after
     that close), `delivered-blocked` (PR OPEN with Closes-ref — carries
     `blocked_on: "merge gate — PR #<n> open"`), `merged-unverified` (PR
     MERGED with Closes-ref, no `review` role record for the subject shows a
     `Present`-only verdict set post-merge), `merged-verified` (PR MERGED +
     review record with no Absent/Incorrect verdicts, read via
     `ledger.collect.parse`).
   - Every non-`not-started` result also carries `problem_still_occurs:
     bool | None` — `True` unless state is `merged-verified`, `None` when it
     cannot be determined (e.g. `gh` call failed) — because "does the
     operator's problem still occur" is the one fact #371 item 4 says must
     never be silently omitted.
   - Network/`gh` failures produce `state: "unknown"` with the failure
     reason attached — never silently reported as passing (matches the
     fail-closed convention already used in `spawn.gate_report`,
     spawn.py:1195-1198).
   - `item3_heuristic(root, subject, role) -> str | None` — a **separate,
     clearly-labeled** function: `None` when the proposal's write set has a
     non-`docs/` path, otherwise a warning string naming the proposal file
     and stating plainly: "structural heuristic only — write set is
     docs-only; this does NOT verify the proposal's behavior satisfies the
     issue, only that it touches code at all. A docs-only write set that
     legitimately fixes a docs-shaped issue will also trigger this — read
     the proposal's own Rationale before treating this as a defect." Never
     merged into the main state enum — surfaced as an independent flag so it
     can never be mistaken for a verified state.
2. `spawn.status()` (spawn.py:1123-1161) — for each role with a record, call
   `status_vocabulary.compute()` and append a line: `  derived: {state}
   (problem still occurs: {problem_still_occurs})` plus the `blocked_on` /
   `item3_heuristic` text when present. Kept as an additional line, not a
   replacement of the existing `loop_state`/`verdict` line — the asserted
   value stays visible so a mismatch between asserted and derived is itself
   visible to the operator.
3. `tests/test_status_vocabulary.py` — unit tests against `compute()`'s pure
   classification logic (state strings in, state out — same style as
   `closure_sweep.classify()`'s existing tests), covering all six states plus
   the `unknown`/fail-closed path and the `item3_heuristic` docs-only trigger.
   This is the runnable acceptance artifact per #310.
4. `docs/handbooks/on-the-record.md` — document the six-value vocabulary next
   to the existing `loop_state` row (docs/handbooks/on-the-record.md:69,94).
5. `docs/decisions/2026-08-07-status-state-vocabulary.md` — record why the
   vocabulary has these six values and why item 3 stays a labeled heuristic
   rather than a semantic check, so the honest-ceiling statement survives
   independent of this PR's description.

## Out of scope

- Building any semantic "does this proposal satisfy less than its issue"
  detector — the issue itself says this is a judgment call; a mechanical
  claim of solving it would repeat #371's own failure mode. Documented
  explicitly as unresolved, not silently dropped.
- Wiring a `Stop` hook that inspects/blocks orchestrator report text (issue
  #298's mechanism) — no `Stop` hook exists in `on-the-record/hooks/hooks.json`
  today; adding one is a separate, larger change outside this write set.
- Rewriting or migrating the existing `loop_state`/`verdict` asserted fields —
  this proposal adds a derived field beside them, per the read-only
  constraint on `status()`.
- #320 (PR-vs-effect prose) and #318 (approval-request content shape) — not
  touched.
- Retroactively re-scoring past reports (e.g. the 15-requirement table the
  operator saw) — this proposal changes what `status()` prints going
  forward.

## How you'll know it worked

`python3 -m pytest tests/test_status_vocabulary.py -q` passes and exercises
all six states plus the fail-closed `unknown` path and the `item3_heuristic`
trigger, without any network call (pure classification functions fed
synthetic state strings, same pattern as `closure_sweep.classify`'s tests).
Running `spawn.py status` in this repo shows a `derived:` line per role
record distinct from its `loop_state`/`verdict` line, and reading
`docs/decisions/2026-08-07-status-state-vocabulary.md` states in one place
what the item-3 heuristic does not catch.
