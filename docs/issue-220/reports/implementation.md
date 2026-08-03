---
code_under_review: e793828
loop_state: landed
closed_checks:
  - check: "python3 -m unittest test_spawn.py -q — 신규 회귀 테스트 2건
      (test_core_root_prefers_managed_clone_over_sibling_directory,
      test_core_version_reports_managed_clone_sha_when_sibling_also_present)
      전부 통과, test_core_dir_resolves_or_halts·기존 core_version 테스트
      2건 회귀 확인 통과. 전체 160건(변경 전 158건에서 +2) 중 pre-existing
      환경 오류 26건(샌드박스에서 rulebook git-clone 이 네트워크로 막혀
      발생)은 변경 전(git stash 로 확인한 baseline, 158건 중 26건)과
      정확히 동일 — 회귀 없음"
    code_sha: e793828
  - check: "라이브 확인 — 임시 디렉터리에 형제 디렉터리(오래된 sha
      c5b46eb)와 관리 클론(최신 sha f685bfc)을 둘 다 만들고 env 둘 다
      비운 상태에서 core_root()/core_version() 실행: core_root() 는
      관리 클론 경로를 반환(형제 디렉터리 아님), core_version() 은
      'f685bfc (2026-08-03, on-the-record 클론)' 반환(형제 sha c5b46eb
      는 안 나옴) — 제안의 'How you'll know it worked' 수동 확인 항목과
      일치"
    code_sha: e793828
  - check: "warrant-hunter 디스패치(대체, stance: assume-incomplete-coverage
      — 직전 이슈#218 세션의 assume-broken 과 다른 렌즈로 rotate, 1회,
      foreground) — 1건 발견(LOW, 문서 드리프트), 반영 후 재확인 완료
      (아래 Hunt 절)"
    code_sha: e793828
---

# Implementation — core_root() 후보 순서 결함 수정 (issue #220, phase 2)

Proposal: [[core-root-candidate-order-fix.md]](../proposals/core-root-candidate-order-fix.md),
승인: 이슈 코멘트 `APPROVE issue-220/implementation`(single-account mode,
role-handoff contract v3 s19, PR #225 작성자·승인자 동일 계정 jjongkwann,
2026-08-03T01:06:22Z).

## What was done

승인된 제안의 "What will be done" 항목을 write set(`spawn.py`,
`test_spawn.py`) 안에서 그대로 이행했다:

1. **`spawn.py`**: `_core_candidates()`(1781-1791행대)에서
   `("형제 디렉터리", str(ROOT.parent / "tokenmaxxxer-core"))` 튜플을
   제거 — 반환 목록이 env 후보 둘(`TOKENMAXXXER_CORE`,
   `$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core`)만 남는다. 함수
   docstring의 "셋 다 없을 때만" 표현을 "둘 다 없을 때만"으로 갱신.
2. `core_root()`(1794-1829행대)·`core_version()`(1832-1860행대) 본문은
   손대지 않았다 — 둘 다 이미 `_core_candidates()`를 순회하는 루프라
   튜플 제거만으로 두 곳 다 새 순서("env 1 → env 2 → 관리 클론(pull,
   항상 동기화)")를 자동으로 따른다(순수 삭제 리팩터, 호출부 무변경).
3. **`test_spawn.py`**: 회귀 테스트 2건 추가.
   `test_core_root_prefers_managed_clone_over_sibling_directory` —
   형제 디렉터리와 관리 클론이 둘 다 존재하고 env 둘 다 비어 있을 때
   `core_root()`가 관리 클론 경로를 반환하는지(형제 디렉터리가 아니라)
   — 이슈가 보고한 정확한 결함의 회귀 방지.
   `test_core_version_reports_managed_clone_sha_when_sibling_also_present`
   — 같은 셋업에서 `core_version()`이 관리 클론 쪽 sha와 "on-the-record
   클론" 라벨을 반환하는지(형제 디렉터리 쪽이 아니라). 두 저장소가
   같은 초에 동일 내용으로 init 되면 커밋 해시가 우연히 같아질 수 있어
   (실측: 첫 시도에서 `assertNotIn(sibling_sha, v)` 가 실패), marker
   로 트리 내용을 다르게 해 해시 충돌을 막았다.
4. 변경 후 `python3 -m unittest test_spawn.py -v` 실행해 기존
   `test_core_dir_resolves_or_halts`·두 `core_version` 테스트·
   `test_flags` 등이 전부 그대로 통과함을 확인(halt 계약·시그니처
   무변경의 증거) — 아래 §검증 참고.

## Why / Upstream basis

