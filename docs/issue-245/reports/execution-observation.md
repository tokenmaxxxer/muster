---
subject: issue-245
role: execution-observation
observed_role: implementation
observed_pr: 257
code_under_review: b3ba2343de3453522406a2d068246c482ee7ed6c
loop_state: landed
---

# Execution-observation record — issue #245, step 2

## Independence

이 역할은 관찰 대상 아티팩트의 어느 부분도 이 세션에서든 다른
세션에서든 저작·편집·실행하지 않았다. 아래의 모든 코드 인용은 `git show`
로 꺼낸 커밋 `b3ba2343d`(및 그 시점의 동결 의존물 `b3ba234:gates/pr_reference.py`)
의 블롭을 가리키며 작업 트리를 가리키지 않는다. `gates/ci.py`,
`gates/pr_reference.py`, `gates/test_closes_gate_ci.py`,
`.github/workflows/plan-aware-closes-gate.yml` 은 한 번도 실행하지
않았다 — 관찰 대상의 태스크를 재실행하지 않았고, CI 를 재실행하지
않았으며, 검증용 PR 을 만들지 않았고, 브랜치 보호 설정을 바꾸지 않았다
(`gh api .../branches/main/protection` 은 GET 만 했다).

이 브랜치가 쓰는 경로는 `docs/issue-245/reports/execution-observation.md`,
`docs/issue-245/reports/execution-observation/`,
`docs/issue-245/proposals/2026-08-04-execution-observation-plan.md` 뿐이다.
관찰 대상의 `src/`·`test/`·`docs/issue-245/reports/implementation*` 는
읽기만 했다. 아래 발견은 오직 여기로만 돌아간다 — 이슈를 만들지
않았고(계약 v3: 이슈는 사람만 저작한다), 관찰 대상의 쓰기 집합을 한 줄도
고치지 않았으며, 승인을 내리거나 중계하지 않았다.

여기서부터 판정이다.

## What was done

승인된 계획(`docs/issue-245/proposals/2026-08-04-execution-observation-plan.md`)
의 검사 항목 C1–C5 를 PR #257 이 실제로 산출한 아티팩트에 대고 수행하고,
이 역할에 요구되는 세 레벨(outcome / trajectory / step) 판정을 냈다.
추가로, 이슈 #245 에 달린 발주자의 추가 판정 항목(커밋 메시지 내 closing
키워드가 closes-gate 를 우회해 #262/#266 을 자동 종결시킨 사건의 존재·
범위·귀속)을 §추가 판정 항목에서 다뤘다. 관찰 대상 코드의 재실행은
없었다 — 계획의 Constraints 가 이미 금지한 바다.

## Why

이슈 #245 의 `## 실행 계획` 이 step 2 를 `execution-observation` 으로
두고 있고, step 1 은 `implementation` 역할이 PR #257 로 인도해
2026-08-04T02:04:01Z 에 머지됐다. 이 관찰의 phase 2 는 이슈 레벨 승인
코멘트(본문이 정확히 `APPROVE issue-245/execution-observation`, 작성자
`jjongkwann`, `gh issue view 245 --comments` 로 이 세션에서 확인)로
열렸고, 그 계정은 `docs/specs/approvers.md:2` 에 있다. PR #268 의
`reviews` 배열은 비어 있다(`gh pr view 268 --json reviews`) — 단일-계정
경로가 맞다.

## Upstream basis

- 이슈 #245 본문 — 요구사항 1/2/3 과 제약 2건, 그리고 승인 코멘트·추가
  판정 항목 코멘트(`gh issue view 245`, `--comments`, 이 세션).
