# Coding proposal — issue-54: structural-context reporting

Status: phase-1 proposal. Not yet applied. Awaiting approver `APPROVE issue-54/coding` before any
edit lands on `orchestrate/commands/run.md`.

upstream: docs/issue-54/reports/product.md (binding requirements, PR #55),
docs/issue-54/reports/ux-design.md (binding presentation spec, PR #56)
survey: docs/issue-54/reports/coding/survey.md

files: orchestrate/commands/run.md

## Request

Issue #54: every report the orchestrator gives about an item (a PR, an issue, a role result) makes
the user reconstruct context on their own — which original request it belongs to, what stage it is
at, what happens next. The user had to ask "what was #48 again?" mid-session. Fix: every step-5
report must carry three additive fields — `flow` (which original request), `stage` (lifecycle
position among six fixed values), and `next` (what follows) — computed at report time from state
the orchestrator already reads, with no new persisted store, and without disturbing the existing
issue-34 (what/why/what-changed/how-verified) and issue-44 (role-classification) obligations already
in `run.md`.

## Constraints

- Must implement product.md's schema exactly: `flow` / `stage` / `next` fields, the six fixed
  `stage` values (`proposal` / `approval` / `implementation` / `verification` / `merge` / `close`),
  the compactness rules (≤8-word flow restatement on first mention per turn, issue-number-only on
  repeat, one-word stage, ≤2 next clauses), and flow-first batching (group by flow, one header per
  flow, shared `next` only within an identical-outcome flow+stage group).
- Must implement all 9 acceptance criteria in product.md §4 verbatim in spirit.
- Must implement ux-design.md's presentation exactly: the batched header/body format (§1), the
  single-item compact form (§2), and the decision-queue global numbering (§3), including the
  empty/edge-state rules (§5 — omit empty decision-queue block; errors stay within the six-value
  vocabulary, expressed via `next`).
- Must NOT remove, weaken, or restate the issue-34 read-before-ask summary obligation (current
  lines 51-65 of `run.md`, the "무엇을/왜/(머지 시) 무엇이 바뀌었는가/어떻게 검증됐는가" four-item
  requirement) — the new fields sit as an additive, structurally distinct prefix, never interleaved.
- Must NOT remove, weaken, or restate the issue-44 role-classification step (current lines 20-35 of
  `run.md`, step 2's routing table and "말하지 않고 coding 으로 기본값 처리하는 것은 절차 위반"
  rule) — `stage` is a distinct lifecycle axis and must never duplicate this line.
- Must NOT introduce a new numbered loop step (currently 1-6) — the edit integrates into step 5 (and
  step 6 for `next`'s branch/decision-relay mechanics), per product.md's scope note and ux-design.md
  trace item 9.
- Must NOT introduce a new stored artifact, file, board, or queue — per issue-43's read-only-view
  condition, reaffirmed by product.md §5 and ux-design.md §3's "per-turn rendering convenience, not
  a persisted queue-slot" note.

## What will be done

Two edits to `orchestrate/commands/run.md`, both inside the existing numbered loop (step 5 and step
6), no new step number introduced.

### Edit 1 — step 5: add the flow/stage/next fields

**Old** (current lines 51-65, unchanged text kept for context):

```
5. **PR 을 설명한다.** 역할이 올린 PR 을 읽고 사용자에게 요약한다: 무엇을
   제안/보고했고, 지금 1단계(제안)인지 2단계(실행 완료)인지.
   - **1단계 승인 요청 시:** 제안 파일(`docs/issue-<n>/proposals/`)을 실제로
     읽고, 다음을 반드시 채워 자연어로 요약한 뒤에만 승인을 물어라 —
     (1) 무엇을 바꾸려 하는가, (2) 왜 (요구/제약과의 연결), (3) 어떻게
     (접근 방식). 파일을 안 읽고 "제안 PR 이 올라왔습니다, 승인할까요?"
     처럼 묻는 것은 절차 위반이다.
   - **2단계 머지(수용) 요청 시:** 실제 diff/커밋(`gh pr diff <n>` 등)을
     읽고, 다음을 반드시 채워 요약한 뒤에만 머지를 물어라 — (1) 무엇이
     바뀌었는가(파일·핵심 변경), (2) 어떻게 검증됐는가(실행한 테스트·확인
     내용, 역할의 기록에서 확인). 파일을 안 읽고 "PR 이 열렸습니다,
     승인할까요?" 처럼 묻는 것은 절차 위반이다.
   - 모든 승인/머지 요청은 최소한 다음 네 항목을 담아야 한다: 무엇을
     바꾸는가, 왜 바꾸는가, (머지 시) 실제로 무엇이 바뀌었는가, 어떻게
     검증됐는가. 이 요약 없이 여닫힌 질문만 던지는 것은 절차 위반이다.
```

**New** (replaces the block above — the four existing bullets are kept byte-for-byte; one new
bullet is appended):

```
5. **PR 을 설명한다.** 역할이 올린 PR 을 읽고 사용자에게 요약한다: 무엇을
   제안/보고했고, 지금 1단계(제안)인지 2단계(실행 완료)인지.
   - **1단계 승인 요청 시:** 제안 파일(`docs/issue-<n>/proposals/`)을 실제로
     읽고, 다음을 반드시 채워 자연어로 요약한 뒤에만 승인을 물어라 —
     (1) 무엇을 바꾸려 하는가, (2) 왜 (요구/제약과의 연결), (3) 어떻게
     (접근 방식). 파일을 안 읽고 "제안 PR 이 올라왔습니다, 승인할까요?"
     처럼 묻는 것은 절차 위반이다.
   - **2단계 머지(수용) 요청 시:** 실제 diff/커밋(`gh pr diff <n>` 등)을
     읽고, 다음을 반드시 채워 요약한 뒤에만 머지를 물어라 — (1) 무엇이
     바뀌었는가(파일·핵심 변경), (2) 어떻게 검증됐는가(실행한 테스트·확인
     내용, 역할의 기록에서 확인). 파일을 안 읽고 "PR 이 열렸습니다,
     승인할까요?" 처럼 묻는 것은 절차 위반이다.
   - 모든 승인/머지 요청은 최소한 다음 네 항목을 담아야 한다: 무엇을
     바꾸는가, 왜 바꾸는가, (머지 시) 실제로 무엇이 바뀌었는가, 어떻게
     검증됐는가. 이 요약 없이 여닫힌 질문만 던지는 것은 절차 위반이다.
   - **구조적 맥락 — flow/stage/next.** 위 네 항목과 별도로, 이 항목이
     속한 원래 요청·지금 위치·다음 단계를 매 보고마다 덧붙인다 (이슈-54).
     이 세 필드는 위 네 항목을 대신하거나 그 안에 섞이지 않으며, 2번의
     역할 분류 줄도 반복하지 않는다 — 서로 다른, 구조적으로 구분되는 축이다.
     - **flow** — 이 항목이 속한 사용자의 원래 요청. `[이슈 #<n>] <요약,
       ≤8단어>` 형식으로, 같은 flow 를 같은 턴에서 다시 언급할 때는
       `[이슈 #<n>]` 만 쓴다 (요약 반복 금지).
     - **stage** — 다음 6개 고정값 중 정확히 하나: `proposal` / `approval`
       / `implementation` / `verification` / `merge` / `close`. 새 값을
       만들지 않는다. 실패/오류가 나도 stage 는 마지막으로 시도한 값을
       그대로 두고, 재작업 분기를 next 로 먼저 표현한다.
     - **next** — 지금 열려 있는 결정 분기마다 한 줄, 최대 2개. 바로
       다음 단계까지만 예측한다 (그 뒤는 예측하지 않는다).
     - **항목이 하나뿐인 턴** — 헤더/본문을 나누지 않고 한 줄로 압축한다:
       ```
       [이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>
       ```
     - **항목이 여럿인 턴** — flow 로 먼저 묶는다. flow 마다 헤더 하나,
       서로 다른 flow 는 stage 가 같아도 절대 하나의 헤더로 합치지 않는다:
       ```
       ### [이슈 #<n>] <flow 요약, ≤8단어> — <stage 분포 요약>
       - <item> — <stage> → <next>
       ```
       같은 flow·같은 stage 이고 분기 결과가 완전히 같을 때만 next 를
       한 줄로 공유한다; 그 외에는 항목마다 next 를 따로 쓴다.
```

### Edit 2 — step 6: add decision-queue global numbering

**Old** (current lines 66-77):

```
6. **사용자의 결정을 중계한다.** 대화의 의미대로:
   - 수정 요구 → `gh pr comment` 로 해당 PR 에 남긴다
   - 제안 승인 → 기본(1계정)에서는 자기 PR 에 리뷰 Approve 가 불가하므로,
     정확히 이 문자열의 코멘트를 단다: `gh pr comment <n> --body "APPROVE issue-<n>/<역할>"`
     (approval-gate 가 이 정확한 문자열만 승인으로 인정한다. 에이전트 계정을
     분리한 하드닝 구성에서는 `gh pr review <n> --approve` 도 된다)
   - 결과 수용 → `gh pr merge <n> --merge --delete-branch` — 머지된
     브랜치는 반드시 함께 지운다. 역할별 이슈 브랜치는 PR 이 생명주기다
   - 거부 → `gh pr close <n>`
   승인·머지는 사용자가 이 대화에서 그 의사를 밝힌 뒤에만. 확신이 없으면
   실행하지 말고 되물어라. 당신이 먼저 승인을 제안할 수는 있어도, 사용자의
   답 없이 실행하는 일은 없다.
```

**New** (adds one bullet before the existing dash list; the four existing bullets and the closing
sentence are kept byte-for-byte):

```
6. **사용자의 결정을 중계한다.** 대화의 의미대로:
   - **결정 대기 항목이 2건 이상이면**, 전체 턴에 걸친 전역 번호로 큐를
     나열한다 (flow 별로 번호를 다시 시작하지 않는다 — 그러면 "1" 이
     어느 flow 인지 또 추적해야 한다):
     ```
     1) [이슈 #<n1>] <flow 요약> · <stage> → <next 선택지 A / B>
     2) [이슈 #<n2>] <flow 요약> · <stage> → <next 선택지 A / B>
     ```
     번호는 매 턴 새로 매기는 표시일 뿐 저장되는 식별자가 아니다(이슈-43
     읽기전용 조건) — 사용자가 "1" 로 답하면 같은 턴에서 가장 최근에
     렌더링된 큐에 대해서만 풀이한다. 각 줄의 flow(이슈 번호)가 실제
     라우팅에 쓰인다. 대기 항목이 없으면 이 블록 자체를 만들지 않는다
     (빈 "0건" 큐를 만들지 않는다).
   - 수정 요구 → `gh pr comment` 로 해당 PR 에 남긴다
   - 제안 승인 → 기본(1계정)에서는 자기 PR 에 리뷰 Approve 가 불가하므로,
     정확히 이 문자열의 코멘트를 단다: `gh pr comment <n> --body "APPROVE issue-<n>/<역할>"`
     (approval-gate 가 이 정확한 문자열만 승인으로 인정한다. 에이전트 계정을
     분리한 하드닝 구성에서는 `gh pr review <n> --approve` 도 된다)
   - 결과 수용 → `gh pr merge <n> --merge --delete-branch` — 머지된
     브랜치는 반드시 함께 지운다. 역할별 이슈 브랜치는 PR 이 생명주기다
   - 거부 → `gh pr close <n>`
   승인·머지는 사용자가 이 대화에서 그 의사를 밝힌 뒤에만. 확신이 없으면
   실행하지 말고 되물어라. 당신이 먼저 승인을 제안할 수는 있어도, 사용자의
   답 없이 실행하는 일은 없다.
```

No other lines in `run.md` change. Steps 1-4 and the "띄우기 전에 확인할 것" / "하지 않는 것"
sections are untouched.

## Out of scope

- No changes to `roles/*.json` role catalogs.
- No changes to `spawn.py` or any executable orchestration code — `run.md` is a prompt, not code;
  this is a text-only edit.
- No new file, board, queue, or persisted schema of any kind (issue-43 condition).
- No new numbered loop step (stays at 6 steps).
- No change to the issue-34 four-item obligation text or the issue-44 classification table/rule —
  both are reproduced byte-for-byte in the diff above, only new bullets are appended around them.
- No localization change — the edit stays in Korean, matching `run.md`'s existing language and the
  Korean examples ux-design.md specifies.

## How you'll know it worked

Mapped to product.md §4's 9 acceptance criteria:

1. Every step-5 report includes `flow` — satisfied by the new bullet's mandatory `flow` field in
   both the single-item and multi-item formats.
2. Every such report includes `stage` from the fixed six-value vocabulary — satisfied; the bullet
   states the closed list and forbids adding values, including on error.
3. Every such report includes `next` per open branch, capped at the immediately-next stage —
   satisfied; the bullet caps `next` at 2 clauses and forbids forecasting beyond the next stage.
4. The three fields are structurally distinguishable from, not interleaved into, the issue-34
   fields — satisfied; the new bullet is appended after, not inside, the four-item bullet, and its
   own text says so explicitly ("위 네 항목을 대신하거나 그 안에 섞이지 않으며").
5. The three fields never duplicate the issue-44 role-classification line — satisfied; the bullet
   states this explicitly and `stage` values share no vocabulary with the step-2 routing table.
6. Multi-item turns group by flow first, shared `next` only within an identical-outcome flow+stage
   group, no default full restatement per item — satisfied by the multi-item sub-bullet's header
   format and the "완전히 같을 때만" shared-next condition.
7. No criterion implies a new stored artifact — satisfied; nothing in Edit 1 or Edit 2 writes a
   file; step 6's queue is explicitly labeled a per-turn rendering, not a stored structure.
8. Compactness caps stated as explicit limits — satisfied; ≤8-word restatement, issue-number-only
   repeat, one-word stage, ≤2 next clauses are all stated as numeric/explicit limits in the bullet.
9. The edit integrates into existing step 5 (and step 6 for `next`'s branch outcomes) rather than
   introducing a new loop step — satisfied; both edits are sub-bullets inside steps 5 and 6, the
   loop stays numbered 1-6.

Because `run.md` is a prompt file with no test harness, verification is by direct text inspection
of the merged diff against this checklist (no automated check exists or is proposed) — reviewers
should confirm the post-merge file still shows the issue-34 and issue-44 blocks unchanged, plus the
two new bullets exactly as drafted above (or as amended during review).
