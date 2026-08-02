# Survey — issue #205: 세션 종결 처리 결함 3건

## 스카우트 스킵 기록

스킵 조건 1(순수 버그픽스) 적용. 이슈 본문이 세 결함 모두 정확한 위치·원인·
방향까지 특정해 뒀고(`fail_closed_downgrade`의 검사 순서, `.warrant-hunt.count`의
gitignore 방향은 "제안이 확정", `spawn.py:2125-2126`의 파일 가드), 세 건 다
`spawn.py`의 내부 세션-종결 로직 교정이라 사용자가 보는 제품형 표면(UI/API/
문서)이 아니다 — 비교할 외부 best-in-class 대상이 없다. scout-brief.md는
작성하지 않는다.

## 결함 1 — `fail_closed_downgrade`의 검사 순서

### 정확한 위치

`spawn.py:1232-1263` `fail_closed_downgrade()`:

```python
def fail_closed_downgrade(outcome, issue, blocked, new_commit, uncommitted,
                          already_delivered=False):
    if outcome != "progressed" or issue is None:
        return outcome
    if blocked:
        return outcome
    if uncommitted:                        # <- 커밋 유무보다 먼저 본다
        return "failed-no-commit"
    if new_commit or already_delivered:
        return outcome
    return "failed-no-commit"
```

호출부는 `spawn.py:2565-2600`. `uncommitted`는 세션 종료 시점의
`git status --porcelain`(`:2569-2571`) — `new_commit`/`already_delivered`는 그
뒤에 계산된다(`:2587-2593`)지만 `fail_closed_downgrade` 내부 순서가 이미
`uncommitted`를 먼저 리턴시켜, 실제 커밋이 있어도(`new_commit=True`) 도달하지
못한다.

### 근거 — 이슈가 인용한 원장 실측 2건

이슈 본문이 실측을 인용한 커밋 두 건은 이 저장소 히스토리에 실재한다:

```
$ git log --oneline | grep -E "^(1ed27b9|7d11c9e)"
7d11c9e issue-192: phase 1 — survey + proposal for session-log retention
1ed27b9 issue-189: phase 1 — survey + implementation-plan proposal for execution-plan build
```

두 커밋 모두 phase-1 세션이 실제로 남긴 커밋(PR #191, #194가 열렸다는 사실도
이슈 본문 인용)이다 — 즉 두 세션 다 `new_commit=True`였는데도, `runs/ledger.jsonl`
(gitignore 대상이라 이 저장소 체크아웃엔 남아있지 않음 — 이슈가 실측한 값을
그대로 인용)에는 `failed-no-commit`으로 찍혔다. `fail_closed_downgrade`의 위
순서가 정확히 이 결과를 만든다: 두 세션 다 dirty 원인이 `.warrant-hunt.count`
(결함 2, 아래) 하나뿐이었고, `uncommitted`가 비어있지 않으니 `new_commit=True`
체크에 닿기도 전에 `"failed-no-commit"`을 리턴한다.

### 기존 테스트가 잠근 계약 — 어디까지가 진짜 제약인가 (오케스트레이터 중계로 수정)

`test_spawn.py:585-655` `FailClosedDowngrade` 클래스가 `fail_closed_downgrade()`를
직접 호출해 지금 순서를 못박아 뒀다. 이 중 두 테스트가 이슈 #205의 설계
결정에 직접 걸리는데, 성격이 다르다:

- `test_new_commit_dirty_tree_is_still_downgraded`(`:600-606`): `new_commit=True`
  + dirty tree → `"failed-no-commit"`을 **기대**한다. 이 단언 자체가 이슈 #205가
  고치려는 바로 그 오판정(원장 실측 두 건이 이 케이스)을 문서화한 것이다 —
  결함을 단언하는 테스트다.
- `test_already_delivered_with_dirty_tree_still_downgrades`(`:648-655`): 주석
  "'already delivered' covers prior commits, not this session's own uncommitted
  leftovers" — 이 세션 **자신이** 남긴 dirty 파일은 already_delivered와 무관하게
  여전히 위험 신호로 다룬다는, 이슈 #205와 **무관한** 독립적 근거다. 결함을
  단언하는 테스트가 아니다.

phase-1 PR #206에 대한 사용자 피드백(오케스트레이터 중계, PR #206 코멘트,
2026-08-02): "'기존 테스트 무변경' 제약을 완화한다 — 결함 자체를 단언하는
테스트는 수정 허용... 제약의 의도는 무관한 동작 보호였지 버그 보존이
아니다." 이 결정으로 위 두 테스트는 더는 같은 취급을 받지 않는다:
`test_new_commit_dirty_tree_is_still_downgraded`는 수정 대상(새 기대값
`"progressed-dirty-tree"`), `test_already_delivered_with_dirty_tree_still_downgrades`는
결함을 단언하지 않으므로 무변경 제약이 그대로 적용된다.

