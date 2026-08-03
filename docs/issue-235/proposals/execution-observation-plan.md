---
subject: issue-235
role: execution-observation
observed_role: implementation
observed_pr: 237
phase: 1
---

# Observation plan — issue #235, PR #237 (`implementation` role)

## Verdict levels this plan will render (declared before any evidence)

Phase 2 will render all three levels of the role-handoff contract's
verdict, each against the evidence named beside it. No level is rendered
here, and no provisional judgment of PR #237 appears anywhere in this
document — this section fixes *what will be judged and from what*, which
is the whole of phase 1's commitment.

1. **Outcome** — did `611c0c0` + `e7a13db` land what issue #235 asked.
   Evidence: issue #235's 요구사항 1-5 text, one item at a time, against
   `git show 611c0c0 -- spawn.py`, `git show 611c0c0 -- test_spawn.py`,
   and `e7a13db:docs/issue-235/reports/implementation.md`.
2. **Trajectory** — was the observed role's phase-1 → phase-2 path sound.
   Evidence: `bf5f71f`'s tree (did phase 1 confine itself to the two
   phase-1 homes and touch no code), the issue comment whose entire body
   is `APPROVE issue-235/implementation` with its author, association and
   timestamp from `gh api .../issues/235/comments`, `611c0c0`'s author
   date, `docs/specs/approvers.md`, and the observed proposal's own
   Scout skip record cited at
   `docs/issue-235/proposals/refusal-classifier-corroboration.md:62-64`.
3. **Step** — which specific artifact, if any, is deficient. Evidence:
   whichever of the checks below does not close, carried into the record
   in the four-part blameless shape (impact, timeline, root cause, action
   item). If no check leaves a residue, the level is stated as
   "no deficient step" rather than omitted; any level that turns out not
   to apply is written as "not applicable, because X".

## Request

Issue #235's `## 실행 계획` step 2 is `execution-observation`, and the
invoking prompt for this session fixes three judgment items against PR
#237: (a) whether the four regression cases required by 요구사항 4 are
forced to diverge on the pre-change blob; (b) whether the
`permission_denials` buffer-then-flush gate carries both "a zero-denials
session emits nothing" and "a spurious match does not suppress a genuine
fallback"; (c) whether the `^` anchor plus hook-stem preference leaves
anything out relative to the four-point prescription from the local
adversarial verification — specifically whether any input exists for
which session-end reporting is *narrower* than pre-change, and whether
per-layer once-only dedup can let one spurious candidate mask a genuine
event in that layer. The prompt also fixes the disposition: judge, do not
fix.

## Constraints

- **No re-execution.** This role may not run `pytest`, invoke `spawn.py`,
  or otherwise re-perform the observed role's task. Admissible evidence is
  the commits' diff text, the pre-change blobs those diffs landed on, the
  observed role's own record, the issue/PR text and comments, and
  externally-owned files read directly. Working-tree copies of `spawn.py`
  and `test_spawn.py` are not evidence of what the observed role did —
  every code citation addresses a blob through its SHA.
- **No edits outside this role's own paths.** Nothing under `spawn.py`,
  `test_spawn.py`, `docs/issue-235/proposals/refusal-classifier-
  corroboration.md`, or `docs/issue-235/reports/implementation*` is
  written or edited, in either phase.
- **No issue filing.** Under contract v3 issues are user-authored only.
  A confirmed deficiency returns as a finding in this role's record on
  this role's PR; the human judges it there.
- **Citation adjacency.** Every verdict-bearing sentence in the phase-2
  record names its source (SHA, `file:line`, or comment URL) adjacent to
  the verdict, and the independence statement precedes all verdict
  language in the document.
- **Phase gating.** The record
  `docs/issue-235/reports/execution-observation.md` is phase-2 output. It
  is not written until an approver listed in `docs/specs/approvers.md`
  posts a PR "Approve" review on this branch's PR, or — single-account
  mode — an issue comment on #235 whose entire body is exactly
  `APPROVE issue-235/execution-observation`.

## Rationale

**Chosen approach: static, per-case derivation on the two blobs.** The
scout brief's first must-be is that test discrimination must be derived
rather than asserted — a suite can pass while the patch violates the
intended semantics, so the audit unit is whether each case *forces* a
divergence, not whether someone reports it did
(`docs/issue-235/reports/execution-observation/scout-brief.md`, Category
must-bes). Since re-execution is prohibited for this role, the derivation
runs on the text of `611c0c0:test_spawn.py` against `bf5f71f:spawn.py`,
one case at a time. This is also the only method that produces the
citation the record requires: a test-run result cites a run, a derivation
cites two blob line ranges.

