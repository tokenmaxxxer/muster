---
code_under_review: dd65451
loop_state: landed
closed_checks:
  - check: 네트워크 차단 재현(TOKENMAXXXER_RULEBOOKS/TOKENMAXXXER_CORE 미설정)
      상태에서 python3 -m pytest test_spawn.py test_gates.py -q — 152 passed,
      0 failed(스파이크 실측치와 일치)
    code_sha: dd65451
  - check: setdefault 비파괴성 — 이미 설정된 ambient 오버라이드(픽스처가
      아닌 별도 임시 체크아웃)를 conftest.py import 전에 미리 채워도
      conftest.py가 그 값을 덮어쓰지 않음을 python3 -c 직접 assert로 확인
    code_sha: dd65451
  - check: 그 ambient 오버라이드 상태에서 python3 -m pytest test_spawn.py
      test_gates.py -q 재실행 — 152 passed, 0 failed(개방 환경에서 기존
      통과 무회귀에 대한 실측 프록시, 요구사항 2)
    code_sha: dd65451
  - check: repo-root 전체 pytest -q(파일 인자 없이) 수행 시 나타나는
      9건의 실패(GitHead/IsNewCommit/Clean/Watchdog/EventExitScope)가
      conftest.py 도입 전/후 동일하게 재현됨 — 이번 변경이 만든 것이
      아니라 이슈 본문이 지목한 커맨드 범위 밖의 기존 현상임을 확인
    code_sha: dd65451
  - check: "warrant-hunter 디스패치(after-proposal, stance 1: composition
      regression) — docs/reports/2026-08-02-hunt-issue-204-rulebook-checkout-test-fixture.md"
    code_sha: dd65451
---

# Implementation — 룰북 체크아웃 테스트 픽스처 (issue #204, phase 2)

Proposal: [[rulebook-checkout-test-fixture.md]](../proposals/rulebook-checkout-test-fixture.md),
승인: 이슈 코멘트 `APPROVE issue-204/implementation` (single-account mode,
role-handoff contract v3 s19) + PR #208 merged (phase-1 산출물,
`docs/issue-204/proposals/rulebook-checkout-test-fixture.md`).

## What was done

승인된 제안의 "What will be done" 4개 항목을 그대로 이행했다 — write set
(`conftest.py` + 픽스처 3개) 밖으로 나가지 않았고, `spawn.py`/
`test_spawn.py`/`test_gates.py` 본문은 한 글자도 바꾸지 않았다(제안
Constraints 그대로):

1. `tests/fixtures/rulebooks/execution-observation-rulebook/.claude-plugin/marketplace.json`
   — `{"plugins": [{"name": "execution-observation", "source": "./execution-observation"}]}`.
2. `tests/fixtures/rulebooks/execution-observation-rulebook/execution-observation/.claude-plugin/plugin.json`
   — `{"name": "execution-observation"}`.
3. `tests/fixtures/rulebooks/tokenmaxxxer-core/core/.claude-plugin/plugin.json`
   — `{"name": "core"}`.
4. 레포 루트 `conftest.py` 신규 작성 — 모듈 최상단에서
   `os.environ.setdefault("TOKENMAXXXER_RULEBOOKS", str(_FIXTURES))` /
   `setdefault("TOKENMAXXXER_CORE", str(_FIXTURES / "tokenmaxxxer-core"))`
   실행. `_FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "rulebooks"`.
   제안 본문의 `(_FIXTURES / "execution-observation-rulebook").parent`
   표현은 `_FIXTURES` 자신과 수학적으로 동일해(Path의 `.parent`가
   자기 자신의 부모 디렉터리로 되돌아가므로) 그대로 `str(_FIXTURES)`로
   단순화해 작성했다 — 값은 제안이 명시한 것과 정확히 같다.

## Why

승인된 제안(phase-1, PR #208 merge, `APPROVE issue-204/implementation`
기록됨)의 실행. 이슈 #204가 요구하는 것: 네트워크 차단 역할 세션
샌드박스에서 `python3 -m pytest test_spawn.py test_gates.py`가 실패 0이
되어야 상시 실패 더미(세션 실측 17~25건)가 진짜 회귀(이슈 #201 재현
사고)를 가리는 문제가 없어진다. 이미 프로덕션이 지원하는 로컬 오버라이드
두 곳(`$TOKENMAXXXER_RULEBOOKS`, `$TOKENMAXXXER_CORE`)을 `setdefault`로
채우는 것만으로 `rulebook_checkout`/`plugin_dirs`/`core_root`/
`core_plugin_dirs`가 전부 **실제로** 실행되게 하면서 네트워크 clone
시도를 없앤다 — 목이 아니다.

## Upstream basis

`docs/issue-204/proposals/rulebook-checkout-test-fixture.md` (frozen write
set), `docs/issue-204/reports/implementation/survey.md` (phase-1 survey,
스파이크로 152 passed 실증).

## 검증 — 제안 "How you'll know it worked" 대응

이 세션의 Bash 샌드박스가 issue #204/#201 survey가 이미 기록한 "네트워크
차단 환경"의 실측 대리자다(저장소 경로 밖 git hook 템플릿 복사 거부 —
`rulebook_checkout`을 `SystemExit`으로 죽인다는 점에서 실제 DNS 차단과
동등).

