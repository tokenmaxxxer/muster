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

## Summary counts (round 1/2, superseded below by round 3's rule flip)
- (a) 1:1 fit: `ux-design`* , `coding`*, `reflect` (3, *with caveats noted above)
- (b) bundled, split candidates: `feasibility` (3 domains → 1 verdict), `product` (partial — market analysis unnamed), `ops` (2 domains → 1 role, weaker split case)
- (c) method not domain: `qa`, `review`, `verify` (3)
- (d) domain, no role: UX engineering/tokens, API design, competitive/market analysis, security/threat-model-as-independent-artifact (4)

## 3. Round-3 re-judgment — promotion-default rule flip (PR #161 second feedback)

PR #161's second feedback withdraws round-2's "promote conservatively" instruction and replaces the judgment rule outright: **promotion is now the default** for any domain whose `decides` (a distinguishable judgment lens) and `produces` (a distinguishable deliverable) can both be named. Two changes to how holds are argued, both retroactive to every row above:

1. **"No single canonical text" is no longer a hold reason.** A domain with a dominant practitioner framework or multiple credible lineages (rather than one canonical book) is anchored to that framework/lineage set instead — canon-absence was round 2's hold reason for nearly all biz/ops rows and it no longer applies.
2. **"Zero current usage signal" is no longer a hold reason.** The feedback states explicitly: role definitions must exist before demand arrives, not after — this was round 1/2's hold reason for rows 17-18, 27-28, 30-34, 36-40, 42, 44 and it no longer applies.

