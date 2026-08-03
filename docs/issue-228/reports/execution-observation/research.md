---
role: execution-observation
issue: 228
phase: 1
kind: research-evidence-log
loop_state: researching
---

# 증거 로그 — issue #228 step 2 가 지시한 4개 각도

이 문서는 **증거만** 적재한다. 판정(outcome / trajectory / step)은 phase 2 의 기록 파일에서 내린다.
모든 줄은 인용을 달고, 인용이 없는 줄은 `가정:` 으로 라벨한다. 관측 대상 코드는 실행하지 않았다 — 전부 커밋 blob 정독이다.

## 각도 (a) — 신규 테스트 9건이 변경 전 코드에서 실제로 실패하는가

변경 전 트리 = `923416d^` = `2c84417`. 변경 전 `check_body(issue: int, body: str, phase: str)` 는 위치 인자 3개이고 `plan` 파라미터가 없다(923416d^ gates/pr_reference.py:26). 변경 후는 `plan: list[dict] | None = None` 이 추가된다(923416d gates/pr_reference.py:28-29).

| # | 테스트 (923416d test_gates.py 줄) | 변경 전 호출 가능? | 단언이 변경 전 로직과 충돌하는가 | 관측 분류 |
|---|---|---|---|---|
| 1 | `t_pr_reference_phase2_plan_none_regression_unaffected` (632) | 불가 — `plan=` 키워드 없음(923416d^ :26) | 해당 없음 | arity 로만 실패 |
| 2 | `t_pr_reference_phase2_incomplete_steps_with_closes_blocks` (639) | 불가 (4번째 위치 인자) | 충돌 — 변경 전은 Closes 있으면 `[]` 반환(923416d^ :29-31) | 로직 충돌 + arity |
| 3 | `t_pr_reference_phase2_incomplete_steps_without_closes_passes` (653) | 불가 | 충돌 — 변경 전은 Closes 없으면 bad(923416d^ :29-31) | 로직 충돌 + arity |
| 4 | `t_pr_reference_phase2_only_last_step_incomplete_with_closes_passes` (663) | 불가 | 충돌 없음 — 변경 전도 `[]` | arity 로만 실패 |
| 5 | `t_pr_reference_phase2_only_last_step_incomplete_without_closes_blocks` (674) | 불가 | 충돌 없음 — 변경 전도 bad | arity 로만 실패 |
| 6 | `t_pr_reference_phase2_fenced_closes_still_blocks_when_incomplete` (685) | 불가 | 충돌 — 변경 전은 펜스 안 Closes 도 매치해 `[]`(923416d^ :29-31) | 로직 충돌 + arity |
| 7 | `t_pr_reference_phase2_reverse_checkbox_order_blocks` (699) | 불가 | 충돌 — 변경 전은 `[]` | 로직 충돌 + arity |
| 8 | `t_pr_reference_phase2_single_step_plan_done_requires_closes` (714) | 불가 | 충돌 없음 — 두 단언 모두 변경 전과 일치 | arity 로만 실패 |
| 9 | `t_ci_check_missing_phase_with_pr_and_issue_blocks` (1044) | **가능** — 양쪽 다 기본값 있음 | 충돌 — 변경 전 기본값 `"phase1"`(923416d^ gates/ci.py:44)로 진행하며 bad 에 `"--phase"` 문자열이 들어가지 않음 | 로직만으로 실패 |

- 요구 4건 대 테스트 대응: (i) → 2,3,4,5,7,8 중 **변경 전 로직과 실제로 갈리는 것은 2,3,7**; (ii) → 1(arity 로만); (iii) → 6(펜스 관용 자체는 변경 전에도 참이었고, 6이 실제로 가르는 것은 계획-차단 분기다); (iv) → `check()` 래퍼를 `phase="phase2"` 로 부르는 테스트가 test_gates.py 에 없다 — 즉 `flows._plan_from_body` 로의 새 배선(923416d gates/pr_reference.py:85-102)을 직접 실행하는 테스트는 0건이다.

## 각도 (b) — ci.py `--phase` 무음 스킵 수정이 이 게이트를 도달 가능하게 했는가

