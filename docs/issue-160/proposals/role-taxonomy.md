# Proposal — target role taxonomy (issue-160)

files: docs/issue-160/reports/coding/survey.md, docs/issue-160/reports/coding/scout-brief.md, docs/issue-160/proposals/role-taxonomy.md (this file). No src/, no roles/*.json edits — this is a design document only; role/system changes execute in a separate issue after owner approval, per the issue's own instruction.

## Request (paraphrased)
Re-derive the role system from the principle "one role = one professional domain at book/course granularity — a domain with a clear lens, required deliverables, and named patterns, orthogonal enough to run in parallel with other roles" — rather than the current lifecycle-stage split.

Round 5 (this revision): PR #161's fifth feedback requires two things across all 43 roles: (1) rename every role whose scope narrowed or whose old name no longer predicts its `decides` — "이름만 읽어도 decides가 예측되는" is the test; (2) make the boundary between adjacent roles concrete — 2+ real "this decision goes here, that similar-looking one goes there" examples per row, a required-field list for `produces` (record-fields-gate level), and an explicit hand-off rule naming which role a discovery-beyond-scope routes to.

## Constraints
- Proposal only — no `roles/*.json` edits, no migration execution.
- Every role name must pass the predictive-name test; every row must carry ≥2 boundary-case examples, a produces required-field list, and a hand-off target.
- Where a boundary case turns out not to be draftable (two roles keep colliding on the same decision), that is itself a finding — merge or re-write `decides`, do not paper over it with prose.

## What will be done

### Renaming pass — full audit

Every one of the 43 roles was re-read against the predictive-name test (`이름만 읽어도 decides가 예측되는가`). Renamed where the old name lied about scope (9 roles); kept as-is where the name already predicts `decides` (34 roles — reasoning noted per cluster below, not repeated per row).

| Old name | New name | Why renamed |
|---|---|---|
| `product` | `product-discovery` | narrowed to Cagan value-hypothesis discovery only; `product` alone reads as "owns the whole product," which is no longer true after user-discovery/requirements-engineering split out |
| `ux-research` (was `ux-design`) | `interaction-design` | `decides` is screen/flow shape, not research method — "research" wrongly predicts an investigative produces (interview notes), not a flow spec |
| `coding` | `implementation` | narrowed to net-new implementation only; refactoring-legacy and test-authoring now own the other two `decides` that "coding" used to cover |
| `feasibility` | `technical-feasibility` | narrowed twice (threat-model, then legal split out); bare "feasibility" now over-predicts scope against `legal-compliance`/`risk-management`, which also answer feasibility-shaped questions in their own domains |
| `qa` | `execution-observation` | `decides` is "does it actually run this way" (direct execution) — "qa" is a department name, not a decides-predictive label, and collides in readers' heads with `test-authoring`/`secure-coding`, which also produce quality artifacts but never execute anything |
| `review` | `conformance-review` | `decides` is claim-by-claim spec conformance, not general code review — bare "review" invites confusion with `test-authoring`'s suite-design review |
| `verify` | `defect-verification` | `decides` is independent reproduction of a disputed defect specifically, not verification in general |
| `ops` | `release-engineering` | narrowed to release/rollout only; observability/incident-postmortem/capacity-planning now own the other three `decides` "ops" used to bundle |
| `reflect` | `issue-retrospective` | narrowed to single-issue retro; knowledge-management now owns the org-level accumulation `decides` that "reflect" ambiguously covered |

Kept as-is (name already decides-predictive, audited not to need a change): `market-analysis`, `ux-engineering`, `api-design`, `architecture`, `security-threat-model`, `legal-compliance`, `data-modeling`, `performance-engineering`, `accessibility`, `secure-coding`, `ml-engineering`, `data-engineering`, `technical-writing`, `finance-unit-economics`, `pricing`, `sales`, `marketing`, `growth-analytics`, `customer-support`, `partnerships-bd`, `pr-communications`, `risk-management`, `brand-design`, `content-design`, `localization`, `devrel`, `user-discovery`, `requirements-engineering`, `refactoring-legacy`, `test-authoring`, `observability`, `incident-response`, `capacity-planning`, `knowledge-management` — each was promoted this cycle with a `decides` written *to* the name already (e.g. `api-design`'s decides is literally interface shape), so no lie to correct.

Everywhere below, "Target role" is the renamed (post-round-5) name; the original-9 table also lists the round-3/4 name it supersedes.

### Kept/renamed from the original 9

| Target role | decides | use_when | produces (required fields) | write_scope | hand-off |
|---|---|---|---|---|---|
| `product-discovery` (was `product`) | 무엇을 만들지 — 가치 가설 (Cagan discovery) | 요구가 문제/가설 수준일 때 | hypothesis statement, target user/JTBD, evidence log, confidence level, next-decision trigger | [] | 가설이 검증 가능한 수준으로 명세화되면 → `requirements-engineering`; 인터뷰가 더 필요하면 → `user-discovery`; 경쟁 구도가 걸리면 → `market-analysis` |
| `interaction-design` (was `ux-research`/`ux-design`) | 문제 → 화면·플로우 | product 스펙 확정 후 | wireframe/flow diagram, state list, edge-case interaction notes, open design questions | [] | 카피/마이크로카피 결정이 나오면 → `content-design`; 토큰화가 필요한 규모가 되면 → `ux-engineering`; 색상/인터랙션이 새 패턴이면 → `accessibility` |
| `implementation` (was `coding`) | 승인된 범위 → 동작 코드 (신규 구현) | 스펙/제안 승인 후 신규 구현 | src/·test/ diff, what-did-not-work log, closed_checks entries | `src/**`, `test/**` | 기존 코드를 고쳐야 하면(신규 아님) → `refactoring-legacy`; 테스트 스위트 설계 자체가 걸리면 → `test-authoring`; API 표면이 여럿에게 걸리면 → `api-design` |
| `technical-feasibility` (was `feasibility`) | 기술적으로 되는가 | 기술 PoC가 필요할 때 | go\|no-go\|conditional verdict, PoC code/measurement, assumptions list | [] | 신뢰 경계/인증이 걸리면 → `security-threat-model`; 법·규제가 걸리면 → `legal-compliance`; 전사 리스크 노출이면 → `risk-management` |
| `execution-observation` (was `qa`) | 실행 시 실제 동작 | 실행 가능 산출물 랜딩 시 | evidence-cited pass/fail/blocked per claim, run command/log reference | [] | 결함이 다투어지면(재현 요청) → `defect-verification`; 테스트 스위트 설계 결함이면 → `test-authoring`; 스펙 자체가 틀렸다고 의심되면 → `review`/`conformance-review` |
| `conformance-review` (was `review`) | 산출물 vs 명세 일치 | coding/implementation 커밋 랜딩 후 | Present\|Surface\|Absent\|Incorrect\|Unverifiable per claim, cited evidence | [] | 실행 결과 자체가 궁금하면 → `execution-observation`; 결함 실재가 다투어지면 → `defect-verification` |
| `defect-verification` (was `verify`) | 결함 실재 — 독립 재현 | 실행 결과가 다투어질 때 | reproduced\|not-reproduced verdict, repro steps/script, environment notes | [] | 재현됐고 원인이 설계 결함이면 → `architecture`/해당 domain role; 재현 안 됐고 관측 부족이면 → `observability` |
| `release-engineering` (was `ops`) | 배포 가능한가 (릴리스/롤아웃) | 머지 후 배포 시 | rollout checklist, rollback plan, go/no-go verdict | [] | 계측 부족이 드러나면 → `observability`; 배포 후 장애면 → `incident-response`; 용량 문제면 → `capacity-planning` |
| `issue-retrospective` (was `reflect`) | 이슈 역사가 무엇을 가르치는가 (단일 이슈 회고) | verify/review 종결 후 | timeline, lessons list, one-line advisory per lesson | [] | 여러 이슈에 걸친 패턴이 보이면 → `knowledge-management` |

### 26 promoted roles (round 3), renamed pass applied

| Target role | decides | use_when | produces (required fields) | write_scope | hand-off |
|---|---|---|---|---|---|
| `market-analysis` | 경쟁 구도에서 이 스펙이 서는가 | product 스펙 확정 후, 경쟁 구도가 걸린 결정일 때 | five-forces summary, competitor list w/ evidence links, JTBD-landscape verdict | [] | 가격 정책이 걸리면 → `pricing`; 포지셔닝 메시지가 걸리면 → `marketing` |
| `ux-engineering` | 디자인 결정 → 토큰/규칙 시스템화 | 화면 스펙이 여러 개 쌓여 시스템화가 필요할 때 | token set (name/value/usage), rule doc, migration note for existing screens | design-system source paths (TBD at execution) | 브랜드 정체성 결정이 필요하면 → `brand-design`; 접근성 기준 미달이면 → `accessibility` |
| `api-design` | 서비스 경계의 인터페이스 형태 | 여러 소비자가 걸리는 API 표면을 설계/변경할 때 | interface spec (endpoints/schema/versioning), lifecycle/deprecation plan | interface/schema paths (TBD at execution) | 컴포넌트 경계 자체가 바뀌면 → `architecture`; 스키마 신설/변경이면 → `data-modeling` |
| `architecture` | 컴포넌트 경계·의존 방향 | 새 모듈 경계나 기존 경계 변경이 걸릴 때 | ADR (context/decision/consequences), boundary diagram | `docs/issue-<n>/decisions/**` | 인터페이스 형태 세부는 → `api-design`; 성능 예산이 걸리면 → `performance-engineering` |
| `security-threat-model` | 신뢰 경계의 위협 표면 | 스펙에 신뢰 경계·인증·민감데이터가 걸릴 때 | STRIDE table, mitigation list per threat, residual risk note | [] | 구현 단계 취약점 점검은 → `secure-coding`; 법적 노출이면 → `legal-compliance` |
| `legal-compliance` | 이 스펙/처리가 법·규제를 통과하는가 | 개인정보·라이선스·계약이 걸릴 때 | compliance verdict, applicable regulation list, required mitigations | [] | 전사 리스크 노출 규모 판단은 → `risk-management` |
| `data-modeling` | 데이터를 어떤 관계/스키마로 모델링할지 | 스키마 신설/변경이 걸릴 때 | schema/ERD, migration plan, normalization rationale | `src/**` migrations | 파이프라인 이동/변환이 걸리면 → `data-engineering` |
| `performance-engineering` | 부하/지연 목표를 만족하는가 | 성능 예산이 걸린 설계/회귀일 때 | performance budget, profiling evidence, bottleneck list | [] | 용량 증설 타이밍이 걸리면 → `capacity-planning` |
| `accessibility` | 화면/토큰이 WCAG를 만족하는가 | 신규 인터랙션 패턴·색상 토큰 도입 시 | WCAG success-criterion checklist w/ pass/fail per criterion | [] | 카피 자체의 이해 가능성이면 → `content-design` |
| `secure-coding` | 구현이 공격에 견디는가 | 인증/입력처리 코드 랜딩 후 | ASVS checklist, pentest finding list w/ severity | [] | 설계 단계 위협표면 재검토가 필요하면 → `security-threat-model` |
| `ml-engineering` | 모델을 서비스로 안정적으로 서빙 가능한가 | 모델 서빙 표면이 걸릴 때 | serving design, risk note (drift/latency/failure mode) | [] | 학습 데이터 파이프라인이면 → `data-engineering` |
| `data-engineering` | 파이프라인이 데이터를 안정적으로 이동·변환하는가 | 파이프라인 신설/변경이 걸릴 때 | pipeline design, data-quality check list, failure-handling plan | [] | 스키마 설계 자체는 → `data-modeling` |
| `technical-writing` | 독자가 알아야 할 것을 어떻게 구조화할지 | 외부 공개 문서가 필요할 때 | doc outline, draft, target-reader note | `docs/**` (외부공개 한정) | 개발자 대상 온보딩이면 → `devrel` |
| `finance-unit-economics` | 단위경제상 성립하는가 | 가격/비용 구조가 걸린 결정일 때 | unit economics model (CAC/LTV/margin), sensitivity note | [] | 실제 가격 숫자 결정은 → `pricing` |
| `pricing` | 얼마를, 어떤 구조로 받을지 | 신규 가격 정책이 걸릴 때 | pricing verdict, tier structure, rationale vs alternatives considered | [] | 단위경제 성립 여부 재확인은 → `finance-unit-economics` |
| `sales` | 리드/기회를 어떻게 진행시킬지 | 영업 프로세스 설계가 걸릴 때 | sales playbook, stage definitions, qualification criteria | [] | 메시지/포지셔닝 자체는 → `marketing` |
| `marketing` | 어떤 메시지로 어떤 채널에 도달할지 | 캠페인/포지셔닝이 걸릴 때 | messaging doc, channel plan, target segment | [] | 퍼널 성과 해석은 → `growth-analytics` |
| `growth-analytics` | 퍼널 병목과 실험 결과가 실제 개선인지 | 퍼널 분석 또는 A/B 실험 해석이 걸릴 때 | funnel diagnosis, experiment trust verdict (SRM/pre-registration check) | [] | 캠페인 메시지 변경이 필요하면 → `marketing` |
| `customer-support` | 문의를 어떤 우선순위/SLA로 처리할지 | CS 플로우/SLA 설계가 걸릴 때 | support playbook, SLA table, escalation path | [] | 반복 문의가 제품 결함이면 → `product-discovery` |
| `partnerships-bd` | 파트너십이 구조적으로 성립하는가 | 제휴/BD 딜 구조가 걸릴 때 | deal structure verdict, term sheet outline | [] | 법적 계약 검토는 → `legal-compliance` |
| `pr-communications` | 메시지가 외부에 어떻게 읽힐지 | 외부 커뮤니케이션이 걸릴 때 | communications plan, key message, risk/Q&A prep | [] | 캠페인 성격 메시지는 → `marketing` |
| `risk-management` | 전사 리스크 노출이 허용 범위인가 | 재무/운영/전략 리스크가 걸릴 때 (feasibility보다 넓은 범위) | ERM verdict, risk register entry, mitigation owner | [] | 개별 법규 컴플라이언스 세부는 → `legal-compliance` |
| `brand-design` | 브랜드 정체성이 시각적으로 일관되는가 | 브랜드 자산 신설/변경이 걸릴 때 | brand guide entry, asset spec, consistency check vs existing guide | design-system source paths | 토큰 시스템화 구현은 → `ux-engineering` |
| `content-design` | 문구가 사용자의 실제 결정을 돕는가 | 플로우에 새 카피/마이크로카피가 걸릴 때 | copy draft, rationale per string, A/B alternative (if applicable) | [] | 화면/플로우 구조 자체가 바뀌어야 하면 → `interaction-design` |
| `localization` | 다른 로케일에서도 산출물이 성립하는가 | i18n 대상 표면이 걸릴 때 | locale-fitness verdict per target locale, string-external issue list | [] | 카피 원문 자체를 다시 써야 하면 → `content-design` |
| `devrel` | 외부 개발자가 이 표면을 채택할 수 있는가 | 외부 개발자 대상 API/SDK가 걸릴 때 | onboarding doc, sample code, adoption-friction list | `docs/**` (외부 개발자 한정) | API 표면 자체 재설계는 → `api-design` |

### 8 promoted roles (round 4), renamed pass applied

| Target role | decides | use_when | produces (required fields) | write_scope | hand-off |
|---|---|---|---|---|---|
| `user-discovery` | 이 문제가 실제 사용자의 고통인가 | 가설 검증을 위해 사용자 인터뷰가 필요할 때 | interview script, per-interview evidence log, pain-confirmed\|not-confirmed verdict | [] | 검증된 가설을 스펙화하면 → `requirements-engineering` |
| `requirements-engineering` | 요구사항이 검증가능·일관·추적 가능하게 명세되었는가 | product 가설이 확정되어 정식 스펙으로 전환할 때 | structured requirements doc, traceability matrix, ambiguity list resolved | [] | 화면/플로우 설계는 → `interaction-design` |
| `refactoring-legacy` | 기존 코드의 관찰 가능한 동작을 바꾸지 않고 안전하게 재구조화할 수 있는가 | 레거시/기존 코드에 손을 대야 할 때 | refactoring plan, characterization tests, before/after behavior-equivalence note | `src/**`, `test/**` | 신규 기능 구현이 섞이면 그 부분은 → `implementation` |
| `test-authoring` | 테스트 코드 자체가 격리성·fixture 전략 면에서 좋은 설계인가 | 신규/기존 테스트 스위트를 설계·리뷰할 때 | suite architecture note, fixture strategy, smell list (Meszaros catalog refs) | `test/**` | 실제 실행 결과 관찰은 → `execution-observation` |
| `observability` | 프로덕션 내부 상태에 대해 사전에 정의하지 않은 질문도 던질 수 있는가 | 신규 서비스/경로에 계측이 필요할 때 | telemetry/instrumentation design, cardinality budget, dashboard/query examples | [] | 장애가 실제로 발생하면 → `incident-response` |
| `incident-response` | 장애 후 무엇을 배웠고 재발을 무엇으로 막을 것인가 | 장애 종결 직후 | timeline, blameless postmortem, action items w/ owner+deadline | `docs/issue-<n>/postmortems/**` | 용량 부족이 원인이면 → `capacity-planning`; 계측 부재가 원인이면 → `observability` |
| `capacity-planning` | 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가 | 용량 예측/증설 시점 결정이 걸릴 때 | capacity forecast, expansion trigger thresholds, cost note | [] | 성능 자체의 병목 원인 분석은 → `performance-engineering` |
| `knowledge-management` | 개별 이슈의 교훈이 조직 차원에서 재사용 가능한 형태로 축적·색인되는가 | 여러 이슈의 회고가 쌓여 지식 큐레이션이 필요할 때 | curated pattern-library entry, cross-issue index, supersession note (if replacing an older pattern) | `docs/patterns/**` | 단일 이슈 회고 자체는 → `issue-retrospective` |

Net role count unchanged from round 4: **43 roles** (round 5 is a naming + specificity pass only, no promotion/attribution changes).

### Boundary-case deep dives — the six adjacent clusters PR #161 named

**`implementation` ↔ `refactoring-legacy` ↔ `test-authoring`**
- "Add a new endpoint with new handler code" → `implementation` (net-new; nothing pre-existing changes shape).
- "Extract a shared helper out of two existing handlers without changing their behavior" → `refactoring-legacy` (behavior-preserving restructure of existing code).
- "The new endpoint's test suite needs a shared fixture strategy decided before writing tests" → `test-authoring` (the decision is about test suite design, not the endpoint code).
- Collision check: a PR that both adds a new endpoint AND restructures its test fixtures splits into two `decides` — `implementation` owns the handler, `test-authoring` owns the fixture strategy; they do not merge because the produces differ (src diff vs. suite architecture note).

**`release-engineering` four siblings (`release-engineering`/`observability`/`incident-response`/`capacity-planning`)**
- "Is this build safe to roll out now" → `release-engineering`.
- "We rolled out fine but can't tell if the new code path is actually healthy in prod" → `observability` (instrumentation gap, not a rollout decision).
- "Prod broke after rollout, need blameless writeup" → `incident-response`.
- "Traffic is trending toward exhausting DB connections in 6 weeks" → `capacity-planning` (no incident yet, purely forward-looking).
- Collision check: an incident caused by insufficient telemetry hands off from `incident-response` to `observability` for the fix — the postmortem's action item names the target role, it does not absorb the observability work itself.

**`product-discovery` three siblings (`product-discovery`/`user-discovery`/`requirements-engineering`)**
- "We think there's a problem worth solving but haven't confirmed it hurts real users" → `product-discovery` frames the hypothesis, then hands to `user-discovery` to confirm via interviews.
- "We ran interviews; users confirmed the pain in their own words" → `user-discovery`'s produces (evidence log).
- "The confirmed hypothesis needs to become an unambiguous, testable spec with a traceability matrix" → `requirements-engineering`.
- Collision check: `product-discovery` never writes interview scripts (that's `user-discovery`'s produces) and never writes traceability matrices (that's `requirements-engineering`'s) — if a `product-discovery` record starts containing either, that's a scope leak to fix by hand-off, not a reason to fold the roles back together.

**`execution-observation` ↔ `defect-verification` ↔ `secure-coding`**
- "Does this feature work when I run it right now" → `execution-observation`.
- "QA and the author disagree about whether a reported bug actually reproduces" → `defect-verification` (independent re-execution of a disputed claim).
- "Does the auth code resist a specific attack class (e.g. timing attack on token comparison)" → `secure-coding` (adversarial lens, not functional-correctness lens — same code, different question).
- Collision check: `execution-observation` and `secure-coding` can both run the same binary and produce different verdicts because they ask different questions (does it work vs. can it be broken) — this is intentional orthogonality, not overlap needing a merge.

**`interaction-design` ↔ `content-design` ↔ `accessibility`**
- "What screens and states does this flow need" → `interaction-design`.
- "What should the button/error text actually say" → `content-design`.
- "Does the color contrast/keyboard nav on this new screen meet WCAG" → `accessibility`.
- Collision check: a new modal with a new color token and new copy touches all three — `interaction-design` owns the modal's states/flow, `content-design` owns its copy, `accessibility` owns its contrast/nav compliance; each role's produces is a distinct artifact (flow diagram vs. copy draft vs. WCAG checklist), so none subsumes another even on the same UI surface.

**`architecture` ↔ `api-design` ↔ `data-modeling`**
- "Should this be one service or two, and which one owns X" → `architecture`.
- "Given the service boundary is settled, what does the request/response shape and versioning look like" → `api-design`.
- "What's the schema/relations for the data this service persists" → `data-modeling`.
- Collision check: `architecture` decides *whether* a boundary exists; `api-design` decides the *shape* of an already-agreed boundary; `data-modeling` decides *storage* structure independent of either — a schema change alone (no new boundary, no new external interface) stays `data-modeling` only.

## Out of scope
- Any `roles/*.json` edit, hook change, or contract-doc update — execution is a separate issue, after owner sign-off. This document proposes the target shape, naming, and migration path only.
- Deciding execution *order* across the 34 non-original roles beyond the two-track split below — sequencing/prioritization is an execution-issue call, not this proposal's.
- Backfilling boundary cases for adjacent pairs PR #161 did not name — the six clusters above are the ones checked this round; other pairs (e.g. `pricing`↔`finance-unit-economics`, already covered by hand-off rows) rely on the table's hand-off column rather than a prose deep dive.

## Migration path — two tracks, unchanged from round 4, renamed roles carried through

**Track A — bulk `roles/*.json` + rulebook skeleton, all 43 at once**, using the round-5 names as the file/branch identifier (`roles/product-discovery.json`, not `roles/product.json`) so no role is ever stood up under a name that will need renaming later.

**Track B — gradual rulebook depth**, filled in as each role is first invoked, unchanged from round 4's rationale.

### Rulebook repo naming convention (round 6, per PR #161's sixth feedback)

**Convention: `<role-name>-rulebook`** — drop `agent` entirely, use the round-5 role name. Applies to every rulebook repo, existing and new; Track A stands up the 34 net-new roles' repos already named this way (`user-discovery-rulebook`, not `user-discovery-agent-rulebook`), so this section covers only the 9 existing repos, which need an actual GitHub rename plus reference updates.

**(a) Rename mapping — existing 9 repos:**

| Current repo | New name | Note |
|---|---|---|
| `tokenmaxxxer/coding-agent-rulebook` | `tokenmaxxxer/implementation-rulebook` | role renamed `coding`→`implementation` |
| `tokenmaxxxer/qa-agent-rulebook` | `tokenmaxxxer/execution-observation-rulebook` | role renamed `qa`→`execution-observation` |
| `tokenmaxxxer/ops-agent-rulebook` | `tokenmaxxxer/release-engineering-rulebook` | role renamed `ops`→`release-engineering` |
| `tokenmaxxxer/verify-agent-rulebook` | `tokenmaxxxer/defect-verification-rulebook` | role renamed `verify`→`defect-verification` |
| `tokenmaxxxer/review-agent-rulebook` | `tokenmaxxxer/conformance-review-rulebook` | role renamed `review`→`conformance-review` |
| `tokenmaxxxer/reflect-agent-rulebook` | `tokenmaxxxer/issue-retrospective-rulebook` | role renamed `reflect`→`issue-retrospective` |
| `tokenmaxxxer/product-agent-rulebook` | `tokenmaxxxer/product-discovery-rulebook` | role renamed `product`→`product-discovery` |
| `tokenmaxxxer/feasibility-agent-rulebook` | `tokenmaxxxer/technical-feasibility-rulebook` | role renamed `feasibility`→`technical-feasibility` |
| `tokenmaxxxer/ux-design-rulebook` | `tokenmaxxxer/interaction-design-rulebook` | role renamed `ux-research`/`ux-design`→`interaction-design`; already lacked `agent`, still renamed to track the role rename |

GitHub repo renames leave the old URL as a redirect, but every hardcoded reference below must still be updated — the redirect is a safety net for stragglers, not a substitute for updating call sites.

**(b) Impact list — sites that depend on the naming convention:**

- `roles/*.json` (9 files) — each role's `"repo"` and `"path"` fields (`spawn.py:3-4` pattern, e.g. `roles/coding.json`) hardcode the old repo name and the `$TOKENMAXXXER_RULEBOOKS/<repo>` local-checkout path; both need updating to the new name, in lockstep with the file's own rename to `roles/<new-role-name>.json` (Track A).
- `.claude-plugin/marketplace.json` — every role's marketplace entries embed `"repo": "tokenmaxxxer/<old-name>-agent-rulebook"` per plugin block (multiple blocks per role, e.g. 9 occurrences for `coding-agent-rulebook` alone); all need the new repo name.
- `spawn.py` — `rulebook_source()`, `rulebook_checkout()`, `ensure_rulebook()` (spawn.py:141-291) read `spec["repo"]`/`spec["path"]` from the role JSON at runtime and do not hardcode repo names themselves, so no code change is needed there — but they will clone whatever `roles/*.json` says, so a stale role file silently points at a now-renamed (redirected) repo until updated.
- Any prose doc referencing a rulebook repo by name (e.g. onboarding/setup docs, `docs/handbooks/*`, `README.md`) — not enumerated here since execution is a separate issue; that issue's write set must grep for `-agent-rulebook` and each old bare name to find every prose mention before landing the rename.

This section is proposal text only — no repo rename, no `roles/*.json`/`marketplace.json` edit happens in this PR; both land in the execution issue per this proposal's existing scope boundary.

## Side-effect analysis
Unchanged from round 4 on orchestration cost and the briefing-cost-vs-work-cost pathology (`use_when` remains the sole lever, not role count) — see [[survey]] §4e and the round-4 side-effect text this document previously carried. This round's addition:

**Renaming cost is one-time and mechanical, paid at Track A.** Because Track A stands up all 43 `roles/*.json` files in one pass (never renamed in place after demand arrives), the round-5 renames cost nothing beyond choosing the right name before that pass runs — there is no in-flight rename of a role with existing issue history to worry about, since no role has executed yet.

**Boundary-case documentation reduces future judgment burden, not increases it.** The six deep dives above exist so that a human approving an issue's role routing (or an agent generating one) can pattern-match against a worked example instead of re-deriving the `decides` distinction from scratch each time — this is the same "briefing cost > work cost" control the owner named, applied to the human's routing decision rather than to role count.
