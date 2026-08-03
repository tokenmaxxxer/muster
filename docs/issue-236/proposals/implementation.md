files:
- on-the-record/commands/run.md (step 5, "PR 을 설명한다." — one new sibling bullet after the
  existing "구조적 맥락 — flow/stage/next" bullet)

## Request

Issue #236: the orchestrator's reply rules (`run.md` step 5, the run.md-side counterpart of
`directive.sh`'s "REPLY STRUCTURE" summary — see survey.md) mandate flow/stage/next *coordinates*
for every reported item but never mandate a link to the *target* itself. The orchestrator can say
"PR #96 수용하시겠습니까?" with a bare number, forcing the user to hand-navigate to GitHub every
time a decision is asked. Add one rule: PR/issue mentions carry a clickable full URL, mandatory
whenever the item is one the user is being asked to decide on (approve/accept/reject/close),
number-only permitted for a repeat mention of the same item later in the same answer, notation
format unconstrained.

## Constraints

- Single file, single new bullet — `run.md` only, per the issue's "문서 한 곳의 최소 수정."
  `directive.sh` (which happens to hold the literal English string "REPLY STRUCTURE") is out of
  scope: it is injected/generated per-prompt text, not the document the issue names, and the issue
  restricts the edit to `run.md`.
- No gate enforcement — the issue states orchestrator replies aren't a gate-checkable surface, and
  survey.md confirms no existing hook targets `run.md`. Nothing to wire.
- Must not alter any existing REPLY STRUCTURE-equivalent rule already in step 5/6 — the flow/stage/
  next coordinate definitions, the four-item 승인/머지 read-before-ask obligation, the step-6
  decision-queue mechanics, and the mission board render format all stay byte-for-byte.
- Rule scope is the orchestration session's own reply text only — role-session PR bodies/records
  are explicitly out of scope per the issue's requirement 3.

## Rationale

Chose to place the new rule as one bullet inside step 5 (sibling to "구조적 맥락 —
flow/stage/next"), phrased generically enough to cover every place a decision-pending item's
number appears — step 5's own 1단계/2단계 승인·머지 요청 prose, step 6's decision-queue block, and
the mission board's `waiting-for-human-decision` group — by naming that class directly, rather than
duplicating the rule text into all three locations.

Considered placing it only inside step 6's decision-queue bullet instead, since that bullet already
defines "결정 대기 항목" as a term and is where the multi-item queue's bare `[이슈 #<n>]` numbering
lives. Rejected: step 6's queue only renders when "결정 대기 항목이 2건 이상" — a single pending
approval or merge ask (the common case) never enters it and is handled entirely in step 5's own
prose. The issue's requirement 1 has no cardinality qualifier ("사용자 결정을 기다리는 항목...
반드시 링크 포함" — one item counts same as two), so a step-6-only placement would silently
under-cover the single-item case, which is the more frequent one in practice. Step 5 is upstream of
and structurally covers both the single-item and (by cross-reference) the queued cases, so it is
the only placement that satisfies the requirement without a second edit site — which also keeps the
change to the "문서 한 곳의 최소 수정" the issue asks for.

## What will be done

One edit to `on-the-record/commands/run.md`, appended after the existing "구조적 맥락 —
flow/stage/next" bullet (current lines 67-91), inside step 5, no new numbered loop step.

**Old** (current lines 90-92, unchanged text kept for context — end of the existing bullet, start
of the next section):

```
       같은 flow·같은 stage 이고 분기 결과가 완전히 같을 때만 next 를
       한 줄로 공유한다; 그 외에는 항목마다 next 를 따로 쓴다.
## 미션 보드 (Mission Board)
```

**New** (inserts one bullet between the end of the existing "구조적 맥락" bullet and the
"## 미션 보드" heading; nothing before this insertion point changes):

```
       같은 flow·같은 stage 이고 분기 결과가 완전히 같을 때만 next 를
       한 줄로 공유한다; 그 외에는 항목마다 next 를 따로 쓴다.
   - **링크 의무 — PR·이슈 언급.** PR·이슈를 언급할 때는 클릭 가능한 전체
     URL 을 함께 건다 (이슈-236). 최소 규칙:
     - **사용자 결정을 기다리는 항목**(승인/수용/반려/종결 요청 — 위
       1단계/2단계 승인 요청, 6번 스텝의 결정 대기 큐, 미션 보드의
       waiting-for-human-decision 항목을 모두 포함)은 **반드시** 클릭
       가능한 URL 을 포함한다.
     - 같은 답변 안에서 같은 PR·이슈를 두 번째 이후 언급할 때는 번호만
       허용한다 (매번 다시 링크할 필요 없음).
     - 표기 형식은 강제하지 않는다 — 마크다운 링크든 生 URL 이든, 클릭
       가능하면 된다.
     - 이 규칙은 오케스트레이션 세션의 보고에 대한 것이다 — 역할
       세션의 PR 본문·기록 형식은 범위 밖이다.
## 미션 보드 (Mission Board)
```

No other lines in `run.md` change. Steps 1-4, step 6's decision-queue mechanics, the mission board
sections, and "띄우기 전에 확인할 것" / "하지 않는 것" stay untouched.

## Out of scope

- `on-the-record/hooks/directive.sh` — its "REPLY STRUCTURE" bullet is a compressed summary of the
  same run.md content; not edited here per the issue's single-file constraint. A follow-up issue
  could resync it, but that resync isn't asked for and isn't assumed.
- Any gate script (new or existing) enforcing the link rule mechanically — the issue explicitly
  excludes this.
- Step 6's decision-queue bullet text and the mission board render-format bullets — not edited
  directly; they are covered by the new step-5 rule's cross-reference instead of a second edit.
- Role-session PR body or record format (`docs/issue-<n>/proposals/`, `reports/*.md`) — explicitly
  out of scope per the issue's requirement 3.

## How you'll know it worked

`run.md` is a prompt document with no test harness (same as issue-54's and issue-229's precedent) —
verification is direct text inspection of the merged diff:

1. The new bullet is present, appended after the existing "구조적 맥락 — flow/stage/next" bullet,
   and nowhere else.
2. All four pre-existing step-5 bullets (1단계/2단계 요청 문구, 네 항목 의무, 구조적 맥락) are
   byte-for-byte unchanged.
3. The new bullet's text states, in Korean matching the file's language: mandatory link for
   decision-pending items, number-only allowed on same-answer repeat, notation format free, and the
   orchestration-only scope note — matching the issue's three numbered requirements one-to-one.
4. No other file in the diff besides `run.md` (confirmed via `git diff --stat` before commit).
5. No gate script references the new bullet or `run.md` (confirmed via `grep -rn "run\.md"
   on-the-record/hooks/*.sh` returning no hits, same as pre-change).
