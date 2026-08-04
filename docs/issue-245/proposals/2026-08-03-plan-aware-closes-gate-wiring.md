files:
- docs/issue-245/reports/implementation/survey.md
- docs/issue-245/reports/implementation/scout-brief.md
- docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md

## Request
issue #245: `gates/pr_reference.py`의 계획-인지 Closes 게이트 판정 로직은 정확하지만(#228), 어떤 경로도 병합 전에 그것을 강제로 실행하지 않는다 — 브랜치 보호 없음(404), 필수 상태체크 0개, `spawn.py:1071`의 자동 호출자가 `pr`/`issue`를 안 넘겨 `pr_reference.check`에 닿지도 못한다. phase-1 브랜치의 "Closes/Fixes/Resolves 금지" 규칙도 에러 메시지만 있고 기계적 검사가 없다(문서-검사 불일치). 요구: (1) 병합 전에 강제로 도는 배선을 만들고 후보 (a)/(b)/(c)의 커버리지 차이(사람이 직접 만든 PR도 잡는가)를 명시해 고를 것, (2) phase-1 금지 규칙도 같은 배선에 태울 것, (3) 배선 자체의 회귀(미완 스텝 이슈 + closing 키워드 PR이 실제로 머지 불가)를 실물/동형 환경에서 확인할 것. `gates/pr_reference.py`의 판정 로직 자체는 무변경(#228 소유). 두-계정/단일-계정 양쪽에서 성립해야 한다.

## Constraints
- `gates/pr_reference.py`의 `check_body`/`check` 판정 로직은 무변경 — phase1 mismatch를 고치더라도 이 파일 밖(오케스트레이션 계층)에서 해결한다.
- 단일-계정 모드(이 저장소의 실사용 기본값 — 승인은 이슈 코멘트 `APPROVE issue-<n>/<role>`)와 두-계정 모드(PR 리뷰 Approve 추가 경로) 양쪽에서 성립해야 한다 — 새 배선이 PR-리뷰 기반 신호에 의존하면 단일-계정 모드에서 무의미해진다.
- phase 1: 조사·제안만. 코드/워크플로/브랜치 보호 설정 변경 없음. 이 PR 본문은 `#245`만 담고 Closes/Fixes/Resolves는 쓰지 않는다.
- main 브랜치 보호 활성화는 이미 가동 중인 자동화 파이프라인(스폰/승인 흐름)에 영향을 주는 공유 인프라 변경 — 되돌리기 어려움. phase 2 실행 자체가 계약 v3 s19의 사람 승인 게이트를 통과해야 하는 것과 별개로, 이 변경의 파급(모든 향후 PR이 즉시 필수 체크 대상이 됨)을 제안 단계에서 명시한다.

## Rationale
후보 (a) 브랜치 보호+필수 상태체크, (b) gh-guard 계열 세션 훅에서 PR 본문 검사, (c) `spawn.py` 자동 호출자에 `pr`/`issue` 배선 + 차단화 — 세 후보를 조사했고 커버리지가 근본적으로 다르다. (a)를 채택(adopted)하고, (b)와 (c)는 아래 이유로 각각 기각(rejected)한다.

