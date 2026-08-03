files:
- spawn.py
- test_spawn.py

## Request

이슈 #221(신청자 jjongkwann): `issue_workspace()`/`checkout_issue_branch()`
계열에 결함 3건 — (1) fetch 호출 4곳(spawn.py:2369/2373/2396/2411)이
returncode 를 안 봐서 네트워크 실패 시 조용히 옛 코드로 진행, (2)
`checkout_issue_branch()`가 워크스페이스 재사용/재스폰 시 로컬에 없고
origin 에만 있는 브랜치를 못 보고 base 에서 새로 파서 영구 분기, (3)
신규 워크스페이스 clone 이 `origin/HEAD`를 clone 시점 `src`의 체크아웃
브랜치로 물려받고 안 고쳐서 `_base()`/`gates.BASE`의 diff 기준까지
오염. 동반 요구로 이 함수군의 실 git 회귀 테스트(현재 0건)를 추가한다.

## Constraints

- 착수 시점: #218(PR #219)·#220(PR #225) 둘 다 main 에 머지됨 —
  확인 완료(survey.md 참조), 착수 가능.
- `issue_workspace()`/`checkout_issue_branch()`의 반환형·인자 시그니처
  불변 — `test_spawn.py`의 `Ledger`/`IssueScopedPrompt`/
  `EventReporting`이 `mock.patch.object`로 이 둘을 대체해서 호출부만
  검사하므로, 시그니처가 바뀌면 그 목(mock)들이 깨진다.
