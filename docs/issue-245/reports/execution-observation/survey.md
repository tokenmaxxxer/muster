---
name: execution-observation-survey
kind: survey
---

# 현재-상태 조사 — issue #245 step 2 (execution-observation) 관찰 대상 확정

phase 1. 판정 없음 — 무엇을 관찰 대상으로 확정했고, 그 대상의 현재
상태가 실측으로 어떠하며, 어떤 지점이 아직 확인되지 않았는지만 적는다.

## 1. 관찰 대상 (역할·세션·이슈·PR 번호 명시)

- **이슈**: #245 "계획-인지 Closes 게이트가 자문 스크립트일 뿐 강제 배선이
  없다" (state OPEN, 실행 계획 `- [ ] step 1 implementation` /
  `- [ ] step 2 execution-observation` 둘 다 미완 — `gh issue view 245`,
  2026-08-04 02:53Z 확인).
- **관찰 대상 역할**: `implementation` (issue #245 실행 계획 step 1).
- **관찰 대상 세션**: 그 역할의 phase-2 세션 — 브랜치
  `issue-245/implementation`, 커밋 `b3ba234`
  (`issue-245: phase 2 - closes-only required-check wiring
  (branch-protection activation handed to human)`,
  committedDate 2026-08-04T02:00:37Z). 같은 브랜치의 phase-1 커밋은
  `a8cddd9` (2026-08-03T11:11:31Z).
- **관찰 대상 PR**: **#257** (MERGED, mergedAt 2026-08-04T02:04:01Z,
  author jjongkwann, reviews 배열 비어 있음 — 승인은 이슈 코멘트
  `APPROVE issue-245/implementation` 단일-계정 경로).
  https://github.com/tokenmaxxxer/on-the-record/pull/257
- **관찰 대상 아님(경계)**: 이 조사는 `gates/pr_reference.py`의 판정
  로직(#228 소유, 이번 PR 무변경)을 재검토하지 않는다. 관찰 대상
  역할의 코드를 재실행하지도 않는다.

## 2. 이번 세션에 실제로 읽은 것 (RESEARCH 근거)

| 아티팩트 | 읽은 방법 |
|---|---|
| 이슈 #245 본문 + 코멘트 | `gh issue view 245` / `--comments` |
| PR #257 메타데이터(본문·커밋 SHA·파일 목록·reviews·mergedAt) | `gh pr view 257 --json ...` |
| PR #257 발주자 피드백 코멘트 2건 | `gh pr view 257 --comments` |
| 관찰 대상 역할의 기록 `docs/issue-245/reports/implementation.md` (417행) | 파일 직접 |
| 승인된 제안 `docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md` | 파일 직접 |
| 결정 기록 `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md` (134행) | 파일 직접 |
| `b3ba234`의 `gates/ci.py` diff, `.github/workflows/plan-aware-closes-gate.yml` diff | `git show b3ba234 -- <path>` |
| main 브랜치 보호 현재 상태 | `gh api repos/tokenmaxxxer/on-the-record/branches/main/protection` |
| 검증 PR #263 (statusCheckRollup, 코멘트, 본문, closedAt) | `gh pr view 263 --json ...` |
| 검증 PR #263의 CI 잡 로그 2건 (job 91872249829 / 91878584150) | `gh run view --log --job <id>` |

관찰 대상 역할의 코드를 재실행하지 않았고, 현재 `gates/ci.py` 파일을
"무슨 일이 있었는가"의 증거로 읽지 않았다 — 증거는 `b3ba234`의 diff.

## 3. 현재 상태 (실측)

**(a) 랜딩된 변경** — PR #257 files 목록(9개): `.github/workflows/plan-aware-closes-gate.yml`
(+49, 신규), `gates/ci.py` (+136/-5), `gates/test_closes_gate_ci.py`
(+173, 신규), `docs/handbooks/operations.md` (+32),
`docs/issue-245/decisions/...` (+134, 신규), `docs/issue-245/reports/implementation.md`
(+417, 신규), phase-1 산출물 3개.

**(b) 브랜치 보호 — 현재 켜져 있음.** `gh api .../branches/main/protection`
(2026-08-04 02:53Z): `required_status_checks.contexts: ["closes-gate"]`,
`checks: [{context: "closes-gate", app_id: 15368}]`, `strict: false`,
`enforce_admins.enabled: true`, `allow_force_pushes: false`,
`allow_deletions: false`. 이슈 본문이 "404"라고 기록한 상태에서 바뀌었다.
활성화 행위 자체는 PR #257 에 담기지 않았다 — 기록
`docs/issue-245/reports/implementation.md:90-141` ("What was NOT done")이
사람에게 넘긴다고 적고 절차를 남겼다.

**(c) 검증 PR #263** (`throwaway: closes-gate 활성화 검증 (머지 금지)`,
head `issue-224/closes-gate-verify`, createdAt 2026-08-04T02:06:44Z,
state CLOSED, mergedAt null, closedAt 2026-08-04T02:51:33Z). CI 실측 2건:

