---
status: proposed
files:
  - docs/specs/impact-classification.md
  - docs/specs/standing-decisions.md
  - docs/specs/enforcement-boundary.md
  - gates/risk_report.py
  - gates/test_risk_report.py
  - on-the-record/hooks/impact-guard.sh
  - on-the-record/hooks/test_impact_guard.py
  - .claude-plugin/hooks.json
---

# Multi-axis impact classification + standing decisions (issue #511)

Phase 1 proposal only — per role-handoff contract v3 s19, this PR stops
here; phase 2 (the s19 amendment's actual body, the code, the boundary-
table update) opens only on an approvers.md Approve.

## Intent
Replace `gates/risk_report.py`'s low/high binary with a four-axis
structural classification, add an ITIL-standard-change-shaped "standing
decision" registry so routine changes stop consuming individual human
approval, and make the resulting classification a blocking gate on
batch-approval — all reachable zero-install from a plugin-installed
session running against an arbitrary target repo, per issue #511
requirements 1–8.

## Constraints (from the issue, unchanged)
- Every axis must be derived mechanically from structure — never from
  reading prose for intent.
- Each grade in each axis is a machine-checkable objective condition;
  unparseable/undecidable input takes the highest grade (fail-closed).
- Axes are never summed or averaged; the worst reversibility grade alone
  forces individual human approval regardless of the other three axes.
- No classification grade, including a standing-decision match, ever
  exempts an existing verification gate — it only reallocates human
  attention. [[scout-brief]]'s cited failure signal (risky files getting
  *less* review once a risk label is trusted) is the reason this
  constraint is load-bearing, not decorative.
- All of it must fire in a plugin-installed session on a target repo that
  is not this repository — paths anchored to the target's root, nothing
  hardcoded to this marketplace checkout.

## Methodology survey (adopt / reject, with rationale)

**ITIL 4 standard change — adopted, for standing decisions (req. 4).**
A standard change is pre-authorized only because its scope, prerequisites,
and approval model are documented *in advance*, and anything outside that
documented envelope reverts to normal (individually-authorized) change —
never silently treated as standard. That reversion-on-mismatch shape is
exactly what requirement 4 asks for ("out-of-condition automatically
escalates"), so standing decisions are modeled as ITIL standard changes:
a registry of pre-defined change types, each with an objective
in-condition check, each defaulting to escalation on any check failure or
parse error.

**AIAG-VDA FMEA — adopted for axis-scale shape, rejected for composition.**
Adopted: FMEA's discipline of an anchored, machine-legible description per
severity/occurrence grade (never a felt number) is the shape requirement 2
asks for, and is used for all four axes below. Rejected: classic FMEA's
Risk Priority Number (severity times occurrence times detection) is
explicitly superseded inside FMEA's own current lineage (AIAG-VDA's
Action-Priority table) for the precise failure this issue names in
requirement 3 — a low score on one axis can mask a catastrophic score on
another when they're multiplied or averaged together. RPN is the
alternative this proposal rejects, and FMEA's own 2019 handbook revision
is the rejection's citation.

**CVSS v4 — adopted for the composition rule, rejected as the output
shape.** Adopted: v4 resolves a full metric vector via worst-case
equivalency sets, not a weighted sum — the same non-averaging lesson FMEA
converged on from a different field, and the direct basis for the
dominant-axis rule below. Rejected: CVSS's single collapsed 0–10 output
score. Requirement 3 wants the *worst axis* to be independently inspectable
by routing logic (which axis fired matters for who gets pulled in), so the
classifier's output stays a per-axis grade vector, never collapsed to one
number.

**Rejected alternative not drawn from any one methodology: weighted
composite score.** A weighted sum of the four axes (however the weights
are chosen) reintroduces exactly the masking failure both FMEA's RPN
retirement and CVSS v4's Scope-metric retirement independently moved away
from — a severe reversibility grade could be numerically diluted by three
mild grades. Rejected on that basis alone, without needing a separate
citation beyond the two already given.

Full sweep detail, sources, and the review-routing failure-signal citation
for requirement 6: [[scout-brief]].

## What will be done (phase 2, once approved)

