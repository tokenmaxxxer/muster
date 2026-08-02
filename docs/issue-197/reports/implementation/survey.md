# Survey — issue #197: `_plan_from_body` 코드펜스·헤더 결함

## 문제의 정확한 위치

`gates/flows.py:72-98` `_plan_from_body(body)`:

```python
def _plan_from_body(body: str) -> list[dict] | None:
    lines = (body or "").splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## 실행 계획":
            start = i + 1
            break
    if start is None:
        return None
    steps = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("##"):
            break
        m = _PLAN_STEP_RE.match(stripped)
        ...
```

두 스캔(헤더 탐색 루프, 스텝 수집 루프) 모두 코드펜스(```` ``` ````) 경계를 전혀
모른다. 헤더 탐색은 `line.strip() == "## 실행 계획"` 정확 일치라 뒤에 텍스트가
붙은 실제 헤더를 놓친다. `_PLAN_STEP_RE`
(`gates/flows.py:69`, `r"^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$"`)는 이번 결함과
무관 — 이슈-189 판정(execution-observation.md)이 이미 "결함 아님"으로 확정했다.

`flows_payload()` (`gates/flows.py:208-340`) 안에서 `_plan_from_body`의 호출부는
두 곳: `plan_by_issue[n] = _plan_from_body(iss.get("body") or "")`
(`flows.py:222`, 매 열린/닫힌 이슈마다)와, 그 결과의 `is not None` 여부로 보드
레코드 없는 subject 를 union-expansion 하는 조건
(`flows.py:226`: `if state == "OPEN" and plan_by_issue.get(n) is not None`).
이 두 소비 지점의 계약은 고정값이다 — `None`=블록 없음, 리스트(빈 리스트 가능)=
블록 있음. 수정은 매칭 로직만 바꾸고 이 반환 계약은 그대로 유지해야
`flows_payload`의 나머지 로직(237번째 줄 이하)을 안 건드릴 수 있다.

## 문법 정의 — `on-the-record/commands/run.md`

`## 실행 계획 (Execution Plan)` 섹션(`run.md:197-260`)의 `### 문법`
하위섹션(`run.md:203-214`)이 고정 문법 견본을 코드펜스(```` ```markdown ````)로
보여준다:

```markdown
## 실행 계획
- [ ] step 1  product-discovery
- [ ] step 2  architecture ‖ security-threat-model
...
```

이 견본 자체가 실제 이슈 본문에도 그대로 인용되는 패턴이다(아래 "실물 재현"
참고) — 계획 포맷을 설명하는 문서가 포맷 견본을 싣는 것은 예외적 상황이 아니라
구조적으로 반복되는 형태다. `### 문법` 절은 헤더가 정확히 `## 실행 계획` 이어야
한다고만 쓰고, 뒤에 부가 설명이 붙을 수 있는지, 견본이 코드펜스 안에 있어야
하는지는 침묵한다. `docs/issue-189/proposals/execution-plan.md:22-23`(승인된
phase-1 제안, §1.1)도 "`## 실행 계획` 은 정확한 리터럴 블록 헤더" 라고만 못박아
두었다 — 이 침묵이 이슈-189 execution-observation 판정의 근본 원인 결론
(코드는 승인된 문법을 정확히 구현했으나 문법 자체가 실물 문서 형태를 안
다뤘다)과 정확히 일치한다.

## 기존 코드베이스의 펜스-스킵 선례 — `gates/gates.py`

`gates/gates.py:376-399` `record_no_tool_residue_in(work)`가 이미 똑같은
문제(레코드 본문을 줄 단위로 스캔하며 코드펜스 안 내용은 후보에서 제외)를
풀어 놓았다:

```python
in_fence = False
for lineno, line in enumerate(f.read_text().splitlines(), start=1):
    if line.lstrip().startswith("```"):
        in_fence = not in_fence
        continue
    if in_fence:
        continue
    m = _TOOL_TAG.match(line)
    ...
```

`record_no_tool_residue`(`gates.py:402-405`)의 자기 docstring이 "코드펜스 안은
제외한다"를 명시한다. 이 토글 패턴(``` 로 시작하는 줄마다 `in_fence` 반전,
`in_fence` 동안 스킵)은 이번 결함과 같은 클래스의 문제를 이 레포 안에서 이미
검증된 방식으로 풀고 있다 — 새 알고리즘을 발명할 필요가 없다는 근거.
`test_gates.py`에 이 함수의 펜스 케이스 테스트가 있는지는 확인하지 않았다(범위
밖: 이번 수정은 `gates/gates.py`를 건드리지 않는다, 읽기 전용 참조일 뿐).

## 기존 테스트 커버리지 — `test_spawn.py::FlowsPayload`

`test_spawn.py:1863-1901`에 플랜 파싱 테스트 3개:
`test_flows_plan_is_null_without_plan_block`,
`test_flows_plan_parses_step_lines`,
`test_flows_plan_only_issue_with_no_board_record_still_gets_entry`. 세 바디
모두 펜스 없음·정확 일치 헤더만 쓴다(`test_spawn.py:1866`, `1876`, `1895`).
이슈-189 execution-observation 판정 finding 2가 지적한 정확히 그 gap —
합성 픽스처가 실제로 실패한 시나리오(펜스+변형 헤더 공존)를 한 번도
실행하지 않았다는 사실이 현재도 그대로 남아 있다.

## 실물 재현 — 이슈 #189 본문 (검증 데이터, `gh issue view 189 --json body`로 확인)

전체 본문을 그대로 받았다(2026-08-02, 현재 이 세션에서 `gh issue view 189`로
재확인). 구조, 위에서 아래 순서대로:

1. `## 배경` — 본문 안에 통계 코드펜스 하나 있음 (플랜과 무관, ``` 만 씀,
   언어 태그 없음). 펜스 토글이 여러 쌍을 정확히 넘나드는지 검증하는 부수
   증거.
2. `## 요구사항`, `## 이미 결정된 것`, `## 알려진 제약`
3. `## 방향` — 이 섹션 안에 ```` ```markdown ```` 펜스로 감싼 4-스텝 견본이
   있고, 그 첫 줄이 정확히 `## 실행 계획` (변형 없음). 지금 코드가 여기서
   멈춘다.
4. `## 실행 계획 (이 이슈 자체 — 요구 1의 첫 적용 사례)` — 진짜 계획, 3
   스텝(`product-discovery`, `implementation`, `execution-observation`),
   현재 전부 `[x]`. 이 헤더는 정확 일치 `"## 실행 계획"`와 다르다(괄호 설명
   접미사). 본문 끝까지 이 섹션 뒤에 다른 `##` 헤더는 없음.

펜스 제외 후 본문에 `## 실행 계획`로 시작하는 헤더는 정확히 1개(4번) —
복수 매치 케이스가 이 실물 문서에는 없다. PR #195 코멘트
(https://github.com/tokenmaxxxer/on-the-record/pull/195#issuecomment-5156219716)
가 이 본문에 대한 `spawn.py flows --json` 실제 출력(3번 펜스 견본의 4-스텝을
`plan`으로 오인식)을 실측으로 남겼다 — 이슈-189 execution-observation 판정이
이미 인용한 그 증거와 동일하다.

## 이슈 #197 본문의 "범위 밖" 절이 이미 고정한 것

- `docs/specs/flows-schema.md`의 `plan` 필드 형태(§2.2, `{step, roles, done}`)는
  안 바뀐다 — 파싱 소스만 고친다. 스키마 문서 수정 불필요, `schema_version`도
  그대로.
- 이슈-189 판정 finding 2(구현 기록의 검증 과대주장)는 별도 사안, 이번
  코드 수정 대상이 아니다.
