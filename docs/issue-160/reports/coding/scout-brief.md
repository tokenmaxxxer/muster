# Scout brief — role taxonomy (issue-160)

Mode: batched-sequential (4 WebSearch calls in one turn, single round). Stages used: 1 sweep + 1 judge point, no deepening — first round already saturated (each query returned a stable canonical anchor; nothing contested).

## Category must-bes (per domain, from search)
- UX/design-systems: token hierarchy (primitive → semantic → component), a maturity model for adoption — *The Design Tokens Book* (Hamila et al.), Material Design 3 token classes.
- API design: consumer-centric, versioned, schema-first (OpenAPI/JSON Schema), lifecycle governance — *RESTful API Design Patterns and Best Practices* (Jarzyna & Amzani).
- Competitive analysis: structural-forces view (five forces) plus demand-side view (jobs-to-be-done); business-school canon treats these as complementary, not either/or — Porter, *Competitive Strategy* (1980).
- Coding: no fresh search needed — SWEBOK/Code Complete/Clean Code lineage is stable, well-known knowledge; treated as assumption, not a web finding.

## Performance axes chosen
1. Does the domain have a *named* literature/methodology lineage (a real book/course exists), vs. being folk practice.
2. Is the domain's judgment orthogonal to neighboring domains (parallelizable) or does it require another domain's output mid-task (sequential).

## Adopt / skip
- Adopt: anchoring every proposed role to a book/methodology citation (mirrors how the four seed examples were each independently anchored above).
- Skip: chasing exhaustive citations for domains that are common CS/SWE knowledge (coding, testing) — diminishing return, budget better spent on the domains the issue actually contests (feasibility split, ops/reflect placement).

## Segment fit
This is an internal role-system design exercise, not a market product — "exemplars" here are academic/professional domain canons, not competitor products. Scout's job narrows to: does a credible named literature exist for each domain claimed in the map.

## Gap line
Current 9 roles (roles/*.json) already cover: coding, feasibility (bundles 3+ domains), product, ops, qa, review, verify, reflect, ux-design. Missing against the domain map: **API design** has no dedicated role (folded into coding), **competitive/market analysis** has no dedicated role (folded into product's hypothesis work), and **security/threat-modeling** is bundled inside feasibility rather than split out.

Sources:
- https://ismailhamila.design/work/DesignTokensBook.html
- https://m3.material.io/foundations/design-tokens
- https://www.amazon.com/RESTful-Design-Patterns-Best-Practices/dp/1835885284
- https://www.goodreads.com/en/book/show/407999.Competitive_Strategy

## Round 2 (re-scout, PR #161 feedback) — company-wide domain sweep

Trigger: reviewer feedback on PR #161 — domain map was dev-biased, missing nearly all biz/ops and design/content lineages. New decision surfacing: for each newly-listed domain, does a credible book/course canon exist (promote-eligible) or only practitioner-consensus/no-canon (hold-only)?

Mode: batched-sequential (4 WebSearch calls in one turn). Results were mostly noisy (SEO content, not canon confirmation) for biz/ops queries — canon assertions below are stated as **prior knowledge, labeled as assumption** where the search did not independently confirm a title; kept anchors where a specific canonical work did surface (Traction, Data Warehouse Toolkit, Database Reliability Engineering).

Judge point: search confirmed the working hypothesis — biz/ops domains overwhelmingly lack one dominant canonical text (fragmented practitioner-guide landscape: CAC/LTV blog posts, no equivalent of a Porter or a SWEBOK), which is itself evidence for the survey's HOLD-not-PROMOTE judgment on nearly all of them. No further deepening changes a build decision — stopped after round 2.

Sources (round 2, supplementary/weak — see assumption labels in survey):
- https://www.oreilly.com/library/view/startup-cxo/9781119772576/c07.xhtml (unit economics chapter, Startup CXO)
- https://growthmethod.com/growth-marketing-books/ (Traction — Weinberg & Mares)
- https://uxcontent.com/product-localization-for-ux/ (UX-writing/localization overlap)
- https://www.oreilly.com/library/view/database-reliability-engineering/9781491925935 (Database Reliability Engineering)
