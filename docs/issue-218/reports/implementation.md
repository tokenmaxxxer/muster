---
code_under_review: f3e5d0f
loop_state: landed
closed_checks:
  - check: "python3 -m unittest test_spawn.py -v — 신규 테스트 2건
      (test_core_version_reports_sha_date_and_label_for_local_override,
      test_core_version_reports_unknown_without_network_when_nothing_found)
      전부 통과, test_core_dir_resolves_or_halts 회귀 확인 통과. 전체
      158건 중 pre-existing 환경 오류 26건(샌드박스에서 rulebook
      git-clone 이 네트워크로 막혀 발생, ProgressEvents 류)은 변경
      전(git stash 로 확인한 baseline)과 정확히 동일 — 회귀 없음"
    code_sha: f3e5d0f
  - check: "라이브 확인 — TOKENMAXXXER_CORE 를 실제 로컬 마켓플레이스
      클론(~/.claude/plugins/marketplaces/tokenmaxxxer-core)으로 가리키고
      core_version() 실행: '33bcb20 (2026-08-03, TOKENMAXXXER_CORE)' 반환.
      TOKENMAXXXER_CORE/TOKENMAXXXER_RULEBOOKS 미설정 + 관리 클론 없음
      상태에서 core_version() 실행: '버전 불명 (core 체크아웃 없음)' 반환"
    code_sha: f3e5d0f
  - check: "warrant-hunter 디스패치(대체, stance: assume-broken, 1회,
      foreground) — 2건 발견, 둘 다 반영 후 재확인 완료(아래 Hunt 절)"
    code_sha: f3e5d0f
---

# Implementation — core 체크아웃 신선도 보고 (issue #218, phase 2)

Proposal: [[core-checkout-freshness-reporting.md]](../proposals/core-checkout-freshness-reporting.md),
승인: 이슈 코멘트 `APPROVE issue-218/implementation`(single-account mode,
role-handoff contract v3 s19, PR 작성자·승인자 동일 계정 jjongkwann).

## What was done

승인된 제안의 "What will be done" 항목을 write set(`spawn.py`,
`test_spawn.py`) 안에서 그대로 이행했다:

1. **`spawn.py`**: `core_root()`의 3후보(`TOKENMAXXXER_CORE`,
   `$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core`, 형제 디렉터리) 인라인
   튜플을 `_core_candidates() -> list[tuple[str, Path]]`로 뽑아냈다 —
   우선순위·스킵 규칙(빈 값, `$` 미해석) 변경 없는 순수 리팩터.
   `core_root()`는 이 함수를 쓰도록 다시 썼고 반환값·halt 동작은
   100% 동일하다.
2. **`core_version() -> str`** 신규 추가(`core_root()` 바로 아래): 읽기
   전용 — pull도 clone도 하지 않는다. `_core_candidates()`를 훑어 첫
   매치를 `checkout_version()`과 같은 모양으로 설명(`"{sha}{dirty 표시}
   ({커밋날짜}, {출처 라벨})"`), 없으면 관리 클론(`runs/rulebooks/
   tokenmaxxxer-core`)이 있는지만 확인해 설명, 둘 다 없으면 `"버전 불명
   (core 체크아웃 없음)"`을 반환한다(halt 하지 않음).
3. `run_role()`의 스폰 로그 줄에 `core {core_version()}`을 추가했고,
   `ledger_write()` 레코드에 `"core": core_version()` 필드를 `"rulebook"`
   옆에 추가했다(기존 필드는 그대로).
4. **`test_spawn.py`**: `SpawnCmd`에 신규 2건 — 로컬 오버라이드에서
   sha·커밋날짜·출처 라벨을 담는지, 후보+관리 클론이 전부 없을 때
   네트워크 접근 없이 "버전 불명"을 반환하는지(관리 클론이 **있는**
   경로에서도 pull/clone 을 걸지 않는지까지 실제 subprocess 호출을
   가로채 검사 — 아래 Hunt 절 참고). 기존 `test_core_dir_resolves_or_halts`
   는 리팩터 후에도 그대로 통과해 halt 계약 무회귀를 확인했다(제안의
   세 번째 테스트 항목 — 새 테스트가 아니라 기존 테스트의 회귀 확인).

## Why / Upstream basis