- 관찰 대상 phase-1 커밋 `a8cddd9`("issue-245: phase 1 - survey + scout
  brief + proposal for enforced Closes-gate wiring", `git log a8cddd9 -1`).
- 관찰 대상 phase-2 커밋 `b3ba2343d` — `git show b3ba234 --stat`: 신규
  `.github/workflows/plan-aware-closes-gate.yml`(+49), `gates/ci.py`
  (+141), 신규 `gates/test_closes_gate_ci.py`(+173),
  `docs/handbooks/operations.md`(+32), 신규 결정 문서(+134), 신규 기록
  (+417). `gates/pr_reference.py` 는 이 커밋에 **없다**(stat 에 0 건) —
  이슈의 제약("판정 로직 무변경")이 지켜졌다.
- 관찰 대상 기록 `docs/issue-245/reports/implementation.md`(417행), 결정
  문서 `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`
  (134행), 승인된 제안 `docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`.
- 실측: `gh api repos/tokenmaxxxer/on-the-record/branches/main/protection`
  (GET, 이 세션), PR #263 의 CI 잡 로그 2건(`gh run view --log --job`),
  PR #257·#263·#265·#267 메타데이터/코멘트/체크 롤업, 이슈 #262·#266 의
  재오픈 코멘트, 커밋 `1c88e073e`·`be53d1eb`·`2f89d5a9b`·`247051e2a` 의
  메시지 원문(`git log -1 --format=%B`).

---

# 판정

세 레벨 모두 해당하며, 어느 레벨도 "해당 없음" 이 아니다.

## 1. Outcome — 이슈가 요구한 것이 랜딩됐는가

**요구사항 1(머지 전 강제 배선): 충족.** `b3ba234` 의 신규
`.github/workflows/plan-aware-closes-gate.yml` 은 `on: pull_request`
`types: [opened, edited, synchronize, reopened]`, `branches: [main]`
에서 잡 `closes-gate` 를 돌리고 마지막 스텝이
`python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only`
이다(같은 커밋의 워크플로 diff 전문). 그 체크는 지금 실제로 필수다 —
이 세션에서 GET 한 `gh api .../branches/main/protection` 이
`required_status_checks.contexts: ["closes-gate"]`,
`checks: [{"context":"closes-gate","app_id":15368}]`,
`enforce_admins.enabled: true`, `allow_force_pushes: false`,
`allow_deletions: false` 를 돌려준다. 이슈 본문이 "404" 로 기록한
상태에서 바뀌었고, 요구사항 1 이 커버리지 기준으로 요구한 "사람이 직접
만든 PR 도 잡는가" 는 서버사이드 필수 체크라는 성질상 병합 경로와
무관하게 성립한다(승인된 제안 `...-plan-aware-closes-gate-wiring.md:22`
가 후보 (a) 를 고른 근거와 같다). **단, "PR 본문에 실린 closing 키워드"
에 한해서다** — §추가 판정 항목 참조.

**요구사항 2(phase-1 "Closes 금지" 도 같은 배선에 태운다): 미충족
(강제 경로 기준).** `b3ba234` 의 `gates/ci.py` diff 에서 `_phase1_mismatch`
는 `check()` 의 `if phase == "phase1":` 분기 안에서만 호출된다. 그런데
배선된 호출은 `--issue` 도 `--phase` 도 주지 않으므로(위 워크플로 마지막
줄) phase 는 `_autodetect_issue_phase` → `_phase_from_body` 로 유도되고,
`_phase_from_body` 는 `_closes_ref_for_issue(body, issue)` 가 참일 때
정확히 `"phase2"` 를 돌려준다(같은 diff). `_phase1_mismatch` 가 무언가를
보고하려면 필요한 술어가 바로 그 `_closes_ref_for_issue(body, issue)`
이다(같은 diff). 즉 배선된 호출에서 이 검사는 **공허하다(vacuous)** —
실행되는 순간 그 술어는 구성상 항상 거짓이다. scout-brief 가 이 부류의
must-be 로 올린 "규칙이 존재가 아니라 발화 가능함의 증거"
(`docs/issue-245/reports/execution-observation/scout-brief.md`, GAP LINE
(i)) 에 정확히 걸리는 항목이다.

공허함이 실제 구멍으로 이어지는 지점도 diff 로 추적된다. 키워드가
있으면 제어는 동결된 phase-2 분기 `b3ba234:gates/pr_reference.py:39-56`
로 간다. 거기서 차단은 `incomplete and not only_last_incomplete` 일
때만 일어나고(`:46-50`), 남은 미완 스텝이 **마지막 하나뿐이면**
`only_last_incomplete` 가 참이라 제어는 `:52-56` 으로 떨어져 "closing
키워드가 있는가" 를 요구하는데 — 그 있으면 안 될 키워드가 바로 그
요구를 만족시켜 **통과**한다. 계획이 없는 이슈(plan 이 falsy)도 같은
`:52-56` 로 떨어진다. 따라서 *마지막 계획 스텝의 phase-1 제안 PR 이
`Closes #N` 을 실으면 강제 체크를 통과한다* — 공교롭게도 이 관찰 자신의
phase-1 PR #268(브랜치 `issue-245/execution-observation`, 2 스텝 중
마지막)이 정확히 그 형태다. 요구사항 2 가 막으라고 한 그 사건이 강제
경로에서 막히지 않는다.

