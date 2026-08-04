---
name: closes-gate-wiring-tradeoffs
kind: decision
---

# 계획-인지 Closes 게이트 강제 배선 — 추출 메커니즘·fail-open/closed·관리자 우회 (issue #245)

phase 2 실행 중 PR #257에 달린 발주자 피드백 2건(2026-08-03 코멘트, 승인과
별도)에 답한다. 둘 다 승인된 제안
(`docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`)이
phase 2로 이월해 둔 미해결 질문(survey §10)의 구체화다.

## 1. 이슈 번호·phase 추출 메커니즘과 실패 시 fail-open/closed

### 메커니즘: 이슈 번호는 PR 본문이 아니라 head 브랜치명에서 뽑는다

발주자 피드백은 "PR 본문에서 이슈 번호·phase를 추출"을 전제했지만,
구현은 이슈 번호를 **본문이 아니라 head 브랜치명**에서 뽑도록 골랐다 —
근거를 여기 명시한다.

- 브랜치명(`issue-<n>/<role>`)은 role-handoff contract v3가 이미
  강제하는 유일한 명명 규칙이다(`gates.py`의 `BRANCH_ROLE` 이 같은
  규칙을 role_scope 판정에 이미 쓰고 있다 — 새 관례가 아니라 기존
  강제 규칙의 재사용). 이슈 하나만 가리켜 모호성이 없다.
- 본문은 여러 이슈를 언급할 수 있다("related to #123, see also #124")
  — "이 PR 이 속한 이슈"를 본문에서 유일하게 뽑아낼 결정적 규칙이 없다.
  `pr_reference.check_body`의 phase1 분기가 이미 이 문제와 씨름한다:
  본문에 `#N`이 하나만 있어야 한다고 강제하지 않고, "선언된 이슈 번호가
  본문에 있는가"만 검사한다 — 그 "선언된 이슈 번호"를 CI가 미리 알아야
  하는 게 바로 이 문제다. 브랜치명은 그 값을 명확히 준다.
- phase는 본문에서 뽑는다: closing 키워드(Closes/Fixes/Resolves)가
  *그 이슈 번호를 향해* 있으면 phase2, 없으면 phase1 —
  `pr_reference._CLOSES_REF`가 이미 판정에 쓰는 것과 같은 신호라 새로운
  모호성이 없다(`gates/ci.py`의 `_phase_from_body`).

구현: `gates/ci.py`의 `_issue_from_branch`(브랜치→이슈, 순수 함수),
`_phase_from_body`(본문→phase, 순수 함수), 이 둘을 엮는
`_autodetect_issue_phase` — CLI `--autodetect` 플래그로 켠다.

### 실패 시: fail-closed. 트레이드오프

**결정: 브랜치가 `issue-<n>/<role>` 형태가 아니어서 이슈 번호를 못
뽑으면 차단한다(fail-closed)** — 통과시키지 않는다.

- **차단(fail-closed)의 비용**: 이 명명 규칙을 따르지 않는 PR(관례를
  모르는 사람이 만든 브랜치명, 이 저장소엔 아직 없지만 향후 붙을 수
  있는 Dependabot류 자동 PR 등)이 무고하게 막힌다. 구제 경로는 있다 —
  브랜치를 `issue-<n>/<role>`로 바꿔 재푸시하면 `synchronize` 이벤트가
  재검사한다. 이 저장소엔 현재 `.github/dependabot.yml` 등 자동 PR
  생성기가 없고(확인됨, 2026-08-04), 계약 자체가 "이슈에 못 묶는 작업은
  당신 일이 아니다"(핵심 상호작용 규약)라고 이미 규정한다 — 즉 이슈에
  안 묶인 PR은 이 저장소의 정상적 작업 단위가 아니다.
- **통과(fail-open)의 비용**: 추출 실패 시 조용히 통과시키면, 브랜치명을
  일부러/실수로 관례에서 벗어나게 만든 PR(또는 애초에 관례를 모르는
  아무 PR)이 계획-인지 Closes 게이트 자체를 완전히 건너뛴다 — 이슈
  #245가 고치려는 정확히 그 구멍("강제 지점 없음")이 이 새 경로로
  되살아난다. issue #228 §3(d)가 이미 실물로 겪은 조기-종결 사고가,
  이번엔 "브랜치명만 살짝 다르게" 하는 것만으로 재현 가능해진다.
- **선택**: 차단. 이 저장소 코드베이스 전역에 이미 있는 원칙과
  일치시킨다 — `pr_reference.check`/`gates.role_scope`가 이미 "검사
  불가는 통과가 아니다"/"fail closed"를 명시적으로 채택하고 있다
  (`gates/pr_reference.py:94,100`, `gates/gates.py:498`). 새 실패
  모드 하나만 반대 방향(fail-open)으로 고르면 게이트 전체의 일관된
  위협 모델이 깨진다.

## 2. 관리자 우회 차단("Do not allow bypassing the above settings")의 단일-계정 정당화

### 이 저장소의 실제 계정 구성 (2026-08-04 실측)

