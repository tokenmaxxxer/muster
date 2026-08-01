files:
- spawn.py (spawn_cmd(), _spawn_one())
- test_spawn.py

## Request
Role 세션을 스폰할 때 spawn.py가 core 클론의 `core/` 플러그인 경로를
`CLAUDE_PLUGIN_ROOT_CORE`로 주입하지 않아, 룰북 게이트가
`${CLAUDE_PLUGIN_ROOT_CORE:-<상대경로>/core}`의 fallback 절로 빠지고 이
fallback이 실배포에서 룰북 클론 내부를 가리켜 해석 실패 → 무가드
source와 결합 시 게이트가 통째로 fail-open한다. 세 가지를 요구:
(1) spawn 시 CLAUDE_PLUGIN_ROOT_CORE 주입, (2) doctor 프로브가 "게이트가
실제로 deny를 낼 수 있는가"까지 검사하도록 확장 검토, (3) 스폰된 세션
env에 변수 존재·경로 유효성을 확인하는 회귀 테스트.

## Constraints
- `spawn_cmd()`는 순수 함수로 유지된다 — 네트워크 clone을 유발하는
  `core_root()`를 두 번 호출하지 않는다(clone은 이미 `_spawn_one()`이
  `core_plugin_dirs()`를 통해 한 번 해결한다).
- 주입되는 경로는 `--plugin-dir`로 실제로 로드되는 core 플러그인 경로와
  1:1로 일치해야 한다(scout-brief.md must-be) — 드리프트가 나면 같은
  fail-open이 자리만 옮긴다.
- core 플러그인이 결손 상태(plugin.json 없음)여서 `core_plugin_dirs()`
  목록에서 아예 빠지는 경우를 무가드로 방치하지 않는다.

## Rationale
두 가지 구현 지점을 검토했다:

1. **`spawn_cmd()` 내부에서 `core_root()`를 다시 호출** — 이미
   `core_plugins: list[Path]` 파라미터를 받고 있으므로 재호출은 불필요한
   두 번째 clone 시도 리스크를 추가한다(`core_root()`는 없으면 clone을
   수행— spawn.py:1770-1775). 기각.
2. **`_spawn_one()`이 `core_plugin_dirs()`로 이미 해결해 놓은 `plugins`
   리스트에서 `.name == "core"`인 엔트리를 골라 `spawn_cmd()`에 (또는
   `spawn_cmd()` 호출 전 `extra_env`에) 반영** — 채택. 이미 해결되고
   `--plugin-dir`로 전달될 경로 그 자체를 재사용하므로 "주입된 경로 ==
   실제 로드된 core 플러그인 경로" 불변식이 코드 구조로 보장된다. 결손
   케이스(목록에 core가 없음)는 자연히 드러나 명시적으로 처리할 수 있다
   (아래 What will be done).

`core_plugins` 파라미터를 `spawn_cmd()`가 이미 받고 있으므로, 이 리스트
안에서 `core`를 찾아 env로 반영하는 쪽이 함수 시그니처 변경 없이
가능하다 — 이 지점이 대안 1을 기각하고 대안 2를 택하는 핵심 이유다.

## What will be done
- `spawn_cmd()`에서 `core_plugins` 인자 중 `.name == "core"`인 항목을
  찾아 있으면 `env["CLAUDE_PLUGIN_ROOT_CORE"] = str(그 경로)`를 설정.
  없으면(결손 core 체크아웃) 변수를 주입하지 않고 stderr에 경고를
  남긴다 — 조용히 fallback에 빠지게 두지 않고, 무엇이 비었는지 보이게
  한다.
- doctor()의 훅-발화 프로브에 더해, 실제 core 플러그인을 `--plugin-dir`로
  붙이고 gate-lib.sh를 소스해 `CLAUDE_PLUGIN_ROOT_CORE`가 해석 가능한지
  (게이트 스크립트가 실제로 로드되어 deny 경로를 낼 수 있는지) 검사하는
  두 번째 프로브 추가를 검토한다. 검토 산출물: 어떤 게이트 스크립트를
  대상으로 삼을지(예: board-gate.sh), 프로브가 어떤 조건에서 deny를
  유도해 발화를 확인할지, doctor-ok 기록 조건에 이 결과를 포함시킬지에
  대한 설계 초안.
- test_spawn.py의 기존 `TestSpawnCmd` 스위트(:82-83, :90 패턴)에
  `spawn_cmd()` 호출 시 `env["CLAUDE_PLUGIN_ROOT_CORE"]`가 전달된
  `core_plugins`의 `core` 엔트리 경로와 일치하는지 확인하는 테스트, 그리고
  `core_plugins`에 `core`가 없을 때 변수가 주입되지 않고 경고가 나는지
  확인하는 테스트를 추가한다.

## Out of scope
- doctor()의 두 번째 프로브 실제 구현(검토/설계까지만 — 이슈 요구
  문구 "검토"에 맞춤).
- gate-lib.sh 등 core 저장소 쪽 스크립트 수정(core는 별도 저장소·별도
  이슈 소관).
- `core_root()`/`core_plugin_dirs()`의 clone·캐시 로직 변경.

## How you'll know it worked
- `spawn_cmd(...)`를 core 플러그인 경로를 포함한 `core_plugins`로 호출하면
  반환 env에 `CLAUDE_PLUGIN_ROOT_CORE`가 그 경로 문자열로 존재한다
  (신규 유닛 테스트로 확인).
- `core_plugins`에서 core 엔트리를 뺀 호출은 변수를 주입하지 않고
  경고를 남긴다 (신규 유닛 테스트로 확인).
- doctor 프로브 확장에 대한 설계 초안이 phase 2 기록에 남는다.
