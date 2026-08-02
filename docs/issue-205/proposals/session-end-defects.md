files:
- spawn.py
- .gitignore
- test_spawn.py

## Request

이슈 #205: 세션 종결 처리(`spawn.py`)의 독립 결함 3건, 위치·원인 전부 특정돼
한 flow로 묶는다.

1. `fail_closed_downgrade()`(`spawn.py:1232-1263`)가 커밋 유무보다 dirty 검사를
   먼저 봐서, 실제 커밋+PR이 있던 세션 2건(issue-189 phase 1 커밋 `1ed27b9`/PR
   #191, issue-192 phase 1 커밋 `7d11c9e`/PR #194 — 둘 다 이 저장소 히스토리에
   실재, survey에서 확인)이 `failed-no-commit`으로 찍혔다. 두 건 다 dirty 원인은
   `.warrant-hunt.count` 하나였다.
2. 그 `.warrant-hunt.count`는 tokenmaxxxer-core warrant 훅의 상태 파일
   (`hunt-guard.sh:81`이 읽고 `hunt-state.sh:43`이 지움)인데 `.gitignore`에
   없어서, 훅이 지울 때마다(또는 만들 때마다) 워크스페이스가 dirty해진다.
3. `clean`의 형제 삭제(`spawn.py:2125-2126`)가 `sibling.unlink()`를 파일 가드
   없이 불러, 형제가 디렉터리면 `IsADirectoryError`로 clean 루프 전체가
   중단된다(현재 형제는 전부 파일이라 잠복).

## Constraints

- 커밋이 있는 세션은 outcome이 실패로 찍히지 않는다. 커밋은 있으나 트리가
  dirty인 경우는 별도 표기로 구분한다 — 기존 `failed-no-commit`의 의미는
  "정말 커밋이 없음"으로 좁아진다(요구사항 1).
- `.warrant-hunt.count`가 워크스페이스 트리를 더럽히지 않는다 — 방향은
  git 추적 해제 + gitignore로 확정(요구사항 2).
- `clean`의 형제 삭제가 디렉터리를 만나도 멈추지 않는다(요구사항 3).
- 원장 스키마 소비자(`gates/flows.py`의 `_ledger_read`/`flows_payload` ledger
  구역)가 깨지지 않는다(요구사항 4) — survey에서 확인: 이 소비자는 `outcome`을
  불투명 문자열로 버킷팅만 하지, 특정 값 집합으로 분기하지 않는다.
- 기존 테스트는 원칙적으로 무변경으로 통과해야 한다 — 특히 `test_spawn.py`의
  `FailClosedDowngrade`(`:585-655`)와 `Clean`(`:1252-1374`) 두 클래스는 이번
  결함들과 정확히 겹치는 영역이라 회귀에 가장 취약하다. 다만 **결함 자체를
  단언하는 테스트는 수정 허용**(phase-1 PR #206에 대한 사용자 피드백,
  오케스트레이터 중계, 2026-08-02) — 최소 `test_new_commit_dirty_tree_is_still_downgraded`
  (`new_commit=True`+dirty → `"failed-no-commit"` 단언은 이 이슈가 고치려는
  바로 그 오판정의 문서화)는 수정 대상이다. 제약의 의도는 이번 수정과 무관한
  동작의 보호였지 버그의 보존이 아니다. `test_already_delivered_with_dirty_tree_still_downgrades`처럼
  결함을 단언하지 않는 테스트는 이 완화 대상이 아니며 무변경으로 남는다.

## Rationale

**결함 1 — 채택(사용자 결정으로 재채택, 2026-08-02): `fail_closed_downgrade()`
내부에서 `uncommitted`/`new_commit` 검사 순서를 직접 교정한다 — 재분류
우회층 없이.** 이슈 본문이 "원인은 검사 순서"라고 지목한 그대로를 고치는
가장 직접적인 방법. 현재 순서(`if uncommitted: return "failed-no-commit"`이
`new_commit` 확인보다 먼저)의 앞에 `new_commit and uncommitted`인 경우만 골라
`"progressed-dirty-tree"`(신규 outcome 값)를 직접 리턴하는 분기 한 줄을
추가한다. 그 뒤로 기존 `if uncommitted: return "failed-no-commit"` 이하는
그대로 둔다 — `new_commit=False`(진짜 커밋 없음)인 dirty tree는 여전히
`"failed-no-commit"`을 받는다.

`already_delivered` 단독(이 세션 자체는 새 커밋 없음, 브랜치에 이전 phase
커밋만 있음) 케이스는 승격 대상에서 제외한다 — 이슈가 실측한 두 사례
(1ed27b9, 7d11c9e) 다 이 세션 자신의 새 커밋이 있는 경우였고,
`already_delivered`+dirty를 여전히 실패로 다루는 기존 테스트
(`test_already_delivered_with_dirty_tree_still_downgrades`)에 이미 "이 세션
자신의 dirty 잔재는 여전히 위험 신호"라는 독립적 근거가 있다 — 실측 범위
밖까지 넓히지 않는다(사용자 결정에서도 이 부분은 원안대로 수용).