`docs/issue-218/proposals/core-checkout-freshness-reporting.md`(frozen
write set), `docs/issue-218/reports/implementation/survey.md`(phase-1
survey) — 이슈 본문이 실측 보고한 문제(마켓플레이스 클론이 이틀간 같은
stale sha로 멈춰 있었는데 아무 로그에도 안 남음)의 근본 원인(`plugin.json`
존재만 확인, sha·신선도 미보고)과 승인된 수정 방향(로컬 오버라이드
우선순위·halt 계약은 그대로 두고, 룰북 쪽 `checkout_version()`과 대칭인
읽기 전용 보고 함수 추가) 그대로.

## 검증 — 제안 "How you'll know it worked" 대응

1. **전체 테스트 무회귀 + 신규 통과:**
   ```
   $ python3 -m unittest test_spawn.py -q
   Ran 158 tests in 5.7s
   FAILED (errors=26)
   ```
   26건은 샌드박스에서 rulebook git-clone 이 네트워크로 막혀 발생하는
   pre-existing 환경 오류(`git stash` 로 되돌린 변경 전 baseline 에서도
   정확히 26건, 156개 테스트 기준)로, 이번 변경과 무관 — 신규 158건
   기준으로도 오류 수는 그대로 26건이라 회귀 없음. `python3 -m
   unittest test_spawn.SpawnCmd -v`(core 관련 19건)는 전부 `ok`.
2. **`core_root()` halt 계약 무회귀:** `test_core_dir_resolves_or_halts`
   리팩터 후에도 그대로 통과.
3. **라이브 확인 — 로컬 오버라이드:**
   `TOKENMAXXXER_CORE=~/.claude/plugins/marketplaces/tokenmaxxxer-core
   python3 -c "import spawn; print(spawn.core_version())"` →
   `33bcb20 (2026-08-03, TOKENMAXXXER_CORE)`.
4. **라이브 확인 — 후보 전부 없음:**
   `env -u TOKENMAXXXER_CORE -u TOKENMAXXXER_RULEBOOKS python3 -c
   "import spawn; print(spawn.core_version())"` →
   `버전 불명 (core 체크아웃 없음)`(이 레포 워크트리엔 관리 클론도,
   형제 디렉터리도 없어 실측됨).

## What did not work

- 승인된 제안의 "How you'll know it worked"는 실측된 stale 마켓플레이스
  클론(`52bdc15`, 2026-08-01)을 `TOKENMAXXXER_CORE`로 가리켜 그 sha가
  나타나는지 수동 확인하라고 적었다. 기대: `52bdc15`가 나타남. 실제:
  로컬 마켓플레이스 클론이 이 세션 이전에 `33bcb20`(2026-08-03)으로 이미
  갱신돼 있어 그 sha가 나타남 — 재현 대상 자체가 사라졌다. 대신
  `core_version()`이 "현재 실제로 체크아웃된 sha·날짜를 정확히
  보고한다"는 계약은 위 검증 3에서 현재 체크아웃 상태와 정확히 일치하는
  값으로 확인됐다.

## Hunt

