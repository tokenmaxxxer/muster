files:
- docs/issue-245/reports/execution-observation/survey.md
- docs/issue-245/reports/execution-observation/scout-brief.md
- docs/issue-245/proposals/2026-08-04-execution-observation-plan.md

## Request
issue #245 실행 계획 step 2 — step 1(`implementation` 역할, 브랜치
`issue-245/implementation`, phase-2 커밋 `b3ba234`, PR #257 MERGED
2026-08-04T02:04:01Z)의 독립 실행 관찰. 관찰 대상 범위: closes-gate CI
워크플로 신설, `gates/ci.py` 의 `--autodetect`/`--closes-only` 모드,
2026-08-04 사람이 실행한 main 브랜치 보호 활성화, 발주자 피드백 2건
(fail-closed 결정 / 관리자 우회 차단 정당화)의 반영, 승인된 제안의
전체-번들 설계에서 `--closes-only` 로 좁힌 이탈. 이 문서는 phase 1 —
무엇을 어떤 증거로 검사할지만 정한다. 판정은 phase 2 의
`docs/issue-245/reports/execution-observation.md` 에서만 낸다.

## 검사할 판정 레벨과 각 레벨의 증거원 (판정 언어 등장 전에 먼저 고정)

세 레벨 전부 다룬다. 어느 레벨이 해당 없으면 "해당 없음, 이유 X" 로
명시하고 침묵으로 생략하지 않는다.

1. **outcome — 이슈가 요구한 것이 PR/기록으로 랜딩됐는가.**
   증거원: 이슈 #245 본문의 요구사항 1/2/3 각 항목 ↔ (i) `b3ba234` 의
   `.github/workflows/plan-aware-closes-gate.yml` diff, (ii) `b3ba234` 의
   `gates/ci.py` diff, (iii) `gh api .../branches/main/protection` 실측
   출력, (iv) PR #263 의 CI 잡 로그 2건(job 91872249829 = FAILURE
   02:06:49Z, job 91878584150 = SUCCESS 02:50:43Z) 과 PR #263 코멘트
   `#issuecomment-5174045441`. 요구사항별로 1:1 매핑해 각각의 근거를
   붙인다.
