---
role: execution-observation
issue: 228
phase: 2
kind: record
loop_state: landed
observed_role: implementation
observed_pr: 231
code_under_review: 923416d
---

# 실행 관측 기록 — issue #228 step 1 (role `implementation`, PR #231, 923416d)

## 독립성 선언

이 role 은 관측 대상 아티팩트를 **저작하지도 편집하지도 않았다**. 이 세션의 쓰기는
`docs/issue-228/reports/execution-observation.md`(이 파일) 한 곳뿐이고,
`gates/pr_reference.py`·`gates/ci.py`·`test_gates.py`·`docs/issue-228/reports/implementation.md`
및 그 role 의 phase-1 산출은 읽기만 했다. 관측 대상의 코드·테스트는 한 번도 실행하지
않았다 — 모든 동작 판단은 커밋 blob 정독에서 연역했고, 연역이 닿지 않는 경계는
아래 각 판정문 안에 명시했다.

**판정은 이 선언 아래에서만 시작한다.**

## What was done (이 관측 세션이 실제로 한 일)

이 세션에서 직접 읽은 것 — 아래 판정은 전부 이 목록에서만 인용한다.

| 아티팩트 | 읽은 방법 |
|---|---|
| issue #228 본문·실행 계획·코멘트 2건 | `gh issue view 228`, `gh api .../issues/228/comments` |
| PR #231 본문·머지 메타(`mergedAt 2026-08-03T05:52:50Z`, `mergeCommit 1fc8e96`) | `gh pr view 231` |
| 커밋 923416d 의 `--stat` 과 `gates/*.py`·`test_gates.py` 전체 diff | `git show --stat 923416d`, `git show 923416d -- <path>` |
| 923416d 시점 `gates/pr_reference.py` blob(phase-1 분기) | `git show 923416d:gates/pr_reference.py` |
| 923416d 시점 `test_gates.py` 의 호출 형태 계수 | `git show 923416d:test_gates.py \| grep` |
| 관측 대상 자기 기록 | `docs/issue-228/reports/implementation.md` |
| 관측 대상 phase-1 산출 | `docs/issue-228/proposals/implementation.md:60-90`, `docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:40-86` |
| 브랜치 커밋 순서 2c84417 → 923416d → 016420f | `git log --date=iso-strict 2c84417~1..016420f` |
| 실물 사건 | `gh api .../issues/235/timeline`, `gh pr view 237`, `gh pr view 238`, `gh issue view 236`, `gh issue view 221`, `gh api .../branches/main/protection` |
| 배선 상태 | `git ls-files .github`(무출력), `git grep -n -- "--phase"`, `spawn.py:1053-1071`, `spawn.py:2372-2375`, `protocol.md:147-151` |

Upstream basis: 이 관측의 착수 근거는 issue #228 코멘트
<https://github.com/tokenmaxxxer/on-the-record/issues/228#issuecomment-5163242598>
(본문 전체가 정확히 `APPROVE issue-228/execution-observation`, jjongkwann,
`2026-08-03T06:55:13Z`, `docs/specs/approvers.md` 등재 계정, 단일 계정 모드)이며,
판정의 층·증거원은 phase-1 제안 `docs/issue-228/proposals/execution-observation.md:15-40`
이 승인 전에 선언한 그대로다.

## Why (왜 이 세 층과 이 네 각도인가)

관측 대상의 작업을 재실행하는 것은 이 role 에 금지돼 있으므로, 판정은 산출된
아티팩트만으로 서야 한다. 그래서 제안이 승인 전에 층(outcome / trajectory / step)과
각 층의 증거원을 먼저 고정했고(`proposals/execution-observation.md:15-40`), step 층은
네 각도로만 열기로 미리 못박았다 — (a) 신규 9건의 변경 전 실패, (b) `ci.py --phase`
도달 가능성, (c) fail-closed 방향의 부작용, (d) 실물 사건 귀속. 판정 척도는
`reports/execution-observation/scout-brief.md:12-17` 이 정리한 현장 기준을 그대로 쓴다:
RED 는 assertion mismatch 여야 하고, fail-closed 는 "평가 불가"와 "위반"을 구분 가능한
신호로 내야 하며, 사건 귀속은 "그 시점에 어느 버전이 실제로 돌았는가"를 먼저 고정한다.

