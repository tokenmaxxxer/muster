# Survey — issue #222: 테스트·배선 위생 3건

## 결함 1 — pytest가 test_gates.py를 0건 수집

repo root에 `pytest.ini`/`setup.cfg`/`pyproject.toml`이 전혀 없다(확인:
`find . -maxdepth 1 -iname "pytest.ini" -o -iname "pyproject.toml"` 0건).
`conftest.py`는 `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` 환경변수
기본값만 설정할 뿐, 수집 규칙과는 무관하다.

`test_gates.py`는 pytest 관례(`test_*`/클래스 없는 순수 함수)를 안 쓰고
자체 `t_` 접두사 러너다(`test_gates.py:926-931`):

```python
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
```

pytest의 `python_functions` 기본값은 `test_*`뿐이라 `t_*` 함수는 전부
스킵된다. 실측(`python3 -m pytest --collect-only -q`):

```
163 tests collected in 0.21s
```

163건은 전부 `test_spawn.py`(unittest.TestCase 기반, `test_` 메서드)와
`test_vocab_coherence_roles.py`에서 나온다 — `test_gates.py`의 61개
`t_*` 함수는 이름조차 안 뜬다. `README.md:507-511`의 "Self-check"
섹션도 `python3 test_gates.py`(자가 러너)만 문서화하며 pytest 실행을
언급하지 않는다 — 그래서 pytest로 전체 스위트를 강제하는 지점이
없다는 이슈 본문의 진단이 정확하다.

### 검증한 수정 방향

`python_functions`에 `t_*`를 추가하면(예: `pytest.ini`에
`python_functions = test_* t_*`) `test_gates.py`의 61개 함수가 전부
pytest 수집 대상이 되고, 다른 파일(`test_spawn.py`,
`test_approve_scope.py`, `test_vocab_coherence_roles.py`)에는 `t_`로
시작하는 최상위 함수가 없어(grep 확인, 0건) 오탐 수집 위험이 없다.
실측:

```
python3 -m pytest -c <scratch>/pytest.ini --collect-only -q
  → 224 tests collected (기존 163 + test_gates.py의 61)
python3 -m pytest -c <scratch>/pytest.ini -q test_gates.py
  → 1 failed, 60 passed
```

유일한 실패는 `t_repo_local_claude_config_stops_the_spawn`
(`PermissionError: ... /Users/jk/.tokenmaxxxer/trusted-repo-config.json`)이고,
이는 `python3 test_gates.py`(자가 러너)로 그대로 돌려도 동일하게
재현되는 샌드박스 전용 기존 실패다(issue #155 coding record, 이 세션의
sandbox에서도 동일 경로로 재확인) — pytest 전환이 만든 회귀가 아니다.

## 결함 2 — record_fulfils_diff가 ci.check()에 배선되지 않음

`gates/gates.py:527-531`의 `ALL` 딕셔너리:

```python
ALL = {"writeset": writeset, "deps": deps,
       "record_enums": record_enums,
       "record_wellformed": record_wellformed,
       "record_no_tool_residue": record_no_tool_residue,
       "record_fulfils_diff": record_fulfils_diff}
```

`ALL`은 `check(names, d, cfg)`(`gates.py:534-538`)를 통해서만 호출되는데,
이 `check()` 함수 자체를 이 레포 전체에서 grep해도(테스트 포함) 호출부가
0건이다(`grep -n "gates.check(\|ALL\[" test_gates.py gates/*.py spawn.py`
→ 정의부 두 줄 외 없음). `gates/pr_reference.py:4`의 주석이 이 진입점을
"라우터용"이라 부르고, `gates/ci.py:60-62`의 "ponytail" 주석이 "라우터
은퇴 시"라고 명시적으로 전제한다 — 즉 `check(names, d, cfg)` +
`writeset()`/`deps()`(둘 다 `d / "work"` 배치를 전제하는 스펙-기반
검사, `spec.md`를 읽는다)는 이슈가 말하는 "은퇴한 라우터"의 죽은
스캐폴딩이다. `writeset`/`deps`도 `ALL`/`check()` 밖에서 호출하는 곳이
없다(`grep -rn "gates\.writeset\|gates\.deps\b" --include="*.py" .` →
정의부와 주석 언급뿐).

반면 `record_enums`/`record_wellformed`/`record_no_tool_residue`는 `ALL`에
**같이** 등록돼 있지만 죽지 않았다 — `gates/ci.py:56-58`가 이들을 직접
호출한다(`ALL`을 거치지 않고):

```python
bad += gates.record_enums(repo, {})
bad += gates.record_wellformed_in(repo)
bad += gates.record_no_tool_residue_in(repo)
```

