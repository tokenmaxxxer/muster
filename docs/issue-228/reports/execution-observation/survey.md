---
role: execution-observation
issue: 228
phase: 1
kind: current-state-survey
loop_state: surveying
---

# 현재 상태 조사 — issue #228, 관측 대상 role `implementation`

## 관측 범위 (누가/어느 세션/어느 이슈/어느 PR)

- **관측 대상 role**: `implementation` (issue #228 실행 계획 step 1).
- **관측 대상 세션의 산출물**: PR **#231** <https://github.com/tokenmaxxxer/on-the-record/pull/231>, delivery 커밋 **923416d** (`923416da059dd43c4268641201fd33056bf8f282`), 부모 **2c84417**, 브랜치 팁 **016420f**, main 으로의 머지 커밋 **1fc8e96** (mergedAt `2026-08-03T05:52:50Z`).
- **관측 대상 role 의 자기 기록**: `docs/issue-228/reports/implementation.md` (frontmatter `loop_state: landed`, `code_under_review: 923416d`, implementation.md:1-3).
- **관측 주체**: 이 문서의 저자 role `execution-observation`, 브랜치 `issue-228/execution-observation`, 이슈 #228 실행 계획 step 2.
- 범위 밖: 이슈 #235/#236/#237/#238/#221 은 **판정 대상이 아니라** step 2 지시가 요구한 실물 검증(각도 d)의 증거로만 읽었다.

## 이 세션에서 실제로 읽은 것 (2차 요약이 아님)

| 아티팩트 | 어떻게 읽었나 |
|---|---|
| issue #228 본문·코멘트 | `gh issue view 228` / `--comments` |
| PR #231 본문·머지 메타 | `gh pr view 231`, `gh pr diff 231` |
| 커밋 923416d 전체 diff | `git show 923416d`, `git show --stat 923416d` |
| 변경 전 소스 | `git show 923416d^:gates/pr_reference.py`, `git show 923416d^:gates/ci.py` |
| implementation 자기 기록 | `docs/issue-228/reports/implementation.md` |
| implementation phase-1 산출 | `docs/issue-228/proposals/implementation.md`, `docs/issue-228/reports/implementation/survey.md`, `docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md` |
| 실물 사건 | issue #228/#235/#236 timeline API, PR #233/#234/#237/#238, issue #221 본문, `spawn.py` 워크스페이스 재사용 경로 |
| 승인 상태 | `docs/specs/approvers.md`, `gh pr list --head issue-228/execution-observation --state all`, #228 코멘트 API |

관측 대상 role 의 코드·테스트는 **한 번도 실행하지 않았다**. 모든 동작 판단은 커밋 blob 정독으로만 얻었다(역할 금지사항: 관측 대상 작업의 재실행 금지). 이 제약이 각도 (a)에 남긴 잔여 불확실성은 아래 U-1 에 적었다.

## 이슈가 요구한 4건 (본문 원문)

1. "미완 스텝(`- [ ]`)이 남아 있으면 … 닫는 키워드를 phase-2 PR 본문에서 **요구하지 않고 오히려 차단**한다. 마지막 스텝의 phase-2 PR에서만 요구한다." (issue #228 본문 L16)
2. "계획이 없는 이슈(단일 스텝)는 현행 동작을 유지한다 — `Closes` 요구." (issue #228 본문 L17)
3. "키워드 탐지는 **백틱/코드펜스 안 인용도 GitHub이 파싱한다**는 점을 반영한다 … 인용했으니 안전하다고 가정하지 않는다." (issue #228 본문 L18)
4. "판정에 필요한 계획 상태는 이미 `gates/flows.py`의 `_plan_from_body`가 파싱한다 — 재구현하지 말고 재사용한다." (issue #228 본문 L19)

실행 계획은 본문 L31-34: `- [ ] step 1  implementation`, `- [ ] step 2  execution-observation` (두 칸 모두 미체크 상태로 관측됨).

## 보드(main)의 현재 상태

- `git rev-parse HEAD main` → 둘 다 `d187559` — 이 브랜치는 main 과 동일하고 **고유 커밋 0개**. `docs/issue-228` 아래 파일은 4개뿐이며 전부 implementation role 산출이다(`git ls-files docs/issue-228`).
- `docs/issue-228/reports/execution-observation.md` 는 **존재하지 않는다**. 이 role 의 phase-1 산출(이 파일 포함)도 이 세션 이전에는 없었다.
- `gates/ci.py` 는 이 저장소의 유일한 CI 진입점이며, `--phase` 로직을 건드린 커밋은 923416d **단 하나**다(`git log -S"--phase" -- gates/ci.py`).
- `.github/workflows` 는 **비어 있다** — `git ls-files .github/workflows` 무출력. main 에 브랜치 보호도 없다(`gh api .../branches/main/protection` → 404 "Branch not protected"). 즉 게이트는 GitHub 이 강제하는 머지 전 체크가 아니라 사람이/역할이 손으로 돌리는 스크립트다.

## 게이팅 상태 (계약 v3 s19)

- `docs/specs/approvers.md` 에 등재된 계정: `JiwonJung94`, `jjongkwann` (approvers.md:1-2).
- 경로 (a) PR review Approve: 이 브랜치에서 나간 PR 이 아직 없으므로 리뷰 자체가 존재하지 않는다.
- 경로 (b) 단일 계정 모드: #228 의 코멘트는 1건이고 본문 전체가 `APPROVE issue-228/implementation` (jjongkwann, <https://github.com/tokenmaxxxer/on-the-record/issues/228#issuecomment-5161635406>). 요구되는 정확문자열 `APPROVE issue-228/execution-observation` 과 **일치하지 않는다**.
- 따라서 이 세션은 phase 1 이다. 기록 파일 `docs/issue-228/reports/execution-observation.md` 는 승인 후 phase 2 에서 쓴다. 이 세션은 phase-1 두 집에만 쓴다.

## step 1 이 이미 결론지은 것 (중복 조사 방지용)

implementation 자기 기록 기준: `check_body(issue, body, phase, plan=None)` 신설로 미완 스텝이 2개 이상이거나 남은 1개가 마지막이 아니면 closing 키워드를 차단하고, 그 외에는 기존 require-Closes 를 유지한다(implementation.md:43-50). `gates/ci.py` 는 `pr`·`issue` 가 모두 주어졌을 때 명시적 `--phase` 를 요구하도록 바꿨다(implementation.md:51-55). 테스트 241 통과·1건은 사전 존재하던 샌드박스 실패(implementation.md:4-19). 자체 hunt 는 `if plan:` 이 `None`(계획 없음)과 `[]`(헤더는 있으나 유효 스텝 0)를 같은 값으로 뭉갠다는 비차단 findings 1건을 남기고 미수정으로 넘겼다(implementation.md:100-127).

## 조사로 드러난 write surface 와 미지 (proposal 이 겨눌 지점)

- **S-1 (각도 a)** 신규 테스트 9건의 변경 전 실패 근거가 두 갈래로 갈린다 — 시그니처 arity(변경 전 `check_body` 는 3-파라미터, 923416d^ gates/pr_reference.py:26) 때문에 호출 자체가 불가능한 8건과, 순수 로직/단언으로 갈리는 1건(`ci.check` 무 `--phase`, 923416d test_gates.py:1044). 이 구분이 "실제로 실패하는지"의 답을 좌우한다.
- **S-2 (각도 b)** 변경 전 `--phase` 생략은 "검사 없음"이 아니라 **다른 약한 검사**(phase1 분기)로 조용히 떨어지는 형태였다(923416d^ gates/ci.py:44,90 → gates/pr_reference.py phase1 분기).
- **S-3 (각도 c)** 923416d 가 새로 만든 fail-closed 경로는 두 곳(`gates/ci.py:49-51`, `gates/pr_reference.py:98-100`)이고, 둘 다 `--pr`/`--issue`/`--phase` 를 넘기는 호출 형태에서만 발동한다. 저장소 안에 그 호출 지점이 없다는 점(위 workflows 부재)이 위해 평가의 전제가 된다.
- **S-4 (각도 d)** #235 는 PR #237 머지(`06:15:33Z`) 직후 `06:15:35Z` 에 closed 로 기록됐다가 재오픈됐고, 재오픈 코멘트가 원인을 #221 재사용 워크스페이스 미동기화로 지목한다(<https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162962921>). `spawn.py:2372-2375` 는 재사용 시 `git fetch -q origin` 만 하고 로컬 브랜치를 `origin/<br>` 로 맞추지 않는다.
- **S-5 (범위 밖 관측, 판정 유보)** PR #238 은 phase-1 산출만 담은 PR 인데 본문에 closing 키워드가 있었고 issue #236 은 `06:15:17Z` 에 CLOSED/COMPLETED 로 기록돼 있다(PR #238; issue #236). 923416d 가 main 에 들어간 뒤 시각이다.
- **U-1 (미지)** 테스트 실행이 금지돼 있으므로 "9건이 변경 전에 실패한다"는 명제는 blob 정독에서 연역할 수 있는 범위까지만 확정된다. 각 테스트가 어떤 근거로 실패하는지(arity 대 로직)를 나눠 적는 것이 이 제약 아래 가능한 최대 해상도다.
- **U-2 (미지)** 저장소 밖 오케스트레이터가 `--pr --issue --phase` 를 넘기는지는 이 저장소 내용만으로 확인 불가.

## scout

이 조사가 드러낸 미지(S-1의 판별 기준, S-3의 위해 평가 기준, S-4의 사건 귀속 기준)를 겨냥해 scout 을 실행했다. 결과는 `scout-brief.md`.
