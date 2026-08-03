# Survey — issue #218: core_root() 신선도 미확인·미보고

## 대상 함수: `core_root()` (spawn.py:1781-1818)

후보 셋을 순서대로 본다:

1. `TOKENMAXXXER_CORE` 환경변수 (직접 경로)
2. `$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core` (RULEBOOKS 변수 재사용) — 변수가
   안 잡혀 있으면 `$`가 그대로 남아 스킵된다(spawn.py:1794-1795, spawn.py:123의
   "문자열이 그대로 경로로 쓰이면" 경고와 같은 방어)
3. `ROOT.parent / "tokenmaxxxer-core"` (형제 디렉터리)

세 후보 각각 **`plugin.json` 파일 존재만** 확인하고(`is_file()`), 매치되면 그
자리에서 즉시 `return p` 한다 — `git pull`도, sha 비교도, 로그 출력도 없다.
셋 다 없을 때만 `ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"`(on-the-record
소유 클론)로 떨어지는데, 이 관리 클론은 반환 직전에 `git pull -q --ff-only`를
돈다(spawn.py:1802-1803) — 셋 중 유일하게 "매 spawn마다 신선한" 경로다. 클론도
없으면 새로 `git clone`을 시도하고, 그래도 없으면 halt(sys.exit)한다.

이 함수의 반환값은 `core_plugin_dirs()`(spawn.py:1821-1831)를 거쳐
`run_role()`의 `spawn_cmd(... , core_plugin_dirs(), plugins)` 호출
(spawn.py:2398-2399)로 들어간다 — 역할 세션에 `--plugin-dir`로 실제 붙는 core
플러그인 경로가 여기서 정해진다.

## 실측 재현 (이 세션의 실제 상태)

이 셸에는 `TOKENMAXXXER_CORE`/`TOKENMAXXXER_RULEBOOKS`가 잡혀 있지 않다
(`printenv`로 확인). 후보 3(`ROOT.parent/tokenmaxxxer-core`, 곧
`/Users/jk/.tokenmaxxxer/work/tokenmaxxxer-core`)도 존재하지 않는다. 이
저장소 체크아웃에는 관리 클론(`runs/rulebooks/tokenmaxxxer-core`)도 아직
없다. 즉 core_root()가 지금 이 자리에서 불리면 새로 클론을 시도하는 경로로
떨어진다.

반면 실제 로컬 머신의 `~/.claude/plugins/marketplaces/tokenmaxxxer-core`
(마켓플레이스 클론)는 확인 결과 `52bdc15` (2026-08-01 커밋)에 멈춰 있다 —
이슈 본문이 "10커밋 뒤"라고 보고한 바로 그 상태와 sha가 일치한다. 이 경로는
현재 세션이 CLI로부터 물려받은 `CLAUDE_PLUGIN_ROOT_CORE=.../marketplaces/
tokenmaxxxer-core/core` 값과도 일치해서, **이 세션 자체가 core_root() 계열
로직이 그 stale 클론을 골랐던 스폰의 산물**임을 뒷받침한다(다만 이 저장소의
`spawn.py` 세 후보 중 무엇이 그 경로와 정확히 매치됐는지는 이 저장소 밖의
스폰 시점 환경변수에 달려 있어 이 세션에서 직접 재현·특정하지는 못했다 —
셋 다 "로컬 오버라이드" 취급이라는 사실 자체는 바뀌지 않는다).

## 비교 대상: 룰북(역할) 체크아웃의 신선도 처리 — 이미 있는 패턴

같은 파일 안에 정확히 이 문제를 이미 풀어 둔 3단 짝이 있다:

- **`rulebook_checkout()`** (spawn.py:174-206): 로컬 경로(`_path(spec)`)가
  있으면 **그대로** 반환한다 — pull도, mtime 확인도 없다. on-the-record 소유
  클론(`runs/rulebooks/<marketplace>`)일 때만 반환 전에
  `git pull -q --ff-only`를 돈다. **로컬 우선은 개발용 오버라이드**라는 원칙이
  core_root()의 `# 로컬 체크아웃이 없으면 룰북과 같은 길` 주석(spawn.py:1798)
  과 완전히 같은 문구로 이미 명시돼 있다 — core_root()가 "룰북과 같은 길"을
  따른다고 자칭하면서도 실제로 흉내 낸 것은 클론 fallback 하나뿐, **신선도
  보고**는 흉내 내지 않았다.