`record_fulfils_diff`(issue #155, `gates.py:411-462`)는 같은 dual-mode
시그니처(`d / "work"`가 있으면 그쪽, 없으면 `d` 자체 — `record_enums`와
글자 그대로 같은 패턴, `gates.py:303`/`gates.py:418` 비교)로 만들어졌으면서도
`ci.py`의 저 세 줄 목록에 추가되지 않았다 — `ALL`에 등록한 것으로
"배선했다"고 착각하기 쉬운 지점이다. 실측 재현(스크래치 스크립트,
`ci.check(work)` vs `gates.record_fulfils_diff(work, {})` 동일 레포에
직접 호출):

```
ci.check() 결과: []                              (통과 — 못 봄)
gates.record_fulfils_diff() 직접 호출 결과:
  ["fulfils 불일치: docs/issue-9/reports/implementation.md:5 —
    'delete some/scratch/path.txt' claim 이 커밋 diff 에 D
    (또는 rename 원본)로 없다"]
```

`ci.py`가 실제로 커밋 diff에 없는 삭제 주장을 걸러내지 못한다 —
issue #145가 실제로 겪은 사고 형태(`test_gates.py:861`의 테스트 주석이
그 사고를 인용)가 `ci.check()` 경로에서는 여전히 재발 가능하다는 뜻이다.

### 속성 커버리지 확인 (제약 조건)

이슈의 제약: "삭제를 택할 경우, 게이트가 검사하려던 속성이 다른 게이트로
커버되는지 제안이 확인할 것." `record_fulfils_diff`가 검사하는 속성은
"레코드의 `fulfils: delete|create|move` 한 줄짜리 claim이 실제 커밋
diff의 A/D/R/C 상태와 일치하는가"다. `ci.check()`가 이미 부르는 다른
게이트들을 확인한 결과 이 속성을 대체하는 것은 없다:

- `record_enums` — frontmatter 필드 값이 role의 enum 안에 있는지만 본다.
  diff 내용과 무관.
- `record_wellformed_in` — `---` frontmatter 구분자 존재 여부만 본다.
- `record_no_tool_residue_in` — 레코드 본문에 새어든 툴 태그 잔여물만
  본다.
- `role_scope`/`writeset`/`is_protected` — 경로가 허용 범위/보호 경로
  안인지만 본다. 레코드 **본문의 주장**과 diff의 대조는 하지 않는다.
- `pr_reference.check` — PR 본문의 `#n`/`Closes #n` 참조 여부만 본다.

즉 "레코드가 주장하는 파일 조작이 실제로 일어났다"를 보는 게이트는
`record_fulfils_diff`가 유일하다 — 삭제 시 그 속성 자체가 사라진다.

### CI 자동화 현황 (부수 관찰)

이 레포에는 `.github/workflows/`가 없다 — `gates/ci.py`는 실제 GitHub
Actions에 배선된 게 아니라, 각 phase-2 코딩 세션이 마무리 확인 단계로
`python3 gates/ci.py .`을 수동 실행하는 관례로 쓰인다(예:
`docs/issue-178/reports/implementation.md:129`, `docs/issue-180/reports/implementation.md:147`).
따라서 "프로덕션에서 안 돎"은 자동 CI 파이프라인이 아니라 이 수동
확인 관례를 가리킨다 — `ci.check()`에 배선하면 이 관례가 실제로
잡아준다.

### 관련이지만 범위 밖인 관찰: role_scope와 이 레포의 write_scope

`gates/ci.py:55`가 `pr` 인자가 있을 때 `gates.role_scope(repo, branch)`도
부른다. `roles/implementation.json`의 `write_scope`는 `["src/**",
"test/**"]`인데(대상 레포 일반형 관례), 이 레포(on-the-record) 자신은
`src/`가 아예 없고 코드가 루트에 있다(`gates/*.py`, `spawn.py`,
`test_*.py`) — issue-149 survey가 이미 지적한 간극이다. 이 레포에
`docs/specs/write_scope.md` 오버라이드가 없어(확인: `docs/specs/`에
`approvers.md`, `flows-schema.md`만 존재), `role_scope()`를 `--pr`과
함께 실제로 돌리면 이번 이슈가 건드릴 `gates/*.py`, `test_gates.py`,
`pytest.ini` 전부가 write_scope 이탈로 걸릴 것이다. 다만 위에서 확인한
대로 이 레포에는 자동 CI가 없어 `role_scope`가 실제로 병합을 막지는
않는다 — issue #222의 3개 결함 중 어느 것도 아니고, 고치려면 별도
write_scope.md 작성이라는 자체 결정이 필요하므로 이번 제안의 범위
밖에 둔다(Out of scope에 명시).

## 결함 3 — _STAGE_MAP이 5값 중 2값만 도출

`docs/specs/flows-schema.md` §2.2가 약속하는 `flows[].stage`의 5개
값: `"proposal"`, `"approved"`, `"implementing"`, `"delivered"`,
`"closed"`(그 외 값은 `stage_derived: false`와 함께 원본 `loop_state`
그대로).

`gates/flows.py:20-26` 현재:

```python
_STAGE_MAP = {
    "scope-proposed": "proposal",
    "scope-approved": "approved",
}
# implementing/delivered/closed are role/rulebook-specific downstream states with
# no central enum today (issue #172 survey) — anything not in this map reports
# raw with stage_derived=False rather than being forced into the wrong bucket.
```

