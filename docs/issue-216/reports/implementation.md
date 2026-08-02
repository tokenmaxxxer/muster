---
code_under_review: dddbada
loop_state: landed
closed_checks:
  - check: "python3 -m pytest test_spawn.py -q — 156 passed, 0 failed
      (기존 FlowsPayload 케이스 무회귀 + 신규 회귀 테스트 3건 포함)"
    code_sha: dddbada
  - check: "라이브 확인 — python3 spawn.py flows --json -C . 를 이 레포
      자신에서 실행, 예외 없이 JSON 출력, repo 필드가
      tokenmaxxxer/on-the-record 로 정확히 찍힘, decision_queue가 이미
      승인된 이 세션 자신의 PR #217을 (승인 기록이 있어) 빈 상태로 정확히
      제외함"
    code_sha: dddbada
  - check: "warrant-hunter 디스패치(대체, stance: assume-broken 1개) —
      docs/reports/2026-08-03-hunt-issue-216-flows-accuracy-fix.md, 3건
      관찰 모두 write-set 확장 없이 종결(disposition 기록됨)"
    code_sha: dddbada
---

# Implementation — `flows --json` 정확도 결함 2건 (issue #216, phase 2)

Proposal: [[flows-accuracy-fix.md]](../proposals/flows-accuracy-fix.md),
승인: 이슈 코멘트 `APPROVE issue-216/implementation`(single-account mode,
role-handoff contract v3 s19, PR 작성자·승인자 동일 계정 jjongkwann).

## What was done

승인된 제안의 "What will be done" 3개 항목을 그대로 이행했다 — write set
(`gates/flows.py`, `spawn.py`, `test_spawn.py`) 밖으로 나가지 않았다:

1. **`gates/flows.py`**:
   - `decision_queue` 생성을 `pr_by_branch.items()` 기반 별도 루프로
     재작성(`flows.py:268-280` 부근) — 보드 레코드(`b.get(subject,
     {}).get(role, {})`)는 있으면 `loop_state`/`phase` 판단에만 조인.
     `phase = 1 if loop_state in (None, "scope-proposed") else 2`.
   - `unapproved_open_prs`/`flows_out` 루프는 `all_subjects` 순회 구조
     그대로 두고 `decision_queue.append`만 걷어냈다(제안 그대로 — 같은
     결함 아님).
   - `_cwd_repo_name(cwd) -> str | None`, `_entry_repo_name(entry) ->
     str | None` 헬퍼 추가(`_ledger_issue` 바로 아래).
   - `flows_payload` 상단에서 `repo_slug = spawn._repo_slug(root)`를 1회
     계산, 함수 끝의 인라인 호출을 이 변수로 교체(호출 횟수 그대로 1회).
   - `_ledger_read()` 직후 `ledger_entries`를 `repo_name = repo_slug.split
     ("/")[-1] if repo_slug else None`와 `_entry_repo_name(e) ==
     repo_name`으로 필터링 — `sessions[].verdict` 조회와 `ledger[]`/
     `unattributed` 집계 양쪽이 이 필터링된 목록을 공유.
2. **`spawn.py`**: `_repo_slug` 바로 아래 `_repo_name(root) -> str | None`
   추가, `ledger_write` 호출부(`_await_bounded` 안)에 `"repo": _repo_name
   (Path(cwd).resolve())` 필드 추가.
3. **`test_spawn.py`**: `FlowsPayload`에 신규 3건 —
   `test_decision_queue_from_open_pr_with_no_board_record`(결함 1, PR #86
   재현), `test_decision_queue_phase_2_when_board_record_is_scope_approved`
   (결함 1, 기존 phase 2 분류 무회귀 확인),
   `test_ledger_filtered_by_repo_field_and_cwd_fallback`(결함 2, `repo`
   필드 매칭/불일치 + `cwd`-only 옛 형태 엔트리 basename 파싱 매칭/불일치
   양쪽). 기존 `test_sessions_alive_is_pending_dead_looks_up_ledger`,
   `test_ledger_aggregation_per_issue_and_unattributed_bucket`의
   `spawn.ledger_write(...)` 호출에 `"repo": "repo"`(setUp의
   `_repo_slug` 패치값 `"acme/repo"`와 일치하는 짧은 이름) 추가.

## Why / Upstream basis

