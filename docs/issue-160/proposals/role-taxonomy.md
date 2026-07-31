# Proposal — target role taxonomy (issue-160)

files: docs/issue-160/reports/coding/survey.md, docs/issue-160/reports/coding/scout-brief.md, docs/issue-160/proposals/role-taxonomy.md (this file). No src/, no roles/*.json edits — this is a design document only; role/system changes execute in a separate issue after owner approval, per the issue's own instruction.

## Request (paraphrased)
Re-derive the role system from the principle "one role = one professional domain at book/course granularity — a domain with a clear lens, required deliverables, and named patterns, orthogonal enough to run in parallel with other roles" — rather than the current lifecycle-stage split. Survey the domain map (must include UX engineering/tokens, competitive analysis, coding, API design), map the current 9 roles onto it, and propose a target system plus a side-effect analysis. Design only; no execution.

## Constraints
- Proposal only — no `roles/*.json` edits, no migration execution.
- Must anchor every proposed role's required-deliverable shape to a named domain pattern (book/methodology), per [[survey]] and [[scout-brief]].
- Must address orchestration-cost/judgment-burden side effects of adding roles, and the "briefing cost > work cost" pathology when domains are sliced too fine.

## What will be done
Target role system below. Each row: `decides` / `use_when` / `produces` (with domain-pattern anchor) / `write_scope` / migration path from the current 9.

| Target role | decides | use_when | produces (anchor) | write_scope | Migration |
|---|---|---|---|---|---|
| `product` | 무엇을 만들지 — 가치 가설 | 요구가 문제/가설 수준일 때 | hypothesis, spec (Cagan/JTBD discovery pattern) | [] | **keep**, scope narrowed: drop implicit market-analysis expectation, hand it to `market-analysis` |
| `market-analysis` *(new)* | 경쟁·시장에서 이 스펙이 서는가 | product 스펙이 나온 뒤, 경쟁 구도가 걸린 결정일 때 | five-forces + JTBD-landscape verdict (Porter anchor) | [] | **new** — split out of `product`'s unnamed domain-2 gap |
| `ux-research` | 문제가 화면·플로우로 어떻게 구현될지 | product 스펙 확정 후 | screen/flow/wireframe spec (NN/Cooper anchor) | [] | **keep** = current `ux-design`, renamed to disambiguate from the new UX-engineering role |
| `ux-engineering` *(new)* | 디자인 결정을 토큰·규칙으로 시스템화 | 화면 스펙이 여러 개 쌓여 재사용 가능한 시스템이 필요할 때 | design token set + programmatic design rules (Design Tokens Book / Material token classes anchor) | design system source paths (TBD at execution) | **new** — split out of the domain-4 gap named explicitly in the issue |
| `api-design` *(new)* | 서비스 경계가 어떤 인터페이스로 노출될지 | 여러 소비자가 걸리는 API 표면을 설계/변경할 때 | interface spec + versioning/lifecycle plan (RESTful API Design Patterns anchor) | interface/schema definition paths (TBD at execution) | **new** — split out of the domain-5 gap; narrow trigger ("여러 소비자") to avoid firing on every internal function signature |
| `coding` | 승인된 범위 → 동작 코드 | 스펙/제안 승인 후 구현 | src/·test/ 코드 (Code Complete/Clean Code anchor) | `src/**`, `test/**` | **keep**, unchanged — API-design decisions now arrive pre-made from `api-design` rather than folded silently in |
| `security-threat-model` *(new)* | 이 설계의 위협 표면이 무엇인가 | 스펙에 신뢰 경계·인증·민감데이터가 걸릴 때 | STRIDE-style threat model + mitigation list (Shostack anchor) | [] | **split from `feasibility`** |
| `feasibility` | 기술적으로 되는가·법적으로 되는가 | 기술 PoC 또는 법/규제 리스크가 있을 때 | go\|no-go\|conditional + PoC 측정 (build-vs-buy practitioner consensus) | [] | **keep, narrowed** — threat-model probe removed (now `security-threat-model`); legal/regulatory sub-probe stays merged here (no separably strong literature/lens yet — see side-effects) |
| `qa` | 실행 시 실제 동작 | 실행 가능 산출물 랜딩 시 | evidence-cited pass/fail/blocked | [] | **keep** — reclassified explicitly as a *method* role (cross-domain execution-observation), not a domain role; kept because parallel/orthogonal execution against any domain's output is exactly the property the issue's separation principle asks for |
| `review` | 산출물 vs 명세 일치 | coding 커밋 랜딩 후 | Present\|Surface\|Absent\|Incorrect\|Unverifiable | [] | **keep** — same reclassification as `qa` |
| `verify` | 결함 실재 — 독립 재현 | 실행 결과가 다투어질 때 | reproduced\|not-reproduced + evidence | [] | **keep** — same reclassification |
| `ops` | 배포 가능·계속 동작 | 머지 후 롤아웃/장애 후 | rollout checklist, postmortem (SRE workbook anchor) | [] | **keep**, unsplit — rollout and postmortem share one literature lineage (SRE workbook treats both), so this bundling is NOT the same pathology as `feasibility`'s three-domain bundle |
| `reflect` | 이슈 역사가 무엇을 가르치는가 | verify/review 종결 후 | advisory lessons (retrospective anchor) | [] | **keep**, unchanged |

Net change: 9 roles → 13 roles (+4: `market-analysis`, `ux-engineering`, `api-design`, `security-threat-model`), 3 renamed/reclassified in meaning only (`qa`/`review`/`verify` labeled explicitly as method roles), `ux-design` renamed `ux-research`, `feasibility` narrowed.

## Out of scope
- Data/analytics engineering and technical-writing domains (survey rows 17-18) — flagged as map gaps but not proposed as new roles; no current role claims them and the issue's 4 seed examples don't include them.
- Any `roles/*.json` edit, hook change, or contract-doc update — execution issue only, after owner sign-off.
- Legal/regulatory split from `feasibility` — considered and rejected for this proposal (see side-effects: no distinct practitioner literature strong enough yet to justify a fourth split there).

## Side-effect analysis
**Orchestration/judgment cost of +4 roles.** Every new role is a branch (`issue-<n>/<role>`), a PR, and a human-approval gate (contract v3 s19) — going from 9 to 13 roles means up to 13 sequential/parallel approval round-trips per feature that touches all of them, versus 9 today. For a typical feature this issue's principle is meant to help with (new UI surface + new API + new backend logic), the realistic role chain grows from `product → ux-design → coding → qa/review/verify → ops` (5-6 hops) to `product → market-analysis → ux-research → ux-engineering → api-design → security-threat-model → coding → qa/review/verify → ops` (9-10 hops) — a first-order thoroughness gain to inspect trades directly against turnaround time and the number of judgment calls a human approver must make ("does this PR's domain boundary actually apply here, or should it be skipped").

**Pathology check — briefing cost > work cost.** The domain-map granularity chosen here (one book/course per domain) keeps each new role's `use_when` narrow enough to skip on most issues: `api-design` only fires when "여러 소비자가 걸리는" (multiple consumers) — an internal-only function change never invokes it, keeping the coding role's default path unchanged. `security-threat-model` only fires when trust boundaries/auth/sensitive data are touched. `market-analysis` only fires post-product-spec, not per issue. This is the design lever against over-fine slicing: if any of these three roles start firing on issues too small for a full domain-lens brief (a one-line bugfix, a copy change), that role's `use_when` should tighten further — narrowing the trigger, not merging the role back, unless usage data over several issues shows near-zero independent value (i.e. it always agrees with the role that would have decided it anyway).

**Why `ops` stays bundled but `feasibility` splits.** The domain map ([[survey]]) shows `ops`'s two sub-domains (release/rollout, incident/postmortem) share one named literature lineage end-to-end (SRE workbook covers both under "production reliability"), whereas `feasibility`'s three sub-domains (tech PoC, legal/regulatory, security/threat-model) have three separate literatures with no natural single text spanning all three — the split criterion is "does one canonical source already treat these as one domain," not "how many probes does the role currently run."