- 변경 전: `check(..., phase: str = "phase1")` (923416d^ gates/ci.py:44), `main()` 의 `phase = opts.get("phase", "phase1")` (923416d^ gates/ci.py:90). `--phase` 생략 시 `pr_reference.check(repo, pr, issue, "phase1")` 이 그대로 실행된다(923416d^ gates/ci.py:49).
- 변경 후: `phase: str | None = None` (923416d gates/ci.py:44), `phase = opts.get("phase")` (923416d gates/ci.py:94), `if phase is None:` 에서 차단 사유를 넣는다(923416d gates/ci.py:49-53).
- 호출 사슬: `ci.main` → `ci.check` → `pr_reference.check` → `pr_reference.check_body` 의 `if phase == "phase2":` (923416d gates/pr_reference.py:39). 변경 전에 `--phase` 를 생략하면 phase1 분기(bare `#issue` 검사, 923416d gates/pr_reference.py:57)가 대신 돌았다 — **검사 부재가 아니라 다른 약한 검사로의 무음 대체**다.
- 이 수정은 별도 PR 이 아니라 923416d **같은 커밋 안**에 있다(`git show --stat 923416d` 가 `gates/ci.py` 와 `gates/pr_reference.py` 를 함께 담는다). 923416d 는 016420f 의 조상이고 1fc8e96 로 main 에 들어갔다.
- 자동 호출 지점: `git ls-files .github/workflows` 무출력, `git grep -n -- "--phase"` 가 `gates/ci.py`·`gates/pr_reference.py`·`test_gates.py` 밖에서 0건. `protocol.md:148-149,158-159` 는 이 검사를 사람이 돌리는 머지 결정 입력으로 규정한다.
- 수정 후에도 남는 무음 경로: `pr`·`issue` 가 둘 다 주어지지 않으면 `pr_reference.check` 자체가 호출되지 않고 아무 메시지도 없다(923416d gates/ci.py:47-53). 이는 변경 전부터 있던 설계다.

## 각도 (c) — fail-closed 방향이 정당한 phase-2 를 새로 막는가

새로 생긴 차단 경로는 두 개다.
- `923416d gates/pr_reference.py:98-100` — `phase=="phase2"` 일 때 `_issue_view_body`(gh issue view) 실패 시 "이슈 #N 본문을 읽을 수 없다" 로 차단. 변경 전 `check()` 는 이슈 본문을 **아예 가져오지 않았다**(923416d^ gates/pr_reference.py:53-58) — 이 실패 경로 자체가 없었다.
- `923416d gates/ci.py:49-51` — `pr`·`issue` 가 있는데 `phase` 가 없으면 즉시 차단. 변경 전 같은 입력은 phase1 로 진행했다(923416d^ gates/ci.py:90).
- 기존 경로 `923416d gates/pr_reference.py:93-94` (PR 본문 못 읽음 → 차단)는 변경 전 923416d^ gates/pr_reference.py:56-57 과 동일하다 — 신규 아님.
- 두 신규 경로 모두 `--pr --issue --phase` 를 넘기는 호출 형태에서만 발동하며, 이 저장소 안에서 그 형태의 호출 지점은 문서 산문 언급(923416d docs/issue-126/reports/coding.md:30, docs/issue-135/reports/coding/survey.md:12) 외에 발견되지 않았다. 워크플로 디렉터리도 비어 있다.
- 배선될 경우 새로 생기는 노출: `gh issue view` 가 `cwd=repo` 로 `-R` 없이 실행되므로(923416d gates/pr_reference.py:76-77) 타 저장소 이슈 번호·토큰 스코프·레이트리밋에서의 일시 실패가 본문상 이미 적법한 PR 을 막을 수 있다.
- `가정:` 저장소 밖 오케스트레이터가 `--pr --issue` 를 넘기지 않는다 — 이 저장소 내용만으로는 확인 불가(U-2).

## 요구 4건의 구현 위치