**요구사항 3(배선 자체의 실물 회귀 확인): 충족 — 단, 관찰 대상이 아니라
사람이 수행.** 관찰 대상 기록은 이것을 스스로 "하지 않았다" 고 선언하고
절차를 넘겼다(`docs/issue-245/reports/implementation.md:90-141`, "What was
NOT done"; 승인된 제안 `:40` 이 이미 out of scope 로 둔 항목이다). 사람이
그 절차를 실행했고, 이 세션에서 잡 로그 원문으로 확인했다: PR #263 의
job 91872249829 — `PR_NUMBER: 263` → `게이트 차단:` →
`- 계획에 미완 스텝이 남아 있다 — 마지막 스텝의 phase-2 PR에서만
Closes/Fixes/Resolves를 쓴다.` → `##[error]Process completed with exit
code 1.`(02:06:54Z), 그리고 job 91878584150 — 같은 커맨드라인
(`Run python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only`),
`PR_NUMBER: 263`, `게이트 통과`(02:50:47Z). 양방향 실증이라는 이 부류의
must-be(scout-brief, Category must-bes 첫 항목)를 충족한다. 인도 경계가
사람에게 넘어간 것은 기록이 사전에 예고하고 절차까지 남긴 문서화된
이관이므로 결함으로 세지 않는다.

**Outcome 종합**: 이슈의 3개 요구사항 중 1·3 은 랜딩됐고, 2 는 코드로는
존재하나 강제 경로에서 발화하지 않는다. 즉 "배선은 섰고, 그 배선이 태우기로
한 규칙 하나가 배선 위에서 죽어 있다."

## 2. Trajectory — phase-1→phase-2 경로가 건전했는가

**건전하다 — 이탈 1건이 있으나 측정에 근거해 사전 공개됐다.**

- **scout / survey 선행**: phase-1 커밋 `a8cddd9`
  ("survey + scout brief + proposal", `git log a8cddd9 -1`)가 조사·scout
  브리프·제안을 함께 담았다. 순서(조사 → 제안)가 커밋 제목에 그대로
  드러나며, 제안 문서 `:27-29` 가 survey/scout-brief 를 자기 선행물로
  명시한다.
- **실제 사람 승인**: 이슈 코멘트 본문이 정확히
  `APPROVE issue-245/implementation`(작성자 `jjongkwann`, member,
  `gh issue view 245 --comments` 이 세션), 승인자 명단
  `docs/specs/approvers.md:2` 에 있음. PR #257 의 `reviews` 는 비어
  있으므로 단일-계정 경로(계약 v3 s19)가 맞다 — 봇/에이전트 승인 아님.
- **승인된 설계에서의 이탈(C5)**: 제안
  `...-plan-aware-closes-gate-wiring.md:31` 은 워크플로가
  `gates/ci.py --pr <n> --issue <n> --phase <phase1|phase2>` 전체 번들을
  돌리는 설계였고, 랜딩된 것은 `--autodetect --closes-only` 다(워크플로
  마지막 줄, `b3ba234`). 이탈 사유는 기록
  `docs/issue-245/reports/implementation.md:200-226` 에 "Rationale for
  deviations" 로 명시됐고, 그 근거는 추측이 아니라 실측이다 —
  `:143-167` 이 승인된 설계의 문자 그대로의 호출을 자기 PR #257 에
  드라이런해 `write_scope 이탈:
  docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`
  로 막히는 것을 기록했다. **그 전제가 사실이었음이 사후에 독립적으로
  확인된다**: 같은 결함이 이슈 #262 로 별도 제기됐고 PR #265 의 phase-2
  커밋 `1c88e073e` 가 `gates/gates.py` 의 글롭을 실제로 넓혔다
  (`git log 1c88e07 -1 --format=%B`, 이 세션). 이탈은 합리화가 아니라
  측정된 자기-잠금 회피였다.
- **범위 축소가 새 노출을 만들지 않았는가(C5 후반)**: `closes_only=True`
  가 건너뛰는 것은 `b3ba234` 의 `check()` diff 상
  protected-path/`role_scope`/`deps`/`record_*` 이고, 이들은 이전에도
  필수가 아니었다(이 커밋 이전에는 `.github/` 자체가 없었다는 것이 이슈
  #245 본문의 실측). 즉 축소는 "덜 걸었다" 이지 "있던 것을 껐다" 가
  아니다. 다만 기록이 이 축소를 Open findings 1번으로 남기며 후속
  경로까지 적었다(`:230-249`).
- **발주자 피드백 2건의 반영(C4)**: PR #257 코멘트 원문 2항목(이 세션
  `gh pr view 257 --comments` 로 읽음)이 결정 문서에 1:1 로 대응한다.
  피드백 1(추출 메커니즘 명시 + fail-open/closed 결정 + 양방향 비용) →
  `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md:15-38`
  (메커니즘: 브랜치명에서 이슈 번호, 본문에서 phase, 구현 함수까지 명시),
  `:40-43`(결정: fail-closed), `:45-58`(차단의 비용과 통과의 비용 양방향),
  `:59-64`(선택 근거). 피드백이 "본문에서 추출" 을 전제했는데 구현이
  브랜치명을 골랐다는 차이도 `:17-19` 에서 먼저 밝히고 이유를 댄다 —
  회피가 아니라 응답이다. 피드백 2(관리자 우회 차단의 단일-계정 정당화
  + 잔여 우회 표면) → `:66-99`(정당화), `:103-128`(잔여 표면), `:129-134`
  (결론). 요구된 4개 요소가 모두 file:line 으로 고정된다.
- **CI 배선의 이름 결합(C3)**: 워크플로의 잡 id 는 `closes-gate`
  (`b3ba234` 워크플로 diff `jobs.closes-gate`)이고 보호 규칙의 컨텍스트
  문자열도 `"closes-gate"`(이 세션 protection GET) — 일치한다.
  scout-brief 가 경고한 이름-기반 매칭 실패 모드[8][9]는 현재 실현되지
  않았다. 본문 편집 재실행 문제도 `types` 에 `edited` 가 포함돼 있어
  덮인다(같은 diff). 트리거되지 않는 경로는 `branches: [main]` 필터
  밖(main 외 베이스)뿐이고, 그 경우 필수 체크는 `expected` 로 남아
  머지가 잠기므로 fail-closed 쪽이다.

**Trajectory 종합**: scout·survey 선행, 진짜 사람 승인, 측정에 근거한
사전 공개된 이탈, 피드백의 문서화된 반영 — 경로 자체에 결함 없음.

## 3. Step — 어떤 아티팩트가 미비한가

**미비 3건.** 각각 아래 §Findings 에 impact / timeline / root cause /
action item 4부 형식으로 적는다.

1. `b3ba234` 의 `gates/ci.py` — `_phase1_mismatch` 가 배선된 호출에서
   공허(F1). 요구사항 2 의 미충족이 여기서 나온다.
2. `b3ba234` 이후의 배선 전반 — 커밋 메시지 내 closing 키워드가 검사
   표면 밖(F2). 발주자의 추가 판정 항목이며 §추가 판정 항목에서 존재·
   범위·귀속을 따로 판정한다.
3. `docs/handbooks/operations.md` 와
   `docs/issue-245/reports/implementation.md` 의 사후 정합성(F3) —
   보호가 실제로 켜진 뒤에도 둘 다 "아직 아무것도 막지 않는다" /
   `loop_state: in-progress` 상태로 main 에 남아 있다.

미비가 **아닌** 것으로 확인한 것: 제약 "판정 로직 무변경" 준수
(`git show b3ba234 --stat` 에 `gates/pr_reference.py` 없음), 잡 이름과
보호 컨텍스트의 결합(C3, 위), 신뢰 브랜치 체크아웃(`ref: main`, 워크플로
diff — scout-brief 의 변조 불가성 must-be[3][4] 충족), 피드백 2건의
반영(C4, 위).

---

# 추가 판정 항목 — 커밋 메시지 closing 키워드 우회 벡터

발주자가 이슈 #245 코멘트로 phase 2 판정에 포함하라고 지정한 항목이다
(`gh issue view 245 --comments`, 이 세션). 존재 / 범위 / 귀속 순으로
판정한다.

## 존재 — 확정. 실물 2건.

**사건 1 (issue #262).** PR #265 본문(이 세션 `gh pr view 265 --json body`)
은 `#262` 를 평문으로만 담고 "Per contract, this phase-1 PR references
`#262` in prose only — merging it must not auto-close the issue." 라고
명시한다. closes-gate 는 그 PR 에서 **SUCCESS** 였다(체크 롤업:
`name: closes-gate`, `conclusion: SUCCESS`, `completedAt
2026-08-04T03:12:34Z`, job 91881848093 — `gh pr view 265 --json
statusCheckRollup`, 이 세션). PR 은 2026-08-04T04:04:48Z 에 머지 커밋
`2f89d5a9b` 로 머지됐고, 그 브랜치 커밋 `1c88e073e` 의 메시지 마지막
줄이 `Closes #262` 다(`git log 1c88e07 -1 --format=%B`, 이 세션).
이슈 #262 에는 재오픈 코멘트가 있다: "재오픈: 실행 계획 step
2(execution-observation)가 남아 있다. 원인 동일 — 머지된 커밋 메시지 내
'Closes #262' (closes-gate 는 PR 본문만 검사)."(`gh issue view 262
--comments`, 이 세션).

**사건 2 (issue #266) — 변수를 분리하는 대조군.** PR #267 의 closes-gate
는 먼저 **FAILURE**(job 91883256165, `completedAt 2026-08-04T03:22:17Z`)
였다가 이후 **SUCCESS**(job 91889376855, `completedAt 04:06:04Z`)로
바뀐다(`gh pr view 267 --json statusCheckRollup`, 이 세션). 즉 게이트는
본문에 대해 **정상적으로 발화했고**, 본문에서 키워드를 뺀 뒤 통과했다 —
최종 본문(이 세션에서 읽음)에는 closing 키워드가 없고 "closing keyword
removed by relay per plan-aware rule" 이라고 적혀 있다. 그럼에도 PR 이
04:08:44Z 에 머지되자 이슈 #266 은 자동 종결됐고, 그 브랜치 커밋
`be53d1eb` 의 메시지 3번째 줄이 `Closes #266` 이다(`git log be53d1e -1
--format=%B`, 이 세션). 재오픈 코멘트가 같은 원인을 지목한다: "PR #267
본문의 closing 키워드는 머지 전 제거했으나 자동 종결됨 — 머지된 커밋
메시지 내 closing 키워드가 유력 원인(closes-gate 는 PR 본문만 검사,
커밋 메시지는 미검사 — 새 우회 벡터)."(`gh issue view 266 --comments`).

사건 2 는 "본문 청결 + 게이트 녹색 + 커밋 메시지 오염 → 이슈 여전히
종결" 을 하나의 PR 안에서 보여주므로, 벡터의 존재는 추정이 아니라
분리된 실측이다.

## 범위 — 검사 표면 밖 전체. 게다가 *체계적으로* 검사를 비껴간다.

- **검사 입력에 커밋 메시지가 없다.** 배선된 호출이 읽는 본문은
  `pr_reference._pr_view` 가 `gh pr view <n> --json body,title` 로 받아
  `data.get("body","")` 만 돌려준 값이다(`b3ba234:gates/pr_reference.py:66-72`).
  `b3ba234` 의 `gates/ci.py` diff 에서 `_closes_ref_for_issue`,
  `_phase_from_body`, `_phase1_mismatch` 는 모두 그 `body` 문자열 하나만
  받는다. 배선 경로 어디에도 커밋 목록을 가져오는 호출이 없다.
- **단순 미검사가 아니라 능동적 우회로 작동한다.** phase 가 본문에서
  유도되므로(`_phase_from_body`, 같은 diff), 본문이 깨끗한 PR 은
  `"phase1"` 로 분류되고 — 그러면 계획-인지 phase-2 규칙
  (`b3ba234:gates/pr_reference.py:46-50`, PR #263 job 91872249829 에서
  실제로 발화한 바로 그 규칙)은 **아예 조회되지 않는다**. 커밋 메시지가
  종결을 수행하는 바로 그 경우에, 그것을 막았을 검사가 건너뛰어진다.
- **다른 통제로도 안 덮인다.** 이 세션에서 GET 한 보호 규칙 JSON 에는
  커밋 메시지에 대한 조항이 없다 — `required_signatures.enabled: false`,
  `required_linear_history.enabled: false`, `required_pull_request_reviews`
  키 자체가 없음, push 제한 없음. 스쿼시/머지 커밋 메시지도 같은
  사각지대다.
- **범위의 상한**: 이 벡터는 머지 차단 자체를 뚫지 못한다(PR 은 여전히
  closes-gate 녹색이어야 머지된다). 뚫는 것은 이슈 #245 가 막으라고 한
  결과물 — 조기 자동 종결 — 뿐이다. 즉 게이트의 **문언은 충족시키면서
  목적을 무력화**한다. 실측된 피해는 2건 모두 사람이 수동 재오픈으로
  복구했다(위 두 재오픈 코멘트).

## 귀속 — 미인지 공백. 설계의 알려진 한계로 기록된 바 없다.

- **어느 아티팩트에도 언급이 없다.** 이 세션에서
  `docs/issue-245/`, `docs/handbooks/operations.md`, `gates/ci.py`,
  `gates/pr_reference.py` 를 대상으로 `커밋 메시지|commit message|commit-message`
  를 grep 한 결과 히트 0건이다(유일한 히트는 이 기록 자신).
- **"아는 한계" 목록 두 곳 모두 이 항목을 담고 있지 않다.** 결정 문서의
  잔여 우회 표면 절은 남는 경로로 **오직 하나** — 보호 규칙 자체의 편집 —
  만 열거한다(`docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md:103-128`,
  결론 `:129-134` 는 그것을 "받아들인 잔여 위험이지, 놓친 위험이 아니다"
  라고 못박는다). 기록의 Open findings 는 **둘** — `_always_writable()`
  패턴 불일치와 다중 fetch 비원자성 — 만 남긴다
  (`docs/issue-245/reports/implementation.md:228-264`). 어느 쪽도 이
  벡터가 아니다.
- **표면의 뿌리는 상속된 것이다.** 본문-전용 검사는 `check_body` 의
  구성 자체이고(`b3ba234:gates/pr_reference.py:28-62`), 그 파일은 이슈
  #245 의 제약으로 동결돼 이 커밋에서 무변경이다(`git show b3ba234
  --stat` 에 부재). 즉 관찰 대상 역할이 구멍을 **만들지는 않았다** —
  #228 의 탐지 표면을 그대로 강제 배선 위에 올렸을 뿐이다.
- **그러나 커버리지 분석은 이 역할의 산출물이다.** 이슈 #245 요구사항 1
  은 "각 후보의 커버리지 차이(사람이 직접 만든 PR 도 잡는가)를 명시하고
  고를 것" 을 명시적으로 요구했다(이슈 본문). 인도된 커버리지 분석은
  **병합 경로** 축(웹 UI / `gh pr merge` / API 직접 호출 — 제안 `:22`,
  결정 문서 `:66-99`)만 훑고, **자동 종결 트리거 표면** 축(본문 vs 커밋
  메시지)은 한 번도 세우지 않았다.

**귀속 판정**: 벡터의 *존재*는 #245 이전부터 있던 #228 의 본문-전용
탐지 표면에 귀속되고 — 관찰 대상 역할이 도입한 결함이 아니다. 배선
시점에 그것이 *발견되지 않은 것*은 #245 의 커버리지 분석에 귀속된다 —
분석이 요구된 커버리지 질문을 한 축(병합 경로)으로만 전개하고 다른
축(종결 트리거 표면)을 세우지 않았기 때문이다. 그 결과가 §추가 판정
항목의 실물 2건이다. "알려진 한계였는가" 에 대한 답은 **아니다** —
알려졌다면 결정 문서의 잔여 표면 절이나 기록의 Open findings 에 있었을
것이고, 둘 다 이 세션에서 읽었으며 둘 다 없다.

---

# Findings

## F1 — 요구사항 2 의 기계 검사가 강제 경로에서 공허하다

- **Impact**: 요구사항 2("phase-1 Closes 금지도 같은 배선에 태운다")가
  강제 경로에서 성립하지 않는다. 구체적 노출: 마지막 계획 스텝의 phase-1
  제안 PR(또는 `## 실행 계획` 이 없는 이슈의 phase-1 PR)이 `Closes #N` 을
  실으면 필수 체크를 **통과**하고, 머지 시 이슈를 자동 종결한다
  (`b3ba234:gates/pr_reference.py:52-56` 로의 낙하). 이 관찰 자신의
  PR #268 이 바로 그 형태(2 스텝 중 마지막의 phase-1)다.
- **Timeline**: `b3ba234` 커밋 2026-08-04T02:00:37Z → PR #257 머지
  02:04:01Z → 사람이 보호 활성화(PR #263 잡이 02:06:49Z 에 이미 돌았으므로
  그 이전) → 이 세션 protection GET 에서 `contexts: ["closes-gate"]` 로
  필수화 확인. 공허한 채로 필수 체크가 된 상태가 계속되고 있다.
- **Root cause**: 유도된 `phase` 와 미비 검사의 술어가 **같은 술어**다 —
  `_phase_from_body` 도 `_phase1_mismatch` 도 `_closes_ref_for_issue(body,
  issue)` 를 본다(`b3ba234` `gates/ci.py` diff). 한쪽에서 다른 쪽을
  유도하면 그 분기는 도달 불가가 된다. 기록의 요구사항-2 검증
  (`docs/issue-245/reports/implementation.md:343-362`)은 이 검사를
  `--phase` 를 명시로 준 경로에서 발화시켜 확인했고, 배선이 실제로 쓰는
  `--autodetect` 경로에서는 확인하지 않았다 — 그래서 공허함이 검증에
  보이지 않았다.
- **Action item**(사람이 판단할 사항; 이 역할은 이슈를 만들지 않는다):
  요구사항-2 검사를 phase 분기 밖으로 빼거나, phase 를 closing 키워드와
  독립적인 신호(브랜치·계획 상태)로 유도해 두 술어를 분리한다. 회귀
  확인은 배선된 호출 형태(`--pr <n> --autodetect --closes-only`) 그대로
  red→green 을 보이는 방식이어야 한다.

## F2 — 커밋 메시지 closing 키워드가 검사 표면 밖이다

- **Impact**: 2026-08-04 하루에 실물 조기 종결 2건 — 이슈 #262(PR #265
  머지 04:04:48Z), 이슈 #266(PR #267 머지 04:08:44Z). 둘 다 사람이 수동
  재오픈해야 했다(각 이슈의 재오픈 코멘트). 이것은 이슈 #245 가 끝내려고
  열린 실패 부류 그 자체다.
- **Timeline**: closes-gate 는 두 PR 모두에서 최종 **녹색**이었다
  (job 91881848093 SUCCESS 03:12:34Z / job 91889376855 SUCCESS
  04:06:04Z). PR #267 은 그 전에 본문 때문에 한 번 FAILURE(job
  91883256165, 03:22:17Z) 였다가 키워드 제거 후 통과했다 — 게이트는
  정상 작동했고, 종결은 커밋 메시지(`be53d1eb` 의 `Closes #266`,
  `1c88e073e` 의 `Closes #262`)가 수행했다.
