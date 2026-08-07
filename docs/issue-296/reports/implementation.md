---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: phase-2-complete
open_findings: none
---

# issue-296: TTL 마커가 클론을 더럽히는 회귀 수정

## Skip record

Pure bugfix — #285 가 만든 회귀를 되돌리는 작업이고, 이슈가 고칠 지점
(`spawn.py:67-68`)과 목적지(`runs/`)를 이미 못박아뒀다. 열린 설계 결정이
없으므로 scout/proposal 단계를 건너뛰었다(계약 v3 s19 의 pure-bugfix
skip 조건).

## What was done

- `spawn.py:_ttl_marker()` — 마커 경로를 `d / ".muster-last-pull"`(클론
  내부)에서 `ROOT / "runs" / "ttl-markers" / <sha256(clone_path)[:16]>`
  로 옮겼다. `runs/` 는 이미 gitignore 되어 있고 다른 오케스트레이터
  상태(`active.json`, `watchdog_state.json` 등)도 그 아래에 있다.
- `spawn.py:_mark_pulled()` — 새 위치의 부모 디렉터리
  (`runs/ttl-markers/`)를 `mkdir(parents=True, exist_ok=True)` 로 만든
  뒤 쓴다.
- `test_spawn.py` — 클론 내부에 직접 `.muster-last-pull` 을 쓰던 기존
  두 테스트(`test_ttl_marker_skips_pull_on_fresh_marker`,
  `test_muster_rulebook_ttl_zero_forces_pull`)를 새 마커 위치를 통해
  쓰도록 갱신. 신규 테스트
  `test_ttl_marker_does_not_dirty_clone` 추가: `_mark_pulled()` 이후
  `git status --porcelain` 이 빈 문자열이고 마커 경로가 클론 디렉터리
  바깥임을 고정.
- `bench/run.py` 는 무변경 — `rulebook_version()` 이 더 이상 항상
  더러움을 보고하지 않으므로 기존 provenance 체크가 그대로 통과한다.

## What did not work

None.

## Rationale for deviations

None — 이슈의 "Fix direction" 이 지시한 대로(클론 밖 `runs/` 로 이동)
그대로 구현했다.

## Verification run (generation-time confirmation, not a review pass)

- `python3 -m unittest test_spawn.RulebookCheckoutMemo -v` → 4 tests OK
  (신규 테스트 포함).
- `python3 -m unittest test_spawn -v` → 233 tests OK, 전체 스위트
  회귀 없음.
- 실측: 이 세션에는 관리 클론(`runs/rulebooks/tokenmaxxxer-core`)이
  아직 없어 실제 클론 위에서의 `core_version()` 출력은 확인하지
  못했다 — 대신 신규 테스트가 임시 클론으로 동일한 경로(`_mark_pulled`
  → `git status --porcelain` 빈 값)를 고정해 확인했다.

## Doc placement

- 코드 변경만 있고 신규 env var/dep/migration 없음 — handbook 갱신
  대상 없음.
- 공개 시그니처/와이어 포맷 변경 없음 — `docs/issue-296/decisions/`
  대상 없음.
- 벤치마크/조사 수치 없음 — `docs/issue-296/reports/` 아래 이 기록
  파일 외 추가 없음.

## Closed checks

- closed_checks: ttl-marker-outside-clone, code_sha: spawn.py+test_spawn.py (this branch's tip at record time)
  — `_mark_pulled()` 이후 `git status --porcelain` 빈 값 확인
  (`test_spawn.py::RulebookCheckoutMemo::test_ttl_marker_does_not_dirty_clone`).