**Alternative 1 — relay the observed role's own verification run.**
Rejected: `e7a13db:docs/issue-235/reports/implementation.md:151-161`
reports all four failing pre-fix, but relaying that report makes this
role's verdict a restatement of the observed role's claim, which is the
one thing independent observation exists to avoid.

**Alternative 2 — re-run the four tests against the pre-change blob.**
Rejected: this is re-execution of the observed role's task, prohibited
outright for this role, and it would produce evidence this record is not
allowed to cite.

**Alternative 3 — judge only 요구사항 1-4 and skip the coverage-delta
sweep.** Rejected: the scout brief's gap line identifies exactly this —
issue #235's five 요구사항 contain no false-negative-regression criterion,
while the field's must-be is that a precision tuning is audited for what
it stopped reporting. Checking only the issue's own list would inherit
that blind spot; the observed role's own Hunt finding 1
(`e7a13db:docs/issue-235/reports/implementation.md:94-115`) is evidence
the shape exists and is worth an independent sweep rather than an
acceptance of the finding as written.

## What will be done (phase 2)

Five checks, each closing into `closed_checks` with its `code_sha`:

1. **`regression-discrimination-static-derivation`** — for each of the
   four cases added by `611c0c0:test_spawn.py`, map it to the 요구사항 4
   item it claims (i)-(iv), then trace its exact input through
   `bf5f71f:spawn.py`'s `_classify_refusal_text` / `_GATE_HOOK_RE` /
   `_GATE_DENY_RE` / event-emission sites and state the concrete
   divergence from the asserted expectation, citing both line ranges. A
   case for which no divergence can be derived from the text is reported
   as such rather than assumed to discriminate.
2. **`denials-gate-property-trace`** — trace the post-change buffer and
   flush path in `611c0c0:spawn.py` for two properties separately: P1, a
   zero-`permission_denials` session emits no refusal event on any path
   including the `unclassified-refusal` fallback; P2, a spurious buffered
   candidate cannot consume state (dedup key, `refusals_seen`, or the
   "did anything flush" condition) that changes what a genuine denial in
   the same session produces. Each property is answered from the control
   flow, not from the one fixture that exercises it.
3. **`coverage-delta-sweep`** — enumerate input shapes for which
   `bf5f71f:spawn.py` emits a refusal event and `611c0c0:spawn.py` emits
   none, with the JSONL line content each shape requires. Includes but is
   not limited to the terminal-`result`-line-absent shape the observed
   record already names; also covers a malformed terminal line, a missing
   `permission_denials` key, and a non-list value.
4. **`dedup-masking-trace`** — extract the dedup key `611c0c0:spawn.py`
   actually computes and enumerate input shapes in which two distinct
   underlying events collapse to one emission, specifically whether a
   spurious candidate can claim a layer's key ahead of a genuine one.
5. **`prescription-coverage-map`** — locate the four-point local
   adversarial prescription (anchor / unconditional fallback / dedup
   safety / 153-fixture corpus) in admissible in-repo sources and map
   each point onto `611c0c0:spawn.py`, or record that a point has no
   admissible source. A prescription this role cannot cite is not used as
   evidence; if it cannot be located, that is stated in the record and
   checks 3 and 4 carry the load its points 2 and 3 would have carried.
   Phase-1 research already searched for it and found only a three-point
   in-repo enumeration
   (`docs/issue-235/reports/execution-observation/research-evidence.md`),
   so this check is expected to run as the second branch: map the three
   admissible points and record the other three labels as unsourced.

Trajectory evidence (the approval comment's timestamp against `611c0c0`'s
author date, `bf5f71f`'s file set, the approver's listing in
`docs/specs/approvers.md`) is gathered alongside and reported under the
trajectory level.

## Out of scope

- Any change to `spawn.py` or `test_spawn.py`. This role does not fix.
- Filing a follow-up issue for the observed role's open Hunt finding 1 —
  issues are user-authored; the finding is reported in this role's record
  for the human to judge.
- Re-judging issue #232 / PR #233. `a670098` is the baseline this fix
  landed on, read as context, not re-reviewed.
- The phase-2 record itself, which is written only after approval.

## How you'll know it worked

- `docs/issue-235/reports/execution-observation.md` exists on this
  branch, committed, with the independence statement preceding every
  verdict-bearing sentence, and all three levels — outcome, trajectory,
  step — addressed explicitly, including any level written as
  "not applicable, because X".
- Each of the five checks above appears in `closed_checks` with
  `code_sha: 611c0c0`, and each of the invoking prompt's three judgment
  items (a), (b), (c) is answered by a named check.
- Every verdict-bearing sentence carries an adjacent SHA, `file:line`, or
  comment URL, and no code claim cites a working-tree path.
- Any deficiency is recorded in the four-part blameless shape and nothing
  in the observed role's write surfaces was modified.