거부한 대안(rejected alternative) 둘:

1. **(이전 phase-1 제안에서 채택했다가 이번에 기각) `fail_closed_downgrade()`는
   손대지 않고, 그 뒤에 재분류 단계(가칭 `reclassify_dirty_but_committed()`)를
   별도로 둔다.** 앞선 제안에서는 "기존 테스트 무변경" 제약을 절대적으로
   읽어, 이 함수를 직접 호출하는 `test_new_commit_dirty_tree_is_still_downgraded`가
   지금 순서의 결과값(`"failed-no-commit"`)을 단언하고 있다는 이유로 직접
   교정을 기각하고 우회층을 채택했다. 그러나 그 단언 자체가 이슈 #205가
   고치려는 오판정의 문서화이고, 제약의 의도는 무관한 동작 보호였지 버그
   보존이 아니라는 사용자 피드백에 따라 이 제약 해석이 뒤집혔다 — 우회층은
   이제 필요 없는 간접 계층일 뿐이라 **기각한다(rejected)**. 직접 교정이
   이슈가 지목한 원인을 그대로 고치는 더 단순한 형태다.
2. **새 outcome 문자열 대신 ledger 엔트리에 `"dirty_tree": bool` 필드를 추가하고
   `outcome`은 그대로 `"progressed"`로 둔다.** 구조적으로는 더 깔끔해 보이지만,
   `gates/flows.py`의 유일한 ledger 소비 지점(`flows_payload`의
   `agg["outcomes"][outcome] += 1`)이 `outcome` 문자열만 읽고 다른 필드는 아예
   보지 않는다 — 새 필드를 추가해도 이 통계(요구사항 1이 고치려는 바로 그
   "outcome 통계가 실제보다 나쁘게 나온다")에는 반영되지 않는다. 이 저장소는
   이미 같은 문제(silent-failure인데 uncommitted가 있음)를 `"uncommitted-work"`
   라는 별도 outcome 문자열로 구분해 온 선례가 있다(`spawn.py:2581-2582`) — 같은
   메커니즘을 그대로 따르는 쪽이 일관적이라 필드 추가 대신 새 outcome 값을
   **채택**하고, 필드 추가안은 **기각한다(rejected)**.

**결함 2 — 채택: `.gitignore`에 `.warrant-hunt.*` 추가.** 방향(git 추적 해제 +
gitignore) 자체는 이슈가 확정했고, 추적 해제는 `1c230db`(issue-197 phase 1)가
이미 부수 효과로 끝냈다(survey 확인) — 남은 일은 gitignore 패턴 하나뿐이다.

거부한 대안: **리터럴 `.warrant-hunt.count` 한 줄만 추가하고 `.warrant-hunt.lock`
(같은 훅 쌍이 쓰는 형제 상태 파일)은 그대로 둔다.** 이슈 본문이 지목한 파일은
`.count`뿐이지만, `.lock`도 같은 훅이 같은 루트에 쓰는 같은 계열의 상태 파일이라
"훅 상태 파일은 소스가 아니다"라는 근거가 동일하게 적용된다. 이 저장소 자신의
`clean()` 형제 삭제 주석(`spawn.py:2123-2125`, 결함 3 바로 옆)이 이미 "접미사를
하나씩 나열하면 다음에 하나 더 생길 때 또 빠뜨린다"고 명시한 원칙과 정확히
같은 상황이라, 리터럴 나열은 **기각하고(rejected)** 와일드카드 패턴을
채택한다.

**결함 3 — 채택: `sibling.unlink()` 앞에 `sibling.is_file()` 가드 한 줄.**

거부한 대안: **디렉터리 형제를 만나면 `shutil.rmtree()`로 재귀 삭제까지
처리한다.** 더 "완결된" 처리처럼 보이지만, 이슈 본문이 명시한 범위는
"파일 가드 한 줄이면 된다"이고, survey에서 확인한 대로 현재 이 글롭이 잡는
형제는 전부 파일(`.session.*.log`/`.events.jsonl`/`.events.offset`/`.task.txt`/
`.respawn-claim-*`)이라 디렉터리 형제가 실제로 생기는 경로 자체가 지금
없다 — 아직 일어나지 않는 케이스를 위한 삭제 정책까지 지금 설계하는 것은
투기적이라 **기각한다(rejected)**. 가드는 죽지 않게만 하고, 디렉터리 형제는
다음 순회 때도 그대로 남아 다음 `clean` 실행에서 다시 판단된다.

## What will be done