1. **요구사항 1 — 네트워크 차단 재현, 실패 0:**
   ```
   $ TOKENMAXXXER_RULEBOOKS= TOKENMAXXXER_CORE= python3 -m pytest test_spawn.py test_gates.py -q
   (env -u로 두 변수 완전 미설정 상태)
   ........................................................................ [ 47%]
   ........................................................................ [ 94%]
   ........                                                                 [100%]
   152 passed in 18.01s
   ```
   스파이크 실측치(survey §스파이크 검증, 152 passed)와 정확히 일치.
   `18 failed, 134 passed` → `152 passed`로 18건 전건 전환.

2. **요구사항 2 — 개방 환경 기존 통과 무회귀 (직접 실측 프록시):**
   제안의 "How you'll know it worked"는 이 세션 샌드박스가 실제 GitHub
   접근이 막혀 있어 진짜 개방-네트워크 clone 비교는 이 세션에서 실행하지
   못한다고 명시하고, 그 대신 논증(설계상 `setdefault`는 비파괴적이고
   `spawn_cmd`가 이미 모킹돼 있어 체크아웃 콘텐츠가 단언에 관여하지
   않는다)으로 검증을 phase 2 execution-observation 세션(이슈 실행 계획
   step 2)에 위임했다. 이 세션에서 실측 가능한 만큼은 직접 확인했다 —
   `setdefault`의 비파괴성 자체를 코드로 검증:
   ```python
   # conftest.py import 전에 TOKENMAXXXER_RULEBOOKS/CORE를 픽스처가 아닌
   # 별도 임시 디렉터리(ambient 체크아웃)로 미리 채운 뒤 import
   os.environ["TOKENMAXXXER_RULEBOOKS"] = AMBIENT   # AMBIENT != 픽스처 경로
   os.environ["TOKENMAXXXER_CORE"] = AMBIENT + "/tokenmaxxxer-core"
   import conftest
   assert os.environ["TOKENMAXXXER_RULEBOOKS"] == AMBIENT   # 통과
   assert os.environ["TOKENMAXXXER_CORE"] == AMBIENT + "/tokenmaxxxer-core"  # 통과
   ```
   출력: `ambient values preserved, not overridden by fixture defaults`.
   이어서 그 ambient 값을 그대로 둔 채 전체 커맨드를 재실행:
   ```
   $ TOKENMAXXXER_RULEBOOKS=<ambient> TOKENMAXXXER_CORE=<ambient>/tokenmaxxxer-core \
     python3 -m pytest test_spawn.py test_gates.py -q
   ........................................................................ [ 47%]
   ........................................................................ [ 94%]
   ........                                                                 [100%]
   152 passed in 14.15s
   ```
   즉 "이미 값이 설정된 환경"(개방 환경에서 사람이 실제 로컬 체크아웃을
   가리키고 있는 경우와 동형) 조건에서도 `setdefault`가 그 값을 밀어내지
   않고, 결과도 여전히 152 passed다. 진짜 GitHub clone 콘텐츠 대 이
   테스트용 ambient 콘텐츠 간의 차이까지 이 세션에서 실측할 수는
   없었지만(§재현 방법론 그대로), 요구사항 2가 실제로 지키려는 성질
   (비파괴적 기본값 + 통과 결과 불변)은 코드로 확인했다. 진짜 개방
   네트워크에서의 최종 확인은 제안이 명시한 대로 phase 2
   execution-observation 세션에 남는다.

3. **부수 확인 — repo-root 전체 `pytest -q`(파일 인자 없음)의 잔여
   실패 9건은 이 변경과 무관:** 이슈 본문이 지목한 커맨드는
   `test_spawn.py test_gates.py`로 범위가 좁혀져 있는데, 인자 없이
   `pytest -q`를 돌리면(다른 테스트 파일들과 함께 수집) `GitHead`,
   `IsNewCommit`, `Clean`, `Watchdog`, `EventExitScope` 클래스에서 9건이
   실패한다. `conftest.py`를 빼고 다시 돌려도 똑같이 9건이 실패해(이번엔
   18건이 더해져 27건) — 즉 이 9건은 이번 변경이 만든 게 아니라 파일
   교차 수집 시 나타나는 기존 현상이고, 이슈 본문의 커맨드 범위(요구사항
   1) 밖이라 이번 제안의 쓰기 대상도 아니다. 손대지 않았다.

## What did not work

None.

## Hunt

