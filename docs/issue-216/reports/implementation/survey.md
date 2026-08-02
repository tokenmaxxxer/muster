# Survey — issue #216: `flows --json` 결함 2건

## 결함 1 — `decision_queue`가 보드 순회 구조에 갇혀 있다

`gates/flows.py:264-304` (현재):

```python
decision_queue = []
unapproved_open_prs = []
flows_out = []

for subject, roles in sorted(all_subjects.items()):
    issue_n = int(subject.split("-", 1)[1])
    role_entries = []
    stage_source = None
    for role, fm in roles.items():
        loop_state = fm.get("loop_state")
        pr = pr_by_branch.get((subject, role))
        ...
        if not pr:
            continue
        comments = comments_for(subject, pr["number"])
        approved = _pr_approved(pr, comments, approvers, subject, role)
        phase = 1 if loop_state == "scope-proposed" else 2
        if not approved:
            decision_queue.append({...})
        ...
```

`decision_queue.append`은 `for role, fm in roles.items()` 안에서만 실행된다.
`all_subjects`(`flows.py:241-244`)는 두 소스로만 채워진다:

1. `b = spawn.board(root)` — **머지된** 레코드가 있는 subject (`spawn.board`,
   `spawn.py:974-989`, `docs/issue-<n>/reports/*.md` 존재 여부).
2. `## 실행 계획` 블록이 있는 열린 이슈 (`all_subjects.setdefault(f"issue-{n}", {})`,
   `flows.py:243-244`) — 이때도 값은 빈 dict `{}`.

머지된 레코드도 계획 블록도 없는 이슈는 두 소스 어디에도 안 걸린다 —
`all_subjects`에 키 자체가 없다. 계획 블록은 있지만 레코드가 없는 이슈는
키는 있지만 `roles = {}`라서 `for role, fm in roles.items()`가 0회 반복된다.
두 경우 다 `pr_by_branch.get((subject, role))` 조회 자체가 전혀 실행되지
않는다 — `role`을 모르니 무엇을 찾을지 모른다. 실측(이슈 본문): PR #86가
열려 있는데 `decision_queue: []`.

`phase = 1 if loop_state == "scope-proposed" else 2`(`flows.py:283`)도 별개
결함이다 — 이 줄에 도달하려면 이미 `pr`가 있어야 하므로 `roles`가 비지
않은 경우에만 실행되지만, `loop_state`가 `None`(레코드는 없고 role 이름만
어쩌다 알려진 경우는 현재 코드 경로상 발생하지 않는다 — 이는 재구성 후
새로 생기는 경로)일 때 `else 2`로 떨어진다. "머지된 레코드가 없으면
정의상 phase 1"이라는 이슈 본문의 요구와 반대다.

### `pr_by_branch` — 이미 존재하는, subject/role 독립적인 PR 소스

`flows.py:246-250`:

```python
pr_by_branch = {}
for pr in prs:
    m = _BRANCH_RE.match(pr.get("headRefName") or "")
    if m:
        pr_by_branch[(m.group(1), m.group(2))] = pr
```

`prs`는 `_pr_list_all(root)`(`flows.py:38-50`) — 레포 전체 열린 PR
1회 호출 결과. `_BRANCH_RE`(`flows.py:28`, `r"^(issue-[0-9]+)/([a-z0-9-]+)$"`)가
브랜치명만으로 `(subject, role)`을 뽑아낸다 — **보드 상태와 무관**하게 이미
모든 열린 PR의 (subject, role) 쌍을 갖고 있다. 즉 결함을 고치는 데 필요한
데이터는 이미 있다 — `all_subjects` 순회를 거치지 않고 이 dict을 직접
순회하면 된다.

### `unapproved_open_prs`는 같은 결함 아님 — 손댈 필요 없음

`unapproved_open_prs.append`(`flows.py:291-295`) 조건은
`loop_state and loop_state != "scope-proposed"` — "scope-approved 이상"은
정의상 이미 머지된 레코드가 존재해야 나오는 값(레코드가 없으면
`fm.get("loop_state")`가 `None`이라 `loop_state`가 falsy)이므로, 그 subject는
`b`(board)에 이미 들어 있어 `all_subjects`에도 있다. 구조적으로 `decision_queue`와
같은 "레코드 없음" 갭이 없다 — 이번 수정 범위에서 제외.

### `comments_for` 클로저 — 재사용 가능

