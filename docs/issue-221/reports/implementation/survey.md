# Survey — issue #221: 워크스페이스 동기화 3중 결함

착수 시점 확인: #218(PR #219, 머지됨 2026-08-03T00:59Z)·#220(PR #225, 머지됨
2026-08-03T01:21Z) 둘 다 CLOSED/COMPLETED, main 에 랜딩 완료 — 착수 제약
충족. 감사 시점 행 번호(2245/2249/2272/2287)는 그 사이 머지들로 현재
2369/2373/2396/2411 로 이동했다(같은 4곳, 순서·개수 불변).

## 대상 코드: `issue_workspace()` / `checkout_issue_branch()` (spawn.py:2327-2421)

## 결함 1 — fetch 실패 무시 (4곳 확인)

`issue_workspace()`:
- spawn.py:2369 — cwd 가 이미 자기 워크스페이스일 때의 재사용 fetch.
- spawn.py:2373 — 기존 워크스페이스 디렉터리 재사용 시의 fetch.
- spawn.py:2396 — 신규 클론 직후, origin 을 실제 원격으로 되돌린 뒤의 fetch.

`checkout_issue_branch()`:
- spawn.py:2411 — 브랜치 갈아타기 전의 fetch.

넷 다 `subprocess.run([...], capture_output=True, text=True)`(2411 은
`capture_output=True` 만) 결과를 변수에 담지 않거나 담아도 returncode를
검사하지 않는다 — 실패해도 다음 줄로 그대로 진행한다.