What still justifies **귀속** (attribution, kept as the only remaining exception, per feedback's own two carve-outs):
- **Pure restatement** of a judgment lens already counted elsewhere in the map (not "a related domain" — the *same* decides/produces pair named twice).
- **Non-separable produces**: splitting the domain out would leave it with no artifact that stands alone from the role it would be split from.

### 3a. Re-judged table — every domain from rows 1-44, final call

| Domain (row #s merged) | Final role | 판정 | decides (lens) | produces (anchor) |
|---|---|---|---|---|
| Product discovery (1) | `product` | keep (existing) | 무엇을 만들지 | Cagan/JTBD hypothesis+spec |
| Competitive/market analysis (2) | `market-analysis` | **PROMOTE** (round 1, unchanged) | 경쟁 구도에서 이 스펙이 서는가 | Porter five-forces + JTBD-landscape verdict |
| UX research/interaction (3) | `ux-research` | keep (renamed from `ux-design`) | 문제→화면/플로우 | NN/Cooper screen-flow spec |
| UX engineering/tokens (4) | `ux-engineering` | **PROMOTE** (round 1, unchanged) | 디자인 결정→토큰/규칙 시스템화 | Design Tokens Book / Material token classes |
| API/interface design (5) | `api-design` | **PROMOTE** (round 1, unchanged) | 서비스 경계의 인터페이스 형태 | RESTful API Design Patterns anchor |
| Software architecture/system design (6, 20 — same domain restated twice) | **`architecture`** (new) | **PROMOTE — reversed from round 1/2 hold** | 컴포넌트 경계·의존 방향을 어떻게 가를지 | Bass/Clements/Kazman + Evans DDD anchor; ADR-style decision record |
| Coding/implementation (7) | `coding` | keep | 승인된 범위→동작 코드 | Code Complete/Clean Code anchor |
| Test/QA methodology (8) | `qa` | keep (method role, unaffected by domain-promotion rule) | 실행 시 실제 동작 | evidence-cited pass/fail |
| Security/threat modeling (9) | `security-threat-model` | **PROMOTE** (round 1, unchanged) | 신뢰 경계의 위협 표면 | Shostack/STRIDE anchor |
| Tech feasibility/build-vs-buy (10) | `feasibility` | keep, narrowed | 기술적으로 되는가 | PoC-driven build-vs-buy verdict |
| Legal/regulatory/compliance (11, 29 — same domain) | **`legal-compliance`** (new) | **PROMOTE — reversed from round 1/2 hold** | 이 스펙/처리가 법·규제를 통과하는가 | dominant framework anchor: ISO 37301 compliance-management-system structure + IAPP privacy-program framework (no single canonical text, but two credible cross-jurisdiction frameworks — satisfies the new rule's "복수 계보" allowance) |
| Code review/audit (12) | `review` | keep (method role) | 산출물 vs 명세 일치 | Present/Surface/Absent/Incorrect/Unverifiable |
| Independent verification (13) | `verify` | keep (method role) | 결함 실재 — 독립 재현 | reproduced/not-reproduced + evidence |
| Release engineering/rollout (14) | `ops` | keep, bundled w/ 15 | 배포 가능한가 | SRE Workbook canary/staged-rollout anchor |
| Incident response/postmortem (15) | `ops` (bundled) | keep | 장애 후 무엇을 배웠나 | blameless postmortem anchor |
| Retrospective/org learning (16) | `reflect` | keep | 이슈 역사가 무엇을 가르치나 | Kerth retrospective anchor |
| Data/analytics engineering (17, 28 — same domain restated) | **`data-engineering`** (new) | **PROMOTE — reversed from round 1 completeness-note / round 2 hold** | 데이터를 안정적으로 이동·변환할 파이프라인 설계 | Reis & Housley *Fundamentals of Data Engineering* anchor |
| Technical writing/documentation (18, 43 — same domain restated) | **`technical-writing`** (new) | **PROMOTE — reversed from round 1 completeness-note / round 2 hold** | 독자가 알아야 할 것을 어떻게 구조화하는가 | Google Technical Writing courses anchor |
| DB design/data modeling (19) | **`data-modeling`** (new) | **PROMOTE — reversed from round 2 hold** (feedback names this explicitly) | 데이터를 어떤 관계/스키마로 모델링할지 | Kimball & Ross / Codd anchor |
| Performance engineering (21) | **`performance-engineering`** (new) | **PROMOTE — reversed from round 2 hold** (feedback names this explicitly) | 이 설계가 부하/지연 목표를 만족하는가 | Brendan Gregg *Systems Performance* anchor |
| Infra/IaC (22) | `ops` | **귀속 유지** — non-separable produces | IaC is *how* `ops` executes a rollout decision, not a distinct judgment lens from row 14; splitting leaves no artifact that isn't already `ops`'s rollout checklist | — |
| CI/CD·build (23) | `ops` | **귀속 유지** — non-separable produces, same reasoning as row 22 | — | — |
| Accessibility/WCAG (24) | **`accessibility`** (new) | **PROMOTE — reversed from round 2 hold** (feedback names this explicitly) | 화면/플로우/토큰이 WCAG를 만족하는가 | W3C WCAG 2.x normative anchor |
| SLO/reliability engineering (25) | `ops` | **귀속 유지** — pure restatement of row 14/15's lens (same SRE-workbook lineage, same "is it up and fast enough" judgment feasibility already asked to reconsider once and reject; feedback's explicit-promotion list does not name this row) | — | — |
| Secure coding/pentest (26) | **`secure-coding`** (new) | **PROMOTE — reversed from round 2 hold** (feedback names this explicitly) | 구현이 실제로 공격에 견디는가 (설계 단계 threat-model과 별개, 구현/사후 검증) | OWASP ASVS/Testing Guide + Weidman anchor |
| ML engineering (27) | **`ml-engineering`** (new) | **PROMOTE — reversed from round 2 hold** ("usage signal" no longer a hold reason) | 모델을 서비스로 안정적으로 서빙할 수 있는가 | Sculley et al. "Hidden Technical Debt" + Huyen anchor |
| Finance/unit economics (30) | **`finance-unit-economics`** (new) | **PROMOTE — reversed** | 이 사업/기능이 단위경제상 성립하는가 | Damodaran valuation coursework / *Startup CXO* ch. anchor |
| Pricing (31) | **`pricing`** (new) | **PROMOTE — reversed** | 얼마를 받을지, 어떤 구조로 받을지 | Nagle & Holden anchor |
| Sales (32) | **`sales`** (new) | **PROMOTE — reversed** | 이 리드/기회를 어떻게 진행시킬지 | Rackham *SPIN Selling* anchor |
| Marketing (33) | **`marketing`** (new) | **PROMOTE — reversed** | 어떤 메시지로 어떤 채널에 도달할지 | Kotler & Keller anchor |
| Growth/funnel analysis (34) + experiment interpretation (35 — same judgment lens, "does the data support the claim", restated) | **`growth-analytics`** (new) | **PROMOTE — reversed** (row 35 merges in as attribution-by-restatement, not held) | 퍼널의 어느 단계가 병목이고, 이 실험이 그 병목을 실제로 개선했는가 | Weinberg & Mares *Traction* + Kohavi/Tang/Xu *Trustworthy Online Controlled Experiments* anchor |
| Customer support/CS (36) | **`customer-support`** (new) | **PROMOTE — reversed** (dominant practitioner framework, not a book canon — satisfies new rule's framework allowance) | 고객 문의를 어떤 우선순위/SLA로 처리할지 | Zendesk/Intercom support-ops playbooks + Customer Effort Score methodology anchor |
| Partnerships/BD (37) | **`partnerships-bd`** (new) | **PROMOTE — reversed** | 이 파트너십이 구조적으로 성립하는가 | alliance/BD practitioner lineage anchor (e.g. Segil *Fast Alliances*) |
| PR/communications (38) | **`pr-communications`** (new) | **PROMOTE — reversed** | 이 메시지가 외부에 어떻게 읽힐지 | Grunig & Hunt anchor |
| Risk management (39) | **`risk-management`** (new) | **PROMOTE — reversed** | 전사 리스크 노출이 허용 범위인가 (feasibility의 "만들어도 되는가"보다 넓은 범위 — 재무/운영/전략 리스크 포함) | COSO ERM framework anchor |
| Brand/visual design (40) | **`brand-design`** (new) | **PROMOTE — reversed** | 브랜드 정체성이 시각적으로 일관되는가 | Wheeler *Designing Brand Identity* anchor |
| Content design/UX writing (41) | **`content-design`** (new) | **PROMOTE — reversed from round 2's attribution into `ux-research`** (feedback names this explicitly as an expected promotion) | 문구가 사용자의 실제 결정을 돕는가 (플로우 설계와 별개의 판단 — Redish 렌즈는 상호작용이 아니라 언어) | Redish *Letting Go of the Words* + Winters content-design lineage anchor |
| i18n/localization (42) | **`localization`** (new) | **PROMOTE — reversed** | 다른 로케일에서도 이 산출물이 성립하는가 | Esselink anchor |
| DevRel (44) | **`devrel`** (new) | **PROMOTE — reversed** | 외부 개발자가 이 표면을 채택할 수 있는가 | Thengvall anchor |

### 3b. What stays held or attributed, and why (the only two carve-outs left)
- **IaC (22), CI/CD (23), SLO (25)** stay attributed to `ops` — non-separable produces / pure restatement of `ops`'s existing rollout-reliability lens. These are the only three rows in the entire 44-row map still held after the rule flip.
- No domain is held purely for lacking a canonical text or lacking current usage — both reasons are retired per feedback.

### 3c. Round-3 summary
44 domains surveyed end-to-end, deduped where the same domain was restated (6=20, 11=29, 17=28, 18=43, 34=35) → **35 target roles**: the original 9 (`ux-design` renamed `ux-research`) + 26 promotions (4 from round 1, 22 from round 3's rule flip). Only 3 rows remain attributed (IaC, CI/CD, SLO → all into `ops`). Zero rows held with no disposition.

## 4. Round-4 re-judgment — kept roles re-examined under the same rule (PR #161 fourth feedback)

Round 3 flipped the rule (promotion is default; 귀속 only for pure restatement or non-separable produces — §3, carve-outs at line 114-116) but only re-ran it across rows 1-44, the domains already named on the map. It never turned the same rule inward on the four roles that round 1-3 passed through untouched as single units: `product`, `coding`, `ops`, `reflect`. PR #161's fourth feedback points out this gap directly, naming specific sub-domains inside each — each anchored to its own book/lineage, distinct from the parent role's existing anchor — and asks them to be re-judged the same way rows 1-44 were. This section applies the identical two-carve-out test (pure restatement of an already-counted lens, or non-separable produces) to each named sub-domain. No other hold reason is used — consistent with round 3.

### 4a. `product`

| 하위 도메인 | Anchor (book/lineage) | 판정 | 근거 |
|---|---|---|---|
| 가설 디스커버리 (Cagan) | Cagan *Inspired* / JTBD | **귀속-유지** | Pure restatement — this *is* `product`'s existing decides/produces pair (round-1 anchor, unchanged since row 1). Not a second lineage inside `product`, it's the lineage `product` was already built on. |
| 사용자 발견/인터뷰 (Fitzpatrick, *The Mom Test*) | Fitzpatrick *The Mom Test* | **PROMOTE → `user-discovery`** | Distinct decides: 이 문제가 실제 사용자의 고통인가를 편향 없는 인터뷰로 검증했는가 — a method for *validating* a hypothesis against real users, not forming the hypothesis (`product`'s lens) or writing it up as a spec (Wiegers' lens below). Distinct produces: interview script + evidence log (verifiable, biased-question-free), separable from `product`'s hypothesis/spec artifact — it feeds `product` but stands alone as its own deliverable. Neither carve-out applies. |
| 요구공학/스펙 (Wiegers, *Software Requirements*) | Wiegers *Software Requirements* | **PROMOTE → `requirements-engineering`** | Distinct decides: 요구사항이 검증가능·일관되고 추적 가능한 스펙으로 작성되었는가 — a rigor/elicitation-and-specification lens, not "what to build" (`product`) or "is this real user pain" (`user-discovery`). Distinct produces: structured requirements doc with acceptance criteria + traceability matrix, a stand-alone artifact type `product`'s looser "hypothesis, spec" line has never actually anchored to (Wiegers is a different book from Cagan/JTBD). Neither carve-out applies. |

### 4b. `coding`

| 하위 도메인 | Anchor (book/lineage) | 판정 | 근거 |
|---|---|---|---|
| 신규 구현 (McConnell, *Code Complete*) | McConnell *Code Complete* / Martin *Clean Code* | **귀속-유지** | Pure restatement — this is `coding`'s existing anchor, unchanged since row 7/round 1. Not a second lineage. |
| 리팩토링/레거시 (Fowler, *Refactoring*; Feathers, *Working Effectively with Legacy Code*) | Fowler *Refactoring*; Feathers *Working Effectively with Legacy Code* | **PROMOTE → `refactoring-legacy`** | Distinct decides: 기존 코드의 관찰 가능한 동작을 바꾸지 않으면서 안전하게 재구조화할 수 있는가 — the judgment lens is safety-under-preservation, categorically different from McConnell's "build correctly to spec from a blank/extending state." Distinct produces: refactoring plan + characterization-test scaffold (Feathers' seam-finding method), an artifact that stands alone from new-feature code and is required *before* touching legacy code, not folded into it. Neither carve-out applies. |
| 테스트 작성 (Meszaros, *xUnit Test Patterns*) | Meszaros *xUnit Test Patterns* | **PROMOTE → `test-authoring`** | Distinct decides: 테스트 코드 자체가 좋은 설계(격리성, fixture 전략, smell 회피)로 작성되었는가 — an *authorship* lens about test code's own design quality. This is explicitly not a restatement of `qa`'s decides ("실행 시 실제 동작" — runtime execution observation): `qa` observes whether running code behaves correctly; `test-authoring` judges whether the test suite itself is well-designed to keep observing that reliably over time. Produces (test suite architecture/pattern review) is separable — it is authored and reviewable independent of any single test run. Neither carve-out applies; explicitly not swallowed by `qa`'s method-role scope. |

### 4c. `ops`

| 하위 도메인 | Anchor (book/lineage) | 판정 | 근거 |
|---|---|---|---|
| 릴리스/배포 엔지니어링 (Humble & Farley) | Humble & Farley, *Continuous Delivery*; SRE Workbook canary/staged-rollout | **귀속-유지** | Pure restatement — this is `ops`'s own existing anchor (round-1 domain 14, restated at round-2 row 23 CI/CD → already folded here). Remains `ops`'s narrowed core: 배포 가능한가. |
| 관측성/모니터링 (Majors, Fong-Jones & Miranda, *Observability Engineering*) | Majors et al., *Observability Engineering* | **PROMOTE → `observability`** | Distinct decides: 프로덕션에서 시스템 내부 상태에 대해 사전에 정의하지 않은 질문도 던질 수 있는가 (high-cardinality/high-dimensionality telemetry 설계) — this is a distinct lineage from release engineering's "can we safely ship" and from incident response's "what already broke." It is the instrumentation layer that makes both possible, not a restatement of either. Distinct produces: telemetry/instrumentation plan (traces, structured events, dashboards) that stands alone as a deliverable independent of any specific rollout or incident. Neither carve-out applies. |
| 인시던트 대응·포스트모템 (Google SRE) | Google SRE Workbook, blameless postmortem culture | **PROMOTE → `incident-response`** | Round 1-3 bundled this into `ops` as "the same SRE-Workbook lineage" without re-testing that claim under the round-3 rule — it was inherited, not re-derived. Under the actual two-carve-out test it fails both: decides is distinct (장애 후 무엇을 배웠고 재발을 무엇으로 막을 것인가, a retrospective-investigative lens) from release engineering's decides (배포 가능한가, a forward go/no-go lens); produces is separable (timestamped timeline + blameless postmortem doc + owned action items — see `blameless-postmortem` skill in this repo, which already treats this as its own procedure distinct from rollout checklists). Not pure restatement, not non-separable → promotes. |
| 용량 계획 (SRE Workbook capacity-planning chapter; queueing-theory practitioner lineage) | SRE Workbook, capacity planning; queueing-theory forecasting practice | **PROMOTE → `capacity-planning`** | Distinct decides: 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가 — a forecasting/provisioning-timeline lens, distinct from `performance-engineering`'s decides (이 설계가 지금의 부하/지연 목표를 만족하는가, a point-in-time design-verification lens promoted in round 3). Distinct produces: capacity forecast/growth-curve model with a provisioning trigger, separable from both a performance profile and a rollout checklist. Neither carve-out applies. |

### 4d. `reflect`

| 하위 도메인 | Anchor (book/lineage) | 판정 | 근거 |
|---|---|---|---|
| 회고 (Derby & Larsen, *Agile Retrospectives*) | Derby & Larsen *Agile Retrospectives* (restates Kerth *Project Retrospectives*, `reflect`'s existing round-1 anchor) | **귀속-유지** | Pure restatement — same decides/produces pair `reflect` already anchors to; Derby & Larsen is the same lineage as Kerth, not a second one. |
| 조직 학습/지식 관리 | Nonaka & Takeuchi, *The Knowledge-Creating Company*; Davenport & Prusak, *Working Knowledge* | **PROMOTE → `knowledge-management`** | Distinct decides: 개별 이슈의 교훈이 조직 차원에서 재사용 가능한 형태로 축적·색인되는가 — a systemic, cross-issue curation lens, distinct from `reflect`'s per-issue advisory decides (이슈 역사가 무엇을 가르치나). Distinct produces: a maintained knowledge base/pattern library artifact (write_scope-bearing), separable from `reflect`'s explicitly advisory-only, no-write_scope output — the two are not the same deliverable at different scales, they are different artifact types (one-off advisory note vs a maintained system of record). Neither carve-out applies. |

### 4e. Round-4 summary
8 sub-domains re-judged as **PROMOTE** (`user-discovery`, `requirements-engineering`, `refactoring-legacy`, `test-authoring`, `observability`, `incident-response`, `capacity-planning`, `knowledge-management`); 4 sub-domains confirmed **귀속-유지** as pure restatements of the parent role's existing anchor (Cagan-discovery stays `product`, McConnell-implementation stays `coding`, release-engineering stays `ops`, retrospective-facilitation stays `reflect` — each parent role's core, narrowed by the sub-domains that left). No sub-domain was held for any other reason. Round-3 total was 35 roles; round 4 adds 8 → **43 target roles**.

## 5. Round-5 pass (renaming + boundary specificity, per PR #161's fifth feedback)

No new domain judgment in this round — the domain map and promote/attribute verdicts above are unchanged. Round 5 is entirely in [[role-taxonomy]]: (1) every one of the 43 role names re-audited against the predictive-name test, 9 renamed (`product`→`product-discovery`, `ux-research`→`interaction-design`, `coding`→`implementation`, `feasibility`→`technical-feasibility`, `qa`→`execution-observation`, `review`→`conformance-review`, `verify`→`defect-verification`, `ops`→`release-engineering`, `reflect`→`issue-retrospective`); (2) every row now carries a produces required-field list and a hand-off target; (3) the six adjacent-pair clusters PR #161 named by name get a worked boundary-case deep dive each, with an explicit collision check confirming no pair needs re-merging. Role count stays **43** — this round changes labels and specificity, not the taxonomy's shape.