- 로컬 오버라이드 강제 이동 금지(#218 제약)는 이 이슈에 문자 그대로
  적용되지 않는다 — 이 이슈의 fetch 4곳은 전부 **세션 소유
  워크스페이스**(`work` 디렉터리, on-the-record 가 만든 격리 클론) 대상이지
  사용자가 스폰한 `cwd`(`src`) 자체가 아니다. `src`에 대한 유일한 git
  호출은 읽기 전용 `remote get-url`(2338-2339)뿐 — 그대로 둔다.
- 로컬에 **이미 있는** 이슈 브랜치는 origin 기준으로 강제 리셋/병합하지
  않는다 — `issue_workspace()`의 재사용 설계 자체가 "진행 중이던 브랜치
  작업을 버리지 않는다"는 목적이라, 여기에 강제 동기화를 얹으면 세션이
  아직 push 못한 로컬 커밋을 지울 수 있다. 이슈 본문도 결함 2의 예시로
  "로컬에 브랜치가 없는" 케이스를 명시적으로 지목한다.
- `_base()`(spawn.py:1041-1051) 자체의 로직·반환형은 바꾸지 않는다 —
  이미 origin/HEAD 를 최우선으로 읽는 로직은 옳다; 결함은 origin/HEAD
  값 자체가 clone 단계에서 잘못 세팅된다는 것이므로, clone 쪽을 고치면
  `_base()`는 손대지 않고도 올바른 값을 읽는다.

## Rationale

**대안 1(rejected) — fetch 실패 탐지를 returncode 단독으로 좁힌다.**
이슈가 실측한 "failed to store: 100001" 사례는 `returncode == 0`으로
끝났다 — returncode 만 보는 안은 이 이슈의 동기 그 자체를 놓친다.
considered and rejected: 이슈가 첨부한 실측 사례를 그대로 재현하지
못한다.

**대안 2(rejected) — stderr 전체에 "error"/"fatal" 같은 광범위한
정규식 패턴을 매칭한다.** 실측된 구체 사례는 "failed to store"
하나뿐이고, git 은 정상 동작 중에도 stderr 에 진행 로그를 남길 때가
있어(예: 협상 메시지) 광범위한 패턴은 근거 없는 추측성 오탐 위험만
키운다. considered and rejected: 근거(실측 사례) 없는 패턴 확장.
채택안(instead of 위 두 대안): `returncode != 0` **또는** stderr 에
`"failed to store"` 포함 시 실패로 판정하는 좁은 fail-closed 헬퍼 —
실측된 두 실패 모드(정상적 returncode 실패, 그리고 이 이슈가 실측한
예외적 exit-0 실패)를 정확히 커버하고, 더 넓히지 않는다.

**대안 3(rejected) — 결함 2를 else 분기로 좁히지 않고, 로컬 브랜치
존재 여부와 무관하게 항상 origin 기준으로 재동기화한다.**
`issue_workspace()`의 기존 재사용 주석이 "진행 중이던 브랜치 작업을
버리지 않는다"를 명시적 설계 목적으로 적어 뒀고, 로컬 브랜치를 origin
기준으로 강제 리셋/병합하면 세션이 커밋만 하고 아직 push 못한 작업을
지울 수 있다 — 워크스페이스 재사용이 존재하는 이유 자체와 정반대
결과를 낳는다. considered and rejected: 미push 로컬 커밋 유실 위험.
채택안(instead of 대안 3): `rev-parse --verify -q br`가 실패하는 else
분기에서만, base 로 새로 파기 전에 `origin/<br>` 존재를 확인하고 있으면
그것을 트래킹하는 로컬 브랜치를 만든다(`git checkout -b br origin/<br>`).
로컬에 이미 있는 브랜치(if 분기)는 지금처럼 그대로 `checkout`만 한다 —
손대지 않는다.

**대안 4(rejected) — origin/HEAD 정정을 매 fetch(재사용 경로 포함)마다
반복 실행한다.** origin/HEAD 오염은 clone 시점에 딱 한 번 발생하는
문제이고(clone 이 `src`의 그 순간 HEAD 를 물려받는 게 원인), 이미
올바르게 세팅된 뒤에는 원격의 default 브랜치가 바뀌는 드문 경우가
아닌 한 매번 다시 계산할 필요가 없다 — 매 재사용 fetch 마다 원격에
`ls-remote --symref`급 질의를 추가하면 재사용 경로의 왕복이 불필요하게
늘어난다. considered and rejected: 반복되는 원격 질의 비용 대비 이득
없음. 채택안(instead of 대안 4): 신규 clone 경로(spawn.py:2381-2397,
`remote set-url` 뒤 fetch 직후)에서만 `git remote set-head origin -a`
1회 호출.

**대안 5(rejected) — 같은 결함 클래스가 있는 `rulebook_checkout()`/
`core_root()`도 이 김에 함께 고친다.** 이슈 본문이 write set 을
"issue_workspace/checkout_issue_branch 계열"로 명시적으로 좁혔고, 두
함수는 다른 이슈 영역(룰북·코어 체크아웃)이라 이 제안의 frozen write
set 밖이다(scope-exceeded 원칙). considered and rejected: 이슈가 정한
범위 밖 — 별도 이슈로 미룬다.

## What will be done

1. `spawn.py`에 fail-closed fetch 헬퍼(가칭 `_fetch_or_halt(work_dir,
   label)`) 신설: `git -C work_dir fetch -q origin` 실행 후
   `returncode != 0` 또는 stderr 에 `"failed to store"` 포함 시
   `sys.exit(f"...: {label} ...: {stderr[:200]}")`로 중단(기존
   `ensure_pushed`/2380/2420 라인의 `sys.exit` house style과 통일).
2. `issue_workspace()`의 fetch 3곳(2369/2373/2396)을 이 헬퍼 호출로
   교체.
3. `issue_workspace()`의 신규 clone 경로(2381-2397, `remote set-url`
   뒤 새 헬퍼 호출 직후)에 `git -C work remote set-head origin -a`
   호출 추가.
4. `checkout_issue_branch()`의 fetch(2411)를 같은 헬퍼로 교체.
5. `checkout_issue_branch()`의 else 분기(2415-2418)를 수정: base 에서
   새로 파기 전에 `git rev-parse --verify -q origin/<br>`로 원격 브랜치
   존재를 먼저 확인 — 있으면 `git checkout -b br origin/<br>`로
   트래킹 생성, 없으면 기존 로직(base 에서 새로 파기, 그마저 실패하면
   현재 HEAD 에서) 그대로 유지.
6. `test_spawn.py`에 실 git 레포 기반(mock 없음, `tempfile
   .TemporaryDirectory()` + `git init -q` — `GitHead`/`Clean` 클래스와
   같은 하우스 스타일) 회귀 테스트 4건 추가: (a) fetch 가 non-zero
   returncode 로 실패하면 `sys.exit` 하는지, (b) fetch 가 exit 0 이면서
   stderr 에 `"failed to store"`를 포함하면 역시 halt 하는지, (c) 로컬에
   없고 origin 에만 있는 이슈 브랜치가 새로 파지지 않고 트래킹 생성되는지
   (기존 origin 커밋 이력을 그대로 갖는지 assert), (d) 로컬에 이미 있는
   이슈 브랜치(아직 push 안 된 로컬 커밋 포함)가 재사용 시 그대로
   보존되는지(회귀 방지 — 결함 2 수정이 이 케이스를 건드리지 않았음을
   확인).

## Out of scope

- `rulebook_checkout()`/`core_root()`의 동일 결함 클래스(fire-and-forget
  `pull --ff-only`) — 다른 이슈 영역, 이 write set 밖(Rationale 대안 5).
- `_base()` 자체의 로직 변경 — origin/HEAD 를 clone 단계에서 바로잡는
  것으로 충분, `_base()`는 손대지 않는다.
- 로컬에 이미 있는 이슈 브랜치를 origin 기준으로 강제 동기화(리셋/병합/
  리베이스) — Rationale 대안 3에서 기각, 세션의 미push 커밋을 지울
  위험.
- `ensure_pushed()` 변경 — 이미 이 파일의 fail-closed 관용구 원본이며,
  이 이슈의 결함 대상이 아니다.

## How you'll know it worked

- `python3 -m unittest test_spawn.py -v`가 신규 4건 포함 전부 통과.
- 신규 테스트 (a)(b)는 fetch 를 강제로 실패시키는 실 git 레포(존재하지
  않는 origin 경로, 또는 fetch 를 가로채는 wrapper)로 `sys.exit`
  (`SystemExit`) 발생을 assert — mock 으로 returncode 만 조작하지 않고
  실제 실패를 재현한다.
- 신규 테스트 (c)는 "origin(실 저장소)에 브랜치 A 를 push해 두고
  로컬에는 없는 상태"에서 `checkout_issue_branch()`를 호출해, 결과
  브랜치의 커밋 이력이 base 가 아니라 origin 의 A 브랜치 이력과 일치하는지
  확인.
- 신규 테스트 (d)는 "로컬에 브랜치 존재 + 그 브랜치에 origin 에는 없는
  커밋 1개 있는 상태"에서 재사용 경로를 호출해, 그 커밋이 여전히
  `git log`에 남아 있는지(지워지지 않았는지) 확인.
- 수동 확인: feature 브랜치에서 `spawn.py`를 스폰해 만든 워크스페이스의
  `git symbolic-ref --short refs/remotes/origin/HEAD`가 실제 GitHub
  저장소의 default 브랜치(main)를 가리키는지 눈으로 1회 확인.
