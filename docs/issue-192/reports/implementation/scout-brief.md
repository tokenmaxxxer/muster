# Scout brief — issue #192

범위: 저장소 내부 도구(spawn.py)의 세션-로그 명명/정리 규약 — product-shaped 아님.
"같은 종류의 산출물"로 잡은 필드: 프로세스 재시작 시 로그 파일이 안 겹치게 하는 통상
관행, 그리고 회전된 로그의 정리(cleanup) 관행. 1단계(sweep), 병렬 WebSearch 2건, 결과
겹치는 지점에서 즉시 판단 — 예산(≤5단계, ≤3분) 안에서 1단계로 포화.

**Must-be 1 — 겹침 방지는 파일명에 세션마다 달라지는 값이 들어가야 한다.** 타임스탬프
포함 명명(`{name}_{timestamp}.log`)이 재시작 간 겹침 방지의 표준 관행으로 확인됨.

**Must-be 2 — 정렬 가능성.** logrotate 의 `dateext`/`dateformat` 관행은 회전 파일명이
"lexically sortable" 해야 한다고 명시 — 연-월-일 순서. PID 단독 접미사는 이 표준에서
벗어난다("PID 포함은 Apache rotatelogs 의 사실상 표준에서 벗어난 방식"으로 명시 언급).

**성능축 1 — 동시성 안전.** 순수 타임스탬프(초 단위)만으로는 이 저장소가 이미 실측한
동시 watchdog 재스폰 레이스(같은 워크스페이스에 두 프로세스가 거의 동시에 respawn,
`spawn.py` 주석 1583-1588줄, O_CREAT|O_EXCL 락으로 완화)에서 충돌 가능 — 이 저장소
자체가 이미 `os.getpid()` 를 유일성 보장 수단으로 쓰는 선례가 있다(애드혹 로스터 키
`f"adhoc/{role}/{os.getpid()}"`, spawn.py:2403).

**성능축 2 — 정리(cleanup) 시 회전 파일 전체를 훑는 방식.** logrotate 는 글롭/개수
기반으로 오래된 회전 파일을 스윕한다 — 접미사를 하나씩 나열하지 않고 패턴으로 모두
잡는 방식이 표준.

**Adopt:** 타임스탬프(정렬 가능, 표준 관행) + PID(이 저장소의 기존 동시성-안전 선례,
레이스 방지) 복합 접미사 — 두 축을 동시에 만족. `clean` 의 형제 파일 정리는 접미사
나열이 아니라 워크스페이스 이름 프리픽스 글롭으로.

**Skip:** logrotate 식 보존 개수(`rotate N`)·압축·크론 스케줄 — 이 이슈는 D1/D2 로
범위가 "로그 보존"에 고정돼 있고, watchdog 관찰-전용 계약(이슈 #90/#132)을 건드리지
않는다. 회전 개수 제한은 요구사항에 없다(clean 이 커밋/push 안전성으로 이미 보존
여부를 가른다).

**Gap line:** 현재 상태는 must-be 1(세션마다 다른 값)도 만족 못 한다 — 매 세션 동일한
고정 문자열. must-be 2(정렬 가능)는 애초에 논의조차 없었다(생성 규약이 하나뿐이었으므로
정렬할 대상이 없었다). 이번 변경으로 둘 다 채운다.

Sources:
- https://mywiki.wooledge.org/ProcessManagement
- https://medium.com/@kumarbiradar7/configuring-file-based-logging-with-multiprocessing-and-threading-in-python-4a7831357cc7
- https://betterstack.com/community/guides/logging/how-to-manage-log-files-with-logrotate-on-ubuntu-20-04/
- https://man7.org/linux/man-pages/man5/logrotate.conf.5.html