`flows.py:253-262`에 이미 정의돼 있고 `comments_cache`로 캐시한다
(`_issue_comments` 호출 dedup, 이슈 본문 §제약과 무관 — 이 캐시는 API
호출 절약용, 기존 코드). `decision_queue`를 별도 루프로 옮겨도 이 클로저를
그대로 재사용하면 캐시가 공유되어 중복 `gh api` 호출이 생기지 않는다
(`unapproved_open_prs` 루프가 같은 (subject, pr_number)를 다시 조회해도
캐시 히트).

## 결함 2 — `_ledger_read()`가 레포 구분 없이 전역 파일을 통째로 돌려준다

`gates/flows.py:134-147`:

```python
def _ledger_read() -> list[dict]:
    p = spawn.ROOT / "runs" / "ledger.jsonl"
    ...
```

`spawn.ROOT`(`spawn.py:34`, `Path(__file__).resolve().parent`)는 **오케스트레이터
자신의 체크아웃 디렉터리** — `spawn.py`가 어느 레포를 대상(`-C`)으로 돌든
항상 같은 파일이다. `docs/specs/flows-schema.md` §5가 이미 이 사실을 문서화:
"`sessions[]`와 `ledger[]`는 spawn.py 자신의 `runs/` 디렉터리에서 온다 —
`-C`로 넘긴 대상 보드 레포가 아니라 로컬 오케스트레이터 체크아웃의 로컬
상태다." 즉 레포별로 분리해야 한다는 자각 자체는 스펙 문서에 이미 있었으나,
`ledger.jsonl` 파일 자체(그리고 그 안의 레코드)에는 레포를 구분할 필드가
없다.

`spawn.py:2614-2624`(`ledger_write` 호출부, `_await_bounded` 안):

```python
ledger_write({
    "ts": int(time.time()), "role": role, "cwd": str(Path(cwd).resolve()),
    "session_id": result.get("session_id"),
    "cost_usd": result.get("total_cost_usd"),
    "turns": result.get("num_turns"), "rc": rc, "outcome": outcome,
    "board_delta": delta, "denials": len(denials),
    ...
})
```

`cwd`는 그 세션이 실행된 대상 레포 체크아웃 경로 — 이슈 본문이 지목한
그대로(`.../work/on-the-record-issue-178-implementation`). 이 세션 자신의
작업 디렉터리도 같은 관례(`/Users/jk/.tokenmaxxxer/work/on-the-record-issue-216-implementation`,
`git rev-parse --show-toplevel` 확인)를 따른다 — `<repo>-issue-<n>-<role>`.
단, 이 관례는 `spawn.py` 어디에도 강제·검증되지 않는다(grep 확인: `spawn.py`가
`-C` 인자를 받아 쓸 뿐, 디렉터리 이름 형식을 만들거나 검사하는 코드 없음) —
호출하는 쪽(오케스트레이터 launcher, 이 레포 밖)의 관례일 뿐이다.

`_ledger_issue()`(`flows.py:150-155`)는 `board_delta` 경로에서 이슈 번호만
뽑는다 — 레포 구분 없음. `flows_payload`(`flows.py:308-338`)는
`ledger_entries = _ledger_read()`를 두 곳에서 그대로 쓴다: (a) `sessions[]`의
`verdict` 조회(`flows.py:314-316`, `_ledger_issue(le) == issue_n`만 비교), (b)
`ledger[]`/`unattributed` 집계(`flows.py:325-338`). 두 소비 지점 다 레포
필터가 전혀 없다 — 다른 레포의 같은 이슈 번호(또는 이 경우처럼 그냥 전역
파일 전체)가 이 레포의 `flows --json` 출력에 섞여 들어간다. 실측(이슈
본문): core #20/#56 비용이 on-the-record 밑에도, on-the-record #178/#180이
core 밑에도 같은 금액으로 집계 — 실제 ~$39가 표시 ~$79.

### `_repo_slug` — 이미 검증된 재사용 대상

`spawn.py:809-812`:

```python
def _repo_slug(root: Path) -> str | None:
    r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner",
                        "-q", ".nameWithOwner"], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
```