`gh api repos/tokenmaxxxer/on-the-record/collaborators` 확인: 승인자
목록(`docs/specs/approvers.md`)의 **두 계정(JiwonJung94, jjongkwann)
모두 `admin: true`**를 갖고 있다. 즉 branch protection의 "관리자
우회" 설정은 이 저장소에서 추상적 위험이 아니라, 실사용 기본값인
단일-계정 모드에서 실제로 병합을 승인하는 그 계정이 이미 우회 권한도
갖고 있다는 뜻이다.

### 왜 필요한가: gh-guard.sh 는 세션의 tool-call 표면만 본다

`tokenmaxxxer-core/core/hooks/gh-guard.sh`(PreToolUse, 125행 확인)는
`CLAUDE_ROLE` 세션의 `Bash` 도구 호출 페이로드만 검사한다 —
`gh pr merge`/`gh pr review --approve`/`git push origin main` 등을
문자열 패턴으로 막는다. 이 훅이 못 보는 것:

1. **Claude Code 세션 밖의 같은 계정.** 사람이 자기 터미널에서 직접
   `gh pr merge --admin`을 치거나, github.com 웹 UI에서 "Merge without
   waiting for requirements to be met" 버튼(관리자에게만 보이는, 필수
   체크 미통과 시 나타나는 우회 버튼)을 누르는 행위는 gh-guard의
   트리거 표면(tool-call payload) 자체를 거치지 않는다 — 이 저장소의
   survey(§4)가 이미 확인한 한계다.
2. **브랜치 보호 규칙 자체를 고치는 API 경로.** gh-guard.sh의 규칙
   목록(74-126행, 2026-08-04 재확인)에 `branches/.../protection`
   엔드포인트를 겨냥한 규칙이 **없다** — merge/review/issue 엔드포인트만
   막는다. `admin: true`를 가진 계정은 `gh api -X PUT
   repos/.../branches/main/protection`로 필수 체크 자체를 빼거나 규칙을
   끄고 병합한 뒤 되돌릴 수 있다. gh-guard가 CLAUDE_ROLE 세션 안에서도
   막지 않는 경로다(위 1과 별개로, 세션 안에서도 뚫려 있음).

두 경로 다, "필수 상태체크 + 관리자 우회 차단"을 켜야 최소한 (1)의
"머지 버튼 옆 원클릭 우회"를 없앨 수 있다 — 서버사이드(GitHub 자체)
설정만이 클라이언트/세션이 무엇이든 동일하게 적용된다는, phase-1에서
후보 (a)를 채택한 것과 같은 근거의 연장이다.

### 단일-계정 모델에서 "그럼에도 남는" 우회 표면

이 설정을 켜도 완전히 안 뚫리는 건 아니다 — 정직하게 남기는 것:

- **경로 2(브랜치 보호 규칙 자체 편집)는 안 닫힌다.** "Do not allow
  bypassing"은 규칙이 살아있는 동안 그 규칙을 건너뛰는 것만 막는다 —
  규칙 자체를 고치거나 끄는 것은 별개의 admin 권한이고, 이 설정으론
  못 막는다. `admin: true`인 두 계정 모두 여전히 이 경로를 갖는다.
  이건 이 이슈의 설계로 못 고치는 것 — GitHub 권한 모델의 근본적
  한계다(자기 권한으로 자기 규칙을 관리할 수 있는 계정을 그 규칙만으로
  묶을 수 없다). 다만 경로 2는 병합 버튼 옆 토글 하나가 아니라 **별도의,
  감사로그에 따로 남는 설정 변경 행위**다 — 실수/습관으로 우연히
  누르는 경로 1과 달리 의도적 조작이 필요하다.
- **단일-계정 모드의 실질적 의미**: 승인(`APPROVE issue-<n>/<role>`
  코멘트)과 병합을 같은 계정이 하므로, 이 설정은 "악의적 내부자를
  막는" 장치가 아니다(그 계정은 이미 승인 권한도, admin 권한도 갖고
  있다 — 막을 수 없다). 실질적으로 막는 것은: **자동화(role 세션·
  spawn.py)가 그 계정의 토큰으로 실행하는 동작이 실수로 필수 체크를
  우회하는 경로**, 그리고 **사람이 웹 UI에서 평소 습관대로 병합
  버튼을 누르다 (관리자에게만 뜨는) 우회 옵션을 무심코 선택하는
  경로**다. gh-guard.sh가 이미 세션의 `gh pr merge` 자체를 막고
  있으므로(위), 이 설정이 진짜로 좁히는 인구는 "Claude Code 세션 밖,
  사람이 직접 웹 UI를 조작하는 경로"로 좁다 — 정확히 이 이슈의 요구사항
  1("사람이 직접 만든 PR도 잡는가")이 "사람이 직접 병합도" 잡아야
  한다는 뜻이므로, 좁더라도 이 이슈의 핵심 요구와 정확히 일치한다.

**결론**: "Do not allow bypassing"을 켠다 — 두-계정/단일-계정 모두에서
유효하고(둘 다 admin이므로 특히 단일-계정에서 더 유효), 완전한
방어가 아님을 알고 켠다. 완전한 방어(경로 2까지 닫는 것)는 이
저장소가 조직(org) 소유가 아니라 개인 소유 저장소라 GitHub 쪽에
추가로 걸 수 있는 상위 통제(예: 조직 소유자 승인 필요)가 없다는 것도
같이 기록해 둔다 — 받아들인 잔여 위험이지, 놓친 위험이 아니다.
