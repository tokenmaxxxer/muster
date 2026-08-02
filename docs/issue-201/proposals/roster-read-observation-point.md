files:
- test_spawn.py

## Request

이슈 #201: PR #198(이슈 #192 2단계, 커밋 `f731bfd`) 머지 후 `test_spawn.py`에
`KeyError`로 항상 실패하는 테스트 2건 —
`Ledger::test_entry_carries_the_live_log_path`(`:843`)와
`IssueScopedPrompt::test_preparation_and_preamble_happen_once`(`:987`). 둘 다
`_spawn_one`이 정상 리턴한 **뒤에** `roster.read_text()`로 로스터 파일을
읽는데, `_spawn_one`은 `proc.wait()` 직후 리턴 전에 `roster_remove(roster_key)`
(`spawn.py:2548`)로 자기 항목을 지운다 — 세션이 끝났으니 로스터에 항목이 없는
게 계약대로다. 로스터에서 읽어야 할 값(라이브 로그 경로)을 로스터가 아직 살아
있는 시점에 붙잡도록 테스트의 관측점만 옮기면 된다. 기능(`spawn.py`)은
survey에서 확인한 대로 이미 정상 — `ledger_write`의 `log` 필드는 로스터
생존 여부와 무관하게 동일한 지역 변수 `log_path`(`spawn.py:2415-2416`)를
읽는다.

## Constraints

- **D1** 준수: `spawn.py`는 변경하지 않는다. 로그 보존 기능은 실측으로 정상
  동작(survey "ledger_write는 로스터와 무관" 절).
- **D2** 준수: 샌드박스의 `rulebook_checkout`/`core_root` 네트워크·clone 제약
  자체는 손대지 않는다. survey에 기록한 우회(`TOKENMAXXXER_RULEBOOKS`/
  `TOKENMAXXXER_CORE`를 로컬 체크아웃으로 지정)는 이번 조사·검증용 국지
  조치이며 저장소에 반영하지 않는다.
- **D3** 준수: `clean`의 `glob(...).unlink()`, `.warrant-hunt.count`,
  `fail_closed_downgrade`의 `failed-no-commit` 오탐 — 다시 마주치지 않았고,
  손대지 않는다.
- 요구사항 3: 세대별 로그 명명 규약(`.session.<ts>.<pid>.log`)을 테스트에
  하드코딩하지 않는다.
- 기존 통과 중인 150건은 그대로 통과해야 한다 — 회귀 없음.

## Rationale

