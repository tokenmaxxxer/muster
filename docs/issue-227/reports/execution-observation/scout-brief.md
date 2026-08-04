---
kind: scout-brief
subject: issue-227
date: 2026-08-04
phase: 1
---

# Scout brief — what a strong independent observation of a policy-doc change checks

Deliverable class scouted: **an independent audit/observation record of a
documentation-and-policy change** (not a product). Aimed at the four unknowns
the survey left open, in that order.

**Segment fit**: the field's closest match is change-management audit +
docs-as-code governance + blameless post-incident review — all three are
"someone other than the author judges an executed change from its evidence,"
which is this role's exact shape.

**Category must-bes (what strong exemplars assume)**

1. The judging party is independent of the requester/author, and that
   independence is an explicit precondition, not a courtesy
   (hightable.io ISO 27001 A.8.32).
2. The audit record states procedures performed, evidence collected, and
   conclusions reached — evidence-first, so a reader can re-verify without
   re-doing the work (scrut.io).
3. Timeline = chronological events with timestamps **and sources, no
   interpretation** (mdkit, incident.io).
4. Root cause is split into primary cause vs contributing factors, each
   evidence-backed; action items carry owners (Atlassian, Google SRE via
   Pluralsight).
5. Duplicated policy text across several documents is itself the named risk
   class — SSOT/docs-as-code treats un-synchronized copies as the defect to
   look for (Docsie, Paligo, Kong).
6. A written policy is only a control once it is enforced at the point of
   action; auditors specifically check whether documented policy is
   *reflected in day-to-day operations* (nhimg.org, madsecurity, Drata).

**Performance axes the field competes on**: (a) evidence traceability per
claim; (b) drift detection across duplicated copies; (c) documented-vs-enforced
gap named explicitly rather than assumed closed.

**GAP LINE** — must-bes 1–4 are already met by this role's own directive and
this repo's prior execution-observation records (independence statement,
citation-per-verdict, three-level verdict, four-part finding shape), so they
need no new invention. Must-bes **5 and 6 are the gap**: nothing in this
repo's observation practice yet names duplicate-copy drift or the
documented-but-unenforced gap as things an observer must check — and PR #254
lands the same rule into three files while leaving two adjacent canon surfaces
(`protocol.md`, `README.md`) untouched, and explicitly defers the enforcing
code out of tree. The observation plan therefore aims at 5 and 6.

**Adopt**: (i) drift check across *every* surface carrying the rule, including
ones the change did not touch; (ii) the "is the policy reflected in actual
operations" check — instantiated here as measuring the live #224/#245/#246
relay comment shapes against the landed recipe.

**Skip**: ISO/CMMC-style control-maturity scoring and any policy-as-code
remediation proposal — this observation judges one executed change, and the
enforcing code is explicitly out of the observed proposal's scope; grading the
repo's control maturity would be re-scoping, not observing.

**Pass shape**: 2 stages (1 sweep of 4 angles + 1 judge point), **parallel**
mode — four concurrent `WebSearch` calls in a single turn. Stopped at
saturation: another round would not change any check in the plan.

Sources:
- https://hightable.io/iso-27001-annex-a-8-32-audit-checklist/
- https://www.scrut.io/post/audit-evidence-documentation-reporting
- https://mdkit.io/blog/post-mortem-template-guide
- https://incident.io/blog/sre-incident-postmortem-best-practices
- https://www.atlassian.com/incident-management/handbook/postmortems
- https://www.pluralsight.com/resources/blog/tech-operations/how-conduct-blameless-postmortems-incident
- https://www.docsie.io/blog/glossary/single-source-of-truth-ssot/
- https://paligo.net/blog/content-reuse/what-is-single-source-of-truth-ssot/
- https://konghq.com/blog/learning-center/what-is-docs-as-code
- https://nhimg.org/glossary/policy-enforcement-in-cicd/
- https://madsecurity.com/madsecurity-blog/cmmc-compliance-written-policies-documentation-technical-controls
- https://drata.com/learn/compliance-as-code/policy-as-code
