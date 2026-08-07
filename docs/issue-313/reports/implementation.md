---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: phase-2-complete
open_findings: none
---

# issue-313: pre-#297 in-clone TTL 마커 마이그레이션

## Skip record

Pure bugfix — #297 이 이미 정한 목적지(`runs/ttl-markers/`)로 기존
마커를 옮기기만 하면 되고, 이슈가 고칠 지점(`rulebook_checkout()`이
관리 클론을 다시 쓸 때)과 목적(레거시 파일 삭제)을 이미 못박아뒀다.
열린 설계 결정이 없으므로 scout/proposal 단계를 건너뛰었다(계약 v3
s19 의 pure-bugfix skip 조건).

## Reproduction

이 박스의 유일한 실사례:
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-implementation/.muster-last-pull`
(pre-#297 마커, untracked). `git status --porcelain` 이 `?? .muster-last-pull`
을 상시로 보고했다 — 같은 박스의 `tokenmaxxxer-architecture` (post-#297
클론)는 clean.

## What was done

- `spawn.py:_migrate_legacy_ttl_marker(d)` 추가 — 클론 안에 남은
  `.muster-last-pull` 을 지운다. 파일이 없으면 조용히 넘어간다(멱등).
- `rulebook_checkout()` 이 이미 있는 관리 클론을 다시 쓸 때마다
  (`_mkt(d).exists()` 분기, pull 여부와 무관하게) 이 마이그레이션을
  먼저 호출한다 — `checkout_version()` 이 그 다음에 `git status
  --porcelain` 을 읽으므로, dirty 검사 이전에 레거시 파일이 사라진다.
- `core_root()` 의 관리 클론 분기(`tokenmaxxxer-core`)와, 읽기 전용
  대칭 함수인 `core_version()`(spawn.py:2164, pull/clone 안 함) 양쪽에
  동일하게 호출 — 두 함수 다 같은 dirty 접미사 로직을 쓰므로 같은 결함
  클래스에 노출돼 있었다. `core_version()` 누락은 랜딩 전 warrant-hunter
  가 잡음(아래 Hunt 섹션) — `core_root()` 가 먼저 그 프로세스에서 돌지
  않은 채 `core_version()` 만 불리는 경로(로그·ledger 기록)에서는
  마이그레이션이 전혀 안 타는 구멍이었다.
- `test_spawn.py:LegacyTtlMarkerMigration` 추가 — (1) 클론 안에 스테일
  마커를 심어 두고 `checkout_version()` 을 부르면 dirty 접미사가
  사라지고 마커 파일도 지워짐을 고정(수정 전 실패 확인, 수정 후 통과
  확인 — 아래 Verification 참고). (2) 같은 픽스처에 진짜 커밋 안 된
  변경을 추가로 심으면 dirty 접미사가 여전히 붙음을 고정 — 마이그레이션이
  검사 자체를 눈멀게 하지 않았음을 보장.

## What did not work

- 첫 테스트 초안에서 `_fake_clone()` 이 `marketplace.json` 을
  `git init` 전에 써서 커밋 안 된 파일로 남겼다 — 그 결과 마이그레이션
  적용 여부와 무관하게 항상 dirty 로 나왔다. 파일 생성을 `git init` 뒤로
  옮기고 커밋해서 고쳤다.

## Rationale for deviations

None — 이슈가 지시한 대로(레거시 마커 삭제 마이그레이션, 두 종류
테스트, 라이브 확인) 그대로 구현했다.

## Verification run (generation-time confirmation, not a review pass)

- `python3 -m unittest test_spawn.LegacyTtlMarkerMigration -v` → 2 tests
  OK (신규).
- 수정 전 상태로 되돌려(`git stash push -- spawn.py`) 같은 테스트를
  다시 돌리면 `test_stale_in_clone_marker_no_longer_reports_dirty` 가
  실패함을 확인(`git stash pop` 으로 복원) — 마이그레이션 전 실패,
  후 통과.
- `python3 -m unittest test_spawn -v` → 235 tests OK, 전체 스위트
  회귀 없음.
- 실측(Live, 이 박스의 유일한 실사례): 배포된
  `runs/rulebooks/tokenmaxxxer-implementation` 클론을 스크래치패드로
  그대로 복사(원본은 수정하지 않음 — 샌드박스가 배포 디렉터리 밖 쓰기를
  막아 원본에 대한 직접 실행은 승인이 필요했다)한 뒤, 수정된
  `spawn.checkout_version("implementation", spec)` 을 그 복사본에 대해
  실행: 이전 `(커밋 안 된 변경 있음)` 대신 `a134797 (main, on-the-record
  클론)` 을 출력했고, 레거시 마커 파일이 사라졌음을 확인.

## Hunt (before-landing, stance: "assume the rule as written cannot hold — find the state nothing maintains")

- Dispatched `warrant-hunter` (sonnet, 120s cap) against the diff.
  FINDING: `_migrate_legacy_ttl_marker()` was wired into `core_root()`
  but not into `core_version()` (its documented read-only, no-pull/no-clone
  sibling) — a process that calls `core_version()` without `core_root()`
  having already run in that same process would still report the
  pre-#297 marker as permanently dirty. Record:
  `docs/reports/2026-08-07-hunt-issue-313.md`.
- Fixed: added the same `_migrate_legacy_ttl_marker(d)` call to
  `core_version()`'s managed-clone branch (spawn.py, just before
  `return describe(d, "on-the-record 클론")`). Full suite re-run after
  the fix: 235 tests OK.

## Doc placement

- 코드 변경만 있고 신규 env var/dep/migration 스크립트(코드 밖) 없음 —
  마이그레이션은 `rulebook_checkout()` 호출마다 자동으로 도는 코드
  경로이지 별도 실행 스크립트가 아니므로 handbook 갱신 대상 없음.

## General defect note (per issue #313's request)

#297 의 검증은 "새 클론은 clean" 과 "진짜 편집은 여전히 dirty" 만
확인했고, 둘 다 "이미 디스크에 있는 레거시 아티팩트" 케이스를 볼 수
없는 구도였다. 이번 수정은 계약의 검증 기대치에 일반 원칙을 하나
추가할 것을 제안한다: **아티팩트가 쓰이는 위치를 바꾸는 수정은, 그
위치를 읽는 첫 호출 지점에서 이전 위치의 잔존 아티팩트를 마이그레이션(또는
최소한 무해화)하지 않으면 완료로 보지 않는다.** 이번 케이스에서는
`rulebook_checkout()`/`core_root()` 호출마다 자동 마이그레이션을 넣어
별도 실행 스크립트 없이 처리했다.