**채택: `spawn.roster_register`를 call-through 스파이로 감싸, 세션이 아직
살아 있는 동안(등록 시점)의 엔트리를 캡처해 그 값을 두 테스트의 관측점으로
쓴다.** 원래 `roster_register`/`roster_remove` 동작은 그대로 실행되므로
로스터의 등록→삭제 생명주기(이 이슈가 지키려는 계약, 요구사항 1의 "세션
종료 시 지워진다는 사실과 양립")는 조금도 바뀌지 않는다 — 테스트는 그저
그 값이 지나갈 때 옆에서 받아 적을 뿐이다.

거부한 대안(rejected alternative) 셋:

1. **`roster_remove`를 no-op으로 몽키패치해 세션 종료 후에도 로스터 파일에
   항목이 남게 만들고, 기존 post-session 읽기(`:843`, `:987`)는 그대로 둔다.**
   이 대안을 채택하는 대신(**rather than** patching away the removal) call-through
   스파이를 택한 이유 — 이 대안은 정확히 요구사항 1이 금지한 것: 로스터
   항목이 세션 종료 시 지워진다는 실제 계약을 테스트 안에서 꺼버리고
   통과시키는 것이다. 실제 운영 코드는 여전히 종료 시 지운다(D1이
   `spawn.py` 불변을 못박음) — 테스트가 그 사실과 다른 조건에서 통과하면,
   이후 누군가 삭제 타이밍을 실수로 앞당겨도(예: `proc.wait()` 전에 지우기)
   이 테스트는 여전히 초록불을 낸다. **이 대안은 검증력을 없애는 방식으로
   통과시키는 것이라 기각한다(rejected)** — 이슈가 명시적으로 경계한 실패
   패턴이다.
2. **`spawn._session_log_path(cwd)`를 테스트에서 직접 다시 호출해 예상
   `log_path`를 재계산하고, 로스터·ledger 둘 다 대체한다.** 이 재계산
   대안 대신(**instead of** re-deriving the value) 관측 방식을 택했다 —
   요구사항 3이 금지하는 것과 본질이 같다: 명명 규약 자체를 하드코딩하진
   않아도, 그 규약을 만드는 **함수**를 테스트가 별도로 다시 불러 "정답"을
   예측하는 방식이라, 실제 세션이 쓴 값을 관측하는 게 아니라 같은 로직을
   두 번 실행해 우연히 같기를 기대하는 셈이다(타이밍 성분이 초 단위로
   바뀌면 실제로 값이 갈릴 위험도 있다). **재계산 방식은 이슈-192가 애초에
   "로스터에서 읽기"로 결정한 이유(#192 요구사항 2의 배경)를 정면으로
   되돌리는 것이라 기각한다(rejected)** — 이번 수정도 그 결정을 뒤집지
   않는다.
3. **`test_entry_carries_the_live_log_path`에서 로스터 비교를 아예 없애고,
   `entries[0]["log"]`(ledger_write가 캡처한 값) 자체의 존재만 확인한다.**
   로스터 비교를 없애는 이 대안 대신(**rather than** dropping the roster
   comparison) 유지하는 쪽을 택했다 — 이슈 #192 요구사항 2의 핵심은
   "ledger가 기록한 log 값이 그 세션이 **실제로 쓴** 라이브 로그와 같다"는
   **독립적인 두 관측점의 교차검증**이다. 로스터 비교를 없애면
   `entries[0]["log"] == entries[0]["log"]` 식의 동어반복이 되어 그
   교차검증 자체가 사라진다 — 예를 들어 나중에 누군가 `ledger_write`
   호출부의 `log_path`를 실수로 다른 변수로 바꿔도 이 테스트는 여전히
   통과한다. **교차검증이 사라지는 대안이라 기각한다(rejected)** — 로스터를
   "세션 도중" 관측점으로 유지해야 검증력이 산다.

## What will be done

1. `test_spawn.py::Ledger::test_entry_carries_the_live_log_path`
   (`test_spawn.py:800-846`): `mock.patch.object(...)` 체인에
   `spawn.roster_register`용 call-through 스파이를 추가한다 — 원본
   `roster_register`를 저장해 두고, 호출될 때마다 `(key, dict(entry))`를
   리스트에 담은 뒤 원본을 그대로 호출한다. `:843`의
   `json.loads(roster.read_text())["issue-9/execution-observation"]`을
   지우고, 캡처 리스트에서 키 `"issue-9/execution-observation"`에 해당하는
   엔트리를 꺼내 `roster_entry`로 쓴다. `:844-846`의 세 단언은 그대로 둔다.
2. `test_spawn.py::IssueScopedPrompt::test_preparation_and_preamble_happen_once`
   (`test_spawn.py:940-992`): 같은 call-through 스파이 패턴을
   `mock.patch.object(...)` 체인에 추가한다. `:987`의
   `json.loads(roster.read_text())["issue-7/execution-observation"]["log"]`를
   캡처 리스트에서 키 `"issue-7/execution-observation"`에 해당하는 엔트리의
   `"log"`로 교체한다. `:988-992`의 나머지 단언은 그대로 둔다.
3. 두 테스트 모두 `spawn.ROSTER = roster` 재할당(`:821`, `:968`)은 그대로
   유지한다 — 실제 `roster_register`/`roster_remove`가 여전히 이 임시
   파일에 대해 온전한 등록→삭제 사이클을 수행하도록(레포의
   `runs/active.json`을 건드리지 않도록) 하기 위해서다.
4. `spawn.py`는 변경하지 않는다(D1).

## Out of scope

- `spawn.py`의 로스터·ledger·로그 보존 로직 변경 — D1, 이미 정상 동작 확인.
- `rulebook_checkout`/`core_root`가 테스트 중 실제 네트워크 clone을 시도하는
  문제와 그로 인한 샌드박스 혼동 — D2, 별도 이슈로 낸다(이 세션은 손대지
  않는다).
- `clean`의 `glob(...).unlink()` 디렉터리 케이스, `.warrant-hunt.count` 유령
  파일, `fail_closed_downgrade`의 `failed-no-commit` 오탐 — D3.
- 로스터 삭제 타이밍 자체를 검증하는 새 단언(예: 세션 종료 후 로스터에 항목이
  없음을 명시적으로 확인) 추가 — 요구사항 1-3이 요구하는 것은 기존 두
  테스트를 계약과 양립하게 고치는 것이지 새 커버리지 추가가 아니다.

## How you'll know it worked

개별 실행 두 건이 각각 통과하고, 전체 스위트에 신규 실패가 없어야 한다:

```
python3 -m pytest test_spawn.py -k test_entry_carries_the_live_log_path -q
python3 -m pytest test_spawn.py -k test_preparation_and_preamble_happen_once -q
python3 -m pytest test_spawn.py -q
```

기대 결과: 위 두 개별 실행이 각각 `1 passed`, 전체 스위트가 `152 passed`
(현재 `150 passed, 2 failed`에서 실패 2건이 통과로 전환, 다른 150건은 그대로).
survey에 기록한 대로 이 저장소의 Bash 샌드박스에서 naive하게 돌리면
`rulebook_checkout`/`core_root`의 실제 git clone 시도가 저장소 경로 하위
쓰기 제약에 걸려 무관한 에러가 먼저 난다 — 이 세 커맨드를 돌릴 때는
`TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE`를 유효한 로컬 체크아웃으로
가리키거나, 네트워크가 완전히 열린 환경에서 실행해야 실제 결과가 보인다
(survey "샌드박스 확인 사항" 절 참고). 이 두 건 외 실패가 하나라도 새로
생기면 회귀로 취급한다.
