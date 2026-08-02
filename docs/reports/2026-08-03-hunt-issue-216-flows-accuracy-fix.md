# Hunt — issue #216 `flows --json` accuracy fix (phase 2, after code)

이 세션에는 `warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아
(available agent 목록에 `claude`/`Explore`/`freelunch:freelunch-worker`/
`general-purpose`/`Plan`/`statusline-setup`뿐), `general-purpose` 에이전트에
adversarial("assume-broken") stance 프롬프트를 직접 넣어 대체 디스패치했다.
stance 1개로 고정: "실제 사용에서 이 변경이 깨질 수 있는 구체적 엣지케이스를
찾아라 — 기존 테스트가 커버 안 하는 것".

코드 리뷰 대상: `dddbada`(gates/flows.py, spawn.py, test_spawn.py).

## Observed — 에이전트가 실측으로 확인한 3건

1. **`repo_slug`가 `None`일 때(예: `gh repo view` 실패) ledger 가 조용히
   전부 빈다** — `_entry_repo_name(e) == None` 매칭 대상이 되는데, 실제
   엔트리는 `cwd`가 항상 있어 `_entry_repo_name`이 `None`을 반환하는 경우가
   없으므로 전건 탈락. 재현: `_repo_slug`를 `None`을 반환하도록 패치하고
   `repo: "widgets"`(정합) 엔트리로 `flows_payload` 호출 → `ledger: []`.
2. **레포 이름 자체가 `-issue-N-role` 모양을 우연히 포함하면 `_cwd_repo_name`이
   잘못 자른다** — 예: 레포 `acme/payment-issue-7-service`를 그 자체
   루트 체크아웃(런처의 `<repo>-issue-<n>-<role>` 접미사 없이)에서 돌리면
   `cwd` basename이 `payment-issue-7-service`이고, 정규식이 이걸
   `payment`로 오인식 → `_repo_slug`가 맞게 찾은 `payment-issue-7-service`와
   불일치해 필터링에서 탈락.
3. **`decision_queue`에는 뜨는데 `flows[]`에는 안 뜨는 이슈가 생길 수
   있다** — `pr_by_branch` 소스와 `all_subjects` 소스가 다시 분리됐으니,
   레코드도 계획 블록도 없는 subject는 `decision_queue`에만 나타나고
   `flows[]`/`unapproved_open_prs`/`prs[]`에는 안 나타난다.

## Disposition — 셋 다 write set 확장으로 고치지 않음

1. **repo_slug=None 케이스:** 승인된 제안이 명시한 필터 표현
   (`_entry_repo_name(e) == (repo_slug.split("/")[-1] if repo_slug else
   None)`)을 글자 그대로 구현한 결과이고, `gh` 실패 시 조용히 빈 값으로
   저하되는 것은 이 모듈의 기존 관례와 같은 급이다(`_pr_list_all`/
   `_issue_list_all`이 이미 `gh` 실패 시 예외 없이 빈 리스트를 반환) —
   전에도 `repo` 최상위 필드 자체가 같은 이유로 `None`이 될 수 있었다.
   phase-1에서 이미 승인받은 리터럴 표현을 phase-2에서 임의로 바꾸는
   것은 승인 범위를 벗어난 재설계라 하지 않았다.
2. **repo 이름이 `-issue-N-role` 모양과 우연히 겹치는 경우:** 제안의
   Rationale이 이미 이 리스크를 논의했다 — cwd 파싱은 "관례가 깨지면
   조용히 틀린 값을 낼 수 있다"는 이유로 신규 엔트리에는 명시적 `repo`
   필드를 권위 소스로 쓰기로 결정했고, cwd 파싱은 **이미 쌓인 과거
   엔트리**에 대한 소급 폴백으로만 남긴다고 명시했다. 이 폴백이 모든
   가능한 레포 이름에 대해 명확할 수 없다는 것은 그 설계가 이미 안고
   가기로 한 트레이드오프이지, 이번 구현이 새로 만든 결함이 아니다.
3. **decision_queue 와 flows[] 소스 분리:** 이슈 #216 결함 1의 핵심이
   바로 이것이다 — 레코드도 계획도 없는 subject의 PR을 **보이게** 만드는
   것이 이번 수정의 목적이므로, 그 subject가 `flows[]`에 없는 채로
   `decision_queue`에만 있는 상태는 버그가 아니라 의도된 수정 결과다.
   `flows --json` 스키마 자체가 두 배열을 별도 소스로 규정하고 있어
   (`docs/specs/flows-schema.md`), 조인을 강제하지 않는다.

세 건 다 phase-2 write set(`gates/flows.py`, `spawn.py`, `test_spawn.py`)
확장 없이 종결. blocking finding 아님 — verify 가 다르게 판단하면
재개봉 가능하다.