phase-2 완료 전 warrant-hunter를 디스패치했다(hunt cadence). 이 세션에는
`warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아(available
agent 목록에 없음), `agents/warrant-hunter.md`(tokenmaxxxer-core `warrant`
플러그인, marketplace 캐시에서 확인)의 페르소나·프로토콜을 그대로
`general-purpose` 에이전트 프롬프트에 넣어 대체 디스패치했다. stance는
composition regression 1개로 고정: "이 conftest.py가 레포 안의 다른
conftest.py/pytest 설정/두 환경변수를 건드리는 다른 코드와 충돌하거나,
수집 순서상 조용히 적용되지 않을 수 있는가."

**결과: FINDING.** 기록:
[docs/reports/2026-08-02-hunt-issue-204-rulebook-checkout-test-fixture.md](../../reports/2026-08-02-hunt-issue-204-rulebook-checkout-test-fixture.md).

요지 — `conftest.py`는 pytest 전용 auto-import 훅이라, 이 레포가 이미
문서화해 둔 두 개의 non-pytest 실행 경로(`README.md`의 `python3
test_gates.py`, 그리고 이슈 #31 QA survey가 기록한 `python3 -m unittest
test_spawn.py`)로 같은 테스트 파일을 돌리면 `conftest.py`가 아예
import되지 않아 `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` 기본값이
채워지지 않고, `rulebook_source`/`rulebook_checkout`/`core_root`가 실제
github/네트워크 경로로 떨어진다(재현 스크립트로 실측 확인됨 — 위 기록
파일 §Observed).

**이 finding을 write set 확장으로 고치지 않은 이유:** 이슈 #204의
요구사항 1이 못박은 커맨드는 정확히 `python3 -m pytest test_spawn.py
test_gates.py`이고, 승인된 제안의 Constraints/Out of scope 절이 이미
`test_gates.py`의 non-pytest 수집·실행 경로를 "네트워크 의존과 무관한
별개 재설계"로 명시적으로 범위 밖에 뒀다(제안 Out of scope 3번째 항목).
`conftest.py`가 pytest 전용이라는 것은 이 메커니즘을 선택한 승인된
설계 자체에 내재한 성질이지, 이번 구현이 새로 만들어낸 결함이 아니다 —
non-pytest 경로(`python3 -m unittest`, `python3 test_gates.py`)는 이
변경 전에도 똑같이 네트워크에 의존했고 이번 변경으로 더 나빠지지도
않았다(회귀 아님). 고치려면 write set 밖(예: README.md의 실행법 안내,
또는 non-pytest 경로에서도 픽스처를 적용하는 별도 부트스트랩 메커니즘
설계)으로 나가야 하는데, 승인된 write set은 `conftest.py`와 픽스처
3개로 이미 확정돼 있고 이번 구현은 그 안에서 완결된다 — write set을
넓히지 않고 여기서 멈추고 아래 Open findings에 정직하게 남긴다.

## Open findings

**hunt finding (미해결, write set 밖, 회귀 아님):** `conftest.py`가
채우는 `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` 기본값은 pytest
수집 경로에서만 적용된다 — `python3 -m unittest test_spawn.py`나
`python3 test_gates.py`처럼 이 레포가 이미 문서화한 non-pytest 실행
경로로 같은 테스트를 돌리면 여전히 실제 네트워크/GitHub 경로를 탄다(위
Hunt 절, 전체 재현은 hunt record 참고). 이슈 #204의 요구사항 1이 지목한
정확한 커맨드(`python3 -m pytest ...`)에는 영향이 없고, 이번 변경 전에도
이미 그랬던 상태라 회귀도 아니다. 모든 실행 경로에서 네트워크 독립성을
보장하고 싶다면 별도 이슈로 등록해 다룰 만한 후속 과제로 남긴다 —
이번 제안의 frozen write set(`conftest.py` + 픽스처 3개)에는 포함되지
않는다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음 —
  새 환경변수·설정·의존성·마이그레이션 없음. `TOKENMAXXXER_RULEBOOKS`/
  `TOKENMAXXXER_CORE`는 `spawn.py`가 이미 프로덕션에서 지원하던 기존
  오버라이드 지점이고, `conftest.py`는 그 기존 변수에 **기본값**만 채운다
  (제안 Constraints 그대로).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-204/decisions/`: 해당 없음 — 승인된 제안의 Rationale이
  이미 이 결정(로컬 오버라이드 픽스처 vs 몽키패치 vs skip 마커 vs
  클래스별 개별 주입)을 phase-1 proposal 문서에 기록했고, phase-2는 그
  결정을 그대로 이행했을 뿐 새 결정을 내리지 않았다.
- [x] benchmark/investigation 수치 → `docs/issue-204/reports/`: 완료 —
  위 §검증의 세 실측(네트워크 차단, ambient 비파괴성, 전체 스위트
  9건 무관 확인) 결과가 이 파일에 있다.
- [x] Phase 1 survey: `docs/issue-204/reports/implementation/survey.md`
  (PR #208로 이미 merge)
- [x] Phase 1 proposal: `docs/issue-204/proposals/rulebook-checkout-test-fixture.md`
  (PR #208로 이미 merge)
- [x] Phase 2 record: `docs/issue-204/reports/implementation.md` (this file)
- [x] Hunt record: `docs/reports/2026-08-02-hunt-issue-204-rulebook-checkout-test-fixture.md`
- [x] Tests: 새 테스트 추가 없음(제안 Out of scope 4번째 항목 — 기존
  18건을 통과시키는 것이 목적이지 신규 커버리지 추가가 아님). 검증은
  기존 `test_spawn.py`/`test_gates.py`를 그대로 실행해 확인했다.