- **`checkout_version(role, spec)`** (spawn.py:211-224): `rulebook_checkout()`
  이 반환한 디렉터리에서 `git rev-parse --short HEAD`(sha),
  `rev-parse --abbrev-ref HEAD`(branch), `git status --porcelain`(dirty 여부),
  그리고 로컬/on-the-record 클론 구분("where")까지 묶어 `"{sha} ({branch},
  {where}){dirty}"` 문자열을 만든다. **읽기 전용** — pull도, 재확인도 안 한다.
  이 값이 `run_role()`의 스폰 로그 줄(spawn.py:2394 `룰북 {checkout_version(...)}`)
  과 ledger 레코드(spawn.py:2628 `"rulebook": checkout_version(...)`) 양쪽에
  찍힌다 — **로컬 오버라이드를 pull하지 않으면서도 무엇이 도는지는 매 spawn마다
  로그에 남긴다.**
- **`rulebook_version(role)`** (spawn.py:523-562): 설치본(cache) vs 클론이
  갈렸는지까지 비교해 보고하는 더 무거운 버전 — `spawn.py status`류 명령이 쓰는
  것으로 보이며, ablation 추적용이라는 docstring이 있다. `checkout_version()`
  만큼 core_root()에 직접 대응되지는 않는다(설치본 개념이 core 플러그인
  로딩(`--plugin-dir`, 비-설치 경로)에는 없다).

core_root()에는 이 셋 중 어느 것에도 대응하는 함수가 없다 — `core_plugin_dirs()`
가 있을 뿐이고, 이건 디렉터리 목록만 반환하지 버전을 보고하지 않는다.

## 이슈가 지목한 두 번째 증상: "gate-lib 부재" 죽음

`gate-lib`라는 이름의 파일/디렉터리는 이 저장소에도, 로컬에 클론된
`~/.claude/plugins/marketplaces/tokenmaxxxer-core`에도 없다(grep 결과
없음) — tokenmaxxxer-core 레포 안쪽 구조라 이 저장소에서 직접 조사할 수
없다. 이 증상은 별도로 조사·수정할 대상이 아니라, **같은 근본 원인(오래된
체크아웃이 plugin.json만 있으면 그대로 통과)의 다른 발현**으로 이슈 본문에
같이 실려 있는 것으로 읽었다 — sha가 로그에 찍혔다면 "어느 커밋이 도는지"를
바로 알 수 있었을 사고다.

## 소비처: ledger 스키마

`ledger_write()`(spawn.py:1770-1778)는 `runs/ledger.jsonl`(gitignore 대상,
"측정 데이터는 소스가 아니다")에 한 줄씩 append만 한다. 이 레포 안에서
`"rulebook"` 키를 읽는 소비처는 없다(grep 결과 write 지점 1곳뿐) — 새 키를
추가해도 이 레포 안에서 깨질 소비처가 없다. `docs/handbooks/`에도 ledger
필드를 문서화한 곳이 없다.

## 테스트 현황

`test_spawn.py`의 `SpawnCmd` 클래스에 `core_root()` 관련 테스트가 이미
하나 있다(`test_core_dir_resolves_or_halts`, spawn.py:59-77) — 세 후보를
전부 막고 halt(`SystemExit`)하는지만 검사한다. `core_version()`류 신선도
보고 함수에 대응하는 테스트는 없다(당연히, 함수 자체가 없으므로).

## 쓸 파일 (write set 예상)

- `spawn.py` — `core_root()` 주변(1781행대)에 신선도 보고 함수 추가 + 두
  로그 지점(2394행 스폰 로그, 2628행 ledger 레코드) 배선.
- `test_spawn.py` — 새 함수에 대한 단위 테스트.

## 스카우트 스킵 사유 (product-shaped 아님)

`scout-brief.md`에 기록. 요약: 이 이슈는 사용자 대면 제품 표면이 아니라
내부 오케스트레이션 도구(spawn.py)의 자기 일관성 버그라, "카테고리
best-in-class"에 해당하는 외부 제품이 없다. 대신 이슈 본문이 직접 지목한
**이 저장소 안의 이미 존재하는 동종 해법**(룰북 체크아웃의
`checkout_version()`/`rulebook_version()` 패턴)을 prior art로 조사했다 —
위 "비교 대상" 절이 그 결과다.
