# Survey — issue #248: `flows[].prs`와 `decision_queue`의 불일치

## 1. 현재 상태: 두 필드가 다른 소스에서 나온다

`gates/flows.py::flows_payload()` 안에 `decision_queue`와 `flows[].prs`를
채우는 두 개의 독립된 루프가 있다.

### 1.1 `decision_queue` (`flows.py:300-312`)

```python
for (subject, role), pr in sorted(pr_by_branch.items()):
    ...
    decision_queue.append({...})
```

`pr_by_branch`(`flows.py:274-278`)는 `_pr_list_all(root)`(`gh pr list
--state open ...`) 결과를 브랜치명(`_BRANCH_RE = issue-<n>/<role>`)만으로
파싱해 만든 `(subject, role) -> pr` 맵이다 — board 레코드 유무와 무관하게
**열려 있는 PR이면 전부** 잡힌다. 이 구조는 issue #216에서 명시적으로
채택됐다(`docs/issue-216/proposals/flows-accuracy-fix.md` Rationale
결함 1) — 이전에는 `decision_queue`도 board 순회(`all_subjects` →
`roles.items()`) 안에서만 채워져 board 레코드가 없는 subject의 PR을
구조적으로 놓쳤고, #216이 이를 `pr_by_branch.items()` 직접 순회로
바꿔 고쳤다.

### 1.2 `flows[].prs` (`flows.py:314-342`, 특히 339-340)

```python
for subject, roles in sorted(all_subjects.items()):
    ...
    for role, fm in roles.items():
        ...
    flows_out.append({
        ...
        "prs": sorted({pr_by_branch[(subject, r)]["number"]
                      for r in roles if (subject, r) in pr_by_branch}),
        ...
    })
```

`roles`는 `all_subjects[subject]`, 즉 `spawn.board(root)`가 돌려주는
`b[subject]` — **`docs/issue-<n>/reports/<role>.md`가 main에 이미 존재하는
role만**의 dict다(`spawn.py:990-997`: `rep / f"{r}.md"` 파일이 있는 role만
`roles` dict에 들어간다). `prs`는 이 `roles`의 키 집합으로 `pr_by_branch`를
**한 번 더 필터링**한다 — board에 머지된 레코드가 없는 role의 PR은
`pr_by_branch`에 있어도 `for r in roles` 자체가 돌지 않으므로 절대
`prs`에 못 들어간다.

`all_subjects`는 `dict(b)`에 "OPEN 상태 + `## 실행 계획` 블록이 issue
본문에 있는" subject를 `setdefault(f"issue-{n}", {})`(빈 dict)로만
추가한다(`flows.py:269-272`) — 이 union-확장도 `roles`를 채우지 않으므로
`prs` 필터링에는 영향이 없다.

### 1.3 재현: issue 27

이슈 본문의 실측과 로컬 코드 추적이 일치한다. issue-27의 board 레코드는
`implementation` 하나뿐이고(다른 두 role은 PR이 아직 open이라 main에
레코드 파일이 없음), `implementation`의 PR #28은 이미 머지돼
`pr_by_branch`에서 빠졌다. 따라서:

- `decision_queue` 루프: `pr_by_branch`에 `(issue-27, conformance-review)`
  PR #32와 `(issue-27, execution-observation)` PR #31이 그대로 있어
  둘 다 채택됨 — 이슈 본문 실측과 일치.
- `flows[].prs` 루프: `roles = {'implementation': ...}` 뿐이라
  `conformance-review`/`execution-observation`은애초에 순회 대상이
  아니고, `implementation`은 `pr_by_branch`에 없음(머지됨) → `prs: []`.

가설("레코드가 있는 role × 열린 PR 교집합이 비면 prs도 빈다")과 코드
추적 결과가 정확히 일치한다.

## 2. 관련 선례 — issue #216이 이 필드를 명시적으로 건드리지 않았다