---

# 판정

## 1. outcome — PR/기록이 이슈가 요구한 것을 실었는가

**충족(요구 4건 전부).** 근거를 요구별로 붙인다.

- **R1(미완 스텝이 남으면 closing 키워드 차단, 마지막 스텝에서만 요구)** — 충족.
  `923416d gates/pr_reference.py` diff 의 `if plan:` 블록이 `incomplete` 와
  `only_last_incomplete` 를 계산해 `incomplete and not only_last_incomplete` 일 때
  `_CLOSES_REF` 매치를 차단 사유로 되돌리고, 그렇지 않으면 기존 require-Closes 로
  낙하한다. 실행 테스트: `923416d test_gates.py:639`(차단), `:653`(무 Closes 통과),
  `:663`·`:674`(마지막만 미완일 때 요구 유지).
- **R2(계획 없는 이슈는 현행 유지)** — 충족. `923416d test_gates.py:632-635` 가
  `plan=None` 두 방향(Closes 있음 → `[]`, 없음 → 차단)을 고정한다.
- **R3(펜스 안 인용도 GitHub 이 파싱한다)** — 충족. `923416d gates/pr_reference.py` 의
  `_CLOSES_REF` 는 가공되지 않은 `body` 원문에 `re.search` 하며 펜스 제거 전처리가
  없고, `923416d test_gates.py:685-697` 이 펜스 안 `Closes #228` 도 차단됨을 고정한다.
  반대 방향(GitHub 이 파싱하지 않는 인라인 스팬·HTML 주석까지 세는 과대 계수)은
  `923416d docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:78-82`
  가 "unchanged by this decision" 으로 명시한 범위 밖이므로 미이행으로 세지 않는다.
- **R4(`_plan_from_body` 재사용, 재구현 금지)** — 충족. `git show --stat 923416d` 의
  변경 파일은 decisions 문서·`gates/ci.py`·`gates/pr_reference.py`·`test_gates.py`
  4개뿐이고 `gates/flows.py` 는 hunk 가 0이다. 소비는 `923416d gates/pr_reference.py`
  의 신규 `import flows` 와 `plan = flows._plan_from_body(issue_body)` 한 곳이다.

**outcome 층의 결함 1건(F-1, 아래 findings)**: 요구된 동작은 전부 코드에 있으나,
그 동작을 프로덕션 경로로 잇는 `check()` 배선(이슈 본문 조회 → `_plan_from_body` →
`check_body`)을 실행하는 테스트가 0건이다 — `git show 923416d:test_gates.py | grep -n
"pr_reference\.check("` 무출력, 같은 파일에서 `check_body(` 직접 호출은 18건.

## 2. trajectory — phase-1→phase-2 경로가 온전했는가

**온전함.** 네 지점 모두 증거가 있다.

- **승인의 실체성** — issue #228 코멘트
  <https://github.com/tokenmaxxxer/on-the-record/issues/228#issuecomment-5161635406>
  는 본문 전체가 정확히 `APPROVE issue-228/implementation` 이고 작성자는
  `docs/specs/approvers.md` 등재 계정 jjongkwann, 시각 `2026-08-03T02:17:03Z` —
  계약 v3 s19 단일 계정 모드의 문자열 동일성 경로를 문자 그대로 만족한다.
- **순서** — `git log 2c84417~1..016420f`: phase-1 산출 2c84417 `02:11:51Z`(=11:11:51+09:00)
  → 승인 `02:17:03Z` → phase-2 구현 923416d `02:35:02Z` → 기록 016420f `02:40:35Z`.
  승인 전에 phase-2 파일이 커밋된 흔적이 없다.
