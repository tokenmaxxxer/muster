---
kind: scout-brief
date: 2026-08-04
subject: issue-266
role: execution-observation
phase: 1
---

# Scout brief — what strong audits of this deliverable-class check

Deliverable class: an **evidence-only post-merge audit** of one merged change
(PR #267) — not a re-implementation, not a re-run. Sweep angles were aimed at
the survey's gaps G1-G5, not at the issue text.

## Category must-bes (what strong hits assume)

- **Deviation from an approved plan is not itself the finding — undocumented
  deviation is.** Change-management audit practice books a deviation as a
  finding when it cannot be shown as controlled and traceable; documented-at-
  execution-time deviations are the expected artifact of a working process
  (Wolters Kluwer, Scrut/ISO 27001 A.8.32 & SOC 2 CC8.1). So an audit checks
  *the deviation record's completeness and intent-preservation*, never the
  bare fact that the plan changed.
- **Inspection-only verification has a stated ceiling, and honest audits state
  it.** Recent agentic-repair work makes the split explicit: "the auditor
  never executes code; verification is performed solely by source inspection,"
  with execution evidence a *separate* artifact, "an integration smoke test
  rather than a functional correctness guarantee" (EviACT, arXiv 2605.27238).
  A red→green claim read from artifacts is auditable for *internal
  consistency and construction*, not for having-actually-passed.
- **Post-merge test relevance is transition-based.** A failure only counts if
  the test *transitioned* — pre-existing breakage is not this change's
  (Aviator, pre/post-merge merge-queue practice). Directly licenses treating
  the 53 pre-existing sandbox ERRORs as out of the change's account.
- **Blameless classification asks the guardrail question first.** "A system gap
  occurs when nobody owned a control, so the guardrail was never built"; the
  useful question about a human error is what made it possible/unrecoverable
  (sph.sh; ilovedevops). A bypass that a control never inspected is booked as
  a control gap with an action item, not as an author's carelessness.
- **Unregister-before-cleanup-finished is a recognized false-death family.**
  Graceful-shutdown guidance pairs "stop advertising ready" with "the process
  is still doing real work" precisely because conflating them misreports a
  draining instance as dead (expressjs healthcheck/graceful-shutdown, godaddy
  /terminus). The observed change sits in a known category, not novel ground.

## Performance axes the strong hits compete on

1. **Traceability** — every claim tied to a named artifact and revision.
2. **Scope discipline** — the audit judges *this* change's account only
   (transition-based relevance), and does not re-open settled ones.
3. **Actionability of findings** — a finding names the control to change, not
   the person who missed it.

## Adopt / skip

- **Adopt**: the auditor-never-executes split — state the inspection ceiling
  explicitly in the record for the red→green claim, and judge construction
  (does the test's arrange actually build the state the issue named?) rather
  than asserting the run happened.
- **Adopt**: guardrail-first classification for the `Closes #266` escape —
  ask what the control inspects before asking what the author typed.
- **Skip**: the Kubernetes liveness/readiness probe-tuning material. Same
  failure family, wrong segment — it prescribes *how to build* a detector,
  and this deliverable audits an already-merged predicate change. Adopting its
  checklist would drift into re-designing the fix, which this role may not do.

## Gap line (field must-bes vs. this repo's current state)

Already met by the observed artifacts: deviation documentation exists and is
traceable (`docs/issue-266/reports/implementation.md:98-141`), and pre-existing
failures were separated by stash-out (record's Verification run). **Missing /
untested**: (a) no artifact states the inspection ceiling for the red→green
claim — the record asserts the run; nothing constrains what a *reader* may
conclude from it; (b) the closing-keyword escape has no owner — the gate
inspects the PR body only (`docs/handbooks/operations.md:662-666`) and no
artifact books the commit-message vector. Those two gaps are what my plan's
checks aim at; the rest of the field's must-bes are already satisfied and get
confirmatory, not investigative, treatment.

## Segment fit / method

Segment fit: change-control and blameless-postmortem practice is the right
segment (single merged change, evidence-only, no re-execution); SRE probe
tuning is not. Pass used **1 stage** of the 5-stage budget — one parallel
sweep of 4 angles (4 concurrent `WebSearch` calls in a single turn, genuine
parallel mode, no fallback), then stopped at the saturation judge point
because no further round would change a check in the plan.

Sources:
- https://www.wolterskluwer.com/en/expert-insights/mastering-it-change-management-audits-best-practices-for-success
- https://www.scrut.io/post/iso-27001-change-management
- https://arxiv.org/pdf/2605.27238
- https://www.aviator.co/blog/pre-and-post-merge-tests-using-a-merge-queue/
- https://sph.sh/en/posts/blameless-culture-postmortem-thinking/
- https://ilovedevops.substack.com/p/your-postmortems-are-compliance-theater
- https://expressjs.com/en/advanced/healthcheck-graceful-shutdown.html
- https://github.com/godaddy/terminus
