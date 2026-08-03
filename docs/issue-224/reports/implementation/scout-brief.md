# Scout brief — issue #224

**스킵 기록(결함 1·2):** 둘 다 pure bugfix 스킵 조건 적용 — 결함 1은
`gh api`/`gh pr list` 자체의 플래그 조합 문제로 설계 결정 여지가
사실상 없고(survey.md 실측: `--paginate` 단독은 오히려 다중 페이지를
`ValueError`로 삼켜 결함을 악화시킨다 — `--paginate --slurp` +
평탄화만 유효한 해), 결함 2는 같은 파일의 자매 함수 `_issue_list_all()`
이 이미 정답 관용구(`--limit 1000`)를 갖고 있어 따라가는 것 외에
대안이 없다. 외부 스카우트 생략.

**모드(결함 3):** WebSearch 2건, 병렬 배치 1스테이지 — 판단점 1회 후
즉시 포화(아래 GAP LINE 참고). 세그먼트: product-shaped 아님(사용자가
안 보는 내부 CLI 의 프로세스 감시 루프) — 비교할 외부 제품이 아니라
비슷한 문제를 푸는 CLI/오케스트레이션 관용구를 조사했다.

**Prior art 1 — `docker logs -f`는 대상이 죽으면 즉시 리턴한다, 안
기다린다.** 컨테이너가 멈추면 `docker logs -f`는 (일부 사용자가
`tail -f`와 다르다고 놀랄 정도로) 그 자리에서 종료한다 — "새 로그가
안 오니 계속 기다린다"가 아니라 "대상이 죽었으니 끝낸다"가 업계
관행의 기본값이다. 이 저장소의 `--follow`가 지금 하는 것(대상 사망과
무관하게 로그 정체만 보고 다시 대기)은 이 관행과 반대 방향이다.

**Prior art 2 — liveness 판정과 idle 타임아웃은 같이 쓰되 역할이
다르다.** 프로세스 감시 루프의 일반 패턴은 (a) 신호가 오면 push 로
받고, (b) 신호가 실제로 안 올 수도 있는 상황에 대비해 timeout 을
안전망으로 깐다 — 이 둘을 **경합**시키는 게 아니라 **결합**한다.
Docker 헬스체크 문서도 "PID 1 이 살아있다"만으로는 hang 을 못 잡으니
liveness 판정(프로세스 존재)과 진행 정체 판정(타임스탬프/idle)을
같이 보라고 권한다. `--watch-pid` 류 플래그(직접 PID 를 붙잡고
죽으면 즉시 종료)도 procfs 기반 OS 에서 표준적으로 쓰인다.

**성능축:** (a) 사망 탐지 정확도 — pid 확인은 "이 특정 프로세스가
죽었다"를 즉시·정확히 안다, 순수 타임아웃은 "얼마나 오래 조용했나"
만 알아 살아있지만 느린 세션과 죽은 세션을 구분 못 한다. (b) 최초
탐지까지 걸리는 시간 — pid 확인은 다음 루프 반복(현재 구조에서는
`stall_timeout_min`, 기본 5분 주기)에 바로 걸리고, 순수 타임아웃
안은 그 타임아웃 값 자체를 늘려 잡아야 "느리지만 살아있는 세션"을
오탐하지 않는데, 그러면 진짜 죽은 세션의 탐지도 그만큼 늦어진다.

**GAP LINE:** 이 저장소는 must-be (a)에 이미 필요한 재료를 다
갖췄다(`_alive(pid)`, roster pid 등록 — survey.md) — 그런데도
`--follow` 루프는 그 재료를 안 쓴다(미달). must-be (b)는 두 안 다
저장소 자체의 `stall_timeout_min` 주기 안에서 판정되므로 사실상
동급 — 차이를 만드는 건 오탐률(정확도)이지 속도가 아니다.

**Adopt:** pid 확인을 1차 판정 신호로 쓰고(prior art 1·2 모두 이
방향), 기존 `stall_timeout_min` 은 그대로 안전망으로 남긴다(신호 자체가
없는 정상 경로에서도 무한정 걸리지 않게) — 두 신호를 경합시키지
않고 pid 확인을 stall 리턴 직후의 "계속 기다릴지" 판단에 얹는다.
**Skip:** 순수 outer 타임아웃 단독안(이슈가 제시한 두 번째 후보) —
GAP LINE 이 보여주듯 이미 있는 정확한 신호(pid)를 버리고 오탐 위험이
있는 근사 신호(경과 시간)만 쓰는 것이라, 채택 대신 Rationale 에서
기각.

**Sources:**
- https://github.com/moby/moby/issues/37630 (`docker logs -f` 종료 동작)
- https://forums.docker.com/t/docker-logs-shows-logs-of-stopped-containers/139452
- https://oneuptime.com/blog/post/2026-01-30-docker-health-check-best-practices/view
  (liveness + idle 타임스탬프 결합 패턴)
- https://oneuptime.com/blog/post/2026-01-24-kubernetes-liveness-readiness-probes/view
- 내부: `spawn.py:1275-1345`(roster/`_alive`), `spawn.py:1773-1808`
  (`_watch` follow 분기), `spawn.py:2601-2727`(`_spawn_one` roster
  등록), `spawn.py:1621-1676`(`_auto_respawn_check`)

**스테이지:** 1스테이지(WebSearch 2건 병렬, 결함 3 한정), 판단점
1회 후 종료 — 두 검색 모두 "pid/liveness 확인이 1차, idle 타임아웃은
안전망"이라는 같은 결론으로 수렴했고, 이 저장소에 이미 pid 재료가
갖춰져 있다는 사실과도 부합해 추가 라운드가 결정을 바꾸지 않는다.