- **Root cause**: 탐지 표면이 PR 본문 하나뿐이다
  (`b3ba234:gates/pr_reference.py:66-72` 의 `body` 단일 반환, `b3ba234`
  `gates/ci.py` diff 의 세 함수 모두 `body` 만 수용). 게다가 phase 가
  본문에서 유도되므로 본문이 깨끗하면 계획-인지 규칙
  (`:46-50`)이 조회조차 되지 않는다. 배선 시점의 커버리지 분석이 병합
  경로 축만 전개하고 자동 종결 트리거 표면 축을 세우지 않아
  (제안 `:22`, 결정 문서 `:66-99`), 이 표면이 "아는 한계" 목록 어디에도
  기재되지 않았다(결정 문서 `:103-134`, 기록 `:228-264` — 이 세션 확인).
- **Action item**(사람 판단 사항): 강제 체크의 입력에 PR 의 커밋 메시지
  집합을 추가하고(예: `gh api .../pulls/<n>/commits` 의 각
  `commit.message`) 같은 `_CLOSES_REF` 술어를 적용한다. 동시에 phase 를
  본문에서 유도하는 설계를 재검토한다 — 본문이 유일한 종결 표면이
  아니라는 것이 실물로 확정됐으므로, 본문만으로 phase 를 정하면 F2 는
  F1 과 같은 "검사를 비껴가는 라우팅" 을 계속 만든다. 스쿼시 머지 시의
  머지 커밋 메시지도 같은 표면이다.