2. **trajectory — phase-1→phase-2 경로가 건전했는가.**
   증거원: phase-1 커밋 `a8cddd9` 의 산출물 3종(survey/scout-brief/제안),
   승인 경로(이슈 코멘트 `APPROVE issue-245/implementation`, 단일-계정
   모드; PR #257 의 `reviews` 배열이 비어 있다는 실측), 승인과 별도로
   달린 발주자 피드백 2건(PR #257 코멘트) ↔
   `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`
   §1/§2, 그리고 제안(`...-plan-aware-closes-gate-wiring.md:31`)의 설계와
   실제 랜딩된 호출(`--autodetect --closes-only`) 사이의 차이가
   `docs/issue-245/reports/implementation.md:143-167, 200-226` 에 어떻게
   기록됐는지.
3. **step — 특정 아티팩트에 미비가 있는가.**
   증거원: scout-brief 의 GAP LINE 이 "아직 대응 확인 안 됨" 으로 남긴
   세 항목을, 아래 검사 항목 C1-C5 로 각각 실물 증거에 대고 확인한다.

## 검사 항목 (전부 실측 증거로만; 관찰 대상 코드 재실행 없음)

- **C1 (요구사항 2의 도달성)**: `b3ba234` 의 `gates/ci.py` diff 에서
  `_phase1_mismatch` 는 `phase == "phase1"` 분기 안에서만 호출되고,
  `--autodetect` 경로의 `_phase_from_body` 는 그 이슈를 향한 closing
  키워드가 있으면 `"phase2"` 를 돌려준다. CI 배선(워크플로가 넘기는 인자는
  `--pr <n> --autodetect --closes-only` 뿐)에서 이 검사가 발화할 수 있는
  입력이 존재하는지를 diff 만으로 추적한다. 계획이 모두 완료된 이슈에
  대한 phase-1 PR 이 closing 키워드를 실었을 때 어떤 분기로 가는지도 같은
  방식으로 따진다(이슈 #245 본문이 기술한 게이트 의미론 — "미완 스텝이
  남은 이슈의 phase-2 PR 에서 차단" — 을 기준으로).
- **C2 (검증의 커버리지)**: PR #263 이 실측한 것은 head 브랜치
  `issue-224/closes-gate-verify` 에 대한 phase-2 차단 1건 + 통과 1건이다.
  이 두 런이 요구사항 3("실물 확인")의 어느 부분을 덮고 어느 부분을 안
  덮는지를 잡 로그의 실제 출력 문자열로 확정한다.
- **C3 (필수 체크가 안 도는 경로)**: 워크플로의 `on.pull_request.types`
  와 `branches: [main]` 필터, 잡 이름 `closes-gate` ↔ 보호 규칙의
  `contexts: ["closes-gate"]` 결합을 `b3ba234` diff 와 protection API
  출력으로 대조한다(scout-brief [8][9]: 이름 기반 매칭의 알려진 실패
  모드).
- **C4 (피드백 2건의 반영)**: PR #257 의 피드백 코멘트 원문 2개 항목을
  `2026-08-04-closes-gate-wiring-tradeoffs.md` §1/§2 의 해당 문장에 각각
  대응시켜, 요구된 요소(메커니즘 명시 / fail-open·closed 양방향 비용 /
  단일-계정 관점 정당화 / 잔여 우회 표면)가 문서의 어느 줄에 있는지를
  file:line 으로 고정한다.
- **C5 (`--closes-only` 이탈)**: 승인된 제안의 문구, 이탈 사유로 기록에
  적힌 측정 결과(`write_scope 이탈` 실측,
  `docs/issue-245/reports/implementation.md:143-167`), 이탈로 인해
  필수화되지 *않은* 검사 집합(`b3ba234` 의 `check()` diff 에서
  `closes_only` 가 건너뛰는 항목들)을 대조한다.

## Constraints
- 관찰 대상의 코드를 재실행하지 않는다. `gates/ci.py`/`pr_reference.py`
  의 현재 파일을 "무슨 일이 있었는가" 의 증거로 읽지 않는다 — 증거는
  `b3ba234` 의 diff, 커밋, PR/이슈 코멘트, CI 잡 로그, GitHub API 실측
  출력뿐이다.
- 관찰 대상의 `src/`·`test/`·`docs/issue-245/reports/implementation*`
  경로를 편집하지 않는다. 미비가 확인되면 이 역할의 기록에만 담는다 —
  이슈는 사람만 만든다(계약 v3).
- 판정문마다 인용을 그 문장 옆에 붙인다. 인용 없는 판정 언어는 쓰지
  않는다.
- 기록의 독립성 선언이 어떤 판정 언어보다 먼저 온다.

## What will be done
- (완료, phase 1) 조사 → `docs/issue-245/reports/execution-observation/survey.md`.
- (완료, phase 1) 이 부류 감사의 기준선 sweep →
  `docs/issue-245/reports/execution-observation/scout-brief.md`.
- (이 문서) 검사할 판정 레벨·증거원·검사 항목 C1-C5 고정, phase 2 승인 대기.
- phase 2(사람 승인 후): `docs/issue-245/reports/execution-observation.md`
  를 phase 2 의 첫 행위로 작성 — 독립성 선언 → outcome/trajectory/step
  3레벨 판정(각 문장에 인접 인용) → 미비가 있으면 4부(impact/timeline/
  root cause/action item) 형식, 그리고 `loop_state` 를 전이마다 갱신.

## Out of scope
- `gates/pr_reference.py` 판정 로직(#228 소유)의 재검토.
- `gates/gates.py` 의 `_always_writable()` 패턴 불일치 자체의 수정 —
  관찰 대상 기록이 "Open findings" 1번으로 남긴 항목이고, 이 역할의 쓰기
  표면 밖이다.
- 브랜치 보호 설정 변경, 검증용 PR 생성, 워크플로 재실행 — 관찰 역할은
  관찰 대상 시스템의 상태를 바꾸지 않는다.

## How you'll know it worked
- phase 1: 이 PR 본문이 `#245` 만 담고 closing 키워드가 없으며(신설된
  closes-gate 필수 체크가 이 PR 자신에도 적용된다), 승인자
  (`docs/specs/approvers.md`)의 `APPROVE issue-245/execution-observation`
  이슈 코멘트로 phase 2 가 열린다.
- phase 2 완료 시: `docs/issue-245/reports/execution-observation.md` 가
  브랜치에 커밋돼 있고, outcome/trajectory/step 세 레벨이 모두 다뤄졌고
  (해당 없음도 이유와 함께), C1-C5 각각이 실물 증거의 위치(SHA·file:line·
  코멘트 URL·잡 ID)와 함께 결론까지 갔다.
