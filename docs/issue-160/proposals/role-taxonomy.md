# Proposal — target role taxonomy (issue-160)

files: docs/issue-160/reports/coding/survey.md, docs/issue-160/reports/coding/scout-brief.md, docs/issue-160/proposals/role-taxonomy.md (this file). No src/, no roles/*.json edits — this is a design document only; role/system changes execute in a separate issue after owner approval, per the issue's own instruction.

## Request (paraphrased)
Re-derive the role system from the principle "one role = one professional domain at book/course granularity — a domain with a clear lens, required deliverables, and named patterns, orthogonal enough to run in parallel with other roles" — rather than the current lifecycle-stage split. Survey the domain map (must include UX engineering/tokens, competitive analysis, coding, API design), map the current 9 roles onto it, and propose a target system plus a side-effect analysis. Design only; no execution.

Round 3 (this revision): PR #161's second feedback withdraws the round-2 conservative-promotion bar. New rule — promotion is the default for any domain with a nameable `decides`/`produces`; attribution is the exception, reserved for pure restatement of an already-counted domain or a produces that can't stand alone if split out. "No canonical text" and "no current usage signal" are both retired as hold reasons.

Round 4 (this revision): PR #161's fourth feedback points out that round 3 re-ran the rule flip across the 44-row domain map but never turned it inward on the four roles round 1-3 passed through as single units — `product`, `coding`, `ops`, `reflect` — each of which bundles multiple distinct book/lineage-anchored sub-domains named explicitly in the feedback (Mom Test / Wiegers / Cagan inside `product`; new-implementation / refactoring-legacy / test-authoring inside `coding`; release-engineering / observability / incident-postmortem / capacity-planning inside `ops`; retro-facilitation / knowledge-management inside `reflect`). Same two-carve-out test applied to each, per [[survey]] §4.

## Constraints
- Proposal only — no `roles/*.json` edits, no migration execution.
- Must anchor every proposed role's required-deliverable shape to a named domain pattern (book/methodology or, where no single canonical text exists, a dominant practitioner framework), per [[survey]] and [[scout-brief]].
- Must address orchestration-cost/judgment-burden side effects of adding roles, and the "briefing cost > work cost" pathology when domains are sliced too fine.

## What will be done
Target role system below. `use_when` is the cost-control lever now (kept narrow per role), not role count — see side-effects.

### Kept/renamed from the original 9

| Target role | decides | use_when | produces (anchor) | write_scope | Migration |
|---|---|---|---|---|---|
| `product` | 무엇을 만들지 — 가치 가설 (Cagan discovery) | 요구가 문제/가설 수준일 때 | hypothesis, spec (Cagan/JTBD) | [] | **keep, narrowed twice** — market-analysis split out (round 3); user-discovery (Mom Test interviews) and requirements-engineering (Wiegers spec-writing) split out this round ([[survey]] §4a) |
| `ux-research` | 문제 → 화면·플로우 | product 스펙 확정 후 | screen/flow/wireframe spec (NN/Cooper) | [] | **keep** = current `ux-design`, renamed |
| `coding` | 승인된 범위 → 동작 코드 (신규 구현) | 스펙/제안 승인 후 신규 구현 | src/·test/ 코드 (Code Complete/Clean Code) | `src/**`, `test/**` | **keep, narrowed** — API/architecture decisions arrive pre-made (round 3); refactoring-legacy and test-authoring split out this round ([[survey]] §4b) |
| `feasibility` | 기술적으로 되는가 | 기술 PoC가 필요할 때 | go\|no-go\|conditional + PoC 측정 (build-vs-buy consensus) | [] | **keep, narrowed** — threat-model AND legal probes both removed (now separate roles) |
| `qa` | 실행 시 실제 동작 | 실행 가능 산출물 랜딩 시 | evidence-cited pass/fail/blocked | [] | **keep** — method role (cross-domain), unaffected by the promotion rule |
| `review` | 산출물 vs 명세 일치 | coding 커밋 랜딩 후 | Present\|Surface\|Absent\|Incorrect\|Unverifiable | [] | **keep** — method role |
| `verify` | 결함 실재 — 독립 재현 | 실행 결과가 다투어질 때 | reproduced\|not-reproduced + evidence | [] | **keep** — method role |
| `ops` | 배포 가능한가 (릴리스/롤아웃) | 머지 후 배포 시 | rollout checklist (Humble & Farley / SRE Workbook) | [] | **keep, narrowed** — previously absorbed IaC/CI-CD/SLO (round 3); observability, incident-response, capacity-planning split out this round ([[survey]] §4c) |
| `reflect` | 이슈 역사가 무엇을 가르치는가 (단일 이슈 회고) | verify/review 종결 후 | advisory lessons (retrospective) | [] | **keep, narrowed** — knowledge-management (조직 차원 지식 축적) split out this round ([[survey]] §4d) |

### 26 promoted roles (4 carried from round 1, 22 new this round)

| Target role | decides | use_when | produces (anchor) | write_scope |
|---|---|---|---|---|
| `market-analysis` | 경쟁 구도에서 이 스펙이 서는가 | product 스펙 확정 후, 경쟁 구도가 걸린 결정일 때 | five-forces + JTBD-landscape verdict (Porter) | [] |
| `ux-engineering` | 디자인 결정 → 토큰/규칙 시스템화 | 화면 스펙이 여러 개 쌓여 시스템화가 필요할 때 | design token set + rules (Design Tokens Book/M3) | design-system source paths (TBD at execution) |
| `api-design` | 서비스 경계의 인터페이스 형태 | 여러 소비자가 걸리는 API 표면을 설계/변경할 때 | interface spec + lifecycle plan (RESTful API Design Patterns) | interface/schema paths (TBD at execution) |
| `architecture` | 컴포넌트 경계·의존 방향 | 새 모듈 경계나 기존 경계 변경이 걸릴 때 | ADR-style boundary decision (Bass/Clements/Kazman + DDD) | `docs/issue-<n>/decisions/**` |
| `security-threat-model` | 신뢰 경계의 위협 표면 | 스펙에 신뢰 경계·인증·민감데이터가 걸릴 때 | STRIDE threat model + mitigation list (Shostack) | [] |
| `legal-compliance` | 이 스펙/처리가 법·규제를 통과하는가 | 개인정보·라이선스·계약이 걸릴 때 | 컴플라이언스 verdict (ISO 37301 + IAPP 프레임워크) | [] |
| `data-modeling` | 데이터를 어떤 관계/스키마로 모델링할지 | 스키마 신설/변경이 걸릴 때 | schema/ERD + migration plan (Kimball/Codd) | `src/**` migrations |
| `performance-engineering` | 부하/지연 목표를 만족하는가 | 성능 예산이 걸린 설계/회귀일 때 | 성능 예산 + 프로파일 근거 (Brendan Gregg) | [] |
| `accessibility` | 화면/토큰이 WCAG를 만족하는가 | 신규 인터랙션 패턴·색상 토큰 도입 시 | WCAG 준수 체크리스트 | [] |
| `secure-coding` | 구현이 공격에 견디는가 | 인증/입력처리 코드 랜딩 후 | ASVS 체크리스트/pentest 소견 (OWASP/Weidman) | [] |
| `ml-engineering` | 모델을 서비스로 안정적으로 서빙 가능한가 | 모델 서빙 표면이 걸릴 때 | 서빙 설계 + 리스크 노트 (Sculley/Huyen) | [] |
| `data-engineering` | 파이프라인이 데이터를 안정적으로 이동·변환하는가 | 파이프라인 신설/변경이 걸릴 때 | 파이프라인 설계 (Reis & Housley) | [] |
| `technical-writing` | 독자가 알아야 할 것을 어떻게 구조화할지 | 외부 공개 문서가 필요할 때 | 문서 구조/초안 (Google Technical Writing) | `docs/**` (외부공개 한정) |
| `finance-unit-economics` | 단위경제상 성립하는가 | 가격/비용 구조가 걸린 결정일 때 | 단위경제 모델 (Damodaran/Startup CXO) | [] |
| `pricing` | 얼마를, 어떤 구조로 받을지 | 신규 가격 정책이 걸릴 때 | 가격 verdict (Nagle & Holden) | [] |
| `sales` | 리드/기회를 어떻게 진행시킬지 | 영업 프로세스 설계가 걸릴 때 | 세일즈 플레이북 (Rackham) | [] |
| `marketing` | 어떤 메시지로 어떤 채널에 도달할지 | 캠페인/포지셔닝이 걸릴 때 | 메시징/채널 계획 (Kotler & Keller) | [] |
| `growth-analytics` | 퍼널 병목과 실험 결과가 실제 개선인지 | 퍼널 분석 또는 A/B 실험 해석이 걸릴 때 | 퍼널 진단 + 실험 trust verdict (Traction + Kohavi) | [] |
| `customer-support` | 문의를 어떤 우선순위/SLA로 처리할지 | CS 플로우/SLA 설계가 걸릴 때 | 지원 플레이북 (Zendesk/Intercom + CES) | [] |
| `partnerships-bd` | 파트너십이 구조적으로 성립하는가 | 제휴/BD 딜 구조가 걸릴 때 | 딜 구조 verdict (alliance/BD 실무 계보) | [] |
| `pr-communications` | 메시지가 외부에 어떻게 읽힐지 | 외부 커뮤니케이션이 걸릴 때 | 커뮤니케이션 계획 (Grunig & Hunt) | [] |
| `risk-management` | 전사 리스크 노출이 허용 범위인가 | 재무/운영/전략 리스크가 걸릴 때 (feasibility보다 넓은 범위) | ERM verdict (COSO) | [] |
| `brand-design` | 브랜드 정체성이 시각적으로 일관되는가 | 브랜드 자산 신설/변경이 걸릴 때 | 브랜드 가이드 (Wheeler) | design-system source paths |
| `content-design` | 문구가 사용자의 실제 결정을 돕는가 | 플로우에 새 카피/마이크로카피가 걸릴 때 | 카피 초안 + 근거 (Redish/Winters) | [] |
| `localization` | 다른 로케일에서도 산출물이 성립하는가 | i18n 대상 표면이 걸릴 때 | 로케일 적합성 verdict (Esselink) | [] |
| `devrel` | 외부 개발자가 이 표면을 채택할 수 있는가 | 외부 개발자 대상 API/SDK가 걸릴 때 | 개발자 온보딩 자료 (Thengvall) | `docs/**` (외부 개발자 한정) |

Net change (round 3): 9 roles → **35 roles** (+26). `qa`/`review`/`verify` stay labeled explicitly as method roles (the promotion rule governs domain roles only). `ux-design` renamed `ux-research`. `feasibility` narrowed twice (threat-model, then legal). IaC/CI-CD/SLO stay attributed to `ops` — the only three domains left un-promoted across the full 44-row map ([[survey]] §3b).

### 8 promoted roles — Round-4 promotions (re-judging `product`/`coding`/`ops`/`reflect` internals, per [[survey]] §4)

| Target role | decides | use_when | produces (anchor) | write_scope |
|---|---|---|---|---|
| `user-discovery` | 이 문제가 실제 사용자의 고통인가 | 가설 검증을 위해 사용자 인터뷰가 필요할 때 | 인터뷰 스크립트 + 근거 로그 (Fitzpatrick, *The Mom Test*) | [] |
| `requirements-engineering` | 요구사항이 검증가능·일관·추적 가능하게 명세되었는가 | product 가설이 확정되어 정식 스펙으로 전환할 때 | 추적 매트릭스 포함 구조화 요구사항 문서 (Wiegers, *Software Requirements*) | [] |
| `refactoring-legacy` | 기존 코드의 관찰 가능한 동작을 바꾸지 않고 안전하게 재구조화할 수 있는가 | 레거시/기존 코드에 손을 대야 할 때 | 리팩토링 계획 + characterization test (Fowler *Refactoring* / Feathers *Working Effectively with Legacy Code*) | `src/**`, `test/**` |
| `test-authoring` | 테스트 코드 자체가 격리성·fixture 전략 면에서 좋은 설계인가 | 신규/기존 테스트 스위트를 설계·리뷰할 때 | 테스트 스위트 아키텍처/패턴 리뷰 (Meszaros, *xUnit Test Patterns*) | `test/**` |
| `observability` | 프로덕션 내부 상태에 대해 사전에 정의하지 않은 질문도 던질 수 있는가 | 신규 서비스/경로에 계측이 필요할 때 | 텔레메트리/계측 설계 (Majors et al., *Observability Engineering*) | [] |
| `incident-response` | 장애 후 무엇을 배웠고 재발을 무엇으로 막을 것인가 | 장애 종결 직후 | 타임라인 + blameless postmortem + 소유자 있는 action item (Google SRE Workbook) | `docs/issue-<n>/postmortems/**` |
| `capacity-planning` | 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가 | 용량 예측/증설 시점 결정이 걸릴 때 | 용량 예측 + 증설 트리거 모델 (SRE Workbook capacity-planning chapter) | [] |
| `knowledge-management` | 개별 이슈의 교훈이 조직 차원에서 재사용 가능한 형태로 축적·색인되는가 | 여러 이슈의 회고가 쌓여 지식 큐레이션이 필요할 때 | 유지되는 지식베이스/패턴 라이브러리 (Nonaka & Takeuchi; Davenport & Prusak) | `docs/patterns/**` |

Net change (round 4): 35 roles → **43 roles** (+8). All 8 come from re-splitting `product`/`coding`/`ops`/`reflect` internals — no other role's boundary changes. `product`/`coding`/`ops`/`reflect` all keep their name and stay the "core" role for their parent lineage (Cagan-discovery, new-implementation, release-readiness, single-issue retro respectively), narrowed each time a sub-domain leaves. Zero sub-domains held for any reason other than the two carve-outs ([[survey]] §4e).

## Out of scope
- Any `roles/*.json` edit, hook change, or contract-doc update — execution is a separate issue, after owner sign-off. This document proposes the target shape and migration path only.
- Deciding execution *order* across 26 new roles beyond the two-track split below — sequencing/prioritization of which role gets built first is an execution-issue call, not this proposal's.

## Migration path — two tracks, per PR #161's fourth point (bulk role-definition setup vs gradual rulebook depth)

**Track A — bulk `roles/*.json` + rulebook skeleton, all 35 at once.** Every promoted role gets a `roles/<name>.json` (decides/use_when/produces/write_scope, as tabled above) and a rulebook skeleton stub (the directive/handbook shell, no filled-in domain content) in one execution pass. This is mechanical — the same shared shape 35 times — and is what makes the roles *exist* before demand arrives, per the owner's stated principle. No orchestration cost is paid until a role's `use_when` actually fires.

**Track B — gradual rulebook depth, filled in as each role is first invoked.** The rulebook body (the domain-pattern anchors, worked examples, handbook detail that make a role's directive actually load-bearing rather than a bare stub) is filled in issue-by-issue, the first time a real issue's `use_when` trips that role — not pre-written for all 35 up front. This keeps the one-time setup cost (Track A) decoupled from the ongoing content-authoring cost (Track B), and naturally prioritizes depth by actual demand order without reintroducing a "wait for demand before the role exists" gate (the role and its trigger exist from Track A; only the depth of its rulebook lags).

## Side-effect analysis
**Orchestration/judgment cost of +26 roles.** Every new role is a branch (`issue-<n>/<role>`), a PR, and a human-approval gate (contract v3 s19). Going from 9 to 35 roles does not mean 35 hops per feature — narrow `use_when` (below) means most issues still only touch the same handful they touch today (`product → ux-research → coding → qa/review/verify → ops`). The cost that does scale with role count is the human's up-front judgment burden reading `docs/specs/approvers.md`-adjacent role definitions and deciding, per issue, which of 35 `use_when` clauses actually apply — that scan cost is real and grows linearly with role count, independent of how many roles actually fire on a given issue.

**Pathology check — briefing cost > work cost.** `use_when` is the only lever that controls this, not role count, per the owner's explicit correction ("역할이 많은 것은 문제가 아니고, 아무 때나 깨어나는 것이 문제다"). Every promoted role's `use_when` above is scoped to a specific trigger condition, not "always" — `api-design` only fires on multi-consumer interface changes, `accessibility` only on new interaction patterns/color tokens, `pricing` only on new pricing policy work. If a role's `use_when` still fires on issues too small to justify a full domain-lens brief, the fix is narrowing that clause further, never merging the role back — per the owner's standing instruction this round.

**Why `ops` stays bundled but the other 26 split out.** The domain map ([[survey]] §3b) shows exactly three sub-domains (IaC, CI/CD, SLO) share `ops`'s existing SRE-Workbook literature end-to-end with no separable produces — that is now the *only* surviving attribution criterion in the whole 44-row map. Every other domain that has its own nameable decides/produces was promoted this round, framework-anchored where no single canonical book exists (finance, pricing, sales, marketing, growth, CS, partnerships, PR, legal-compliance — all anchored to a dominant practitioner framework per [[survey]] §3a instead of a book).

**Legal/regulatory — now resolved, reversing round 2.** Round 2 held `legal-compliance` for lacking a single canonical text; that hold reason is retired this round per the owner's rule flip, and the domain is promoted with a dual-framework anchor (ISO 37301 + IAPP). This directly answers PR #161's first-round objection to leaving legal folded into `feasibility`.

**Content design — reversed from round 2's attribution.** Round 2 attributed content design/UX writing into `ux-research` (same flow/screen deliverable in practice). The owner's feedback explicitly names content design as an expected promotion (distinct lens: language, not interaction) — reversed to `content-design` this round.

**Track A/B split is the actual cost-control answer to "35 roles at once."** Standing up 35 `roles/*.json` + skeletons (Track A) is a fixed, one-time, mechanical cost. Writing 35 fully-fleshed rulebooks up front is not attempted — Track B defers rulebook depth to first real invocation, so the ongoing authoring cost tracks actual issue demand even though the role and its trigger condition exist from day one.

**`test-authoring` vs `qa`/`review`/`verify` — overlap risk, addressed.** Round 4 promotes `test-authoring` (Meszaros *xUnit Test Patterns*) out of `coding`, and it sits closest to the three existing method roles of anything promoted so far, so it needs an explicit boundary rather than an implicit one. The three method roles are epistemic *methods applied to already-produced artifacts*: `qa` observes a running system's actual behavior (실행 시 실제 동작 — direct execution), `review` audits a produced artifact against its spec claim-by-claim (Present/Surface/Absent/Incorrect/Unverifiable), `verify` independently reproduces a disputed defect. None of the three write or design test code — they consume it (`qa` runs it as an execution surface; `review` might audit it as one produced artifact among others) or ignore it entirely (`verify` reproduces bugs directly, with or without a test suite). `test-authoring` is upstream and authorial: it decides whether the test *code itself* is well-designed — isolated, fixture-strategy-sound, free of the smells Meszaros catalogs — the same way `refactoring-legacy` decides whether *production* code is well-restructured. The risk case to watch is a PR that touches both new test code and its execution results: `test-authoring` should review the suite's design (before or independent of a run), `qa` should observe an actual run's pass/fail, and neither role's `use_when` should be written broadly enough to swallow the other — `test-authoring`'s `use_when` is scoped to test suite design/authoring points (new suite scaffolding, fixture refactors), not "every time tests run," which stays `qa`'s trigger exclusively.
