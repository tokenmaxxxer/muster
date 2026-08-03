files:
- gates/flows.py
- docs/specs/flows-schema.md
- test_spawn.py

## Request

이슈 #248: `flows --json`의 `flows[].prs`가 사실상 항상 빈 배열(라이브
실측: flow 49건 중 1건만 채워짐)이라 대시보드 PRs 열이 의미를 잃는다.
같은 payload의 `decision_queue`는 같은 PR을 정상적으로 찾아낸다 — issue
27 사례에서 `decision_queue`는 PR #31/#32를 잡지만 같은 issue의
`flows[].prs`는 `[]`. 요구사항 셋: (1) `prs` 산출 로직을
`decision_queue`와 같은 열린-PR 목록 기반으로 통일할지 결정하고 구현,
(2) `flows-schema.md` §2.2의 `prs` 설명을 실제 포함 기준이 드러나게
보완, (3) `schema_version`은 유지(동작 정정 + 문서 보완, 필드 추가/제거
없음).

## Constraints

- `docs/specs/flows-schema.md`가 규율하는 출력 페이로드의 필드 형태는
  안 바뀐다 — `flows[]` 필드 목록 변경 없음, `schema_version` 범프 없음
  (요구사항 3, 같은 문서 §3: 필드 추가조차 없는 순수 동작 정정 +
  문서 보완은 범프 대상 아님).
- `gates/flows.py`가 만드는 `gh` 호출 횟수는 늘리지 않는다 — 같은 문서
  §4의 폴링 비용 계약. `prs` 재계산은 이미 `decision_queue` 생성에
  쓰인 `pr_by_branch`(1회 `gh pr list` 호출로 채워짐)를 재사용하고,
  새 `gh` 호출을 추가하지 않는다.
- `decision_queue`/`unapproved_open_prs` 루프 구조는 건드리지 않는다 —
  survey §5에서 확인: 이 두 필드는 이번 결함(`prs`가 board 레코드
  존재 여부로 추가 필터링되는 것)과 같은 갭이 없다(issue #216 survey의
  같은 판단을 재확인).
- 기존 `test_spawn.py::FlowsPayload` 케이스는 회귀 없이 통과해야 한다.

## Rationale

