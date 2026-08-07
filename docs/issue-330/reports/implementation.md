---
code_under_review:
  - gates/gates.py
  - gates/test_gates.py
loop_state: phase-2-complete
open_findings: none
---

# issue-330: 변경의 반경(reach) 검사 — path-shaped 오차니드 게이트

## What was done

1. `gates/gates.py::orphaned_references(work, base=BASE)` — PR 이 삭제
   (`D`)하거나 개명(`R`/`C` 구경로)한 경로를, diff 밖의 나머지 추적
   파일에서 `git grep -F`로 문자열 검색해 아직 살아있는 참조를
   `(구경로, 참조파일)` 쌍으로 낸다. `_committed_changes_with_status`
   가 이미 계산해두는 status 를 재사용 — 새 diff 파싱 로직을 만들지
   않았다.
2. `gates/gates.py::reach_check(work, record_text, base=BASE)` —
   `orphaned_references`의 히트마다, 레코드 텍스트의 `## Reach`
   섹션 본문에 그 구경로(또는 그 상위 디렉터리)가 언급됐는지 검사한다.
   언급 안 된 히트는 실패 문자열로 낸다. 빈 히트는 트리비얼 통과.
3. `gates/test_gates.py`(신규 파일) — 임시 git 저장소를 실제로 초기화해
   커밋 diff 를 만드는 6개 테스트: 삭제 없음(트리비얼 통과), 삭제된
   경로가 diff 밖에서 참조되는 경우(히트), 개명 구경로가 참조되는
   경우(히트), `## Reach`에 미언급이면 `reach_check` 실패, 언급되면
   통과, 삭제가 없으면 `reach_check`도 트리비얼 통과.
   `python3 gates/test_gates.py` → 6 passed (실제로 실행해 확인함).

`ALL` 딕셔너리(CI/PreToolUse 배선용 게이트 레지스트리)에는 추가하지
않았다 — 제안서 Out of scope #1(CI 배선은 별도 이슈)과 일치한다.
`reach_check`는 `(work, record_text)` 시그니처라 `ALL`의 균일한
`(d, cfg)` 시그니처와 안 맞기도 한다 — 배선 시점에 어댑터가 필요하고,
그건 CI 와이어링 이슈의 몫이다.

## 조건부 승인 피드백 이행 — 3개 사고 중 실제로 몇 개를 잡았을까

승인에 붙은 피드백이 요구한 대로, `orphaned_references`를 세 사고의
**실제 히스토리 diff**에 대고 그대로 돌렸다:

- **#285→#296/#297** (`d04b36a^1...d04b36a`, 그리고 `d04b36a...11e459e`):
  `git diff --name-status` 둘 다 `M spawn.py`/`M test_spawn.py`만 낸다.
  삭제도 개명도 없다 — 마커의 *쓰기 위치*가 클론 내부에서 `runs/`로
  바뀐 것이지, 어떤 경로도 diff 상에서 삭제·개명되지 않았다. **잡지
  못한다.**
- **#297→#313** (`11e459e...ec85a22`): 마찬가지로 `M spawn.py`,
  `M test_spawn.py`만 있다. 사고의 본질(이미 디스크에 쓰인 옛 위치의
  마커 파일들이 무효화되지 않고 남음)은 git diff 에 전혀 나타나지
  않는 상태다 — 그 마커 파일들은 애초에 버전관리 대상이 아니다(런타임
  생성물). **잡지 못한다.**
- **#140→#147** (`da2c3de...3ae588b`): `M README.ko.md`, `M README.md`,
  `M protocol.ko.md`, `M protocol.md`만 있다. 어휘를 추가한 것이지
  어떤 경로도 삭제·개명되지 않았다. **잡지 못한다.**

**정직한 숫자: 3개 중 0개.** 세 사고 모두 파일 *내용*(런타임 상태 값,
쓰기 목적지, 어휘)이 바뀐 것이었고 파일 *경로*는 셋 다 안 바뀌었다 —
제안서의 Rationale/Out of scope 가 이미 "path-shaped reach만 잡는다,
semantic/behavioral impact는 out of scope"라고 명시했던 그대로다. 이
게이트가 잡는 범위(경로 삭제·개명 후 잔존 참조)와, 세 사고가 실제로
속한 범위(같은 경로 안에서 값·의미·어휘가 바뀐 것)는 겹치지 않는다.

승인 코멘트가 지적한 "1/3(어휘 경로 아님)"보다도 더 좁다 — dependency
graph 대안을 기각한 근거였던 세 사고 자체가, 이 게이트로도 하나도
안 잡힌다. 이 게이트는 세 사고와 다른 종류의 위험(경로 삭제 후 잔존
참조)에 대한 방어이지, 세 사고의 재발 방지 수단이 아니다. 그 사실을
호도하지 않기 위해 여기 그대로 적는다.

**남은 유형(이 PR 에서 확장하지 않음, 범위 밖)**: 값·의미·어휘 수준의
반경 — 같은 경로 안에서 쓰기 목적지, 런타임 상태 값, 또는 계약 어휘가
바뀌었을 때 그걸 가정하는 다른 코드/이미 디스크에 있는 상태를
찾아내는 검사. 별도 이슈로 제출할 것 (조건부 승인 요구사항).

## Reach

이 변경은 어떤 경로도 삭제·개명·이동하지 않는다 — `gates/gates.py`
수정(함수 2개 추가)과 `gates/test_gates.py` 신규 생성뿐이고,
`orphaned_references`/`reach_check` 자체도 `ALL` 레지스트리에
등록하지 않아 기존 CI/PreToolUse 배선의 동작을 바꾸지 않는다.
이미 디스크에 있는 상태 중 이 변경이 무효화하는 것은 없다.
`docs/issue-330/proposals/2026-08-07-impact-reach-check.md`의
`## What will be done` 항목 1(레코드 필수 섹션에 `## Reach` 추가)은
이 레코드 자신에 그 섹션을 두는 것으로 충족했다 — `record-fields-gate.sh`
자체(온더레코드 레포의 규칙 스켈레톤, 이 저장소 밖)를 고치는 건
이 프로포절의 write-set(`gates/gates.py`, `gates/test_gates.py`,
`docs/issue-330/reports/implementation.md`)밖이라 손대지 않았다 —
그래서 다른 role/이슈의 레코드에 `## Reach`를 강제하는 기계적 장치는
아직 없다. 그 갭은 후속 이슈(CI 배선 이슈와 별도로)로 남는다.

## What did not work

None.

## Hunt

Docs-only fast path 아님(코드 diff 존재) — before-landing 워런트헌트는
`git diff --stat` 기준 diff 크기가 작아(gates.py +~65줄, test_gates.py
신규 ~110줄) 120초 캡, 단일 스탠스로 별도 백그라운드 세션에서 이미
after-proposal 시점에 1회 수행되었다는 전제 하에, 이번 phase-2
완료 시점 두 번째 디스패치는 이 세션이 headless/single-shot이라 결과를
같은 턴 안에서 소비할 수 없어(계약 v3 s22 우선) 생략한다 — 대신 이
레코드가 그 사실 자체를closed_checks 아닌 스킵으로 명시한다.

closed_checks:
- `python3 gates/test_gates.py` 실행 확인 (6 passed) — code_sha 는 이
  레코드와 같은 커밋.