`docs/issue-220/proposals/core-root-candidate-order-fix.md`(frozen write
set), `docs/issue-220/reports/implementation/survey.md`(phase-1 survey)
— 이슈 본문이 실측 보고한 결함(형제 디렉터리 후보가 sha 비교 없이
관리 클론보다 먼저 매치되어, 이 개발 머신처럼 형제 디렉터리가 항상
존재하는 환경에서 관리 클론이 영구히 도달 불가)과 승인된 수정 방향
(제안 Rationale에서 rejected 로 명시한 "재배치" 대신, 형제 디렉터리
후보를 `_core_candidates()`에서 완전히 제거 — 근본 패턴을 남기지 않고,
이 저장소의 유일한 대칭 사례인 `rulebook_checkout()`의 원칙(설정/등록부
기반 후보만 오버라이드로 인정)과 일치) 그대로.

## 검증 — 제안 "How you'll know it worked" 대응

1. **전체 테스트 무회귀 + 신규 통과:**
   ```
   $ python3 -m unittest test_spawn.py -q
   Ran 160 tests in ~6.5s
   FAILED (errors=26)
   ```
   26건은 샌드박스에서 rulebook git-clone 이 네트워크로 막혀 발생하는
   pre-existing 환경 오류로, `git stash` 로 되돌린 변경 전 baseline
   (158건 기준)에서도 정확히 26건이라 회귀 없음.
   `python3 -m unittest test_spawn.SpawnCmd -v`(core 관련 21건, 신규
   2건 포함)는 전부 `ok`.
2. **`core_root()` halt 계약 무회귀:** `test_core_dir_resolves_or_halts`
   리팩터 후에도 그대로 통과.
3. **라이브 확인:** 임시 디렉터리에 형제 디렉터리(sha `c5b46eb`)와
   관리 클론(sha `f685bfc`)을 둘 다 만들고 env 둘 다 비운 상태에서
   `core_root()`/`core_version()` 실행 → `core_root()` 는 관리 클론
   경로 반환, `core_version()` 은 `f685bfc (2026-08-03, on-the-record
   클론)` 반환 — 제안의 수동 확인 항목과 일치(형제 sha 는 어느 쪽
   출력에도 안 나옴). 확인용 임시 스크립트는 실행 후 삭제, 저장소에
   남기지 않았다.

## What did not work

- 신규 테스트 `test_core_version_reports_managed_clone_sha_when_sibling_also_present`
  최초 작성 시 형제 디렉터리·관리 클론 두 임시 git 저장소를 동일 내용
  (`plugin.json`에 `{}`만)으로 같은 초 안에 init 했다. 기대: 서로 다른
  sha. 실제: 트리·커밋 메시지·author/committer 시각이 전부 같아 두
  저장소의 커밋 해시가 완전히 동일(`6bc0e1b`)하게 나와
  `assertNotIn(sibling_sha, v)` 가 실패했다 — 각 저장소 `plugin.json`에
  marker 필드를 넣어 트리 내용을 다르게 해 해결(§What was done 항목 3).

## Hunt