`docs/issue-216/reports/implementation/survey.md:71` 절
"`unapproved_open_prs`는 같은 결함 아님 — 손댈 필요 없음"에서 #216의
survey는 `flows_out`/`prs` 코드를 이미 읽었지만(같은 survey 62-70행대,
`prs`가 `_pr_list_all` 기반이라고 언급) `decision_queue`만 고치고
`prs`는 out-of-scope로 남겼다(`docs/issue-216/proposals/flows-accuracy-fix.md`
"Out of scope" 절: "`unapproved_open_prs` 로직 변경 없음" — `prs`는
언급조차 안 됨, 즉 전환 자체가 안 됨). 이번 이슈(#248)가 지적하는
불일치는 바로 이 미전파의 결과다.

## 3. `docs/specs/flows-schema.md` §2.2 현재 서술

`flows-schema.md:85`:

```
| `prs` | array of integers | PR numbers associated with the subject |
```

"associated with the subject"만으로는 (a) open PR만인지 merged 포함인지,
(b) board 레코드가 있는 role만인지 전체 role인지가 계약상 불명확하다 —
이슈 본문이 지적한 것과 동일. 정정 후에는 실제 포함 기준(§1.2에서 확인한
현재 동작이 아니라, 이번 수정 후의 동작)을 명시해야 한다.

## 4. 테스트 현황

`test_spawn.py::FlowsPayload`(2704-2883행)가 `gates/flows.py`의 테스트
홈이다. `setUp`이 `_pr_list_all`/`_issue_list_all`/`_repo_slug`/
`_issue_comments`/`_roster_load`/`closure_sweep.find_violations`를
전부 몽키패치해 라이브 `gh` 호출 없이 동작한다. `_write_record(subject,
role, loop_state, ...)` 헬퍼가 board 레코드 파일을 만든다.

기존 `test_decision_queue_from_open_pr_with_no_board_record`(2777행)가
정확히 이번 결함의 `decision_queue` 쪽 대응 사례(#216 회귀 테스트)다 —
`flows[].prs`에 대한 대응 테스트는 아직 없다. 이번 수정은 같은 패턴
(`_pr_list_all`을 패치해 board 레코드 없는 role의 open PR을 주입,
`payload["flows"]`에서 해당 subject를 찾아 `prs`를 단언)으로 추가하면
된다 — 새 헬퍼나 새 몽키패치 지점 불필요.

## 5. 예상 write set

- `gates/flows.py` — `prs` 산출 로직을 `pr_by_branch`(subject 필터링)
  기반으로 교체. `decision_queue`/`unapproved_open_prs` 루프 구조는
  그대로(같은 결함 아님, #216 survey와 동일 판단 근거).
- `docs/specs/flows-schema.md` — §2.2 `prs` 행 설명을 실제 포함 기준으로
  보완. `schema_version`/필드 목록은 불변(요구사항 3).
- `test_spawn.py` — `FlowsPayload`에 board 레코드 없는 role의 open PR이
  `flows[].prs`에 채워지는 회귀 테스트, 그리고 `decision_queue`와
  `flows[].prs`가 같은 PR 집합에 대해 일치함을 단언하는 테스트 추가.

## 6. Scout skip record

이 변경은 **pure bugfix**에 해당해 scout 단계를 skip한다(scout-directive
skip condition 1). 근거:

- 결함이 단일 레포 내부 JSON API의 **자기 일관성**(같은 payload 안
  `decision_queue`와 `flows[].prs`가 같은 PR에 대해 다른 값을 냄) 문제이지,
  외부 제품/UI 표면이나 카테고리 모범 사례가 관여하는 지점이 아니다 —
  소비자(repo-status-board)는 받은 배열을 그대로 렌더링할 뿐(이슈 본문
  명시).
- 고칠 방향이 이미 같은 파일 안에 확립된 패턴(`pr_by_branch`, #216이
  `decision_queue`에 채택한 것과 동일한 소스)을 재사용하는 것으로 좁게
  결정돼 있다 — 이슈 본문 "추정 원인" 절 자체가 근본 원인과 해법 방향을
  이미 상당히 짚어 놓았다.
- 남은 설계 결정은 "두 필드가 완전히 같은 PR 집합을 공유하도록 통일할지,
  아니면 다른 기준(예: role별 필터 유지)을 새로 도입할지" 하나뿐이고,
  이는 이슈 수용 기준("decision_queue와 flows[].prs가 같은 PR에 대해
  불일치하지 않음")이 이미 답을 못박아 폭넓은 외부 리서치가 필요한
  결정이 아니다.

## loop_state

phase 1 완료 — survey 작성 후 proposal 작성으로 진행.
