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

### 1a. Round-2 expansion (PR #161 feedback) — full product-company sweep

PR #161 feedback: rows 1-18 above are dev/product-eng biased; the domain map must cover the whole software product company (dev, biz/ops, design/content), each domain judged **승격**(promote to new role) / **귀속**(attribute into an existing role) / **보류**(on the map, held — no role now) with a reason, not silently cut. Judgment stays conservative: promotion bar is unchanged from the original 4 (`market-analysis`, `ux-engineering`, `api-design`, `security-threat-model`) — this round adds zero further promotions; see [[scout-brief]] round 2 for why (biz/ops domains overwhelmingly lack a single canonical text, which argues against promoting a role that would have no named-pattern anchor).

**개발 계열 — additional domains**

| # | Domain | Anchor (book/course/methodology) | 판정 | 사유 |
|---|---|---|---|---|
| 19 | 데이터 모델링/DB 설계 | Kimball & Ross *The Data Warehouse Toolkit*; Codd relational model | **귀속** → `coding` | Schema design is inline with implementation today (`src/**` covers migrations); no separate literature contest raised by the issue, and DB design decisions are sequential-dependent on the code they back, not orthogonal enough to parallelize as its own PR/branch. |
| 20 | 소프트웨어 아키텍처/시스템 설계 | Bass/Clements/Kazman *Software Architecture in Practice*; Evans DDD (= domain 6, restated here for judgment completeness) | **귀속** → `coding` (unchanged from round 1) | Named domain, no dedicated role; `coding`'s `produces` folds architecture decisions in ad hoc via `docs/issue-<n>/decisions/`. Held rather than promoted: architecture calls are usually sequential-coupled to the implementation they justify, not independently dispatchable. |
| 21 | 성능 엔지니어링 | Brendan Gregg *Systems Performance* | **귀속** → `coding`/`ops` split by phase | Design-time perf budget → `coding`; production perf regression → `ops` (SRE workbook already anchors capacity/latency under production reliability). No standalone literature contest strong enough to promote. |
| 22 | 인프라/IaC | Kief Morris *Infrastructure as Code* | **귀속** → `ops` | SRE workbook (ops's existing anchor) already treats provisioning/rollout as one lineage; IaC is the *how*, not a separate decision-lens. |
| 23 | CI/CD·빌드 | Humble & Farley *Continuous Delivery*; Forsgren et al. *Accelerate* | **귀속** → `ops` | Same reasoning as row 22 — release-engineering literature (row 14) already spans this. |
| 24 | 접근성(WCAG) | W3C WCAG 2.x (normative spec, not a book — practitioner-standard anchor) | **보류** | Named literature exists (a spec, unusually canonical for this list) and it is genuinely orthogonal to visual/interaction design — but no current role or seed example names it, and it cuts across both `ux-research` (interaction) and `ux-engineering` (token-level contrast/focus rules) rather than sitting in one. Held as a map gap for a future issue to decide whether it's a checklist inside those two roles or its own gate. |
| 25 | 신뢰성 엔지니어링(SLO) | Google SRE Workbook — same anchor as `ops`'s existing domain 14/15 | **귀속** → `ops`, explicitly not split | Issue asked to "consider separating from ops" — considered and rejected: SLO-setting and incident/postmortem response share the same SRE-workbook lineage `ops` already anchors to (see round-1 rationale for why `ops` stays bundled). No second canonical text argues for a split. |
| 26 | 시큐어 코딩/침투 테스트 | OWASP ASVS/Testing Guide; Weidman *Penetration Testing* — distinct lineage from Shostack's STRIDE (design-time threat modeling, already promoted as `security-threat-model`) | **보류** | Genuinely distinct literature from threat modeling (STRIDE is design-time architecture review; secure coding/pentest is implementation-time and post-hoc verification) — a real map gap, not folded into `security-threat-model`. Not promoted this round: no current usage signal (no issue has hit this gap yet), and `qa`/`review`'s existing execution-observation method already catches some class of these bugs incidentally. Flagged for a future issue if a security-specific execution/pentest need recurs. |
| 27 | ML 엔지니어링 | Sculley et al. *"Hidden Technical Debt in Machine Learning Systems"*; Huyen *Designing Machine Learning Systems* | **보류** | No current role, no current project usage (no ML-model-serving surface in this repo as of this survey) — named for completeness only, same treatment as rows 17-18 in round 1. |
| 28 | 데이터 파이프라인/데이터 엔지니어링 | Reis & Housley *Fundamentals of Data Engineering* | **보류** | Same as row 27 — no current usage signal in this project. |

**사업·운영 계열 — almost entirely new to the map**

| # | Domain | Anchor (book/course/methodology) | 판정 | 사유 |
|---|---|---|---|---|
| 29 | 법률/규제 컴플라이언스 | No single canonical text — jurisdiction-specific statute + regulator guidance (same characterization as round-1 domain 11) | **보류**, flagged as a live disagreement | Feedback explicitly objects to leaving this folded into `feasibility` ("독립 검토, feasibility 잔류 아님"). Held rather than promoted this round for the same conservative-promotion reason as row 26 (no distinct book/course canon — the compliance-scan *skill* already exists as a non-role tool for this), but the round-1 proposal's framing ("legal stays merged, no separable literature yet") is noted as contested and worth revisiting in a follow-up issue rather than settled here. |
| 30 | 재무/단위경제 | Aswath Damodaran valuation coursework; *Startup CXO* (O'Reilly) ch. "Unit Economics and KPIs" | **보류** | Named literature exists but no current role or project surface touches financial modeling/unit-economics decisions — map gap only. |
| 31 | 프라이싱 | Nagle & Holden, *The Strategy and Tactics of Pricing* | **보류** | Same — named canon, zero current usage signal. |
| 32 | 세일즈 | Rackham, *SPIN Selling* | **보류** | Named canon (sales-methodology literature is genuinely well-established), zero current usage signal — this repo has no sales-process surface. |
| 33 | 마케팅 | Kotler & Keller, *Marketing Management* | **보류** | Same treatment. |
| 34 | 그로스/퍼널 분석 | Weinberg & Mares, *Traction*; Croll & Yoskovitz, *Lean Analytics* | **보류** | Named canon confirmed by round-2 search ([[scout-brief]]). Zero current usage signal. |
| 35 | 데이터 분석(실험 해석) | Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments* | **귀속** → overlaps existing `experiment-trust`/`hypothesis-testing` *skills* (not roles) | Distinct from a role-worthy domain here: this project already has skill-level tooling for exactly this judgment (experiment SRM/trust gates, pre-registered hypothesis testing) — attributing to existing skill infrastructure rather than flagging as a role gap. |
| 36 | 고객지원/CS | No dominant canonical text — practitioner playbooks (Zendesk/Intercom support-ops guides), fragmented | **보류** | No canon, no current usage — lowest-priority map entry. |
| 37 | 파트너십/BD | No dominant canonical text | **보류** | Same. |
| 38 | PR/커뮤니케이션 | Grunig & Hunt, *Managing Public Relations* | **보류** | Named canon exists but zero current usage signal. |
| 39 | 리스크 관리 | COSO Enterprise Risk Management framework | **보류** | Named canon (COSO is genuinely the dominant cross-industry framework), zero current usage signal — and meaningfully overlaps `feasibility`'s go/no-go verdict shape if it were ever promoted. |

**디자인·콘텐츠 계열 — new to the map**

| # | Domain | Anchor (book/course/methodology) | 판정 | 사유 |
|---|---|---|---|---|
| 40 | 브랜드/비주얼 디자인 | Alina Wheeler, *Designing Brand Identity* | **보류** | Distinct from `ux-research` (interaction/flow) and `ux-engineering` (tokens/system rules) — a real map gap, not silently subsumed into either, but zero current usage signal in this project (no brand-identity surface has been requested). |
| 41 | 콘텐츠 디자인/UX 라이팅 | Redish, *Letting Go of the Words*; Content Design (Winters) practitioner lineage | **귀속** → `ux-research` | Named literature exists and is arguably distinct, but the round-2 search ([[scout-brief]]) surfaced it as tightly coupled to interaction design in practice (same deliverable — the flow/screen spec — carries the copy) — attributed rather than promoted; revisit if copy/microcopy review ever becomes its own contested deliverable. |
| 42 | i18n/현지화 | Esselink, *A Practical Guide to Localization* | **보류** | Named canon, zero current usage signal (no localization surface in this project). |
| 43 | 테크니컬 라이팅 | Google Technical Writing courses (= round-1 domain 18, restated here for judgment completeness) | **보류**, unchanged from round 1 | No canon contest, no current usage signal. |
| 44 | DevRel | Mary Thengvall, *The Business Value of Developer Relations* | **보류** | Named canon, zero current usage signal — this project has no external-developer-facing surface today. |

**Round-2 summary**: 26 additional domains surveyed (rows 19-44) covering dev-gap, biz/ops, and design/content lineages per feedback's three explicit categories. Judgment distribution: 0 promoted (conservative bar unchanged — the round-1 4 stand alone), 5 attributed into an existing role/skill (rows 19-21, 23, 35, 41 partially — see individual rows), 21 held on the map with no role. One entry (row 29, legal/compliance) is flagged as a **contested** hold, not a settled one — feedback explicitly disagrees with the round-1 proposal's framing and this survey records the disagreement rather than silently resolving it.

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