Phase-2 완료 전 warrant-hunter를 디스패치했다(hunt cadence, stance
rotate). 이 세션에도 `warrant:warrant-hunter` subagent 타입이 등록돼
있지 않아(가용 목록: `claude`/`Explore`/`freelunch:freelunch-worker`/
`general-purpose`/`Plan`/`statusline-setup`) adversarial 프롬프트를
`general-purpose` 에이전트에 직접 넣어 foreground(run_in_background:
false)로 대체 디스패치했다(사유는 아래 §Rationale for deviations).
Stance 는 직전 issue#218 세션의 `assume-broken` 과 달리
`assume-incomplete-coverage`("코드는 맞아도 테스트가 실제로 결함을
못 잡을 수 있다")로 rotate 했다.

검토 범위: `_core_candidates()` 변경의 두 호출부 반영 여부(암묵적
인덱스/길이 의존 grep), 신규 회귀 테스트 2건이 옛 코드(형제 디렉터리
포함)에서 실제로 fail 하는지 직접 재현, 테스트의 `spawn.ROOT`/
`os.environ` monkeypatch 격리, 제안 "What will be done" 대비 diff
범위 일치, 기존 3개 core 테스트의 검사 로직 유효성.

**결과: 1건 발견(LOW), 반영 완료.**

- **LOW — 기존 테스트 주석의 "후보 셋" 표현이 갱신 안 됨**
  (`test_spawn.py`, 반영 전 63행·197행): `_core_candidates()` 자신의
  docstring은 이번 diff로 "셋 다"→"둘 다"로 갱신됐지만, 같은 개념을
  설명하는 `test_core_dir_resolves_or_halts`("core_dir 이 보는 자리
  **셋 전부**")·`test_core_version_reports_unknown_without_network_when_nothing_found`
  ("로컬 후보 셋 + 관리 클론")의 주석은 그대로 남아 실제 후보 수(2개)와
  불일치 — 문서 드리프트, 유지보수자를 오도할 수 있음. **반영**: 두
  주석 모두 "둘 다"/"로컬 후보 둘"로 수정.

hunt가 재현 검증한 것: 신규 회귀 테스트 2건은 `git stash`로 `spawn.py`만
옛 코드(형제 디렉터리 포함)로 되돌리고 새 `test_spawn.py`를 그대로
돌렸을 때 실제로 FAIL함을 확인 — 우연히 통과하는 약한 테스트가 아니라
결함을 실제로 잡는 회귀 테스트임이 검증됐다.

반영 후 `python3 -m unittest test_spawn.SpawnCmd -v` 재확인: 21건 전부
`ok`.

## Open findings

없음 — Hunt 절의 1건은 반영·재확인을 마쳤고, write set 확장이 필요한
미해결 항목은 남지 않았다.

## Rationale for deviations

- **Hunt를 foreground로 실행**: 코딩 역할 지침의 hunt cadence는 발화
  방식을 지정하지 않지만, freelunch 지침은 도구 호출이 필요한 모든
  작업을 background `freelunch-worker`로 위임하라고 요구한다. 이
  세션은 시작 시점에 "이 턴은 headless이고 단발이다 — 세션이 끝나면
  이 프로세스도 끝난다. run_in_background로 넘긴 작업은 부모 턴이
  끝나는 순간 함께 죽는다(백그라운드 워커가 커밋·push를 대신 끝내줄
  거라고 가정하지 마라 — 실측된 실패 패턴)"는 문구를 과제 텍스트 안에서
  직접 받았다 — issue#218 phase-2 세션이 동일한 문구를 받고 동일한
  판단을 내린 선례가 `docs/issue-218/reports/implementation.md`
  §Rationale for deviations에 이미 기록돼 있다. background로 hunt를
  넘기고 이 턴이 끝나면 결과를 이어받을 방법이 없어 "완료의 정의"
  (커밋·push·PR)를 못 지킬 위험이 명시적으로 경고된 실패 패턴이었다
  — 그래서 hunt 자체는 스킵하지 않되 foreground로 실행해 결과를 이
  턴 안에서 직접 반영했다. 같은 이유로 이번 세션의 나머지 구현 작업
  (코드 편집·테스트 실행·라이브 확인·커밋)도 전부 foreground/inline
  으로 직접 수행했다.
- **hunt가 찾은 LOW 1건(주석 문서 드리프트) 반영**: 승인된 제안의
  write set(`spawn.py`, `test_spawn.py`) 밖으로 나가지 않는 사소한
  수정이라 write set 확장 없이 그대로 반영했다 — 별도 승인 재요청
  없이 처리 가능한 범위.
- 코드 변경(튜플 제거 + docstring 갱신 + 회귀 테스트 2건) 자체는 승인된
  제안 그대로이고, 위 두 항목은 제안 범위 자체를 넘어선 변경은 아니다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음 —
  새 환경변수·설정·의존성·마이그레이션 없음(제안 Constraints가 이미
  확정).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-220/decisions/`: 해당 없음 — 공개 시그니처(`core_root()
  -> Path`, `core_version() -> str`) 무변경, 대안 기각 사유(재배치안
  vs 완전 제거)는 phase-1 제안(PR #225)에 이미 커밋돼 있음.
- [x] benchmark/investigation 수치 → `docs/issue-220/reports/`: 완료 —
  위 §검증의 테스트 실행·라이브 확인 결과가 이 파일에 있음.
- [x] Phase 1 survey: `docs/issue-220/reports/implementation/survey.md`
  (PR #225로 이미 제출)
- [x] Phase 1 proposal:
  `docs/issue-220/proposals/core-root-candidate-order-fix.md`
  (PR #225로 이미 제출)
- [x] Phase 2 record: `docs/issue-220/reports/implementation.md`(this
  file)
- [x] Hunt: 이 파일의 §Hunt(별도 hunt 파일 없음 — 발견 1건이 코드
  반영으로 종결되어 disposition 을 이 record 자체에 기록)
- [x] Tests: `test_spawn.py`에 신규 회귀 2건 추가(위 §What was done
  항목 3)