**채택 — `flows[].prs`를 `pr_by_branch`(subject로 그룹핑) 기반으로
다시 쓰고, `roles`(board 레코드 존재 여부) 필터를 완전히 제거한다.**
`decision_queue`가 이미 `pr_by_branch.items()`를 직접 순회해 board
레코드 유무와 무관하게 열린 PR을 전부 잡는 소스로 issue #216에서
검증됐다(survey §1.1) — `prs`도 같은 소스를 쓰면 두 필드가 구조적으로
같은 PR 집합을 공유하게 돼, 수용 기준("decision_queue와 flows[].prs가
같은 PR에 대해 불일치하지 않음")을 산출 로직 수준에서 보장한다.

거부한 대안(rejected alternative) — **`roles` 필터는 유지하되
`all_subjects[subject]`(board 순회 대상 role 집합)를 `pr_by_branch`에
나타나는 모든 role까지 넓히는 것**(예: 레코드 없는 role도
`all_subjects[subject].setdefault(role, {})`로 placeholder 추가). 이
대안은 겉보기엔 기존 `for r in roles` 구조를 안 건드리는 더 작은 변경
같지만 두 가지 문제가 있다. 첫째, `roles`는 `flows[].roles`(role별
`loop_state`/`verdict` 표시)의 소스이기도 해서, PR만 있고 아직 board
레코드가 없는 role을 여기 섞으면 `flows[].roles`에 `loop_state: null`인
가짜 role 엔트리가 생겨 그 필드의 의미("board에 머지된 레코드가 있는
role의 상태")가 흐려진다 — `prs`의 갭 하나를 고치려고 다른 필드의
계약을 침범한다. 둘째, 애초에 `roles`가 `prs`를 게이팅해야 할 이유가
없다 — board 레코드 존재는 "이 role의 loop_state를 보여줄 수 있는가"의
문제이지 "이 PR이 이 subject에 속하는가"의 문제가 아니다(PR-subject
소속은 브랜치명만으로 이미 결정됨, `_BRANCH_RE`). 필터를 걷어내는 채택
안이 이 개념적 혼동 자체를 없앤다 — issue #216이 `decision_queue`에서
이미 같은 결론(브랜치명 기반 `pr_by_branch`가 board 상태와 무관한
완전한 소스)에 도달했다.

## What will be done

1. **`gates/flows.py`**: `all_subjects` 순회 루프 진입 전에
   `pr_by_branch`를 subject로 그룹핑하는 `prs_by_subject: dict[str,
   set[int]]`를 한 번 계산(`pr_by_branch`는 이미 존재하는 값을
   재사용, 새 `gh` 호출 없음). `flows_out.append(...)`의 `"prs"` 값을
   `sorted({pr_by_branch[(subject, r)]["number"] for r in roles if
   (subject, r) in pr_by_branch})`에서 `sorted(prs_by_subject.get(subject,
   set()))`로 교체 — `roles` 필터 제거.
2. **`docs/specs/flows-schema.md`**: §2.2의 `prs` 필드 설명 행을
   "PR numbers associated with the subject"에서 실제 포함 기준(현재
   열려 있는 PR 중 브랜치명이 `issue-<subject>/<role>` 패턴에 매칭되는
   전부, role의 board 레코드 존재 여부와 무관, `decision_queue`와 동일
   소스)으로 교체하고, 표 아래에 두 필드가 같은 소스를 공유해 불일치하지
   않는다는 한 문단을 추가(issue #248 참조).
3. **`test_spawn.py`**: `FlowsPayload`에
   - issue-27 재현 회귀: 한 role만 board 레코드가 있고(다른 role의 PR은
     머지돼 `pr_by_branch`에서 빠진 상태를 흉내) 레코드 없는 두 role의
     open PR이 있을 때, `flows[].prs`에 그 두 PR 번호가 모두 채워지는지
     단언.
   - 일관성 회귀: 같은 subject에 대해 `decision_queue`에 등장하는 모든
     PR 번호가 해당 subject의 `flows[].prs`에도 포함되는지 단언(승인된
     PR과 미승인 PR을 섞어 `decision_queue`가 부분집합만 갖는 경우도
     `prs`는 전체를 갖는지 확인).

## Out of scope

- `decision_queue`/`unapproved_open_prs` 로직 변경 — Constraints에서
  명시한 대로 이번 결함과 같은 갭이 없음(survey §5 확인).
- `flows[].roles`(role별 `loop_state`/`verdict`) 구조 변경 — board
  레코드가 없는 role을 여기 섞지 않는다(Rationale 거부 대안 참고).
- `repo-status-board` 레포 수정 — 소비 측은 받은 배열을 그대로
  렌더링할 뿐, 이 레포 문제가 아님(이슈 본문 명시, issue #216·#189와
  같은 이유).
- `flows-schema.md` §4의 `gh pr list` 커맨드 문구(`--state all` vs
  실제 코드의 `--state open`) 정정 — 이번 이슈가 요청한 §2.2 범위
  밖의 기존 문서 드리프트이며 별개 이슈.

## How you'll know it worked

- `python3 -m pytest test_spawn.py -q` 전부 통과 — 기존 `FlowsPayload`
  케이스 회귀 없음, 새 회귀 테스트 2건 통과.
- 라이브 확인: 이 레포 자체에서 `python3 spawn.py flows --json -C .`
  실행, 예외 없이 JSON이 나오고 현재 open PR이 있는 subject의
  `flows[].prs`가 채워지는지 직접 확인(합성이 아니라 이 세션 자신의
  `-C .` 실행 결과).
