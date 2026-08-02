files:
- conftest.py
- tests/fixtures/rulebooks/execution-observation-rulebook/.claude-plugin/marketplace.json
- tests/fixtures/rulebooks/execution-observation-rulebook/execution-observation/.claude-plugin/plugin.json
- tests/fixtures/rulebooks/tokenmaxxxer-core/core/.claude-plugin/plugin.json

## Request

이슈 #204: 네트워크 차단 샌드박스에서 `python3 -m pytest test_spawn.py
test_gates.py`를 돌리면 `test_spawn.py`의 18개 테스트가 실패한다(실측,
survey 참고). 전수 조사 결과 18건 전부 원인이 하나로 좁혀진다 —
`EventReporting`/`ProgressEvents`(그리고 이미 #201로 고쳐진 `Ledger`/
`IssueScopedPrompt`)가 공통으로 부르는 `spawn._spawn_one(..., "execution-observation", ...)`
가, 로컬 룰북 체크아웃도 없고 네트워크도 안 되는 상태에서 `rulebook_checkout`/
`core_root`가 GitHub clone을 시도하다 죽는다. 두 함수 다 이미
`$TOKENMAXXXER_RULEBOOKS`/`$TOKENMAXXXER_CORE` 로컬 오버라이드를 지원하는
프로덕션 경로이고, 이 두 테스트 클래스는 `spawn_cmd` 자체를 이미
`["cat"]`으로 모킹해 두었기 때문에(실제 `claude` CLI를 안 부름) 룰북
체크아웃의 **내용물**은 어차피 실행되지 않는다 — 필요한 건 오직 "체크아웃이
있고 최소 플러그인 하나가 딸려 있다"는 구조뿐이다. `test_gates.py`는
조사 결과 네트워크 의존 실패가 0건이다(순수 판단 함수만 호출하거나, 애초에
pytest 명령으로 수집조차 안 됨 — survey 참고).

## Constraints

- `spawn.py`는 변경하지 않는다 — 18건 전부 테스트 하네스의 관측 준비
  부족이지, 프로덕션 로직 결함이 아니다(스파이크 실측으로 확인, survey
  §스파이크 검증).
- 이슈 #201 범위(`Ledger::test_entry_carries_the_live_log_path`,
  `IssueScopedPrompt::test_preparation_and_preamble_happen_once`)는 이미
  머지된 수정을 그대로 둔다 — 관측점 로직을 다시 손대지 않는다. 이 두
  테스트가 이번 변경으로 부수적으로 통과하게 되는 것은 병목 제거의
  결과이지, 별도로 그 테스트를 고치는 것이 아니다.
- 요구사항 2(개방 환경 기존 통과 테스트 무회귀)를 지키려면 이미 설정된
  환경변수를 강제로 덮어써선 안 된다 — 픽스처는 **기본값**으로만 채운다.
- `test_gates.py`가 `python3 -m pytest ...`로 수집되지 않는 문제(발견,
  survey 참고)는 네트워크 의존과 무관하므로 이번 제안에서 다루지 않는다 —
  범위를 벗어난 별도 재설계다.
- skip은 이번 제안에서 발생하지 않는다 — 전수 조사 결과 "검증 대상 자체가
  네트워크 fetch"인 실패가 0건이라 (b) 배정 대상이 없다.

## Rationale

**채택: (a) 로컬 오버라이드 픽스처 주입.** 레포 루트 `conftest.py`에서
`os.environ.setdefault("TOKENMAXXXER_RULEBOOKS", ...)`/
`setdefault("TOKENMAXXXER_CORE", ...)`로 `tests/fixtures/rulebooks/` 밑
최소 골격(빈 플러그인 하나씩)을 기본값으로 채운다. 이미 지원되는
프로덕션 오버라이드 지점 두 곳을 그대로 쓰므로 새 코드 경로가 생기지
않고, `rulebook_checkout`/`plugin_dirs`/`core_root`/`core_plugin_dirs`가
전부 **실제로** 실행된다 — 그 함수들이 찾는 자리에 미리 채워 두는 것뿐이라
드리프트 위험이 없다(이슈 배경이 "목이 아니다"라고 못박은 그 근거).
`setdefault`를 쓰는 이유는 이미 값이 있는 환경(개발자가 실제 로컬 룰북
체크아웃을 가리키고 있는 경우)을 밀어내지 않기 위해서다 — `test_spawn.py`의
`test_core_dir_resolves_or_halts`(`test_spawn.py:59`) 자체가 "ambient
TOKENMAXXXER_RULEBOOKS가 설정된 셸에서 이 케이스가 조용히 통과했다"는
과거 실측을 주석으로 남겨 둔 정확히 그 함정을 반복하지 않으려는 것이다.

거부한 대안(rejected alternative) 셋:

1. **`spawn.rulebook_checkout`/`core_root`/`plugin_dirs`를 각 테스트에서
   직접 몽키패치해 고정된 반환값을 주는 방식(방향 c, 모킹).** 이 대안을
   채택하는 대신(**rather than** mocking these functions directly) 로컬
   오버라이드 픽스처를 택했다 — 모킹은 `_spawn_one`이 실제로 로컬 우선
   판단(`rulebook_source`)과 marketplace.json 파싱을 거치는 경로 자체를
   건너뛴다. 이 경로가 깨지는 회귀(예: 로컬 체크아웃이 있는데도 github로
   떨어지는 버그, 실제로 이슈 #201 survey가 기록한
   "등록부가 다른 출처를 문다" 류의 실측 사고와 같은 클래스)가 나도 모킹된
   테스트는 여전히 초록불을 낸다. **실제 코드 경로를 검증력 없이 통과시키는
   방식이라 기각한다(rejected)** — 이슈 본문이 "목 드리프트 비용 때문에
   최후 수단"이라고 명시한 바로 그 이유다. (a)로 18건 전부 대체 가능해
   최후 수단을 쓸 이유 자체가 없다(스파이크 실측 확인).
2. **`@pytest.mark.network` + 차단 환경에서 skip(방향 b).** 이 16건을
   skip 처리하는 대신(**instead of** marking them network-dependent and
   skipping) 픽스처로 통과시키는 쪽을 택했다 — 이 테스트들이 검증하는
   대상(`EventReporting`의 이벤트 기록 정확성, `ProgressEvents`의 progress
   중복 억제)은 네트워크와 무관하다. 룰북 체크아웃은 `_spawn_one`을 부르기
   위한 **부수적** 전제 조건이지 검증 대상이 아니다. skip 처리하면 이
   테스트들이 실제로 지키는 회귀(이벤트 오탐 3건, 이슈 #129/#180 실측
   재현)에 대한 커버리지가 차단 환경에서 통째로 사라진다. **검증 대상이
   아닌 것을 이유로 검증 자체를 꺼버리는 방식이라 기각한다(rejected)** —
   (b)는 "검증 대상 자체가 fetch인 테스트"용이지, fetch가 우연히 경로에
   낀 테스트용이 아니다.
3. **환경변수 기본값을 `conftest.py`가 아니라 각 테스트 클래스의
   `setUp`/헬퍼에서 개별로 주입.** 전역 `conftest.py` 대신(**rather than**
   a repo-root `conftest.py`) 클래스별 개별 설정을 검토했으나 기각했다 —
   16개 테스트가 전부 동일한 병목(`execution-observation` 역할 하나)을
   타므로 개별 주입은 같은 값을 16곳에 중복시키는 것과 같고, 앞으로 새로
   추가될 `_spawn_one` 호출 테스트가 이 설정을 빠뜨리면 요구사항 3이
   막으려는 "환경 탓 차분 논리"가 그 새 테스트에서 조용히 되살아난다.
   **중복과 미래 누락 위험이 있는 대안이라 기각한다(rejected)** — 진입점
   하나(`conftest.py`)가 현재와 미래의 모든 해당 테스트를 동시에 지킨다.

## What will be done

1. `tests/fixtures/rulebooks/execution-observation-rulebook/.claude-plugin/marketplace.json`
   생성 — `{"plugins": [{"name": "execution-observation", "source": "./execution-observation"}]}`.
2. `tests/fixtures/rulebooks/execution-observation-rulebook/execution-observation/.claude-plugin/plugin.json`
   생성 — `{"name": "execution-observation"}` (최소 골격, `plugin_dirs`가
   요구하는 존재 확인만 통과하면 됨, survey §`EventReporting._run`이 이미
   모킹하는 것 참고 — 내용물은 실행되지 않는다).
3. `tests/fixtures/rulebooks/tokenmaxxxer-core/core/.claude-plugin/plugin.json`
   생성 — `{"name": "core"}` (`core_root`의 두 번째 후보 경로가 아니라
   `$TOKENMAXXXER_CORE`를 직접 이 디렉터리로 채워 넣을 것이므로, 후보 순서
   우연에 기대지 않는다 — survey §단일 병목점).
4. 레포 루트에 `conftest.py` 신규 작성 — 모듈 최상단(임포트 시점, 어떤
   테스트도 아직 안 돈 시점)에서 `os.environ.setdefault("TOKENMAXXXER_RULEBOOKS",
   str(_FIXTURES / "execution-observation-rulebook").parent)`와
   `os.environ.setdefault("TOKENMAXXXER_CORE", str(_FIXTURES / "tokenmaxxxer-core"))`
   실행. `_FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "rulebooks"`.
5. `spawn.py`, `test_spawn.py`, `test_gates.py` 본문은 손대지 않는다.

## Out of scope

- 이슈 #201 범위(`Ledger`/`IssueScopedPrompt`의 로스터 관측점 로직) — 이미
  머지됨, 재론하지 않는다.
- `test_gates.py`가 `python3 -m pytest ...`로 수집되지 않는 문제(발견,
  survey 참고) — 네트워크 의존이 아니라 테스트 발견 규칙(`t_` vs `test_`
  접두)의 별개 사안, 이번 제안의 쓰기 대상에 없다.
- `t_repo_local_claude_config_stops_the_spawn`이 이 세션의 Bash 도구
  샌드박스에서 `$HOME/.tokenmaxxxer/trusted-repo-config.json` 쓰기가
  막혀 실패하는 것(발견, survey 참고) — 네트워크와 무관하고, 애초에
  이슈 본문이 지목한 pytest 명령으로는 실행되지도 않는다.
- `spawn.py`의 `rulebook_checkout`/`core_root`가 여전히 실제 네트워크
  clone을 시도하는 코드 경로 자체 — 이슈 #201 D2와 같은 이유로 그대로
  둔다. 이번 제안은 테스트가 그 경로를 아예 안 타게(로컬 우선 판단이
  픽스처에서 이기게) 만드는 것이지, clone 실패 처리 자체를 바꾸는 것이
  아니다.
- 새 커버리지 추가(예: 픽스처 구조 자체를 검증하는 신규 테스트) — 요구사항
  1-3이 요구하는 것은 기존 18건을 차단 환경에서 통과시키는 것이지 신규
  테스트가 아니다.

## How you'll know it worked

차단 환경(이 세션의 Bash 샌드박스, `TOKENMAXXXER_RULEBOOKS`/
`TOKENMAXXXER_CORE` 미설정 상태 — `conftest.py`가 기본값을 채움):

```
python3 -m pytest test_spawn.py test_gates.py -q
```

기대 결과: `152 passed`(현재 `18 failed, 134 passed`에서 전건 전환),
`test_gates.py` 기여분은 오늘과 동일하게 0건(수집 자체가 안 되는 기존
상태 그대로 — 이번 제안이 새로 깨뜨리는 것이 아님, 위 Out of scope 참고).
스파이크로 이미 이 정확한 수치(152 passed)를 픽스처 등가물로 실측했다
(survey §스파이크 검증) — `conftest.py`가 `setdefault`로 채우는 값이
스파이크에서 직접 설정한 값과 동일한 구조이므로 같은 결과를 기대한다.

개방 환경(요구사항 2, 기존 통과 무회귀) 검증은 이 세션에서 직접 실행하지
못한다 — 이 세션의 샌드박스는 실제 GitHub 접근이 막혀 있다(§재현
방법론). 대신 이렇게 논증한다: `setdefault`는 이미 값이 설정된 환경(개방
환경에서 사람이 직접 로컬 체크아웃을 가리키고 있는 경우)을 건드리지 않고,
값이 비어 있던 경우(순수 개방 환경, 오버라이드 없이 매번 실제 clone)에는
`EventReporting._run`/`ProgressEvents._run`이 `spawn_cmd`를 이미 모킹해
두어 룰북 디렉터리의 실제 내용물이 어떤 어서션에도 관여하지 않는다(survey
§`EventReporting._run`이 이미 모킹하는 것) — 따라서 실제 GitHub 클론
콘텐츠를 로컬 픽스처로 대체해도 그 16개 테스트의 통과/실패를 가르는 조건은
바뀌지 않는다. 이 논증은 phase 2에서 개방 네트워크 환경이 있는 세션이
`python3 -m pytest test_spawn.py test_gates.py -q`를 돌려 `152 passed`를
직접 재현하는 것으로 최종 확인되어야 한다(이슈 실행 계획의 step 2,
execution-observation).