`flows.py`에서 이미 이 함수로 대상 레포를 식별한다(`flows.py:347`,
`"repo": spawn._repo_slug(root)` — 출력 스키마 최상위 `repo` 필드,
`docs/specs/flows-schema.md` §1 `owner/name`). `gates/closure_sweep.py:134`도
독립적으로 같은 함수를 호출한다 — 이번 수정으로 `flows.py` 안에서 호출
횟수를 1회로 유지하려면(현재도 1회, `flows.py:347` 단일 호출) 결과를
변수에 담아 필터링과 출력 필드 양쪽에 재사용해야 한다(새 호출 추가 시
`docs/specs/flows-schema.md` §4의 "1 call — gh repo view" 계약과 다른
얘기가 되지는 않지만 — 그 계약은 `flows --json`의 반복 폴링 비용에 대한
것이고, `closure_sweep.find_violations`가 이미 별도로 부르는 것과 같은
급의 호출이라 문제는 아니다 — 그래도 불필요한 재호출은 피한다).

### 스카우트 — 멀티테넌트 비용 로그 귀속 관행 (외부 근거, 2026-08-03)

내부 CLI 데이터 계약(사용자향 제품 아님) — 스윕 1회(병렬 WebSearch 2건),
judge point 1회 후 수렴(내부 신호만으로 결정 가능, 추가 딥닝 불필요).

- **명시적 태깅이 경로-추론보다 우월하다는 것이 업계 공통 결론.** AWS
  Bedrock 멀티테넌트 비용 추적 가이드, LLM 코스트-어트리뷰션 사례들이
  공통으로 "요청/로그 생성 시점에 tenant_id 를 명시적으로 태깅"을 권장하고,
  "경로/리소스 이름에서 테넌트를 추론하는 방식"은 컨테이너·워크트리처럼
  리소스가 재배치·재생성되는 환경에서 깨지기 쉽다고 지목한다.
  (https://aws.amazon.com/blogs/machine-learning/cost-tracking-multi-tenant-model-inference-on-amazon-bedrock/,
  https://particula.tech/blog/per-tenant-llm-cost-attribution-multi-tenant-saas)
- **OpenTelemetry 시맨틱 컨벤션도 같은 방향**: 리소스 속성(무엇이 이
  로그를 냈는지)은 소스에서 한 번 명시적으로 기록하는 필드지, 소비
  시점에 파생시키는 값이 아니다.
  (https://opentelemetry.io/docs/specs/otel/logs/data-model/)
- **Gap**: 이 레포의 `ledger.jsonl`은 지금 어느 쪽도 아니다 — 명시적
  귀속 필드도 없고, 그렇다고 경로 파싱을 하지도 않는다(그냥 전역
  미필터). 이미 쌓인 과거 엔트리는 명시적 필드를 소급 부여할 방법이
  없다(`cwd`가 유일한 흔적) — 신규 엔트리에 명시적 필드를 넣는 것만으로는
  이슈가 실측으로 보고한 기존 이중계산이 안 고쳐진다.

## 기존 테스트 커버리지 — `test_spawn.py::FlowsPayload`

`test_spawn.py:1910-2154`. 관련 기존 케이스:

- `test_decision_queue_from_open_pr`(`:1970-1981`) — 보드 레코드가 **있는**
  subject의 PR만 검증. 레코드 없는 subject 시나리오(이번 결함의 핵심)는
  커버 안 됨.
- `test_ledger_aggregation_per_issue_and_unattributed_bucket`(`:2024-2035`),
  `test_sessions_alive_is_pending_dead_looks_up_ledger`(`:1983-1995`) —
  `spawn.ledger_write({...})` 호출에 `cwd`/`repo` 필드를 아예 안 넣는다.
  `setUp`(`:1919`)이 `spawn._repo_slug`를 `"acme/repo"` 고정값으로
  패치해둔 것은 있음 — 레포 필터링 도입 시 이 값과 맞아떨어지는 `cwd` 또는
  `repo`를 픽스처에 추가해야 두 테스트가 계속 통과한다(고치지 않으면
  깨짐 — 필터링이 매치 실패로 빈 결과를 냄).

## 결정된 범위 밖 사항 (이슈 본문이 이미 고정)

- `docs/specs/flows-schema.md`의 `ledger[]`/`decision_queue[]` 출력 필드
  **형태**는 안 바뀐다 — 둘 다 기존 필드 그대로, 새 최상위 스키마 필드
  없음. `ledger.jsonl`(내부 원시 로그, 스키마 문서가 규율하는 대상이
  아님 — `docs/specs/flows-schema.md` §5가 "local-orchestrator data"라고만
  씀, 필드 목록 없음)에 새 키(`repo`)를 추가하는 것은 이 문서의 버전 정책
  대상이 아니다.
- `repo-status-board` 레포 수정 범위 밖(이슈 본문 명시, issue #189 D3와
  같은 이유).