1. `spawn.py` — `fail_closed_downgrade()`(`:1232-1263`) 내부, 기존
   `if uncommitted: return "failed-no-commit"` 줄 바로 앞에 한 줄 추가:
   `if new_commit and uncommitted: return "progressed-dirty-tree"`. 그 아래
   기존 로직(`if uncommitted: return "failed-no-commit"` 이하)은 무변경 —
   `new_commit=False`인 dirty tree(진짜 커밋 없음)와 `already_delivered`+dirty는
   그대로 `"failed-no-commit"`을 받는다. 우회 재분류 함수는 두지 않는다.
2. `spawn.py:2590` 부근 호출부: `downgraded = fail_closed_downgrade(...)`
   다음의 `if downgraded != outcome:` 로그 블록 문구를 두 경로로 분기 —
   `downgraded == "progressed-dirty-tree"`이면 "새 커밋은 있지만 워크스페이스에
   정리 안 된 변경이 남았다"는 취지의 새 문구, 그 외(`"failed-no-commit"`)면
   기존 문구 그대로.
3. `.gitignore`에 `.warrant-hunt.*` 한 줄 추가.
4. `spawn.py:2125-2126`: `for sibling in w.parent.glob(w.name + ".*"):` 안,
   `sibling.unlink()` 앞에 `if not sibling.is_file(): continue` 추가(또는 동치인
   `if sibling.is_file(): sibling.unlink()`로 감싸기 — 스타일은 구현 시 결정).
5. `test_spawn.py`:
   - `FailClosedDowngrade.test_new_commit_dirty_tree_is_still_downgraded`
     (`:600-606`)를 수정한다 — 결함을 단언하는 테스트라 수정 허용 대상(위
     Constraints 참조). 이름을 실제 동작에 맞게 바꾸고
     (`test_new_commit_dirty_tree_is_promoted_not_downgraded` 등), 기대값을
     `"failed-no-commit"`에서 `"progressed-dirty-tree"`로 바꾼다. 그 외
     `FailClosedDowngrade`의 8개 테스트(특히
     `test_already_delivered_with_dirty_tree_still_downgrades`)는 한 줄도
     건드리지 않는다.
   - `Clean` 클래스에 테스트 1건 추가(기존 줄 수정 없음): 죽은 워크스페이스의
     형제 글롭 안에 디렉터리 하나(예: `<name>.somedir/`)와 파일 하나를 같이
     만들고 `clean` 실행 — 예외 없이 끝나고, 파일 형제는 지워지고, 디렉터리
     형제는 (가드만 추가하므로) 그대로 남는다는 것과, 목록의 다음 워크스페이스도
     정상 처리된다는 것을 단언.

## Out of scope

- `already_delivered`만 있고 이 세션 자체 새 커밋은 없는 경우의 재분류 —
  이슈가 실측한 두 사례 밖이고, 기존 테스트가 이미 그 케이스를 위험 신호로
  다루는 근거를 대고 있다.
- `clean`이 디렉터리 형제를 재귀 삭제하도록 확장 — Rationale에서 기각한
  대안, 이슈 범위 밖("파일 가드 한 줄이면 된다").
- `rulebook_checkout`/`core_root`의 실제 네트워크 clone이 이 샌드박스에서
  실패하는 문제(전체 스위트 18건) — survey에서 확인한 대로 이 결함 3건과
  무관한 별개의 샌드박스 아티팩트(issue-201 survey가 이미 같은 클래스를
  기록해 뒀다). 손대지 않는다.
- `docs/handbooks/`·`docs/decisions/` 갱신 — survey에서 확인: outcome 값을
  나열해 둔 문서가 없어 갱신 대상이 없다.

## How you'll know it worked

phase 2에서 구현 후 아래가 전부 성립해야 한다:

```
python3 -m pytest test_spawn.py -k "FailClosedDowngrade or Clean" -v
```

- `FailClosedDowngrade`의 9건 전부 통과 — 8건은 문구까지 그대로(특히
  `test_already_delivered_with_dirty_tree_still_downgrades`가 여전히
  `"failed-no-commit"`을 리턴받는 것으로 통과), 수정된 1건
  (`test_new_commit_dirty_tree_is_promoted_not_downgraded`, 옛
  `test_new_commit_dirty_tree_is_still_downgraded`)은 새 기대값
  `"progressed-dirty-tree"`로 통과.
- `Clean`(기존 2건 + 신규 1건) 전부 통과.
- `python3 -m pytest test_spawn.py -q`가 이 세션에서 확인한 베이스라인(관련
  없는 18건 실패는 그대로, 네트워크·룰북-clone 샌드박스 아티팩트) 대비 새
  실패를 추가하지 않는다 — 새로 추가/수정되는 테스트 개수만큼 `collected`
  건수가 늘어난다.
- 수동 확인: `.warrant-hunt.count`/`.warrant-hunt.lock`을 워크스페이스 루트에
  만든 뒤 `git status --porcelain`이 비어 있음(gitignore 적용 확인).
- 수동 확인: `clean` 대상 워크스페이스의 형제 글롭에 디렉터리를 하나 끼워도
  `clean`이 예외 없이 끝까지 순회하고 다른 워크스페이스도 정리한다.
