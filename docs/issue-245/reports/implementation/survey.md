# Survey: 계획-인지 Closes 게이트 강제 배선 부재 (issue #245)

## 조사 범위와 방법
5개 앵글 병렬 조사(freelunch 리서치 위드 5) + 실측 확인(`gh api`, `ls .github`). 요약 아래.

## 1. `gates/pr_reference.py` — 판정 로직 (변경 금지 대상, #228 소유)
- `check_body(issue, body, phase, plan=None)` (28-62행): 순수 함수.
  - phase2 분기(39-56행): `_CLOSES_REF` 매치 + plan 미완료 스텝 있으면 위반(계획-인지, #228/#189 계약).
  - phase1 분기(57-62행): `_PLAIN_REF`(평문 `#N`)만 확인. **에러 메시지는 "Closes/Fixes/Resolves 금지"를 주장하지만(59-61행) 실제로는 closing 키워드 부재를 검사하지 않는다** — `"Closes #126"` 도 `_PLAIN_REF`에 걸려 통과한다.
- `check(repo, pr, issue, phase)` (85-102행): `gh pr view`/`gh issue view` 로 본문을 읽어 `check_body`에 위임. 실패 시 fail-closed.
- `main()` (105-123행): CLI, `python3 gates/pr_reference.py <pr> <issue> [phase1|phase2] [--repo <path>]`, exit 0/1. `python -m` 형태 없음.
- 호출자: `test_gates.py`(단위테스트만), `gates/closure_sweep.py`(정규식만 재사용, "reports only, closes nothing"), `gates/ci.py`(아래).
- 단일/두-계정 개념 없음 — 이 모듈은 approvers.md 를 전혀 참조하지 않는다.

## 2. `gates/ci.py` — 오케스트레이션 계층
- `check(repo, pr=None, issue=None, phase=None)`: `pr`·`issue` 가 **둘 다 not None** 일 때만 `pr_reference.check()` 호출(48-53행). 하나라도 없으면 조용히 스킵(자체 문서화된 opt-in, 13-17행).
- 어떤 `.github/workflows/*.yml` 도 이 스크립트를 `--pr --issue` 로 호출하지 않는다 — 그런 워크플로 자체가 없다(§5).

## 3. `spawn.py` — 자동 호출자와 그 위치
- `gate_report(cwd)` (1054-1075행)이 `ci.check(Path(cwd).resolve())` 를 호출 — **`pr`/`issue` 인자 없음**, 확인됨. 따라서 `ci.check()`의 가드가 항상 스킵 분기를 타 `pr_reference.check`에 닿지 않는다.
- `gate_report` 자신의 독스트링이 명시: "막지는 않는다. 세션이 끝난 뒤라 되돌릴 수 없고…" — 반환값은 stderr 출력과 ledger 기록에만 쓰이고 제어흐름에 전혀 관여하지 않는다(2924, 2928-2929행).
- 호출 시점(`_spawn_one()`, 2882행)은 **`proc.wait()`(세션 종료, 2848행) 이후, `ensure_pushed()`(실제 `gh pr create`/push 수행, 2881행) 이후** — 즉 PR이 이미 존재할 수 있는 시점에서야 돈다. 막을 지점이 이미 지나갔다.
- 대조: 같은 함수 안에 있는 `_acquire_spawn_claim()`(issue-223/PR#249, a30f56c 추가)은 세션 시작 *전에* `return 1`로 실제로 막는다 — spawn.py에 차단 패턴 자체는 이미 존재하지만 게이트 결과에는 적용되지 않았다.
- spawn.py는 role 세션과 별도 프로세스(부모 오케스트레이터)이며, `ensure_pushed`(PR 생성)는 spawn.py 자신의 프로세스에서 샌드박스 아웃바운드 릴레이로 실행된다.

## 4. 기존 훅 인프라 — gh-guard 계열과 PreToolUse 게이트
- `proposal-shape-gate.sh`/`record-shape-gate.sh`/`survey-order-gate.sh`: `PreToolUse`, matcher `Write|Edit|MultiEdit` — 파일쓰기 도구에만 반응, `Bash`(=`gh`/`git`)는 못 본다.
- `gh-guard.sh`(`tokenmaxxxer-core/core/hooks/gh-guard.sh`, 125행): `PreToolUse`, matcher `.*` — 모든 도구 호출에서 실행되고 내부에서 `Bash` 페이로드 중 `gh|git|curl|wget|http(s)://` 포함 여부로 자체 필터링. `CLAUDE_ROLE` 세션 한정으로 사람 전용 행위(`gh pr review --approve`, `pr merge/close/reopen`, `issue create/close/...`, `main`으로의 `git push` 등)를 차단하지만, **PR 본문 내용을 검사하는 규칙이 전혀 없다** — Closes 키워드 검사는 오늘 존재하지 않는, 새로 추가해야 하는 규칙이다.
- 문서화된 한계(테스트 스위트에 의도적으로 남긴 gap-c/gap-d): 명령어 텍스트만 매치 — 스크립트 파일 실행, 다른 도구(Write)로 같은 페이로드 작성, 키워드 회피 텍스트는 통과.
- **결정적 한계: 이 harness의 어떤 훅도 Claude Code CLI 세션의 자체 tool-call 밖에서는 아무 도달력이 없다.** 사람이 github.com 웹 UI에서 직접 PR 본문을 수정하거나 Merge 버튼을 누르는 행위는 이 훅들의 트리거 표면(tool-call payload) 자체를 거치지 않는다.
- 저장소 자체엔 `.claude/settings.json` 없음 — 배선은 전부 플러그인 `hooks.json`에 있다.

## 5. 실측 확인 — 브랜치 보호·CI 상태
- `.github/` 디렉터리 자체가 없음(`ls .github` → No such file or directory). 워크플로 0개.
- `gh api repos/tokenmaxxxer/on-the-record/branches/main/protection` → **404** `Branch not protected` (오늘 재확인, issue #245의 주장과 일치).

## 6. 실물 사건 — issue #228 execution-observation §3(d)
- PR #237 머지(06:15:33Z) — 게이트 로직은 이미 main에 있었음(05:52:50Z 머지). issue #235는 `- [ ] step 1`, `- [ ] step 2` 모두 미완인 채 `Closes #235`로 자동 종결(06:15:35Z), 사람이 수동 재오픈(06:16:22Z).
- 원인 A(워크스페이스 staleness) — issue #221이 고쳤음(확인).
- **원인 B(더 결정적) — 강제 실행 경로 자체가 없음**: 브랜치 보호 없음 + 필수 상태체크 0개 + `spawn.py:1071` 자동 호출자 미배선. issue #221이 랜딩해도 원인 B는 남는다(issue #228 F-3에 명시).
- F-4: plan 체크박스가 기계적으로 갱신되지 않아 "마지막 스텝만 Closes 허용" 절반도 실제로 작동한 적이 없다.

## 7. 승인 모드 — `docs/specs/approvers.md` + `docs/handbooks/operations.md:312-316`
- `approvers.md`는 계정 목록(2줄, JiwonJung94/jjongkwann)만 담고 있고, 실제 규칙은 handbook에 있음.
- **단일-계정(기본, 이 저장소 전 사례 관측)**: 승인 = 이슈 코멘트 정확히 `APPROVE issue-<n>/<role>`.
- **두-계정(하드닝)**: 별도 계정의 PR 리뷰 Approve도 추가 경로로 허용.
- `gates/pr_reference.py`는 이 구분을 전혀 참조하지 않음 — 승인 흐름과 병합-차단 게이트는 별개 관심사이나, #245의 제약("두 모드 모두에서 성립")은 새 배선이 PR-리뷰 기반 신호에 의존해선 안 된다는 뜻으로 해석됨(단일-계정 모드엔 그런 신호가 아예 없으므로).

## 8. `docs/decisions/` 선례
- CI/브랜치보호 관련 선례 없음(그린필드).
- 관련 철학적 선례: `2026-07-29-permanently-closed-alternatives.md` — "모델을 스케줄러로 쓰는 설계는 기각됨", "게이트를 강제하는 훅은 훅으로 남아야 하고 모델 자신의 판단이 되면 안 된다" — 결정론적 외부 강제를 선호하는 이 저장소의 기존 방향과 일치.

## 9. 확실히 만질 write set (예상)
- `docs/issue-245/reports/implementation/survey.md` (본 파일)
- `docs/issue-245/reports/implementation/scout-brief.md`
- `docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`
- (phase 2, 승인 후에만) 후보 (a) 채택 시: 신규 `.github/workflows/*.yml`, 브랜치 보호 설정(코드 아님, GitHub 설정 API 호출), `gates/ci.py`에 phase1 mismatch를 잡는 소규모 신규 검사 추가(가능하면 `pr_reference.py`는 무변경 유지 — `_CLOSES_REF`를 재사용만).

## 10. 미해결 질문 (phase 2로 이월)
- CI 워크플로가 PR body에서 issue 번호와 phase 를 어떻게 뽑아낼지(현재 `gates/ci.py`는 호출자가 명시적으로 `--pr --issue --phase`를 줘야 함).
- 후보 (c)를 병행 채택할 경우, `ensure_pushed()` 이전 시점엔 아직 PR 번호가 없어 `pr_reference.check()`가 요구하는 `gh pr view` 를 못 한다 — 로컬 diff/브랜치 상태 기반 사전검사로 바꿔야 하는지 여부.
- main 브랜치 보호를 이 저장소(이미 운영 중인 자동화 파이프라인)에 적용하는 작업 자체가 공유 인프라에 대한 되돌리기 어려운 변경이므로, phase 2 실행 전 사람 승인 필요(승인 게이트 자체는 계약 v3 s19가 이미 요구).