이 구분을 적용하면 `fail_closed_downgrade()` 내부 검사 순서를 직접
고치는 것(이슈 본문이 원인으로 지목한 바로 그 순서)과 "기존 테스트
무변경" 제약이 더는 충돌하지 않는다 — 재분류를 별도 단계로 분리해 원래
함수를 우회할 이유가 없다. 사용자 결정에 따라 이전 phase-1 제안에서
기각했던 이 직접 교정안을 재채택한다(아래 Rationale 갱신 절 참조).

`already_delivered`(이 세션 자체는 새 커밋이 없고, 브랜치에 이전 phase의
커밋+PR만 있는 경우)는 이슈의 실측 두 건(두 건 다 `new_commit=True`) 어디에도
해당하지 않고, 위 두 번째 테스트가 "이 세션 자신의 dirty 잔재는 여전히
위험"이라는 독립적 근거를 이미 대고 있다 — 되돌리는 대상에서
`already_delivered` 단독 케이스는 제외한다(범위를 이슈가 실측한 것만큼만
좁힌다). 이 부분은 사용자 피드백도 "실측 범위 밖 확장 금지"로 그대로
수용해, 변경하지 않는다.

## 결함 2 — `.warrant-hunt.count`

### 상태 파일의 출처

로컬(이 세션 워크스페이스 밖) 룰북 체크아웃의 `warrant/hooks/`:

- `hunt-guard.sh:81-84` — `count = posixpath.join(root, ".warrant-hunt.count")`를
  열어 세션당 hunter 디스패치 횟수를 셈한다(`WARRANT_HUNT_MAX`, 기본 3).
- `hunt-state.sh:43` — `reset` 액션에서 `rm -f "$root/.warrant-hunt.lock"
  "$root/.warrant-hunt.count"`로 지운다(SessionStart 훅).

같은 훅 쌍이 `.warrant-hunt.lock`(hunt-guard.sh:76, single-flight 락)도
루트에 쓴다 — 이슈 본문은 `.count`만 지목했지만 두 파일 다 "훅 상태는 소스가
아니다"라는 같은 근거에 해당하는 동일 계열 파일이다.

### 이 저장소에 커밋됐던 이력

```
$ git log --all --diff-filter=A --oneline -- ".warrant-hunt.count"
aa59f97 Restructure for contract v3: ...   (대규모 재구성 커밋에 실려 추가됨)

$ git log --all -p -- ".warrant-hunt.count" | head -8
commit 1c230dbce4829c3ebda9013818ab8747171faa18   (issue-197 phase 1 세션)
  diff --git a/.warrant-hunt.count b/.warrant-hunt.count
  deleted file mode 100644
  -3
```

`1c230db`(issue-197 phase 1, 이 세션 이전)가 이미 이 파일을 저장소에서
지웠다 — 커밋 로그 자체가 "이 이슈의 write set 밖, 이전 세션 잔재"라고 밝힌
부수 효과다. 그래서 현재 `main`(`git ls-files`로 확인, `.gitignore`에도 없음)
에는 이 파일이 트래킹돼 있지 않다 — **하지만 `.gitignore`에 없으므로, 훅이
다음에 이 파일을 다시 만들면 untracked 파일로 잡혀 `git status --porcelain`이
다시 비지 않게 된다.** 즉 "git 추적 해제"는 이미 끝났고, 남은 일은
"gitignore"뿐이다.

### 방향 — 이슈가 확정한 대로, 다만 패턴을 넓힌다

이슈 요구사항 2는 "git 추적 해제 + gitignore… 제안이 확정"이라 대안을 다시
따질 대상이 아니다. 다만 `.gitignore` 항목을 리터럴 `.warrant-hunt.count` 한
줄로만 좁히는 대신 `.warrant-hunt.*` 패턴으로 잡아 `.lock` 형제까지 함께
덮는다 — `spawn.py:2123-2125`(clean의 형제 삭제, 결함 3 바로 옆)의 주석이
이미 같은 교훈을 명시한다: "접미사를 하나씩 나열하면 다음에 하나 더 생길 때
또 빠뜨린다." 이 저장소 자신의 코드가 이미 채택한 원칙을 `.gitignore`에도
그대로 적용하는 것뿐이라 새 판단이 아니다.

## 결함 3 — `clean`의 형제 삭제가 디렉터리를 만나면 멈춘다

### 정확한 위치

`spawn.py:2117-2126`:

```python
import shutil
shutil.rmtree(w)
# 세대별 로그(...)와 ... 형제 산출 파일을 전부 글롭으로 잡는다 —
# 접미사를 하나씩 나열하면 다음에 하나 더 생길 때 또 빠뜨린다.
for sibling in w.parent.glob(w.name + ".*"):
    sibling.unlink()
```

`Path.unlink()`는 디렉터리를 만나면 `IsADirectoryError`(`OSError` 서브클래스)를
던진다 — `for` 루프 안이라 그 예외가 잡히지 않으면 이 반복 전체(바깥의
`for w in sorted(wb.glob("*"))` 루프까지)가 중단된다. `shutil.rmtree(w)` **다음에**
있으므로 그 워크스페이스는 이미 반쯤 지워진 채로, 그리고 목록의 나머지
워크스페이스는 전부 미처리로 남는다.

