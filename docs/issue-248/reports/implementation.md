---
code_under_review:
  - gates/flows.py
  - docs/specs/flows-schema.md
  - test_spawn.py
loop_state: landed
closed_checks:
  - check: "python3 -m pytest test_spawn.py -q — 181 passed, 0 failed
      (기존 FlowsPayload 17건 무회귀 + 신규 회귀 테스트 2건 포함)"
    code_sha: c0daeab
  - check: "라이브 확인 — python3 spawn.py flows --json -C . 를 이 레포
      자신에서 실행, 예외 없이 JSON 출력(schema_version 1, flows 31건).
      flows[].prs 가 채워진 6건 중 issue 248 자신이 이 세션의 실물 PR
      #252 를 정확히 담음. decision_queue 의 모든 (issue, pr) 쌍이 같은
      issue 의 flows[].prs 부분집합임을 jq 로 직접 대조 확인
      (issue 224/227/245/246/247 전부 일치, 불일치 0건)."
    code_sha: c0daeab
  - check: "warrant-hunter 디스패치(대체, general-purpose, stance:
      composition regression 1개 고정) —
      docs/reports/2026-08-03-hunt-issue-248-flows-prs-consistency-fix.md.
      FINDING 1건(design-error: 방금 쓴 스키마 문서 문단의 '결코
      불일치하지 않는다' 주장이 flows[] 자체에 엔트리가 없는 subject에는
      성립하지 않음) — write set 확장 없이 같은 파일 문구를 정확한
      범위로 좁혀 종결. blocking 아님."
    code_sha: c0daeab
---

# Implementation record — issue #248

Phase 2, executing the approved proposal
(`docs/issue-248/proposals/flows-prs-consistency-fix.md`, approved via
issue-level comment `APPROVE issue-248/implementation`, single-account
mode, role-handoff contract v3, PR author and approver both
jjongkwann, 2026-08-03T11:29:03Z).

## What was done

1. **`gates/flows.py`**: `pr_by_branch` 바로 뒤에 `prs_by_subject: dict[str,
   set[int]]`를 추가(같은 값 재사용, 새 `gh` 호출 없음) — `pr_by_branch`를
   subject로 그룹핑. `flows_out`의 `"prs"`를
   `sorted(prs_by_subject.get(subject, set()))`로 교체 — 이전에 있던
   `roles`(board 레코드가 있는 role만) 필터를 제거.
2. **`docs/specs/flows-schema.md`**: §2.2 `prs` 행 설명을 실제 포함
   기준(현재 열려 있는 PR 중 브랜치명이 `issue-<subject>/<role>` 패턴에
   매칭되는 전부, role의 board 레코드 존재 여부와 무관)으로 교체하고,
   `decision_queue`와 `flows[].prs`가 같은 소스를 공유해 (flows[]에
   엔트리가 있는 subject에 한해) 불일치하지 않는다는 문단을 추가.
3. **`test_spawn.py`**: `FlowsPayload`에
   `test_flows_prs_includes_open_prs_for_roles_with_no_board_record`(issue
   27 재현: board 레코드가 하나뿐인 role은 PR이 머지돼 없고, 레코드 없는
   두 role의 open PR이 `flows[].prs`에 모두 채워지는지 단언)와
   `test_flows_prs_and_decision_queue_share_the_same_pr_set`(승인된 PR과
   미승인 PR을 섞어 `decision_queue`가 부분집합만 가질 때도
   `flows[].prs`는 전체를 갖는지, 그리고 `decision_queue` 쪽 PR 전부가
   `flows[].prs`의 부분집합인지 단언) 두 건 추가.

## Why

`decision_queue`는 이미 `pr_by_branch.items()`를 직접 순회해 board 레코드
유무와 무관하게 열린 PR을 전부 잡는다(issue #216). `flows[].prs`는 대신
`roles`(board 레코드가 있는 role만)로 한 번 더 필터링해 issue 27 같은
사례에서 빈 배열을 냈다. 같은 소스(`pr_by_branch`)를 subject로만 그룹핑해
공유하면 두 필드가 구조적으로 같은 PR 집합을 갖게 돼 수용 기준을
산출 로직 수준에서 보장한다. 제안서 Rationale 참고 — 거부한 대안은
`roles` 필터를 유지하며 `all_subjects`를 넓히는 안이었으나, 이는
`flows[].roles`의 계약(board 레코드가 있는 role의 상태만 표시)을
침범하므로 기각됨.

## Open findings

None blocking. 헌트가 찾은 1건(스키마 문서 문단의 과잉 일반화)은 같은
턴에서 문구를 좁혀 종결 — 아래 "What did not work" 참고.

## What did not work

- §2.2에 처음 쓴 일관성 문단이 "decision_queue와 flows[].prs가 결코
  불일치하지 않는다"를 무조건 성립하는 것처럼 썼는데, 실제로는
  `flows[]`에 엔트리 자체가 없는 subject(board 레코드도 `## 실행 계획`도
  없는 이슈, issue #216 선례와 동일 케이스)에서는 비교 대상인
  `flows[].prs`가 존재하지 않아 그 문장이 과잉 일반화였다 — 헌트
  디스패치(위 closed_checks)가 재현으로 확인, 같은 파일 안에서 "flows[]에
  엔트리가 있는 subject에 한해"로 범위를 좁혀 고쳤다.

## Rationale for deviations

해당 없음 — 제안서의 "What will be done" 항목 1-3을 그대로 구현했다.
헌트가 찾은 문서 문구 수정은 제안서가 이미 정한 write set
(`docs/specs/flows-schema.md`) 안에서의 정확도 보정이며, 새 파일이나
새 동작을 추가하지 않았으므로 이탈로 보지 않는다.
