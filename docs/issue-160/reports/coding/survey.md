# Current-state survey — role taxonomy (issue-160)

## Method
Read all 9 role definitions (`roles/*.json` on main) verbatim. Cross-checked against [[scout-brief]] for external anchors. Unit of analysis: "role" = one `roles/<name>.json` with its `decides`/`use_when`/`produces`/`write_scope`.

## 1. Domain map — professional domains at "one book/one course" granularity

Format: domain — representative literature/methodology lineage.

| # | Domain | Anchor (book/course/methodology) |
|---|---|---|
| 1 | Requirements/product discovery | Cagan *Inspired*; Christensen jobs-to-be-done |
| 2 | Competitive/market analysis | Porter *Competitive Strategy* (five forces); JTBD landscape mapping |
| 3 | UX research & interaction design | Nielsen Norman heuristics; *About Face* (Cooper) |
| 4 | UX engineering (design systems/tokens) | *The Design Tokens Book*; Material Design 3 token classes; Atomic Design |
| 5 | API/interface design | *RESTful API Design Patterns and Best Practices*; OpenAPI/JSON Schema governance |
| 6 | Software architecture/system design | *Software Architecture in Practice* (Bass/Clements/Kazman); DDD (Evans) |
| 7 | Coding/implementation | *Code Complete* (McConnell); *Clean Code* (Martin); SWEBOK |
| 8 | Test/QA methodology | *Lessons Learned in Software Testing*; ISTQB syllabus |
| 9 | Security/threat modeling | Shostack *Threat Modeling*; STRIDE |
| 10 | Technical feasibility/tech selection | build-vs-buy, PoC-driven evaluation (no single canonical text; practitioner consensus) |
| 11 | Legal/regulatory/compliance | no single canonical text; jurisdiction-specific practitioner + regulator guidance |
| 12 | Code review/audit | Google engineering practices (code review docs); implementation-audit style claim-by-claim grading |
| 13 | Independent verification/adversarial QA | root-cause/incident-investigation methodology; adversarial red-team practice |
| 14 | Release engineering/DevOps rollout | *The Site Reliability Engineering Workbook* (canary/staged rollout) |
| 15 | Incident response/postmortem | Google SRE *postmortem culture* (blameless postmortem) |
| 16 | Retrospective/organizational learning | Kerth *Project Retrospectives*; blameless retro practice |
| 17 | Data/analytics engineering | (no dedicated role today; not contested by this issue's 4 seed examples, noted for completeness) |
| 18 | Technical writing/documentation | (same — noted for completeness, not scoped for this proposal) |

Rows 1-16 are the domains contested by or adjacent to the current 9 roles; rows 17-18 are out-of-map completeness notes, not migration candidates (no current role touches them and the issue doesn't ask for new ones there — flagging, not proposing).

## 2. Mapping current 9 roles onto the domain map

| Role (`roles/*.json`) | `decides` | Mapping |
|---|---|---|
| `ux-design` | 화면·플로우 구현 | **(a) 1:1** → domain 3 (UX research & interaction design). Domain 4 (UX engineering/tokens) is NOT covered — `produces` is "screen/flow/wireframe spec", no token/system-rule artifact. Named as a seed example in the issue but currently absent from the role's actual scope. |
| `coding` | 승인된 범위 → 동작 코드 | **(a) 1:1-ish** → domain 7 (coding/implementation), but `produces` folds in domain 5 (API/interface design) implicitly — no API-design artifact or pattern-anchor is named in the role, it just falls out of whatever `src/**` needs. |
| `feasibility` | 만들 수 있는가·만들어도 되는가 | **(b) bundled — split candidate.** One role covers domain 9 (security/threat model), domain 10 (tech feasibility/build-vs-buy), and domain 11 (legal/regulatory) — three domains with distinct literatures and distinct question-shapes ("does it work" vs "may we ship it" vs "is it legal"), currently one `verdict`. |
| `product` | 무엇을 만들지 | **(b) bundled — partial.** Covers domain 1 (requirements/discovery) fully. Domain 2 (competitive/market analysis) is named as a seed example in the issue but has no separate artifact in `product.json` — `produces` is "hypothesis, 스펙, product record", nothing named for competitor/market landscape. |
| `qa` | 실행 시 실제 동작 | **(c) method, not domain.** `decides`/`use_when` describe an epistemic method (direct execution observation) applicable across domains 7, 5, 6 — not itself a professional literature. |
| `review` | 산출물 vs 명세 일치 | **(c) method, not domain.** Claim-by-claim audit method (domain 12's audit style), appliable to any produced artifact — not a domain with its own body of practice beyond "how to audit." |
| `verify` | 결함 실재 — 독립 재현 | **(c) method, not domain.** Adversarial reproduction method (domain 13), same shape regardless of which domain produced the disputed artifact. |
| `ops` | 배포 가능·계속 동작 | **(a) 1:1, bundled internally.** Domain 14 (release/rollout) and domain 15 (incident/postmortem) share one role — arguably a natural pair (SRE workbook treats both under one discipline) but they are two named domains (14, 15) collapsed to one role, closer to (b) than a clean 1:1. |
| `reflect` | 이슈 역사가 무엇을 가르치나 | **(a) 1:1** → domain 16 (retrospective/organizational learning). Advisory-only, no write_scope — consistent with the domain's practitioner literature (retros produce recommendations, not artifacts). |

| Domain in map with no role | Status |
|---|---|
| Domain 4 (UX engineering: tokens/programmatic design rules) | **(d) domain, no role** — `ux-design` produces screens/flows, not the token/rule layer the issue names explicitly. |
| Domain 5 (API/interface design) | **(d) domain, no role** — silently subsumed into `coding`, no named artifact or pattern-anchor. |
| Domain 2 (competitive/market analysis) | **(d) domain, no role** — silently subsumed into `product`'s hypothesis work, no named artifact. |
| Domain 9 (security/threat modeling) | **(d) domain effectively unnamed** — exists only as one probe inside `feasibility`'s "4-probe" verdict, no independent literature-anchored artifact. |

## Summary counts
- (a) 1:1 fit: `ux-design`* , `coding`*, `reflect` (3, *with caveats noted above)
- (b) bundled, split candidates: `feasibility` (3 domains → 1 verdict), `product` (partial — market analysis unnamed), `ops` (2 domains → 1 role, weaker split case)
- (c) method not domain: `qa`, `review`, `verify` (3)
- (d) domain, no role: UX engineering/tokens, API design, competitive/market analysis, security/threat-model-as-independent-artifact (4)