### 현재 잠복 상태인 이유 — 테스트로 확인

`test_spawn.py:1252-1374` `Clean` 클래스의 두 테스트 다 형제로 파일만
만든다(`:1325-1336`, `.session.*.log`/`.events.jsonl`/`.events.offset`/
`.task.txt`/`.respawn-claim-*` — 전부 `p.write_text("x")`로 만든 평범한
파일). 디렉터리 모양 형제를 만드는 테스트는 없다 — 이슈 본문의 "현재 형제는
전부 파일이라 잠복 상태"와 일치. 실제로 이런 형제가 디렉터리가 될 수 있는
경로는 아직 이 저장소에 없다(글롭이 잡는 접미사들은 전부 `.log`/`.jsonl`/
`.offset`/`.txt`/락 파일류) — 그래서 "잠복"이지 재현된 실패가 아니다.

### 가드

`sibling.unlink()` 앞에 파일 여부 확인 한 줄이면 된다(`sibling.is_file()`
가드, 또는 동치인 `not sibling.is_dir()` — 심볼릭 링크가 형제로 나타날
경로가 없으므로 두 표현은 이 문맥에서 동일하다). 디렉터리 형제를 실제로
지우는 로직은 이슈가 요구하지 않았다("파일 가드 한 줄이면 된다") — 건드리지
않고 건너뛴다.

## 원장 스키마 소비자 — `gates/flows.py`

```
gates/flows.py:308   ledger_entries = _ledger_read()
gates/flows.py:316   verdict = matches[-1].get("outcome") if matches else None
gates/flows.py:328   outcome = entry.get("outcome") or "unknown"
gates/flows.py:338   agg["outcomes"][outcome] = agg["outcomes"].get(outcome, 0) + 1
```

`outcome`을 특정 문자열 집합으로 분기(`if outcome == "..."류`)하는 곳이
`gates/`, `ledger/`, 테스트 전체에 없다 — `grep -rn '"outcome"' gates/*.py
ledger/*.py`로 확인, `flows.py`의 두 지점(`:316`, `:328`) 뿐이고 둘 다
`entry.get("outcome")`을 그대로 딕셔너리 키로 쓰는 불투명 버킷팅이다. `runs/`는
`.gitignore` 대상(`spawn.py:1763-1764` 주석 "runs/ 는 gitignore 되어 있다 —
측정 데이터는 소스가 아니다")이라 `ledger_write()`도 스키마를 강제하지 않는
`dict → jsonl` 그대로다. 새 `outcome` 문자열 값을 추가하는 것은 이 소비자
쪽에 코드 변경도, 회귀도 만들지 않는다 — `agg["outcomes"]`에 새 버킷 키가 하나
늘어날 뿐이다. `docs/handbooks/`에도 outcome 값을 나열해 둔 문서가 없다
(`grep -rl` 확인) — 갱신할 문서 없음.

## 기존 테스트 베이스라인 (이 세션, 실측)

관련 클래스만 격리 실행(네트워크·룰북 clone에 의존하지 않는 순수 함수
테스트):

```
$ python3 -m pytest test_spawn.py -k "FailClosedDowngrade or Clean" -v
...
12 passed, 140 deselected in 1.09s
```

전체 스위트(`python3 -m pytest test_spawn.py -q`)는 이 샌드박스에서 18건
실패한다 — 전부 `rulebook_checkout`/`core_root`가 실제 `git clone`을 시도하다
샌드박스의 git-hook-템플릿 복사 제약(`cannot copy '.../commit-msg.sample'
... Operation not permitted`)에 걸려서다. 이슈-201 survey가 이미 같은 클래스의
샌드박스 아티팩트를 문서화해 뒀다(`docs/issue-201/reports/implementation/survey.md`
"개별 재현" 절) — `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE`를 로컬
체크아웃으로 돌리면 우회 가능하나, 이 세션의 승인 모드에서는 그 환경변수
경유 실행 자체가 별도 승인을 요구해 이 세션 안에서는 못 걸었다. 이 결함
3건과 무관 — `FailClosedDowngrade`/`Clean` 두 클래스는 네트워크를 전혀 안 쓰고
위에서 격리 실행으로 12건 전부 통과 확인했다.

## 쓰기 대상(write set) 예상

- `spawn.py` — `fail_closed_downgrade()` 뒤에 붙는 새 재분류 단계(신규 함수),
  그 신규 함수를 부르도록 호출부(`:2590` 부근) 수정, `clean`의 `sibling.unlink()`
  앞 파일 가드(`:2125-2126`).
- `.gitignore` — `.warrant-hunt.*` 한 줄 추가.
- `test_spawn.py` — 신규 함수를 위한 새 테스트 클래스, `clean`의 디렉터리 형제
  가드를 위한 새 테스트 1건. 기존 테스트는 한 줄도 수정하지 않는다.
- 문서: 이 survey와 곧 이어지는 proposal 외에 handbook/decision 갱신 대상
  없음(위 "원장 스키마 소비자" 절 — 나열된 outcome 값을 문서화한 곳이 없다).