대안 (b)(rejected — considered and rejected): `gh-guard.sh`(`tokenmaxxxer-core/core/hooks/gh-guard.sh`)는 `PreToolUse` 훅으로 Claude Code CLI 세션 자신의 tool-call payload에서만 작동한다 — 이 harness의 모든 훅이 그렇듯, 사람이 github.com 웹 UI에서 직접 PR 본문을 고치거나 Merge 버튼을 누르는 행위는 훅의 트리거 표면 자체를 거치지 않는다(git-scm.com 문서, pre-commit/pre-commit-hooks#303 커뮤니티 확인). 이슈 본문이 요구하는 "사람이 직접 만든 PR도 잡는가" 기준에서 (b)는 명백히 실패한다 — 커버리지가 "에이전트 세션이 만든 PR"로 좁혀진다. 실물 사건(issue #228 §3(d))의 PR #237도 어차피 세션이 만든 PR이었으므로 (b)만으로 그 사건 하나는 막았을 수 있지만, repo-status-board 파일럿의 추가 사례(2026-08-03, PR #26의 백틱 인용까지 GitHub이 파싱해 이슈를 또 닫은 사건)처럼 사람의 개입이나 GitHub 자체의 예상 밖 파싱이 섞이는 경로는 (b)로 원천 차단이 안 된다. 이런 한계 때문에 (b) 단독안은 기각(rejected)한다.

대안 (c)(rejected — considered and rejected instead of relying on it alone): `spawn.py`의 `gate_report()`는 `_spawn_one()` 안에서 `proc.wait()`(세션 종료) 이후, `ensure_pushed()`(실제 `gh pr create`) 이후에 돈다 — 구조적으로 이미 PR이 존재할 수 있는 시점이라 막을 지점을 지났다. `pr`/`issue` 배선을 고치고 호출 시점을 `ensure_pushed()` 이전으로 옮기더라도, 그 시점엔 아직 PR 번호가 없어 `pr_reference.check()`가 요구하는 `gh pr view`를 할 수 없다(로컬 diff 기반 사전검사로 바꿔야 하는 별도 설계가 필요 — 조사에서 확인한 미해결 지점). 게다가 (c)는 spawn.py 프로세스가 도는 그 순간에만 유효해서, PR이 만들어진 뒤 사람이 본문을 나중에 고쳐 Closes를 추가하는 경로는 애초에 다루지 못한다 — (b)와 같은 세션-표면 한계를 공유하면서 커버리지는 오히려 더 좁다. 이 이유로 (c) 단독안도 기각(rejected)한다.

(a)를 택한다(adopted, rather than (b) or (c) alone): 필수 상태체크는 GitHub 서버사이드에서 PR/브랜치 상태 자체에 대해 평가되어 병합 경로(웹 UI 버튼, `gh pr merge`, API 직접 호출) 와 무관하게 동일하게 적용된다(GitHub Docs). 유일한 우회는 관리자 권한(`gh pr merge --admin` 등)인데, 이는 브랜치 보호 규칙의 "Do not allow bypassing the above settings"를 켜면 닫힌다(GitHub Docs, 커뮤니티 확인). 이 저장소는 `.github/workflows` 자체가 없는 그린필드라 신설 비용이 들지만, 그 비용을 대가로 이 이슈가 요구하는 "사람이 직접 만든 PR도 잡는가"를 유일하게 충족하는 후보다. 머지 큐/Mergify류 대안도 검토했으나 기각(rejected)한다 — 그 도구들이 푸는 문제(동시 병합 간 시맨틱 충돌)는 이 저장소처럼 낮은-동시성 단일 저장소에는 해당하지 않아 과잉설계다.

phase1 불일치(요구사항 2)는 `pr_reference.py`를 안 건드리는 선에서, `gates/ci.py`(오케스트레이션 계층)에 phase1일 때 `pr_reference._CLOSES_REF`(이미 `closure_sweep.py`가 같은 방식으로 재사용 중인 공개 정규식)로 closing 키워드 존재 여부만 추가로 검사하는 소규모 신규 체크를 얹는 방향을 phase 2 설계로 제안한다 — `check_body`의 판정 로직 자체는 무변경.

## What will be done
- (완료, 이 제안 자체) 5개 조사 앵글 병렬 수행 결과를 `docs/issue-245/reports/implementation/survey.md`에 기록.
- (완료) 외부 선례(GitHub 브랜치 보호 시맨틱, 대안 비교)를 `docs/issue-245/reports/implementation/scout-brief.md`에 기록.
- (이 문서) 후보 비교와 선택을 기록, phase 2 승인 대기.
- phase 2(사람 승인 후)에서 할 일의 설계 방향만 여기 명시(실행은 phase 2):
  - `.github/workflows/`에 `gates/ci.py --pr <n> --issue <n> --phase <phase1|phase2>`를 `pull_request` 이벤트에서 실행하는 워크플로 신설.
  - `gates/ci.py`에 phase1용 closing-키워드 존재 검사(신규, `pr_reference.py` 비변경)를 추가해 요구사항 2 해소.
  - main 브랜치 보호 규칙에 그 체크를 필수로 등록 + "Do not allow bypassing" 활성화.
  - 회귀 확인: 미완 스텝 이슈를 참조하는 closing-키워드 PR을 실물 또는 동형 테스트 저장소에서 만들어 실제 머지 차단을 확인(요구사항 3) — 프로덕션 `main`에서 직접 실험하지 않는다.

## Out of scope
- `gates/pr_reference.py`의 판정 로직 변경(#228 소유, 제약사항).
- (b)/(c) 배선을 아예 안 만드는 것은 아니다 — 방어 심층화(defense-in-depth)로 나중에 추가할 여지는 남기되, 이번 phase 2 최소 배선의 필수 요건으로는 포함하지 않는다(각각 커버리지가 (a)의 부분집합이라 (a) 없이는 이슈의 핵심 요구를 못 채움).
- 머지 큐/Mergify 등 큐잉 도구 도입.
- 브랜치 보호 규칙을 실제로 켜는 작업(코드 변경이 아니라 GitHub 설정 변경) 자체 — phase 2에서 사람 승인 후 수행.

## How you'll know it worked
- phase 1: 이 PR이 `#245`만 본문에 담고(Closes/Fixes/Resolves 없음) 승인자(`docs/specs/approvers.md`)의 `APPROVE issue-245/implementation` 코멘트(또는 두-계정 모드의 PR 리뷰 Approve)로 phase 2가 열린다.
- phase 2 완료 시: 미완 스텝 이슈를 참조하고 closing 키워드를 담은 테스트 PR이 필수 상태체크 실패로 병합 버튼이 잠기는 것을 실물 확인 — 관리자 우회도 막혀 있는지 별도 확인. phase1 PR에 closing 키워드가 섞이면 같은 체크가 잡는 것도 확인.