주석이 "중앙 enum이 없다"고 적은 시점(issue #172) 이후, 빌드형 역할들의
`roles/*.json`이 실제로 4값 enum으로 수렴해 있다 — grep 확인
(`roles/implementation.json`, `roles/architecture.json`,
`roles/data-modeling.json`, `roles/incident-response.json`,
`roles/refactoring-legacy.json`, `roles/test-authoring.json`, 6개 role
전부 동일):

```json
"loop_state": ["scope-proposed", "scope-approved", "in-progress", "landed"]
```

`in-progress`/`landed`는 이제 중앙 enum이 있다 — "없다"던 전제가 더
이상 사실이 아니다. 43개 role 파일을 전수 분류하면: 4값 빌드형 6개
(위 목록), `landed` 단독 29개(도메인 role 대부분), 그 외 8개는
판단형 role마다 다른 완료 상태(`product-discovery`: `measuring`,
`technical-feasibility`: `measuring`/`verdict`,
`conformance-review`: `reported`, `execution-observation`:
`handed-off`, `defect-verification`: `cleared`,
`interaction-design`: `reviewed`, `issue-retrospective`/
`release-engineering`: `record_fields.loop_state` 자체 없음) — 이들에겐 5값
enum으로 강제로 밀어넣을 근거가 없어 원본대로 남아야 한다(이슈의
제약: "스키마 변경 아님, 약속 이행"과 정합 — 억지 매핑이 아니라 이미
존재하는 약속을 채우는 것만).

`"landed"`는 위 29개 role(예: `brand-design`, `accessibility`,
`marketing`, ...)에서도 유일한 값으로 쓰인다 — 이 role들에도
`"landed" → "delivered"` 매핑이 똑같이 의미가 통한다(작업이 최종
상태에 도달했다는 뜻은 role과 무관하게 같다).

### `closed`는 loop_state가 아니라 이슈 상태에서 나온다

`_STAGE_MAP`에 `in-progress`/`landed`를 추가해도 5번째 값 `closed`는
여전히 안 나온다 — `closed`는 어떤 role의 `loop_state`도 아니고, GitHub
이슈 자체의 상태(`OPEN`/`CLOSED`)에서 나와야 하는 값이기 때문이다.
`flows_payload()`(`flows.py:245-389`)는 이미 이슈 상태를 갖고 있다 —
`issue_state_by_n: dict[int, str]`(`flows.py:253-259`,
`_issue_list_all()`의 `"state"` 필드로 채워짐)가 stage 계산 루프
(`flows.py:307-335`) 안에서 `issue_n` 키로 그대로 조회 가능하다. 오늘은
이 값이 stage 계산에 전혀 안 쓰인다 — `stage_source`는 오직 프런트
role의 `loop_state`(`spawn._front_role`로 고른)에서만 나온다
(`flows.py:316-317`, `328`). 그 결과 이슈가 실제로 닫혀 있어도
`flows[].stage`는 마지막으로 기록된 `loop_state`(또는 그 raw 값)를
그대로 보여준다 — `closed`가 나올 길이 없다.

### 스카우트 확인 (아래 scout-brief 참고)

`closed`를 "그 무엇보다 우선하는 종결 상태"로 두는 방향이 업계 관례와
어긋나지 않는지 짧게 확인했다 — Jira/Linear 둘 다 "진행 중" 카테고리와
분리된, 더 이상 전이(transition)가 없는 별도의 종결 상태 카테고리를
둔다(scout-brief 참고). `closed`가 `loop_state` 기반 매핑보다 항상
우선하도록 설계하는 것이 이 업계 패턴과 정합적이다.

### 테스트 배치의 제약: test_spawn.py를 건드릴 수 없다

`gates/flows.py`를 검사하는 테스트는 전부 `test_spawn.py`의
`FlowsPayload` 클래스 안에 있다(전용 `test_flows.py`는 존재하지 않음 —
확인: `find . -iname "test_flows*.py"` 0건). issue #172가 `flows.py`를
독립 모듈로 뽑았을 때(issue #178) 테스트는 같이 안 옮겨졌다. 이슈
본문은 `spawn.py`·`test_spawn.py`를 건드리지 말라고 명시한다(#218이
동시에 수정 중) — `FlowsPayload`에 새 케이스를 추가하는 통상적인
방법이 막혀 있다는 뜻이다. 제안은 이 결함의 테스트를 새 파일
`test_flows.py`에 담아 `test_spawn.py`를 전혀 건드리지 않는 경로를
택한다(Rationale에서 대안과 함께 설명).

## 이 이슈에서 건드리지 않는 것 (확인됨)

- `spawn.py`, `test_spawn.py` — 이슈 본문 명시, issue #218 진행 중.
- `roles/*.json`의 `record_fields.loop_state` enum 자체 — 이미
  `scope-proposed`/`scope-approved`/`in-progress`/`landed` 4값으로
  수렴돼 있어 스키마 변경이 필요 없다(위 확인).
- `docs/specs/flows-schema.md` — 5값 enum과 `stage_derived`의 의미는
  이미 문서가 규정한 그대로다. 이번 변경은 그 약속을 채우는 것이지
  바꾸는 것이 아니다(이슈의 제약과 정합).