`docs/issue-216/proposals/flows-accuracy-fix.md`(frozen write set),
`docs/issue-216/reports/implementation/survey.md`(phase-1 survey) — 이슈
본문이 실측 보고한 두 결함(PR #86 미노출, core/on-the-record 비용
이중계산 ~$39 대 표시 ~$79)의 근본 원인과 고정된 수정 방향 그대로.

## 검증 — 제안 "How you'll know it worked" 대응

1. **전체 테스트 무회귀 + 신규 회귀:**
   ```
   $ python3 -m pytest test_spawn.py -q
   ........................................................................ [ 46%]
   ........................................................................ [ 92%]
   ............                                                             [100%]
   156 passed in 16.22s
   ```
2. **라이브 확인 — 이 레포 자신에서 `flows --json -C .` 직접 실행:**
   예외 없이 JSON 출력, `"repo": "tokenmaxxxer/on-the-record"` 정확히
   찍힘. `decision_queue`는 빈 리스트로 나왔는데, 이는 결함이 아니라
   정확한 동작이다 — 이 세션 자신의 PR #217이 이슈 코멘트
   `APPROVE issue-216/implementation`으로 이미 승인된 상태이고,
   `_pr_approved`가 `comments_for`를 통해 이슈 레벨 코멘트까지 검사하므로
   `approved=True`가 되어 대기열에서 정확히 빠진다 — 재구성된
   `decision_queue` 로직이 실물 데이터에서도 승인 여부를 올바르게
   반영한다는 실측 확인.

## What did not work

None.

## Hunt

phase-2 완료 전 warrant-hunter를 디스패치했다(hunt cadence). 이 세션에는
`warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아(available
agent 목록에 없음 — `claude`/`Explore`/`freelunch:freelunch-worker`/
`general-purpose`/`Plan`/`statusline-setup`뿐), adversarial(stance:
assume-broken) 프롬프트를 `general-purpose` 에이전트에 직접 넣어 대체
디스패치했다.

**결과: 3건 관찰, 전부 write set 확장 없이 종결.** 기록:
[docs/reports/2026-08-03-hunt-issue-216-flows-accuracy-fix.md](../../reports/2026-08-03-hunt-issue-216-flows-accuracy-fix.md).

요지 — (1) `repo_slug`가 `None`이면(`gh` 실패) ledger가 조용히 전부
빈다: 승인된 제안의 필터 표현을 글자 그대로 구현한 결과이고 모듈의
기존 `gh`-실패 관례(조용한 빈 값 저하)와 같은 급이라 phase-2에서
임의로 재설계하지 않았다. (2) 레포 이름 자체가 `-issue-N-role` 모양과
우연히 겹치면 `_cwd_repo_name`이 오인식할 수 있다: 제안 Rationale이
이미 이 리스크를 논의했고(cwd 파싱은 과거 엔트리 소급 폴백일 뿐, 신규
엔트리는 명시적 `repo` 필드가 권위 소스), 설계가 이미 안고 가기로 한
트레이드오프다. (3) `decision_queue`에는 뜨는데 `flows[]`에는 없는
이슈가 생길 수 있다: 이것이 바로 결함 1을 고치는 목적이라 버그가 아니다.

## Open findings

없음 — Hunt 절의 3건은 모두 disposition을 마쳤고(hunt record 참고)
write set 확장이 필요한 미해결 항목은 남지 않았다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음 —
  새 환경변수·설정·의존성·마이그레이션 없음(`ledger.jsonl`의 `repo` 키는
  제안 Constraints가 이미 스키마 정책 대상 아니라고 확정).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-216/decisions/`: 해당 없음 — `flows --json` 출력 스키마
  필드 형태 불변(제안 Constraints), 새 결정 없이 phase-1 제안의 결정을
  그대로 이행.
- [x] benchmark/investigation 수치 → `docs/issue-216/reports/`: 완료 —
  위 §검증의 테스트 실행·라이브 확인 결과가 이 파일에 있음.
- [x] Phase 1 survey: `docs/issue-216/reports/implementation/survey.md`
  (PR #217로 이미 제출)
- [x] Phase 1 proposal: `docs/issue-216/proposals/flows-accuracy-fix.md`
  (PR #217로 이미 제출)
- [x] Phase 2 record: `docs/issue-216/reports/implementation.md`(this file)
- [x] Hunt record: `docs/reports/2026-08-03-hunt-issue-216-flows-accuracy-fix.md`
- [x] Tests: `test_spawn.py`에 신규 회귀 3건 추가 + 기존 2건 픽스처 보정
  (위 §What was done 항목 3).