- R1: `incomplete` / `only_last_incomplete` 계산과 차단 사유 문자열 — 923416d gates/pr_reference.py:40-51; 그 외에는 기존 require-Closes 유지 — :52-56.
- R2: `_plan_from_body` 는 `## 실행 계획` 헤더가 없으면 `None`(923416d gates/flows.py:99-102), `if plan:` 이 거짓이라 기존 분기로 떨어진다(923416d gates/pr_reference.py:52-56). 테스트 923416d test_gates.py:632-635.
- R3: `_CLOSES_REF` 는 가공하지 않은 `body` 원문에 대해 `re.search` 한다(923416d gates/pr_reference.py:25,47,52) — 펜스 제거 전처리가 없다. 펜스 건너뛰기는 `_plan_from_body` 의 스텝 파싱 루프 안에만 있고(923416d gates/flows.py:90-97) `_CLOSES_REF` 입력에는 닿지 않는다. 반대 방향(GitHub 이 파싱하지 **않는** `<!-- Closes #N -->` HTML 주석·인라인 백틱)에 대한 제거도 없다 — `git grep -n "<!--" 923416d -- 'gates/*.py'` 0건. 이 과잉 매치는 변경 전과 동일하고(923416d^ gates/pr_reference.py:22-23,30), 결정 문서가 범위 밖으로 명시한다(923416d docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:79-82).
- R4: 프로덕션 호출 지점은 정의부 923416d gates/flows.py:79 와 신규 소비부 923416d gates/pr_reference.py:101 (`plan = flows._plan_from_body(issue_body)`), `import flows` 는 신규(923416d gates/pr_reference.py:20). `flows.py` 에는 이 커밋의 diff hunk 가 하나도 없다.

## 각도 (d) — 실물 검증

- **사건 1**: PR #231 본문은 closing 키워드를 담지 않으며, 그 이유를 본문에 명시한다 — "Deliberately does not carry `Closes #228`. Issue #228's own plan still has step 2 (`execution-observation`) open" (PR #231). issue #228 은 `state: OPEN, closedAt: null` 이고 timeline 에 `closed` 이벤트가 없다(issues/228/timeline API).
- **순서**: 923416d 는 PR #231 자신의 브랜치 위 커밋이고, 1fc8e96 로 `2026-08-03T05:52:50Z` 에 main 에 들어갔다. 즉 PR #231 의 머지 전 시점에 main 에는 이 게이트가 아직 없었다.
- **사건 2**: PR #237 본문에는 `Closes #235` 가 한 줄로 들어 있다(PR #237). issue #235 timeline: `closed` at `2026-08-03T06:15:35Z` (머지 `06:15:33Z` 직후), 이어서 `06:16:2x` 에 `commented` + `reopened` (issues/235/timeline API). 재오픈 코멘트 원문: "실행 계획 step 2(execution-observation)가 미완인 채 PR #237 머지의 closing 키워드로 자동 종결됐다 — 8번째 사례. #228 의 계획-인지 게이트는 이미 main 에 랜딩됐지만, 이 세션의 워크스페이스가 phase 1 때 만들어져 재사용되면서 머지 전 게이트로 검사됐다(#221 이 지적한 재사용 브랜치 미동기화의 실물 결과)." (<https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162962921>)
- **배포 경로**: issue #221 은 OPEN 이고 머지된 PR 이 없다(`gh pr list --search "221" --state merged` → `[]`). 그 결함 #2 원문: "재사용 시 브랜치 미동기화: 워크스페이스를 재사용할 때 로컬 브랜치를 `origin/<br>`로 동기화하지 않는다(2288-2289)." 현재 코드 `issue_workspace()` 는 `.git` 이 있으면 `git -C <work> fetch -q origin` 후 곧장 반환한다(spawn.py:2372-2375) — 원격 추적 ref 만 갱신하고 체크아웃된 로컬 브랜치는 맞추지 않는다.
- **구조적 전제**: main 에 브랜치 보호가 없고(`gh api .../branches/main/protection` → 404) PR #237 에 보고된 상태 체크는 0건(`gh pr checks 237` → "no checks reported"). `spawn.py:1054-1064` 의 `gate_report()` 는 스스로를 비차단·사후로 규정한다 — "**막지는 않는다.** 세션이 끝난 뒤라 되돌릴 수 없고…".
- **923416d 이후 머지된 다른 PR**: #233(`04:48:59Z`)·#234(`05:19:12Z`)는 1fc8e96 이전 — 게이트 이전 시대. #238 은 `06:15:16Z` 머지된 **phase-1 전용** PR 인데 본문에 closing 키워드가 있고 issue #236 은 `06:15:17Z` 에 `CLOSED / COMPLETED` 로 기록돼 있다(PR #238; issue #236). phase-1 분기 코드는 `_PLAIN_REF` 존재만 보고 `_CLOSES_REF` 를 검사하지 않는데(gates/pr_reference.py:60-64), 같은 파일 주석은 phase-1 에서 "Closes/Fixes/Resolves는 금지"라고 적는다(gates/pr_reference.py:22-23). 이 불일치의 성격은 phase 2 에서 판정한다.