### Axes (each: 4 grades, each grade an anchored structural condition)
1. **Blast radius** — DEPENDS-ON edge count reaching the changed paths,
   write_scope overlap with other open proposals (reuse the existing
   `parallel-conflict-methodology` overlap computation rather than a new
   parser — see [[survey]]), and count of roles whose `WRITE_SCOPE`/role
   directive lists a touched path as read. Undecidable (edges/overlap
   uncomputable from the target repo's current state) → highest grade.
2. **Reversibility** — path-class ordering: leaf docs < application code
   < gates/hooks < contract/approval-rule files (`protocol.md`,
   `spawn.py`, `approvers.md`, anything under a hook directory).
   Classification derives from `gates.py`'s existing
   `PROTECTED_DIRS`/`PROTECTED_ROOT_DIRS`/`PROTECTED_ROOT_FILES` ordering
   rather than a new list, extended with one more tier for the
   contract/approval class specifically (those constants currently
   collapse "protected" to one tier; reversibility needs the leaf/code
   split beneath it too).
3. **Propagation** — count of distinct rulebooks/roles that document the
   touched path as within their governance (derived from
   `docs/specs/enforcement-boundary.md`'s own per-mechanism rows plus each
   role's `WRITE_SCOPE`, both already-declared, machine-parseable lists —
   no new authoring surface).
4. **Existing signals** — protected-path membership and changed-line
   count, carried forward from `risk_report.py`'s current logic unchanged.

### Dominant-axis rule
The four grades are never summed or averaged. The classifier's decision is
`max(reversibility_grade, standing_decision_escalation)`, i.e. worst
reversibility alone routes to individual human approval regardless of the
other three axes' grades; the other three axes only affect *how much*
attention a same-reversibility-tier item gets inside the review surface
(ordering, batching eligibility), never whether it needs a human at all.

### Standing decisions (ITIL standard change)
`docs/specs/standing-decisions.md` becomes the pre-defined-change-type
registry: each entry names a change type, its objective in-condition check
(a structural predicate over the write-set, same shape as an axis grade),
and its pre-approval scope. A proposal matching a standing decision's
condition still runs every existing gate — it only skips the *individual*
human-approval requirement, replaced by the standing decision's own
pre-approval record. Any check failure, parse error, or partial match
escalates to normal individual approval; there is no partial-credit
standing-decision match.

### Contract v3 s19 amendment (draft, filed as part of this same doc)
Section 19 does not currently exist in the injected role-handoff contract
text (confirmed in [[survey]]); this proposal introduces it rather than
patching an existing body:
> **s19 — Impact classification and standing decisions.** A proposal's
> impact is classified on four independent axes (blast radius,
> reversibility, propagation, existing signals), each graded against an
> anchored, machine-checkable scale; axes are never summed or averaged.
> The worst reversibility grade alone determines whether the proposal
> requires individual human approval; classification never substitutes
> for or exempts any verification gate, it only allocates attention. A
> proposal whose write-set matches a registered standing decision
> (`docs/specs/standing-decisions.md`) skips individual approval only
> while every condition of that entry holds; any mismatch, parse failure,
> or undecidable input reverts to individual approval. High-impact
> proposals (worst-reversibility grade above the registry's batch
> threshold) cannot be included in a batch approval action.

### risk_report wiring (requirement 5)
A new zero-install `PreToolUse` hook, `impact-guard.sh` (same
`_checkout_resolve()`-style split as `decision-queue-stopgate.sh` — see
[[survey]] — between the on-the-record checkout and the target repo it is
classifying), intercepts the batch-approval act and denies it when any
proposal in the batch classifies above the threshold, naming which
proposal and axis. This is the delivery that moves `risk_report.py` out of
`n/a (infrastructure)` in `docs/specs/enforcement-boundary.md`'s table
into `contract` — that table update ships in the same PR
(`gates/test_boundary.py` fails the build otherwise, per [[survey]]).

## Out of scope
- Detecting drift in already-existing (already-merged) standing-decision
  matches — this proposal classifies proposals at review time only, not a
  board-wide sweep (that pattern, if wanted later, follows issue #464's
  orchestrator-loop precedent, not this issue).
- Any change to the two-account/single-account approval-comment mechanism
  itself; classification changes *whether* an approval act is required,
  never *how* one is authenticated.
- A UI/report redesign beyond what's needed to show four grades instead of
  one; `risk_report.report()`'s Markdown-table shape is extended, not
  rebuilt.

## Verification (phase 2)
- `gates/test_risk_report.py` extended with one fixture per axis grade
  boundary (four axes times four grades) plus the dominant-axis
  non-averaging case (one severe axis, three mild axes → still routes to
  individual approval).
- `on-the-record/hooks/test_impact_guard.py` (new): batch containing one
  above-threshold proposal is denied; a batch of only standing-decision
  matches is allowed; a batch run against a synthetic non-marketplace
  target-repo fixture proves requirement 7 (path anchoring holds with no
  hardcoded marketplace-repo assumption).
- `gates/test_boundary.py` passes with `risk_report.py`'s row updated.
- A warrant-hunter dispatch (stance 4, "the write set cannot carry this
  work") runs after this proposal per the standing warrant directive.
