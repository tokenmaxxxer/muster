# Scout brief — issue #221

**모드:** 내부 prior-art 조사 1건 + 외부 WebSearch 1건 (병렬 배치, 1
스테이지) — #218/#220과 같은 세그먼트 판단.

**세그먼트 판단:** product-shaped 아님. `issue_workspace()`/
`checkout_issue_branch()`는 사용자가 보지 못하는 내부 오케스트레이션(role
세션의 격리 클론 관리)이다 — 비교할 외부 "카테고리 best-in-class" 제품이
없다. 이 저장소 안의 동종 해법 + git 자체의 fetch 실패 처리에 대한 일반
prior art로 대체.

**Prior art 1 (내부): `ensure_pushed()`의 fail-closed 스타일**
(`spawn.py:2424-2452`) — 이 파일 안에서 이미 검증된 패턴: 하드 실패는
`sys.exit(f"...: {r.stderr.strip()[:200]}")`로 중단(2380, 2420), 재시도
가능한 실패(push)는 stderr 로그 후 조용히 리턴(호스트 릴레이가 뒤에서
처리). fetch 4곳의 fail-closed화는 이 house style을 그대로 따른다 —
새 관용구를 발명하지 않는다.

**Prior art 2 (내부, 반면교사): `rulebook_checkout()`/`core_root()`의
동일 결함 클래스** — 재사용 분기의 `git pull -q --ff-only`가 이 이슈와
똑같이 returncode 미검사(fire-and-forget)다. 이슈 write set 밖(다른
이슈 영역)이라 고치지 않지만, "이 저장소에 이미 있는 패턴이니 그대로
둔다"는 안일한 정당화는 배제 — 오히려 이 이슈가 고치는 함수군에서만이라도
fail-closed 원칙을 실제로 지키는 첫 사례를 만든다는 근거로 쓴다.

**Must-be (외부 prior art, WebSearch 1건):** git 은 개별 ref 갱신
실패가 fetch 프로세스 전체의 exit code 에는 반영되지 않는 경우가
있다(puppetlabs/r10k#115, r10k#96) — returncode 단독 검사는 불충분하고,
stderr 의 ref 갱신 실패 메시지를 같이 확인해야 한다는 게 일반적 권고.
이슈가 실측한 "failed to store" 문구가 정확히 이 패턴.

**성능축:** (a) 실패 탐지 범위 — returncode 만 볼지, stderr 패턴도
같이 볼지. (b) 재사용 시 안전성 — 로컬에 이미 있는 브랜치를 건드리지
않고 "원격 전용" 케이스만 좁게 고치는지, 아니면 광범위하게 강제
동기화하는지.

**GAP LINE:** must-be (a)는 이 저장소 전체가 미달 — fetch 4곳
전부 returncode 도 안 본다(가장 기초 단계에서부터 미달). must-be (b)는
`issue_workspace()`의 재사용 자체 설계(주석: "진행 중이던 브랜치 작업을
버리지 않는다")는 이미 원칙을 세워 뒀지만 `checkout_issue_branch()`의
else 분기가 그 원칙과 무관하게 "원격에만 있는 브랜치"를 무시하고 새로
파는 것으로 그 원칙을 무너뜨린다 — 원칙은 있는데 구현이 못 따라간
케이스.

**Adopt:** `ensure_pushed()`의 fail-closed 로그/exit 관용구(성능축 a 대응),
"로컬에 이미 있는 브랜치는 건드리지 않는다"는 기존 재사용 설계 원칙(성능축
b 대응) — else 분기만 좁게 고쳐 원칙과 구현을 일치시킨다.
**Skip:** stderr 전체에 대한 광범위한 실패 패턴 매칭(정규식 라이브러리
등) — 실측된 구체 사례("failed to store")는 하나뿐이라 그 문구 매칭 +
returncode 검사로 좁힌다. 과도한 패턴 목록은 근거 없는 추측이 된다(근거는
proposal Rationale).

**Sources:** 내부 — `spawn.py:2327-2452`(대상 함수군),
`spawn.py:174-220`(`rulebook_checkout`/`checkout_version`),
`spawn.py:1851-1887`(`core_root`), `test_spawn.py`(`GitHead`/
`IsNewCommit`/`Clean`의 실 git fixture 패턴). 외부 —
https://github.com/puppetlabs/r10k/issues/115 ,
https://github.com/puppetlabs/r10k/issues/96 ,
https://git-scm.com/docs/git-fetch 。

**스테이지:** 1스테이지(내부 정독 + 외부 WebSearch 1건, 병렬 배치),
판단점 1회 후 즉시 포화 — 외부 검색 결과가 이슈 코멘트가 이미 실측한
사실("returncode 단독 불충분")을 그대로 재확인했을 뿐 새 결정을 바꾸지
않아 조기 종료.
