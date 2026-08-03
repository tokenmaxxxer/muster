# Scout Brief: 병합 게이트 강제 배선 (issue #245)

- 범위: non-product 엔지니어링 결정(머지 게이트 강제 배선) — "최고 수준 사례"는 GitHub 저장소의 병합 보호 관행.
- 진행: 5개 앵글 병렬 스윕(내부 4 + 외부 1), 1 라운드로 포화 판단(외부 앵글 결과가 issue 본문의 3개 후보와 정확히 대응해 추가 딥닝 불필요) — judge point 1에서 STOP. 병렬 Agent-tool dispatch 사용(배치-순차 아님).

## Must-bes (카테고리 필수 요건)
- 병합 차단은 actor-무관해야 한다 — 사람이 웹 UI로 직접 병합해도 걸려야 진짜 게이트다(git-scm.com, pre-commit/pre-commit-hooks#303: 클라이언트 훅은 웹 UI 병합을 절대 못 본다).
- "required" 로 만들려면 (1) 워크플로 파일 + (2) 브랜치 보호 규칙에 그 체크 이름 등록, 두 가지 다 필요(GitHub Docs).
- 관리자 우회 구멍은 "Do not allow bypassing" 로 명시적으로 닫아야 한다 — 기본값은 admin 이 빠져나간다(GitHub Docs, `gh pr merge --admin`).

## 성능 축
- 커버리지(actor/경로 무관 여부), 우회 난이도, 신설 인프라 비용(이 저장소는 `.github/workflows` 자체가 없음 — 그린필드).

## Adopt / Skip
- Adopt: 서버사이드 필수 상태체크 + 브랜치 보호(범위가 이 이슈의 요구와 정확히 일치, 저장소 규모에 비례).
- Skip: 머지 큐/Mergify/bors-ng 류 — PR 동시성 낮은 단일 소규모 저장소엔 과잉설계(mergify.com, lobste.rs 논의).

## Segment fit
이 저장소는 저-트래픽 단일 저장소, 병합 대부분이 자동화 세션 1개가 순차 처리 — 큐잉 기능이 필요한 세그먼트가 아니다.

## Gap line
현재 상태가 이미 충족: 판정 로직 자체(`gates/pr_reference.py`)는 이미 정확함(#228). 누락: (1) 서버사이드 필수 체크 없음 — 액터 무관 강제가 전혀 없음, (2) `spawn.py:1071` 자동 호출자가 `pr`/`issue` 미배선, (3) phase1 "Closes 금지"의 기계적 검사 부재(에러 메시지만 존재).

Sources:
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule
- https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
- https://cli.github.com/manual/gh_pr_merge
- https://github.com/pre-commit/pre-commit-hooks/issues/303
- https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
- https://mergify.com/learn/merge-queue
- https://lobste.rs/s/exhcza/migrating_from_bors_ng_github_merge