- FAILURE — job 91872249829, startedAt 02:06:49Z / completedAt 02:06:55Z.
  로그 실물: `PR_NUMBER: 263` → `게이트 차단:` / `- 계획에 미완 스텝이
  남아 있다 — 마지막 스텝의 phase-2 PR에서만 Closes/Fixes/Resolves를
  쓴다.` → `Process completed with exit code 1`.
- SUCCESS — job 91878584150, startedAt 02:50:43Z / completedAt 02:50:49Z.
  로그 실물: 같은 커맨드라인, `게이트 통과`.
- PR #263 코멘트(02:51:32Z, jjongkwann): "closing 키워드 + 미완 계획
  이슈 → closes-gate FAILURE + merge BLOCKED 실측, 키워드 제거 →
  SUCCESS + CLEAN 실측. 브랜치 보호(필수 체크 closes-gate,
  enforce_admins) 정상 작동 확인."
  https://github.com/tokenmaxxxer/on-the-record/pull/263#issuecomment-5174045441

**(d) 발주자 피드백 2건** (PR #257 코멘트, 승인과 별도): (1) 본문 추출
실패 시 fail-open/closed 를 정하고 트레이드오프 기록, (2) 관리자 우회
차단을 단일-계정 모델 관점에서 정당화 + 잔여 우회 표면 분석. 대응
문서는 `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`
§1(fail-closed 채택, 양방향 비용 기재) / §2(두 승인자 계정 모두
`admin: true` 실측, gh-guard.sh 미커버 경로 2개, 잔여 표면 = 보호 규칙
자체 편집).

**(e) 승인된 제안에서의 이탈**: 제안(`...-plan-aware-closes-gate-wiring.md:31`)은
워크플로가 `gates/ci.py --pr <n> --issue <n> --phase <...>` 전체 번들을
돌리는 설계였고, 랜딩된 워크플로는 `--autodetect --closes-only`
(`b3ba234` 워크플로 파일 마지막 줄)다. 이유는
`docs/issue-245/reports/implementation.md:143-167, 200-226`에 기재
(`gates/gates.py`의 `_always_writable()` 제안-파일 패턴 불일치로 번들
전체를 필수화하면 자기 잠금).

## 4. 쓰기 표면과 아직 확인 안 된 지점 (scout 조준점)

이 역할의 쓰기 표면은 `docs/issue-245/reports/execution-observation.md`
(phase 2) 와 `docs/issue-245/reports/execution-observation/`,
`docs/issue-245/proposals/` (phase 1) 뿐이다. 관찰 대상의 어떤 파일도
고치지 않는다. 아직 확인 안 된 지점:

- **G1 (도달성)**: `b3ba234`의 `gates/ci.py` diff 에서 `_phase1_mismatch`
  는 `phase == "phase1"` 분기 안에서만 호출되고, `--autodetect` 경로의
  `_phase_from_body`는 그 이슈를 향한 closing 키워드가 있으면 `"phase2"`
  를 돌려준다. 요구사항 2(phase-1 Closes 금지의 기계 검사)가 CI 배선
  경로에서 실제로 도달 가능한 상태인지 아직 확인되지 않았다.
- **G2 (범위 축소)**: 필수 체크를 `--closes-only`로 좁힌 이탈이 이슈
  요구사항 대비 어디까지를 덮고 어디를 안 덮는지, 그 판단 근거가 기록에
  어떻게 남았는지.
- **G3 (강제력 검증의 충분성)**: PR #263 의 양방향 실측이 "필수 체크가
  실제로 머지를 막는다"의 증거로서 무엇을 덮고 무엇을 안 덮는지 —
  이런 변경 부류(필수 상태체크 신설 + 브랜치 보호 활성화)를 강하게
  감사할 때 통상 무엇을 더 보는지가 아직 조사되지 않았다.
- **G4 (경로/책임 경계)**: 요구사항 3의 "실물 확인"을 관찰 대상 역할이
  아니라 사람이 실행했다는 사실이 outcome/trajectory 판정에서 어떻게
  다뤄져야 하는지 — 기록이 그 이월을 어떻게 예고했는지는 (3)(b)에
  있으나, 이월 자체의 타당성 기준은 아직 세우지 않았다.
