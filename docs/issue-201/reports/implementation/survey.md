# Survey — issue #201: 로스터를 세션 종료 뒤에 읽는 테스트 2건

## 스카우트 스킵 기록

스킵 조건 1(순수 버그픽스) 적용. 이슈 #201은 프로덕션 동작 변경이 전혀 없는 —
`spawn.py`는 D1에 의해 그대로다 — 테스트 관측점 교정 작업이다. 제품-형
표면(사용자가 보는 UI/API/문서)이 아니라 내부 테스트 하네스이므로 외부
best-in-class 비교 대상이 없다. scout-brief.md는 작성하지 않는다.

## 문제의 정확한 위치

`spawn.py:2461` `roster_register(roster_key, {...})` — 세션이 시작하면서
로스터에 자기 항목을 등록한다. 등록 딕셔너리 안 `"log": str(log_path)`
(`spawn.py:2464`)가 그 세션이 실제로 쓰는 라이브 로그 경로다.

`spawn.py:2548` `roster_remove(roster_key)` — `proc.wait()` 직후, `_spawn_one`이
리턴하기 **전에** 같은 항목을 로스터에서 지운다. 두 호출 사이에 `bounded` 분기
(`spawn.py:2424-2456`)가 없는 한(두 테스트 모두 `bounded` 인자를 안 넘겨
`False`가 기본이라 이 분기 자체가 안 돈다) 포크도 없다 — 동기 실행 한 줄기뿐이라
`roster_register` → (세션 실행) → `roster_remove` 순서가 예외 없이 보장된다.

즉 `_spawn_one`이 정상 리턴한 시점에는 로스터에 그 세션의 항목이 **존재하지
않는 것이 계약**이다. 두 테스트는 이 리턴 뒤에 로스터 파일을 직접 읽는다:

```python
test_spawn.py:843  roster_entry = json.loads(roster.read_text())["issue-9/execution-observation"]
test_spawn.py:987  log_path = json.loads(roster.read_text())["issue-7/execution-observation"]["log"]
```

둘 다 `KeyError`로 죽는다 — 코드가 아니라 테스트의 관측 시점이 계약과 어긋난다.

## `ledger_write`는 로스터와 무관하게 이미 올바른 값을 받는다

`spawn.py:2602-2612`의 `ledger_write({... "log": str(log_path), ...})` 호출은
로스터 상태와 완전히 독립이다 — `log_path`는 `spawn.py:2415-2416`에서 **한 번**
계산되는 지역 변수이고, `roster_register`(2464)와 `ledger_write`(2611) 둘 다
이 같은 변수를 그대로 읽는다. 로스터 등록·삭제 여부는 이 값에 전혀 영향을
못 준다. **D1이 확정한 대로 `spawn.py`는 이미 정상 동작한다 — 고칠 대상은
`test_spawn.py`뿐이다.**

## 두 테스트 전문 — 정확히 무엇이 필요한가

### `Ledger::test_entry_carries_the_live_log_path` (`test_spawn.py:800-846`)

`ledger_write`를 몽키패치해 `entries` 리스트에 실제로 넘어온 엔트리를 담는다
(`test_spawn.py:835-836`). `_spawn_one` 실행 후 세 가지를 단언한다:
1. `entries`가 정확히 1건(`:844`).
2. `entries[0]["log"] == roster_entry["log"]`(`:845`) — **ledger가 기록한 log
   값이, 세션이 실제로 라이브 중이던 동안 로스터에 등록된 값과 같다**는
   교차검증. 이슈 #192 요구사항 2의 핵심.
3. `Path(entries[0]["log"]).exists()`(`:846`) — 그 경로에 실제로 파일이 있다.

깨진 지점은 `roster_entry` 계산(`:843`) 하나뿐 — 세션 종료 후 로스터를 읽는다.

### `IssueScopedPrompt::test_preparation_and_preamble_happen_once` (`test_spawn.py:940-992`)

`spawn_cmd`를 `cat`으로 갈아끼워(`:975-976`) stdin으로 넘어간 프롬프트가 그대로
라이브 로그에 tee된다는 성질을 이용해, 워크스페이스 준비·브랜치 체크아웃·
프리앰블이 정확히 한 번만 도는지 확인한다. 이 검증은 `log_path`(그 세션이
실제로 쓴 라이브 로그 파일 경로)를 알아야만 가능하다 — 그 값을
`json.loads(roster.read_text())[...]["log"]`(`:987`)로 얻는데, 여기서 깨진다.
나머지 단언(`:989-992`, 프리앰블 1회·prep 1회)은 `log_path`만 구하면 그대로
유효하다.

이 테스트의 `ledger_write` 몽키패치는 `lambda *a, **k: None`(`:979-980`) —
값을 버린다. `log_path`를 얻을 다른 관측점이 필요하다.

## 로스터가 "세션 도중" 값을 붙잡을 수 있는 유일한 정확한 지점

`roster_register(roster_key, entry)` 호출(`spawn.py:2461`) 자체가 유일하게
"세션이 아직 살아있는 동안"의 값이 지나가는 지점이다. 이 함수를
call-through(원래 동작은 그대로 실행하되 인자를 옆에서 기록하는) 스파이로
감싸면, 로스터 파일 자체의 등록·삭제 라이프사이클(이 이슈가 지키려는
계약)을 건드리지 않으면서 그 값을 테스트 쪽에서 붙잡을 수 있다. 두 테스트
모두 `bounded=False`(기본값)라 `roster_register`는 세션당 정확히 1회만
불린다 — 캡처된 엔트리가 모호할 일이 없다.

