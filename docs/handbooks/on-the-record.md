# on-the-record plugin handbook

Hook-behavior tests for the `on-the-record/` plugin (directive injection,
deliverable-guard, board-gate) live in `tests/run-orchestrate-tests.sh`
(filename kept from the plugin's former `orchestrate` name) and point at
`on-the-record/hooks/`. Run it directly: `bash tests/run-orchestrate-tests.sh`.

## 오케스트레이션 모델

역할을 소집한다 — 그 역할의 룰북만 깔린 샌드박스 세션 하나를 띄운다.

배차 기사가 아니라 콘센트가 있는 컨시어지다: contract v3 에서는 오케스트레이션
세션(이 마켓플레이스의 `on-the-record` 플러그인)이 사용자와 대화하고, 사용자가
불러주는 이슈를 작성하고, 역할 세션을 띄우고, 돌아온 PR 을 설명하고, 사용자의
결정 — 코멘트, 리뷰 Approve, 머지 — 을 사용자 본인 계정으로 대신 전달한다.
역할 세션은 AGENT 계정(`MUSTER_AGENT_GH_TOKEN`)으로 돌고, `issue-<n>/<role>`
브랜치에서 작업하며, 모든 결과는 PR 로 돌아온다. **각 역할이 자기 상태를 갖고,
on-the-record 는 읽기만 한다.**

```
protocol.md   규약 — on-the-record 가 하는 일 셋, 상태 노출 계약, 격리
roles/        역할 하나 = 파일 하나. 룰북 번들 + 샌드박스 경계
spawn.py      상태를 읽고, 역할 환경으로 세션을 띄운다
              (--issue <n> 가 브랜치를 만들고 프롬프트를 고정한다)
on-the-record/  그걸 대화에서 부르는 플러그인 (/on-the-record:run)
gates/        결정론 검사. 세션이 끝나면 spawn.py 가 부른다. LLM 0회
ledger/       runs/ledger.jsonl 를 읽는 집계기 (저장소 자체는 runs/)
```

## Orchestration model

Musters a role — brings up one sandboxed session with only that role's
rulebook and the tokenmaxxxer-core plugins installed.

Not a dispatcher. A power outlet with a concierge: on contract v3 the
orchestration session (this marketplace's `on-the-record` plugin) talks to
the user, drafts issues the user dictates, spawns role sessions, explains
the PRs that come back, and relays the user's decisions — comments,
review Approve, merge — with the user's own account. Role sessions run on
the AGENT account (`MUSTER_AGENT_GH_TOKEN`), work on `issue-<n>/<role>`
branches, and return everything by PR. **Each role owns its state; on-the-record
only reads it.**

```
protocol.md   the contract — on-the-record's three jobs, the state-exposure deal, isolation
roles/        one role is one file: rulebook bundle plus sandbox boundary
spawn.py      reads state, brings up a session in a role's environment
              (--issue <n> creates the branch and anchors the prompt)
on-the-record/  the plugin that drives the loop from a conversation (/on-the-record:run)
gates/        deterministic checks, run by spawn.py after a session. Zero LLM calls
ledger/       aggregator over runs/ledger.jsonl (the storage itself is runs/)
```

## 역할

역할 파일은 마켓플레이스와 경계만 적는다. 플러그인 목록은 `spawn.py` 가 그 룰북의
`marketplace.json` 을 읽어 펼친다 — 룰북에 플러그인이 추가돼도 여기를 안 고쳐도 된다.

**`<role>-agent-env` 번들만 켜는 방식은 안 된다.** 번들의 `dependencies` 는
`--settings` 의 `enabledPlugins` 로 해결되지 않는다(A/B 실측: 번들만 켠 세션은
doctrine 의 SessionStart 훅이 안 돌아 `docs/` 버킷이 안 생겼고, 개별로 켠 세션은
생겼다). 번들이 켜졌다는 사실만 보고 넘어가면 **룰북 0개로 도는 세션을 성공으로
착각한다.**

| 역할 | 룰북 | 무엇을 정하나 |
|---|---|---|
| product | tokenmaxxxer-product | 무엇을 만들지 |
| feasibility | tokenmaxxxer-feasibility | 될 일인지 (명세만 보고, 시장 논리 없이) |
| coding | tokenmaxxxer-coding | 만든다 — `build-proposal`, `loop_state: proposed,approved,landed` |
| review | tokenmaxxxer-review | 명세대로인지 (요구사항별 판정) |
| qa | tokenmaxxxer-qa | 실제로 도는지 |
| ux-design | tokenmaxxxer-ux-design | 쓰는 모습이 어때야 하는지 |
| verify | tokenmaxxxer-verify | coding 과 qa 의 산출물이 서로 맞는지 |
| reflect | tokenmaxxxer-reflect | 착지한 라운드가 무엇을 가르쳤는지 |
| ops | tokenmaxxxer-ops | 내보내고 지킨다 |

## Roles

A role file records the marketplace and the boundary, nothing else. `spawn.py` expands
the plugin list by reading that rulebook's `marketplace.json`, so a rulebook can add a
plugin without anyone editing a role file.

**Enabling only the `<role>-agent-env` bundle does not work.** A bundle's
`dependencies` are not resolved through `--settings`' `enabledPlugins` (measured A/B:
the bundle-only session never ran doctrine's SessionStart hook and grew no `docs/`
buckets; the session that enabled each plugin individually did). Taking "the bundle is
enabled" as proof is how **a session running zero rulebooks gets recorded as a
success** — which contaminates an ablation outright.

| role | rulebook | decides |
|---|---|---|
| product-discovery | tokenmaxxxer-product-discovery | what to build |
| technical-feasibility | tokenmaxxxer-technical-feasibility | whether it can be built, from the spec alone, with no market reasoning |
| implementation | tokenmaxxxer-implementation | builds it — `build-proposal`, `loop_state: proposed,approved,landed` |
| conformance-review | tokenmaxxxer-conformance-review | whether it matches the spec, requirement by requirement |
| execution-observation | tokenmaxxxer-execution-observation | whether it actually runs |
| interaction-design | tokenmaxxxer-interaction-design | what it should look like to use |
| defect-verification | tokenmaxxxer-defect-verification | whether implementation's and execution-observation's artifacts agree |
| issue-retrospective | tokenmaxxxer-issue-retrospective | what the round taught, once it landed |
| release-engineering | tokenmaxxxer-release-engineering | ships it and keeps it up |