## F3 — 활성화 이후의 기록·핸드북 정합성이 주인 없이 남았다

- **Impact**: 상시 운영 문서가 현재 강제 상태를 **과소** 진술한다.
  `docs/handbooks/operations.md` 의 "머지 게이트 (CI)" / "Merge gate (CI)"
  절은 여전히 "**아직 아무것도 실제로 막지 않는다**" / "**Nothing is
  actually blocked yet**" 라고 적혀 있는데(`b3ba234` 의 operations.md
  diff), 실제로는 `closes-gate` 가 필수 체크이고 `enforce_admins` 가
  켜져 있다(이 세션 protection GET). 같은 이유로 관찰 대상 기록의
  frontmatter 는 `loop_state: in-progress` 다
  (`docs/issue-245/reports/implementation.md:1-7`). 두 파일 모두 현재
  `origin/main`(247051e)에서 그대로다 — 이 세션에서
  `git diff --stat FETCH_HEAD -- docs/handbooks/operations.md
  docs/issue-245/reports/implementation.md` 가 빈 출력임을 확인했다.
  main 의 핸드북만 읽는 사람은 아무 머지도 막히지 않는다고 결론 내리게
  된다.
- **Timeline**: `b3ba234`(02:00:37Z) 시점에는 두 진술 모두 참이었다 →
  사람이 02:04:01Z(PR #257 머지)와 02:06:49Z(PR #263 첫 CI 잡) 사이에
  보호를 활성화 → 02:50:43Z 통과 확인 → 그 이후 지금(origin/main
  247051e)까지 두 문서 모두 미갱신.
- **Root cause**: 기록이 자신의 종료 전이를 사람 스텝의 완료에
  걸어두었으나("Once steps 1-2 land, `loop_state` moves to `landed` and
  `docs/handbooks/operations.md` picks up the standing CI/gates
  description", `docs/issue-245/reports/implementation.md:289-291`),
  그 완료를 *기록할* 주체는 지정되지 않았다 — 헤드리스 세션은 이미
  끝났고, 이관은 "누가 수행하는가" 만 정하고 "누가 완료를 기록하는가" 를
  정하지 않았다.
- **Action item**(사람 판단 사항): 이슈 #245 를 닫는 주체가
  `loop_state` 를 넘기고 핸드북의 두 "아직 안 막힌다" 문단을 현재 상태로
  고친다. 일반화하면, 활성화를 사람에게 이관하는 기록은 수행자뿐 아니라
  **완료 기록자**를 함께 지명해야 한다.

---

## Open findings

F1·F2·F3 모두 이 역할의 쓰기 표면 밖 아티팩트에 대한 것이라 여기서
고치지 않는다 — 관찰 역할은 관찰 대상의 `src/`·`test/`·기록을 편집하지
않는다. 세 건 모두 미해결 상태로 이 기록에 남는다.

이 관찰 자체에서 미해결로 남기는 것: 없음. 계획의 C1–C5 와 발주자의
추가 판정 항목이 모두 실물 증거의 위치까지 도달했다.

## Next steps

이 기록이 브랜치에 커밋되고 PR #268 로 인도되면 이 역할의 일은 끝난다.
`loop_state: landed`.

## Open-finding resolution path

발견은 오직 여기로만 돌아간다. 사람이 PR #268 에서 F1·F2·F3 을 판단하고,
타당하다고 보면 **사람이 직접** 후속 이슈를 만든다 — 계약 v3 에서 이슈는
사용자 저작 전용이고, 이 역할은 이슈를 만들지도 관찰 대상 파일을 고치지도
않는다. F2 는 실물 사고 2건이 이미 발생했고 재발 경로가 열려 있다는
점에서 셋 중 가장 시급하다.