이 값은 실제 코드가 계산한 `log_path`를 그대로 담고 있으므로(위 절 참고)
요구사항 3("`.session.<ts>.<pid>.log`를 테스트에 다시 하드코딩하지 않는다")도
자동으로 만족한다 — 테스트는 그 값을 재계산하지 않고 관측만 한다.

## 개별 재현 — 샌드박스 확인 사항 포함

이 세션의 Bash 샌드박스에서 `python3 -m pytest test_spawn.py -k '<이름>' -q`를
그대로 돌리면 이슈가 경고한 것과 같은 클래스의, 그러나 세부 증상이 다른
오염이 먼저 걸린다: `rulebook_checkout`(`spawn.py:191-`)과 `core_root()`
(`spawn.py:1773-`)가 `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE`가 안 잡히면
`ROOT/runs/rulebooks/...`로 실제 `git clone`을 시도하는데, **이 저장소 경로
밑으로 clone하면 샌드박스가 git hook 템플릿 복사를 막는다**
(`fatal: cannot copy '.../commit-msg.sample' ...: Operation not permitted`,
실측: `git clone ... runs/rulebooks/test-clone` 직접 실행으로 격리 확인). 같은
`git clone`이 `$TMPDIR` 밑으로는 문제없이 끝난다(격리 확인) — 이건 네트워크
차단이 아니라 저장소 경로 하위 쓰기에 걸린 샌드박스 훅-복사 제약이다. 이
제약이 `_spawn_one` 안 서로 다른 지점(rulebook clone 실패 시 `SystemExit`,
core clone 실패 시 `is_parent_return` 참조 전에 `SystemExit`가 나 `finally`에서
`UnboundLocalError`)에서 서로 다른 가짜 실패를 낸다 — 이슈 본문이 경고한
"샌드박스발 대량 에러"의 이번 세션판 변주다.

우회: `/private/tmp/claude-501/rulebooks-cache/execution-observation-rulebook`에
이미 유효한 로컬 룰북 체크아웃이 있었고, `tokenmaxxxer-core`는
`git clone https://github.com/tokenmaxxxer/tokenmaxxxer-core.git $TMPDIR/...`로
직접(레포 경로 밖에) 떠서 확보했다. `TOKENMAXXXER_RULEBOOKS`·
`TOKENMAXXXER_CORE`를 이 둘로 가리키자 두 clone 시도 모두 로컬 체크아웃
히트로 스킵되고, 실제 코드 경로(로스터 등록 → 세션 실행 → 로스터 삭제)까지
도달한다.

### 개별 실행 결과 (라우팅 후, 실측 2026-08-02)

```
$ python3 -m pytest test_spawn.py -k test_entry_carries_the_live_log_path -q
...
>           roster_entry = json.loads(roster.read_text())["issue-9/execution-observation"]
E           KeyError: 'issue-9/execution-observation'
test_spawn.py:843: KeyError
FAILED test_spawn.py::Ledger::test_entry_carries_the_live_log_path - KeyError...
1 failed, 151 deselected in 0.48s
```

```
$ python3 -m pytest test_spawn.py -k test_preparation_and_preamble_happen_once -q
...
>           log_path = json.loads(roster.read_text())["issue-7/execution-observation"]["log"]
E           KeyError: 'issue-7/execution-observation'
test_spawn.py:987: KeyError
FAILED test_spawn.py::IssueScopedPrompt::test_preparation_and_preamble_happen_once
1 failed, 151 deselected in 0.43s
```

### 전체 스위트 (라우팅 후)

```
$ python3 -m pytest test_spawn.py -q
...
FAILED test_spawn.py::Ledger::test_entry_carries_the_live_log_path - KeyError...
FAILED test_spawn.py::IssueScopedPrompt::test_preparation_and_preamble_happen_once
2 failed, 150 passed in 13.14s
```

이슈 본문이 실측한 "2 failed, 150 passed"와 정확히 일치 — 이 두 건 말고 다른
회귀는 없다. `main` = `93038c0` (이 브랜치의 시작점과 동일).

## 이미 결정된 것(D1-D3)과의 관계

- **D1** (spawn.py는 안 되돌린다): 위 "ledger_write는 로스터와 무관" 절이
  실측으로 뒷받침 — `spawn.py`를 건드릴 이유 자체가 없다.
- **D2** (샌드박스 네트워크/clone 문제는 범위 밖): 위 "샌드박스 확인 사항"에
  기록한 우회는 이번 세션이 재현·검증하기 위한 국지적 조치일 뿐, 저장소에
  반영할 변경이 아니다. `rulebook_checkout`/`core_root`의 clone 경로 자체를
  고치는 건 이 이슈의 범위가 아니다.
- **D3** (clean의 glob(...).unlink(), `.warrant-hunt.count`, fail_closed_downgrade
  오탐): 이번 조사에서 다시 마주치지 않았다 — 손대지 않는다.

## 쓰기 대상(write set) 예상

`test_spawn.py` 단 하나. 두 테스트 함수의 로스터 읽기 지점만 교체한다.
프로덕션 코드(`spawn.py`), 문서, 의존성, 마이그레이션 변경 없음.