- **범위 확장이 사후가 아니었는가** — 이슈가 "같이 볼지는 제안이 판단한다"로 남긴
  인접 결함(`ci.py --phase`)은 승인 **전** 문서인
  `docs/issue-228/proposals/implementation.md:68-77`("채택 2")에서 거부 대안까지
  적어 범위에 넣기로 선언했고, 결정 문서
  `docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:50-62` 가 같은
  근거를 반복한다. 사후 확장이 아니다.
- **자기 발견의 처분** — 스스로 돌린 hunt 가 찾은 결함(`if plan:` 이 `None` 과 `[]` 를
  뭉갠다)을 숨기지 않고 미수정 사유 3가지와 함께 남겼다
  (`docs/issue-228/reports/implementation.md:108-127`). 관측 대상이 자기 결함을
  기록에 남긴 것은 이 경로에서 가장 확인하기 어려운 항목이고, 여기서는 확인된다.
- **자기 PR 의 종결 키워드 처리** — PR #231 본문은 closing 키워드를 담지 않고 그 이유를
  명시하며("Deliberately does not carry `Closes #228`", PR #231 본문), issue #228 은
  `gh issue view 228` 기준 여전히 `state: OPEN` 이다.

## 3. step — 어느 아티팩트가 미흡한가

### (a) 신규 테스트 9건의 "변경 전 실패"

**명제는 참이지만 해상도가 낮다 — 게이팅 력을 가진 것은 9건 중 5건이다.**
`923416d test_gates.py` diff 와 `923416d gates/pr_reference.py`·`gates/ci.py` diff 의
변경 전 쪽(`-` 줄)을 대조해 각 테스트를 분류했다. 변경 전 시그니처는
`check_body(issue, body, phase)` 3-파라미터이므로 `plan` 을 넘기는 8건은 **모두**
호출 자체가 불가능하다. 그 arity 실패를 걷어내고 단언만 옛 로직에 대입하면:

| 테스트 (923416d test_gates.py) | 옛 로직에서 단언이 깨지는가 | 게이팅 력 |
|---|---|---|
| `:632` plan_none_regression_unaffected | 아니오 — 옛 로직도 동일 결과 | 없음(고정용) |
| `:639` incomplete_steps_with_closes_blocks | 예 — 옛 로직은 `[]` 반환 | **있음** |
| `:653` incomplete_steps_without_closes_passes | 예 — 옛 로직은 차단 | **있음** |
| `:663` only_last_incomplete_with_closes_passes | 아니오 | 없음(고정용) |
| `:674` only_last_incomplete_without_closes_blocks | 아니오 | 없음(고정용) |
| `:685` fenced_closes_still_blocks_when_incomplete | 예 — 옛 로직은 펜스 안 Closes 를 매치해 `[]` | **있음** |
| `:699` reverse_checkbox_order_blocks | 예 — 옛 로직은 `[]` | **있음** |
| `:714` single_step_plan_done_requires_closes | 아니오 | 없음(고정용) |
| `:1044` ci_check_missing_phase_blocks | 예 — 옛 기본값 `phase1` 로 진행해 차단 사유에 `"--phase"` 가 들어가지 않는다 | **있음** |

관측 대상 기록은 실패 사실 자체는 정직하게 적었다 —
`docs/issue-228/reports/implementation.md:13-19` 는 "`check_body` 는 plan kwarg 자체를
TypeError 로 거부"라고 메커니즘까지 밝힌다. 문제는 그 위에 얹힌 요약이다: PR #231 본문의
"Confirmed each fails against pre-change code" 와 기록의 "신규 9건 … 변경 전 코드에서
실제로 실패하는 케이스임을 실측"(implementation.md:9-19)은 **arity 실패와 회귀 포착력을
같은 층위로 합산**한다. scout-brief.md:14 의 척도(RED 는 assertion mismatch 여야 하고
TypeError 는 "옛 코드에서 돌려볼 수 없었다"는 사실일 뿐)로는 4건이 RED 증거가 아니다.
고정용 테스트 4건 자체는 정당한 설계다 — 바뀌면 안 되는 동작을 못박는 것이 목적이므로.
결함은 테스트가 아니라 **증거 진술의 해상도**에 있다(F-2).

한 가지 정밀도 지적: 기록의 "`ci.check()` 는 `--phase` 없이도 차단 사유를 내지 않음을
확인"(implementation.md:17-19)은 문언대로는 정확하지 않다. 변경 전
`ci.check(repo, pr, issue)` 는 `pr_reference.check` 를 거쳐 `_pr_view` 실패 시
"PR #N 본문을 읽을 수 없다" 를 되돌린다(`923416d gates/pr_reference.py` diff 의 변경 전
컨텍스트 줄). 즉 차단 사유가 없는 게 아니라 **`--phase` 사유가 없는** 것이고, 테스트
`:1044` 의 단언(`any("--phase" in b)`)이 정확히 그 형태다. 실질 주장은 옳고 문언만
느슨하다 — 결함으로 세지 않고 정밀도 지적으로 남긴다.

### (b) `ci.py --phase` 수정과 도달 가능성

**변경 전은 "검사 없음"이 아니라 "다른 약한 검사로의 무음 대체"였고, 수정은 그 대체를
없앴다. 그러나 이 수정이 phase-2 게이트를 자동 경로에서 도달 가능하게 만들지는
않았다 — 도달 가능성은 여전히 0이다.**

- 변경 전: `check(..., phase: str = "phase1")` 와 `phase = opts.get("phase", "phase1")`
  (`923416d gates/ci.py` diff 의 `-` 줄) — `--phase` 를 빼면 phase1 분기가 조용히 돌았고,
  그 분기는 평문 `#N` 참조만 본다(`923416d gates/pr_reference.py:57-63`).
- 변경 후: `phase: str | None = None` / `opts.get("phase")` 와, `pr`·`issue` 가 둘 다
  있는데 `phase` 가 없으면 명시 차단(`923416d gates/ci.py` diff 의 `+` 줄).
- 그러나 **자동 호출 경로에 `--pr`/`--issue` 를 넘기는 지점이 없다.** 이 저장소의
  유일한 자동 게이트 호출은 `spawn.py:1071` 의 `bad = ci.check(Path(cwd).resolve())`
  이고 `pr`·`issue` 인자가 없다 — 그러면 `pr_reference.check` 자체가 호출되지 않아
  phase-2 로직도, 새 `--phase` 가드도 발동하지 않는다. `git ls-files .github` 는
  무출력이고(워크플로 0개), `git grep -n -- "--phase"` 의 히트는 전부 문서 산문과
  제안·결정·이 role 의 조사 파일이며 실행 호출 지점은 0건이다.
- 따라서 이 수정의 실효 범위는 **사람이 손으로 `python3 gates/ci.py . --pr N --issue N`
  을 칠 때**로 한정된다. 제안의 "지금 고치지 않으면 죽은 코드로 남는다"
  (`proposals/implementation.md:71-77`)는 그 범위 안에서 옳지만, 배선이 함께 오지
  않았으므로 게이트는 여전히 자동으로 돌지 않는다(F-3). 이슈가 배선을 요구하지
  않았으므로 요구 미이행은 아니고, 잔여 위험이다 — (d)에서 이 잔여 위험이 실물로
  터진 것을 본다.

### (c) fail-closed 방향의 부작용

**정당한 phase-2 PR 을 본문 내용 때문에 새로 막는 입력은 없다. 새로 생긴 것은
"평가 불가" 차단 두 개이며, 둘 다 구분 가능한 신호를 낸다.** scout-brief.md:15-16 의
네 질문으로 답한다.

1. `923416d gates/ci.py` 의 `--phase` 누락 차단 — 신호 구분: 있다("--phase가
   필요하다(phase1|phase2) — 생략하면 phase-2 검사가 조용히 건너뛰어진다"). 위험 등급:
   게이트 자신의 평가 가능성에 관한 것이라 fail-closed 가 정당하다. 우회: `--phase` 를
   주면 된다. 폭발 반경: 위 (b)대로 자동 호출자는 `pr`·`issue` 를 넘기지 않으므로
   `spawn.py:1071` 경로의 거동은 변하지 않는다 — 새 소음 0.
2. `923416d gates/pr_reference.py` 의 `check()` 안 "이슈 #N 본문을 읽을 수 없다" 차단 —
   **신규 실패 경로**다. 변경 전 `check()` 는 이슈 본문을 아예 가져오지 않았다(같은
   diff 의 변경 전 컨텍스트: `body = _pr_view(...)` → 곧장 `check_body`). 신호 구분:
   있다("검사 불가는 통과가 아니다"). 다만 `_issue_view_body` 는 `gh issue view` 를
   `cwd=repo` 로 `-R` 없이 실행하므로, 레이트리밋·토큰 스코프·오리진 불일치 같은
   **가용성 사유가 본문상 이미 적법한 PR 을 막을 수 있다**. 단계적 warn 롤아웃은
   없었다. 폭발 반경은 (b)와 같은 이유로 현재 0이지만, 배선되는 순간 phase-2 검사
   전체가 `gh issue view` 가용성에 의존하게 된다 — 배선 시 재평가할 잔여 위험으로
   남긴다.
3. 과잉 차단 방향(역순 체크박스에서 마지막 스텝까지 차단)은 결함이 아니라 **선언된
   설계 선택**이다 — `decisions/...-check-body-plan-aware-closes.md:40-47` 이 "fails
   toward blocking … 이 파일의 기존 fail-closed 관례와 같은 방향"으로 명시하고 비용도
   적었다. 숨기지 않았으므로 미흡으로 세지 않는다.
4. 다만 그 선언이 전제한 비용 계산("사람이 한 번 더 확인하는 정도")은 이 보드의 실제
   체크박스 위생과 어긋난다(F-4). issue #228 본문의 실행 계획은 step 1 이 1fc8e96 로
   랜딩된 뒤에도 여전히 `- [ ] step 1`(gh issue view 228 본문)이고, issue #235 도
   PR #237 머지 뒤 `- [ ] step 1`(gh issue view 235 본문 L75-76)이다. 체크박스가
   갱신되지 않는 한 어떤 이슈도 "마지막 스텝만 미완" 상태에 도달하지 못하므로,
   R1 의 후반부("마지막 스텝의 phase-2 PR 에서만 요구한다")는 이 보드에서 **작동하지
   않는 반쪽**으로 남는다. 차단 반쪽은 정상 작동한다.

### (d) 실물 사건 귀속 — PR #231 과 PR #237 은 서로 다른 사건이다

**사건 1(PR #231 이 #228 을 자동 종결하지 않음) — 게이트의 공로가 아니라 저자의
수동 준수다.** PR #231 은 `mergeCommit 1fc8e96`, `mergedAt 2026-08-03T05:52:50Z`
(`gh pr view 231`)이고, 923416d 는 바로 그 PR 의 브랜치 위 커밋이다. 즉 PR #231 이
머지되기 **전** main 에는 계획-인지 게이트가 존재하지 않았고, 어떤 버전의 게이트도 이
PR 을 평가할 수 없었다. 자동 종결이 없었던 이유는 PR #231 본문이 closing 키워드를
의도적으로 빼고 그 이유를 적었기 때문이다(PR #231 본문). **이 사건은 게이트가
작동한다는 증거가 아니다.**

**사건 2(PR #237 머지로 #235 자동 종결) — 게이트 로직 결함이 아니라 배포 경로 결함이다.
다만 통상 지목되는 원인 하나로는 설명이 불완전하다.**

- *타임라인 고정*: 게이트는 `05:52:50Z`(1fc8e96)에 main 에 들어갔다. PR #237 머지
  `06:15:33Z`(`gh pr view 237`, `mergeCommit d187559`), issue #235 `closed`
  `06:15:35Z`, `reopened` `06:16:22Z`(`gh api .../issues/235/timeline`). 게이트는 그
  시점 main 에 **있었다**.
- *로직 판정*: issue #235 본문의 실행 계획은 `- [ ] step 1` / `- [ ] step 2`
  (`gh issue view 235` 본문 L73-76)로 미완 2건이다. `923416d gates/pr_reference.py` 의
  `if plan:` 분기에 그대로 대입하면 `incomplete=2`, `only_last_incomplete=False` 이고
  PR #237 본문에는 `Closes #235` 가 있으므로(`gh pr view 237` 본문) 차단이 나온다.
  **로직은 이 사건을 정확히 잡도록 돼 있었다 — 게이트 결함 아님.**
- *원인 A(지목된 것)*: 재사용 워크스페이스가 로컬 브랜치를 origin 으로 맞추지 않아
  세션이 923416d 이전 코드로 검사했다. `spawn.py:2372-2375` 는 `.git` 이 있으면
  `git -C <work> fetch -q origin` 만 하고 곧장 반환한다 — 원격 추적 ref 만 갱신하고
  체크아웃된 로컬 브랜치는 그대로다. issue #221 의 결함 2("재사용 시 브랜치
  미동기화", `gh issue view 221` 본문)와 정확히 같은 형태이고, #235 재오픈 코멘트가
  지목한 것도 이것이다
  (<https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162962921>).
- *원인 B(지목되지 않은 것, 그리고 더 결정적인 것)*: **워크스페이스가 완벽히
  동기화됐어도 이 게이트는 머지를 막지 못한다.** main 에 브랜치 보호가 없고
  (`gh api .../branches/main/protection` → 404 "Branch not protected"),
  `git ls-files .github` 가 무출력이라 필수 상태 체크가 0개이며, 자동 호출자
  `spawn.py:1071` 은 `pr`·`issue` 를 넘기지 않아 `pr_reference.check` 에 닿지도
  않는다. 게다가 그 보고 함수는 스스로를 비차단·사후로 규정한다 —
  "**막지는 않는다.** 세션이 끝난 뒤라 되돌릴 수 없고…"(`spawn.py:1053-1055`).
  즉 이 게이트는 강제 체크가 아니라 사람이 손으로 돌리는 자문 스크립트다.
- *귀속 결론*: 사건 2 의 root cause 는 배포 경로에 있고 두 겹이다 — 원인 A(stale
  워크스페이스)는 그 시점에 옛 코드를 돌게 했고, 원인 B(강제 배선 부재)는 A 를
  고쳐도 재발을 막지 못한다. 원인 B 는 issue #221 의 범위 밖이라 #221 이 랜딩돼도
  남는다(F-3 과 같은 뿌리).

**범위 밖 관측(판정하지 않음)**: PR #238 은 phase-1 전용 PR 인데 본문에 closing
키워드가 있고(`gh pr view 238`, `06:15:16Z` 머지) issue #236 은 `06:15:17Z` 에
`CLOSED / COMPLETED` 로 기록됐다(`gh issue view 236`). 923416d 의 phase-1 분기는
평문 `#N` 존재만 검사하고 `_CLOSES_REF` 를 보지 않는데
(`923416d gates/pr_reference.py:57-63`), 같은 분기의 오류 메시지는
"Closes/Fixes/Resolves는 금지"라고 적는다 — 문서화된 규칙과 기계 검사의 불일치다.
issue #228 은 "phase-1 PR의 현행 규칙은 그대로 둔다"를 제약으로 명시했으므로
**관측 대상의 미흡이 아니다.** 사람이 별도 이슈로 다룰지 판단할 재료로만 남긴다.

---

## Open findings (미흡 — 각 4부 blameless 형태)

**F-1 (outcome 층) — 신규 프로덕션 배선을 실행하는 테스트가 0건.**
- impact: `check()` 가 phase-2 에서 이슈 본문을 조회해 `_plan_from_body` 로 계획을
  파싱하고 `check_body` 에 넘기는 경로 — 즉 이 이슈의 로직이 실제로 프로덕션에서
  돌 유일한 경로 — 이 회귀 없이 깨질 수 있다. 함께 도입된 fail-closed 차단
  (이슈 본문 조회 실패)도 검증되지 않았다.
- timeline: 923416d 에서 `check()` 배선과 8건의 `check_body` 단위 테스트가 함께 들어옴.
  `git show 923416d:test_gates.py | grep "pr_reference\.check("` → 0건,
  `check_body(` → 18건.
- root cause: 테스트가 `plan` 을 인자로 직접 주입하는 형태로 설계돼, `plan` 을
  **만들어 오는** 계층이 테스트 표면 밖에 남았다. `gh` 호출이 끼어 있어 단위
  테스트로 감싸기 번거롭다는 구조적 유인도 있다.
- action item(사람의 판단 대상): `_issue_view_body` 를 주입 가능하게 하거나 monkeypatch
  해 `check()` 수준 케이스 2건(정상 파싱 / 이슈 본문 조회 실패 시 차단)을 추가.

**F-2 (step 층, 각도 a) — "9건 전부 변경 전 실패"가 arity 실패와 회귀 포착력을 합산한다.**
- impact: 이 커밋의 회귀 방어력을 읽는 사람이 9건을 게이팅 력으로 오독한다. 실제로
  옛 로직을 잡는 것은 5건(`:639`, `:653`, `:685`, `:699`, `:1044`)이고 4건
  (`:632`, `:663`, `:674`, `:714`)은 시그니처 때문에 호출만 불가했을 뿐 단언은 옛
  로직에서도 참이다.
- timeline: PR #231 본문 "Confirmed each fails against pre-change code" 와
  `docs/issue-228/reports/implementation.md:9-19` 의 closed_checks 요약. 같은 기록
  :13-19 는 TypeError 메커니즘을 밝히고 있어 **정보는 있으나 요약이 그것을 흡수했다**.
- root cause: 시그니처를 바꾸는 변경에서는 "옛 코드에서 실패한다"가 두 가지 서로 다른
  뜻(호출 불가 / 단언 거짓)을 갖는데, 검증 절차가 그 둘을 나누는 단계를 두지 않았다.
- action item(사람의 판단 대상): 시그니처 변경을 동반하는 커밋에서는 신규 테스트를
  "옛 시그니처에 맞춰 적응시켰을 때도 실패하는가"로 한 번 더 걸러 집계.

**F-3 (step 층, 각도 b·d) — 게이트가 어떤 자동 경로로도 실행되지 않는다.**
- impact: 이 이슈가 만든 차단 로직이 실제 머지를 막을 수 없다. issue #235 가 그
  실물 결과다 — 게이트가 main 에 있었는데도(`1fc8e96`, `05:52:50Z`) PR #237 머지
  (`06:15:33Z`)를 막지 못했고 `06:15:35Z` 에 자동 종결됐다.
- timeline: `git ls-files .github` 무출력(워크플로 0), `gh api
  .../branches/main/protection` 404, `spawn.py:1071` 은 `ci.check(cwd)` 를 `pr`·`issue`
  없이 호출, `spawn.py:1053-1055` 는 스스로를 비차단으로 규정.
- root cause: 게이트 로직과 게이트 **배선**이 서로 다른 이슈에 흩어져 있고, #228 은
  로직만 요구했다(이슈 제약 "이 게이트가 실제로 도는지의 문제 — 같이 볼지는 제안이
  판단한다"). 제안은 `--phase` 기본값까지만 범위에 넣었고 배선은 넣지 않았다
  (`proposals/implementation.md:68-77`) — 그 선택 자체는 선언됐으므로 절차 위반이
  아니다.
- action item(사람의 판단 대상): 게이트를 실제로 실행하는 경로(필수 상태 체크,
  또는 `spawn.py` 의 게이트 보고가 `--pr/--issue/--phase` 를 넘기도록)를 별도 이슈로
  세울지 판단. issue #221 이 랜딩돼도 이 구멍은 남는다.

**F-4 (step 층, 각도 c) — 게이트의 입력인 체크박스를 보드가 갱신하지 않아 R1 의 후반부가
작동하지 않는다.**
- impact: "마지막 스텝의 phase-2 PR 에서만 Closes 를 요구한다"가 실제로 발동하지
  못한다. 어떤 이슈도 "마지막만 미완" 상태에 도달하지 않기 때문이다. 차단 방향은
  정상이므로 안전 쪽 실패지만, 사람이 매번 손으로 닫아야 한다.
- timeline: issue #228 은 step 1 이 `1fc8e96`(`05:52:50Z`)로 랜딩된 뒤에도 본문이
  `- [ ] step 1`(`gh issue view 228`), issue #235 도 PR #237 머지 뒤 `- [ ] step 1`
  (`gh issue view 235` 본문 L75-76).
- root cause: 계획 체크박스를 누가 언제 갱신하는지가 계약에 없다. 게이트는 그 체크박스를
  진실의 원천으로 삼는데, 그 원천을 유지하는 주체가 지정돼 있지 않다.
- action item(사람의 판단 대상): 체크박스 갱신 주체·시점을 계약에 명시할지, 아니면
  게이트가 머지된 PR 로 스텝 완료를 추론하도록 할지 판단.

### 미흡이 아닌 것 (명시)

- 관측 대상이 hunt 로 스스로 찾은 `if plan:` 의 `None`/`[]` 뭉갬은 기록에 findings 로
  남기고 미수정 사유 3가지를 적었다(`docs/issue-228/reports/implementation.md:108-127`).
  숨김이 아니므로 이 관측의 미흡 목록에 다시 세지 않는다.
- 펜스 과대 계수(HTML 주석·인라인 스팬)와 phase-1 분기의 `Closes` 미검사는 이슈가
  명시한 범위 밖이다 — 각각 `decisions/...:78-82`, issue #228 본문 제약.

## Open-finding resolution path

F-1~F-4 는 전부 **이 기록 안에서 종결되지 않는다.** 이 role 은 관측 대상의 `src/`·
`test/`·기록을 편집할 수 없고 계약 v3 상 이슈를 발행할 수도 없다. 해결 경로는 하나다:
사람이 이 PR 에서 findings 를 읽고, 유효하다고 판단한 것만 직접 이슈로 세운다.
이 role 은 그 이후 아무것도 하지 않는다. F-3 은 issue #221 과 뿌리를 공유하지만
#221 의 범위(워크스페이스 동기화)로는 닫히지 않는다는 점을 함께 판단 재료로 남긴다.

## Next steps

1. 이 기록을 브랜치 `issue-228/execution-observation` 에 커밋하고 PR #243 으로 push —
   phase 2 의 유일한 인도물.
2. 사람의 판단 대기: PR #243 머지 = 이 판정의 수용, 미머지 종결 = 거부. F-1~F-4 의
   이슈화 여부도 사람이 결정한다.
3. issue #228 실행 계획 step 2 의 체크박스 갱신과 이슈 종결은 사람 몫이다 — 이 PR 은
   closing 키워드를 담지 않는다.