Phase-2 완료 전 warrant-hunter를 디스패치했다(hunt cadence). 이 세션에는
`warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아(available
agent 목록에 `claude`/`Explore`/`freelunch:freelunch-worker`/
`general-purpose`/`Plan`/`statusline-setup`뿐), adversarial(stance:
assume-broken) 프롬프트를 `general-purpose` 에이전트에 직접 넣어
foreground(run_in_background: false)로 대체 디스패치했다(이유는 아래
Rationale for deviations 절).

**결과: 2건 발견, 둘 다 반영.**

1. **HIGH — 스폰 로그가 pull 전 sha를 찍을 수 있음** (`spawn.py`, 반영
   전 2436-2441행): `core_version()`이 `core_plugin_dirs()`(내부에서
   `core_root()`를 불러 관리 클론이면 그 자리에서 `git pull`을 돔) 보다
   **먼저** 스폰 로그 프린트 줄에서 불렸다. 관리 클론이 origin 보다
   뒤처진 상태에서 로컬 오버라이드가 전혀 없으면, 로그엔 pull 전 sha가
   찍히고 세션 종료 후 `ledger_write()`엔(그 사이 `core_root()`가 이미
   pull 했으므로) pull 후 sha가 찍혀 같은 run 안에서 두 기록이 어긋난다
   — 이슈 #218이 고치려던 것과 같은 부류의 신선도 불일치가 로그 쪽에
   남는 결과였다. **반영**: `core_plugin_dirs()` 호출을 `plugins =
   plugin_dirs(...)` 바로 다음으로 당겨 pull이 항상 print보다 먼저
   끝나게 했다(룰북 쪽 `checkout_version()`은 `plugin_dirs()`가 이미 이
   순서로 pull을 앞에 두므로, 이제 core도 같은 순서로 맞아 대칭이
   완전해졌다).
2. **HIGH — "네트워크 없음" 테스트가 자기 mock을 한 번도 안 태움**
   (`test_spawn.py`, 반영 전 신규 테스트): 후보+관리 클론이 전부 없는
   경로는 `describe()` 자체를 안 불러 `subprocess.run`을 아예 안 부른다
   — `subprocess.run`을 가로챈 guard가 이 경로에서 발화한 적이 없어,
   진짜 위험(관리 클론이 **있는** 경로에서 `core_version()`이 실수로
   pull을 걸 가능성 — `core_root()`는 바로 그 경로에서 pull을 돈다)은
   검사하지 못했다. **반영**: 같은 테스트 안에 관리 클론이 실제로
   존재하는 시나리오를 추가하고 `mock.patch(..., wraps=subprocess.run)`
   으로 실제 호출을 가로채 인자에 `"pull"`/`"clone"`이 없는지 직접
   검사하도록 강화했다(신규 테스트 수는 그대로 2건 — 기존 테스트를
   강화한 것이라 새로 세지 않음).

두 반영 모두 write set(`spawn.py`, `test_spawn.py`) 밖으로 나가지 않았다.
반영 후 `python3 -m unittest test_spawn.SpawnCmd -v` 재확인: 19건 전부
`ok`.

## Open findings

없음 — Hunt 절의 2건은 모두 반영·재확인을 마쳤고, write set 확장이
필요한 미해결 항목은 남지 않았다.

## Rationale for deviations

- **Hunt를 foreground로 실행**: 코딩 역할 지침의 hunt cadence는 발화
  방식을 지정하지 않지만, freelunch 지침은 도구 호출이 필요한 모든
  작업을 background `freelunch-worker`로 위임하라고 요구한다. 이
  세션은 spawn.py가 스폰 시점에 주입한 문구("이 턴은 headless이고
  단발이다 — 세션이 끝나면 이 프로세스도 끝난다. run_in_background로
  넘긴 작업은 부모 턴이 끝나는 순간 함께 죽는다")를 과제 텍스트 안에서
  그대로 받았다 — 이 문구가 정확히 spawn.py 자신의 `_spawn_one()`이
  만드는 것과 같은 문자열임을 코드에서 확인했다(이번 변경 대상 함수
  바로 옆, `spawn.py:2420-2429`). background로 hunt를 넘기고 이 턴이
  끝나면 결과를 이어받을 방법이 없어 "완료의 정의"(커밋·push·PR)를
  못 지킬 위험이 실측된 실패 패턴으로 명시돼 있었다 — 그래서 hunt
  자체는 스킵하지 않되 foreground(run_in_background: false)로 실행해
  결과를 이 턴 안에서 직접 반영했다.
- 코드 변경(리팩터 + `core_version()` + 두 wiring 지점)은 승인된
  제안 그대로이고, hunt가 찾은 2건은 "What will be done"의 실행
  정확도를 지키기 위한 수정이라 write set을 넘지 않았다 — 승인된
  제안의 범위 자체를 넘어선 변경은 없었다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음 —
  새 환경변수·설정·의존성·마이그레이션 없음(제안 Constraints가 이미
  확정).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-218/decisions/`: 해당 없음 — `core_version()`은 신규 함수
  추가라 기존 공개 시그니처를 바꾸지 않았고, 대안 기각 사유(Rationale)는
  phase-1 제안(PR #219)에 이미 커밋돼 있다.
- [x] benchmark/investigation 수치 → `docs/issue-218/reports/`: 완료 —
  위 §검증의 테스트 실행·라이브 확인 결과가 이 파일에 있음.
- [x] Phase 1 survey: `docs/issue-218/reports/implementation/survey.md`
  (PR #219로 이미 제출)
- [x] Phase 1 proposal: `docs/issue-218/proposals/core-checkout-freshness-reporting.md`
  (PR #219로 이미 제출)
- [x] Phase 2 record: `docs/issue-218/reports/implementation.md`(this file)
- [x] Hunt: 이 파일의 §Hunt(별도 hunt 파일 없음 — 발견 2건 모두 코드
  반영으로 종결되어 disposition 을 이 record 자체에 기록)
- [x] Tests: `test_spawn.py`에 신규 회귀 2건 추가(위 §What was done
  항목 4)
