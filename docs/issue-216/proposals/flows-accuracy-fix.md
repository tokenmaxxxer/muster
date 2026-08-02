files:
- gates/flows.py
- spawn.py
- test_spawn.py

## Request

이슈 #216: `flows --json`(이슈 #172 계약, 이슈 #189 확장) 정확도 결함 2건.
(1) `decision_queue`가 보드 순회(`all_subjects` → `roles.items()`) 안에서만
채워져, 머지된 레코드도 계획 블록도 없는 이슈의 첫 PR(=승인 대기 중인
1단계 제안서)을 구조적으로 못 본다(`gates/flows.py:268-290`) — 실측: PR
#86가 열려 있는데 `decision_queue: []`. 부수로 `phase = 1 if loop_state ==
"scope-proposed" else 2`(`flows.py:283`)가 레코드 없음(`loop_state is None`)을
phase 2로 오분류한다. (2) `_ledger_read()`가 오케스트레이터 전역
`runs/ledger.jsonl`을 레포 구분 없이 통째로 돌려줘, 다른 레포의 세션
비용이 이 레포의 `ledger[]`/`sessions[].verdict`에 섞여 이중계산된다
(`flows.py:134-135`) — 실측: core #20/#56 비용이 on-the-record 밑에도,
on-the-record #178/#180이 core 밑에도 잡혀 실제 ~$39가 표시 ~$79.

## Constraints

- `docs/specs/flows-schema.md`가 규율하는 `flows --json` **출력** 페이로드의
  필드 형태는 안 바뀐다 — `decision_queue[]`/`ledger[]` 필드 목록 변경
  없음, `schema_version` 범프 없음(같은 문서 §3: 추가적 변경은 범프
  대상 아님, 이번 변경은 필드 추가조차 없음). `ledger.jsonl`(내부 원시
  로그, 같은 문서 §5가 "local-orchestrator data"로만 언급하고 필드
  목록을 규율하지 않음)에 새 키를 추가하는 것은 이 정책 대상이 아니다.
- `gates/flows.py`가 만드는 `gh` 호출 횟수는 늘리지 않는다 — 같은
  문서 §4의 폴링 비용 계약. `spawn._repo_slug(root)`는 현재도 `flows.py`
  안에서 1회만 호출된다(`:347`); 이번 수정도 1회 유지, 필터링과 출력
  필드 양쪽에 재사용.
- `repo-status-board` 레포 수정은 범위 밖(이슈 본문 명시, issue #189 D3와
  같은 이유).
- 기존 `test_spawn.py::FlowsPayload` 케이스는 (레포 필터링 도입으로
  깨지는 두 건을 고쳐 넣는 것 외에는) 회귀 없이 통과해야 한다.

## Rationale

**결함 1 — `pr_by_branch`를 대기열의 1차 소스로 삼는다.** 채택: `decision_queue`
생성 루프를 `for subject, roles in all_subjects.items(): for role, fm in
roles.items(): ...` 대신 `for (subject, role), pr in pr_by_branch.items():
...`로 바꾸고, 보드 레코드(`b.get(subject, {}).get(role, {})`)는 있으면
`loop_state`/`phase` 판단에만 조인한다. `phase = 1 if loop_state in (None,
"scope-proposed") else 2`로 바꿔 레코드 없음도 phase 1로 분류한다.

거부한 대안(rejected alternative) — **`all_subjects` union-expansion을
"열린 PR이 있는 모든 subject"까지 넓히는 것** (예: `pr_by_branch`의 모든
subject를 `all_subjects.setdefault(subject, {})`에도 추가). 이 대안은 겉보기엔
더 작은 변경이지만 근본 문제를 안 고친다 — `decision_queue.append`가 여전히
`for role, fm in roles.items()` **안에** 있으므로, `roles`가 빈 dict인 subject는
그 안쪽 루프가 0회 반복돼 PR 조회(`pr_by_branch.get((subject, role))`) 자체가
한 번도 실행되지 않는다. `role`을 알아낼 방법이 애초에 `roles`(보드 프런트매터)
말고 없기 때문이다. 즉 이 대안은 실측 재현 사례(PR #86, 레코드도 계획도
없는 이슈)를 여전히 못 잡는다 — survey가 코드를 직접 추적해 확인. 반면
`pr_by_branch`는 이미 브랜치명만으로 (subject, role)을 뽑아내므로(`_BRANCH_RE`,
`flows.py:28`) 보드 상태와 무관하게 완전한 소스다.

**결함 2 — 두 후보(cwd 파싱 소급 귀속 / 신규 엔트리 명시적 `repo` 필드)를
경쟁시키지 않고 함께 채택한다:** 신규 엔트리는 `ledger_write` 호출부
(`spawn.py:2614`)에서 `_repo_slug(Path(cwd).resolve())`로 얻은 레포 짧은
이름을 `repo` 필드로 박고, `flows.py`의 필터는 이 필드를 우선 신뢰한다.
필드가 없는(과거) 엔트리는 `cwd` basename을 `<repo>-issue-<n>-<role>`
관례로 되짚는 소급 폴백을 쓴다.

거부한 대안(rejected alternative) 1 — **cwd 파싱만 채택(단일 방법, 신규
필드 없음).** 스카우트 근거(AWS Bedrock 멀티테넌트 비용 추적 가이드,
OpenTelemetry 리소스 속성 모델 — survey 인용)가 공통으로 지적하는 것은
"경로에서 귀속을 추론하는 방식은 리소스가 재배치되는 환경에서 깨지기
쉽다"는 것이다. `<repo>-issue-<n>-<role>` 디렉터리 명명은 `spawn.py`
어디에도 강제·검증되지 않는 관례일 뿐(survey 확인, grep으로 스스로
검사·생성하는 코드 없음 확인)이라 향후 그 관례가 깨지면(다른 launcher,
수동 클론 등) 조용히 다시 틀린 값을 낼 수 있다. 이미 검증된
`spawn._repo_slug`(같은 함수를 `flows.py` 자신과 `closure_sweep.py`가
이미 신뢰하는 근거로 쓰고 있음)를 새 엔트리에 한해 권위 있는 소스로 쓰는
쪽이 이 리스크를 없앤다.

거부한 대안(rejected alternative) 2 — **신규 명시적 필드만 채택(cwd 폴백
없음).** 이슈 본문이 실측으로 보고한 이중계산은 **이미 쌓인 과거
엔트리**(`repo` 필드가 있을 리 없음, 이 필드는 이번 수정 이후에만 생김)에서
나온 것이다. 소급 폴백이 없으면 이번 PR이 머지된 시점 이후에 새로
쌓이는 세션부터만 고쳐지고, 이슈가 실측으로 지목한 core #20/#56,
on-the-record #178/#180 자체는 여전히 이중계산된 채로 남는다 — 신고된
증상 자체를 못 고치는 수정은 채택할 수 없다.

두 후보를 함께 쓰면 비용도 낮다 — `_repo_slug` 재호출은 세션 종료
시점(`_await_bounded`, 세션 생명주기당 1회)에만 일어나고, 이슈 본문이
명시한 `flows --json`의 폴링 비용 계약(§4, "1 call — gh repo view")과는
무관한 별개 호출 지점이다(그 계약은 `flows --json` 자체의 반복 호출
비용에 대한 것이지, 세션 종료 훅의 부수 호출까지 막지 않는다 — 이미
`ensure_pushed` 등 세션 종료 시점에 다른 `gh`/`git` 호출들이 있다).

레포 짧은 이름(owner 뗀 `name`만)으로 통일한 이유: `_repo_slug`는
`owner/name` 전체를 주지만, cwd 파싱 폴백은 owner를 복원할 방법이 없다
(디렉터리 이름에 owner가 안 들어감). 신규 필드에 전체 slug를 저장하면
읽기 쪽에서 신규/소급 두 경로가 다른 키 형태를 비교해야 하는 복잡도가
생긴다 — 짧은 이름 하나로 맞추면 비교 로직이 한 줄(`==`)로 끝난다. 이
레포가 다루는 조직이 사실상 하나(`tokenmaxxxer`)뿐이라 이름 충돌
리스크는 무시할 만하다.

## What will be done

1. **`gates/flows.py`**:
   - `decision_queue` 생성 루프를 `pr_by_branch.items()` 기반으로 재작성
     (위 Rationale). `unapproved_open_prs`/`flows_out` 루프는 구조 그대로
     둔다(survey: 같은 결함 아님).
   - `_cwd_repo_name(cwd) -> str | None`(basename에서 `-issue-<n>-<role>`
     접미사를 떼는 정규식, 안 맞으면 basename 그대로)와
     `_entry_repo_name(entry) -> str | None`(`entry.get("repo")` 우선,
     없으면 `_cwd_repo_name` 폴백) 헬퍼 추가.
   - `flows_payload` 상단에서 `repo_slug = spawn._repo_slug(root)`를 1회
     계산해 저장, 함수 끝의 `"repo": spawn._repo_slug(root)` 인라인 호출을
     이 변수로 교체(호출 횟수 그대로 1회 유지).
   - `_ledger_read()` 직후 `ledger_entries`를
     `[e for e in _ledger_read() if _entry_repo_name(e) == (repo_slug.split("/")[-1] if repo_slug else None)]`로
     필터링 — `sessions[].verdict` 조회와 `ledger[]`/`unattributed` 집계
     양쪽이 이 필터링된 목록을 공유해 자동으로 같이 고쳐진다.
2. **`spawn.py`**:
   - `_repo_slug` 바로 아래에 `_repo_name(root: Path) -> str | None`
     헬퍼 추가(`_repo_slug(root)`의 owner 뗀 짧은 이름).
   - `ledger_write` 호출부(`:2614-2624`)에 `"repo": _repo_name(Path(cwd).resolve())`
     필드 추가.
3. **`test_spawn.py`**: `FlowsPayload`에
   - 결함 1 회귀: 보드 레코드도 계획 블록도 없는 이슈의 열린 PR이
     `decision_queue`에 phase 1/`approve-scope`로 뜨는지 단언(PR #86 재현).
   - 결함 1 phase 분류: 보드 레코드가 `scope-approved`(scope-proposed
     아님) 상태이고 열린 PR이 있을 때 `decision_queue`가 phase 2를
     내는지 단언(기존 동작 보존 확인).
   - 결함 2 회귀: `repo` 필드가 다른 두 ledger 엔트리 중 매칭되는 것만
     집계되는지, `repo` 필드 없이 `cwd`만 있는 옛 형태 엔트리도 basename
     파싱으로 올바르게 필터링되는지(매칭/불일치 둘 다) 단언.
   - 기존 `test_sessions_alive_is_pending_dead_looks_up_ledger`,
     `test_ledger_aggregation_per_issue_and_unattributed_bucket`의
     `spawn.ledger_write(...)` 호출에 `"repo": "repo"`(setUp의
     `_repo_slug` 패치값 `"acme/repo"`와 일치하는 짧은 이름) 추가 —
     안 그러면 새 필터링 때문에 두 테스트가 빈 결과로 깨진다.

## Out of scope

- `docs/specs/flows-schema.md` 수정 — 출력 스키마 필드 형태 불변, 버전
  범프 불필요(survey/Constraints).
- `repo-status-board` 레포 수정 — 이슈 본문 명시.
- `unapproved_open_prs` 로직 변경 — 구조적으로 결함 1과 같은 갭이 없음
  (survey에서 확인: 이 필드가 채워지려면 이미 머지된 레코드가 전제됨).
- `runs/ledger.jsonl`에 이미 쌓인 과거 엔트리를 일괄 재작성(마이그레이션
  스크립트)하는 것 — 소급 폴백(cwd 파싱)이 읽기 시점에 같은 효과를 내므로
  파일을 직접 고칠 필요가 없다.

## How you'll know it worked

- `python3 -m pytest test_spawn.py -q` 전부 통과 — 기존 `FlowsPayload`
  케이스 회귀 없음(레포 필터링에 맞춰 고친 두 건 포함), 결함 1·2 회귀
  테스트 새로 통과.
- 라이브 확인: 이 저장소 자체에서 `python3 spawn.py flows --json -C .`
  실행, 예외 없이 JSON이 나오고 `repo` 필드가 이 레포의 `owner/name`으로
  찍히는지 직접 확인(합성이 아니라 이 세션 자신의 `-C .` 실행 결과).
