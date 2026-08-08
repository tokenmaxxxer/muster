---
name: standing-decisions
description: >
  Contract v3 s19 amendment (issue #511): standing decisions as ITIL
  standard-change-shaped pre-approvals, plus the registry format that
  `gates/risk_report.py:batch_blocked()` and
  `on-the-record/hooks/impact-guard.sh` read.
---

# Standing decisions (contract v3 s19 amendment)

## Amendment text

> **s19 amendment — impact classification and standing decisions
> (issue #511).** A proposal's impact is classified on four independent
> axes (blast radius, reversibility, propagation, existing signals), each
> graded against an anchored, machine-checkable scale
> (`docs/specs/impact-classification.md`); axes are never summed or
> averaged. The worst reversibility grade alone determines whether the
> proposal requires individual human approval; classification never
> substitutes for or exempts any verification gate — it only allocates
> attention. A proposal whose write-set matches a registered standing
> decision below skips individual approval only while every condition of
> that entry holds; any mismatch, parse failure, or undecidable input
> reverts to individual approval. A high-impact proposal (worst
> reversibility grade at `AXIS_MAX`) cannot be included in a batch
> approval action.

This text amends the phase-gating s19 already stated in `protocol.md`
("Work the PR in TWO PHASES") — it does not replace it. That s19 governs
*when* phase 2 opens; this amendment governs *what a human is shown and
asked to individually approve* once it has. Both are the same section
because both are the shape of the human-approval gate; neither exempts
the other.

## Registry format

Each entry is a pre-defined change type in the ITIL 4 standard-change
sense: pre-authorized only because its scope and objective in-condition
check are documented in advance. Anything failing the check reverts to
normal individually-approved change — never silently treated as
standard.

```
- id: <slug>
  condition: <structural predicate over the write-set, same shape as an
              axis grade — e.g. "all paths under docs/issue-*/reports/**
              with reversibility_grade == 1">
  scope: <what pre-approval covers — batch-approval eligibility only,
          never a skipped gate>
```

No entries are registered yet. This proposal ships the registry format
and its escalation default; populating it with a first real standing
decision is a follow-up, not part of issue #511's acceptance (issue #511
requirement 6: no grade exempts any verification gate — an empty
registry is the fail-closed default: every proposal starts as normal
individual change until a matching entry says otherwise).

## Escalation default

`gates/risk_report.py` has no standing-decision matcher yet — the
registry above is empty, so every write-set falls through to the
dominant-axis rule in `docs/specs/impact-classification.md` unchanged.
Adding a matcher is scoped to `batch_blocked()`'s existing fail-closed
contract: a match that cannot be verified (parse failure, missing
condition field) must return the same result as no match at all.