이슈 코멘트가 실측을 첨부했다: core issue-90 관찰 세션에서 `git fetch
origin`이 `failed to store: 100001`을 stderr에 찍고도 **exit 0**으로
끝났다 — `returncode != 0` 검사만으로는 이 실패를 못 잡는다. 이 저장소
바깥의 사례도 같은 패턴을 보고한다: git 은 개별 ref 갱신이 실패해도
`fetch` 프로세스 자체는 성공으로 끝내는 경우가 있어(puppetlabs/r10k#115,
r10k#96), stderr 의 ref 갱신 메시지를 같이 봐야 한다는 게 일반적인
권고다(`git-fetch` 문서: 성공/실패는 ref 별로 갈릴 수 있다).

## 결함 2 — 재사용 시 브랜치 미동기화 (spawn.py:2412-2418)

```python
if git("rev-parse", "--verify", "-q", br).returncode == 0:
    r = git("checkout", br)
else:
    base = _base(cwd)
    r = git("checkout", "-b", br, base)
```

`rev-parse --verify -q br`는 **로컬** ref 만 본다. 워크스페이스가 새로
클론된 직후(예: `Clean` 이 죽은 워크스페이스를 지운 뒤 재스폰 — 이슈가
든 예시와 동일)라면 `git clone`이 모든 브랜치를 `origin/<br>`로는
가져오지만 로컬 브랜치는 clone 시점 `src`의 HEAD였던 것 하나만 생긴다.
phase 1이 이미 `origin/issue-221/implementation`에 커밋을 push해 뒀어도
`rev-parse --verify -q issue-221/implementation`는 실패하고, else 분기가
`base`(origin/main)에서 **새 브랜치를 판다** — origin 의 기존 브랜치를
무시하고 완전히 다른 이력에서 출발한다. 이후 이 로컬 브랜치가 push되면
origin 과 공통 조상이 없어 논-패스트포워드로 거부되거나(정상 push
경로라면), 혹은 `ensure_pushed`가 애초에 이 상황을 가정하지 않은 채
동작해 브랜치 이력이 영구히 갈라진다.

**주의 — 로컬 브랜치가 이미 있는 경우(2412번째 줄 if-분기)는 건드리지
않는다.** `issue_workspace()`의 재사용 주석이 명시하듯("재스폰이면 기존
작업 디렉토리를 fetch 로 재사용한다 — 진행 중이던 브랜치 작업을 버리지
않는다") 로컬에 이미 있는 브랜치를 origin 기준으로 강제 리셋/병합하면
세션이 아직 push 못한 로컬 커밋을 지울 위험이 있다 — 이는 워크스페이스
재사용 설계 자체의 목적과 정반대다. 이슈 본문도 이 결함의 예시로 "clean
후 재스폰처럼 원격 브랜치에서 이어가야 하는 경로가 정확히 이 케이스"라고
**로컬 브랜치가 없는 경우**를 명시적으로 지목한다 — 범위는 else 분기(로컬
브랜치 부재 + origin 에는 존재)로 좁힌다.

## 결함 3 — origin/HEAD 오염 (spawn.py:2377, 2381-2382, 2396-2397)

```python
c = subprocess.run(["git", "clone", "-q", str(src), str(work)], ...)   # 2377
...
subprocess.run(["git", "-C", str(work), "remote", "set-url", "origin", origin], ...)  # 2381-2382
...
subprocess.run(["git", "-C", str(work), "fetch", "-q", "origin"], ...)  # 2396-2397
```

`git clone`은 **clone 시점의 `src` 원격**을 질의해 `refs/remotes/origin/HEAD`
심볼릭 ref를 그 원격의 기본 브랜치(정확히는 clone 시점 `src`가 체크아웃
중이던 브랜치)로 고정한다. 그 직후 `remote set-url`로 origin 을 실제
GitHub 원격으로 바꿔도 이 심볼릭 ref는 자동 갱신되지 않는다 — `git
remote set-url`은 URL만 바꾸고 `refs/remotes/origin/HEAD`는 손대지
않는다. 사용자가 feature 브랜치에서 스폰하면 `src`의 HEAD가 그 feature
브랜치이므로, 작업 클론의 `origin/HEAD`는 실제 GitHub 저장소의 default
브랜치(main)가 아니라 사용자의 그 순간 WIP 브랜치 이름을 가리킨 채로
남는다.

`_base(cwd)`(spawn.py:1041-1051)는 diff 비교 기준을 고를 때 이 심볼릭
ref를 **최우선**으로 읽는다:

```python
p = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short",
                    "refs/remotes/origin/HEAD"], ...)
if p.returncode == 0 and p.stdout.strip():
    return p.stdout.strip()
```

`gate_report()`(spawn.py:1054-1075)가 `gates.BASE = _base(cwd)`로 이
값을 그대로 게이트 비교 기준에 꽂는다 — origin/HEAD 오염은 `_base()`를
경유해 게이트의 diff 기준 자체를 오염시킨다. 고치려면 `git remote
set-head origin -a`(실제 origin 을 질의해 심볼릭 ref를 다시 계산)를
`remote set-url` + fetch 뒤에 호출해야 한다.

## 이 저장소 안 prior art — 같은 결함 클래스가 이미 다른 곳에도 있다

`rulebook_checkout()`(spawn.py:198-202)의 재사용 분기도 `git pull -q
--ff-only`를 fire-and-forget으로 돈다(returncode 미검사) — 이슈 #221과
정확히 같은 결함 클래스지만 이 이슈의 write set(`issue_workspace`/
`checkout_issue_branch` 계열) 밖이다. `core_root()`의 관리 클론 분기
(spawn.py:1870-1871, `git pull -q --ff-only`)도 마찬가지. 둘 다 고치지
않는다 — 이슈 본문이 명시적으로 "이 함수들(issue_workspace/
checkout_issue_branch 계열)"로 범위를 좁혔고, 두 곳 모두 다른 이슈의
영역(룰북/코어 체크아웃)이다. Rationale에서 "전부 한 번에 고치는 대안"을
기각 근거로 다룬다.

`ensure_pushed()`(spawn.py:2424-2452)는 이 파일 안에서 이미 fail-closed
스타일로 짜여 있다 — `rev-list --count`의 returncode 를 `unborn` 판정에
쓰고, push 실패 시 `sys.exit`이 아니라 stderr 로그 후 조용히 리턴한다
(호스트 릴레이가 뒤에서 재시도하므로 세션을 죽일 필요가 없다는 판단).
이 파일의 기존 `sys.exit(f"...: {r.stderr.strip()[:200]}")` 패턴
(spawn.py:2380, 2420)이 하드 실패 보고의 house style이다 — 결함 1의
fail-closed 헬퍼도 이 스타일을 따른다.

## 외부 prior art — git fetch 실패가 exit 0 으로 새는 사례

WebSearch 1건(2026-08-03): puppetlabs/r10k#115·#96 이 "개별 ref 갱신
실패가 fetch 프로세스 전체의 exit code 에는 안 잡힌다"는 같은 패턴을
보고 — 권장 대응은 stderr 캡처 + ref 갱신 실패 메시지 파싱, returncode
단독 검사가 아니다. 이 이슈가 실측한 "failed to store" 문구도 이
패턴에 부합한다.

## 시그니처·계약 확인 (건드리면 안 되는 부분)

- `issue_workspace(cwd: str, issue: int, role: str) -> str` — 반환형·
  인자 불변. 호출부 `_spawn_one()`이 문자열 경로를 그대로 기대한다.
- `checkout_issue_branch(cwd: str, issue: int, role: str) -> str` —
  반환형(브랜치명 문자열) 불변. `test_spawn.py`의 `Ledger`/
  `IssueScopedPrompt`/`EventReporting` 클래스들이 이 둘을
  `mock.patch.object`로 완전히 대체해서 쓰므로, 시그니처가 바뀌면 그
  목(mock)들도 깨진다 — 순수 내부 구현 교체만 허용.
- `_base(cwd)` — 반환형 `str` 불변. `gate_report()`가 그대로 소비.
  이 이슈는 `_base()` 자체를 고치지 않는다 — origin/HEAD 를 clone 단계
  에서 올바르게 맞춰서 `_base()`가 이미 하는 "origin/HEAD 우선" 로직이
  제대로 된 값을 읽게 만드는 것으로 충분하다.
- 사용자 로컬 체크아웃 강제 이동 금지(#218 제약) — 이 이슈의 fetch 4곳은
  전부 **세션 소유 워크스페이스**(`work` 디렉터리, on-the-record 가 clone한
  격리 클론) 대상이지 사용자가 스폰한 `cwd`(원본 `src`) 자체가 아니다.
  `src`에 대해 실행하는 유일한 git 호출은 `remote get-url`(읽기 전용,
  2338-2339)뿐 — 이 이슈의 fail-closed 화는 `src`를 건드리지 않는다.

## 테스트 현황

`test_spawn.py`에서 `issue_workspace`/`checkout_issue_branch`를 검사하는
테스트는 전부(`Ledger`, `IssueScopedPrompt`, `EventReporting`)
`mock.patch.object`로 두 함수를 가짜로 바꿔서 그 **호출자**
(`_spawn_one` 계열)의 배선만 검사한다 — 두 함수 자체의 실 git 동작(fetch
실패 처리, 브랜치 재사용, origin/HEAD)을 실 git 레포로 검사하는 테스트는
0건(grep 결과 없음, 이슈 본문의 "실 git 테스트 0건" 주장과 일치). 다른
클래스(`GitHead`, `IsNewCommit`, `Clean`)는 이미 `tempfile
.TemporaryDirectory()` + `git init -q`로 실 레포를 만드는 하우스 스타일을
쓴다 — 이번 회귀 테스트도 이 패턴을 따른다(로컬 "origin" 역할을 할 실
저장소 하나 + 그걸 clone 한 작업 디렉터리 하나, 두 실 레포 구성이 필요).

## 쓸 파일 (write set 예상)

- `spawn.py` — `issue_workspace()`의 fetch 3곳(2369/2373/2396)을
  fail-closed 헬퍼로 교체, 신규 클론 경로에 `git remote set-head origin
  -a` 추가, `checkout_issue_branch()`의 fetch(2411)를 같은 헬퍼로 교체,
  else 분기(2415-2418)를 origin 전용 브랜치 존재 확인 후 트래킹 생성으로
  교체.
- `test_spawn.py` — 실 git 레포 기반 회귀 테스트 추가(대략 4건: fetch
  실패 fail-closed, 원격 전용 브랜치 트래킹 생성, origin/HEAD 정정,
  기존 로컬 브랜치 재사용 시 로컬 커밋 보존 회귀).

## 스카우트 판단

product-shaped 아님 — #218/#220과 동일 사유(내부 오케스트레이션
git-동기화 로직, 비교할 외부 카테고리 제품 없음). 스킵하지 않고 두 갈래로
조사: (1) 이 저장소 내부 prior art(`rulebook_checkout`/`core_root`의 같은
결함 클래스, `ensure_pushed`의 fail-closed 스타일 — 위 절), (2) 외부
prior art 1건(WebSearch, git fetch 부분 실패가 exit 0 으로 새는 일반
패턴). 상세·소스는 `scout-brief.md`.
