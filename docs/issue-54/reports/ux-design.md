---
loop_state: reviewed
---

# UX design record — issue-54: structural-context reporting

upstream: docs/issue-54/reports/product.md (phase-2 binding requirements, approved via PR #55)

## What was done

Specified the concrete conversational presentation of the `flow` / `stage` / `next` schema
defined by the product record: how a batched flow report groups stage-completions under one
header, how a lone stage-completion renders in a terser compact form, how pending decisions
are numbered so a user can answer by number, and Korean example renderings of every case. This
is a UX specification only — no code, no changes to `orchestrate/commands/run.md` itself. The
coding stage implements this spec verbatim into loop step 5 (and step 6 for `next`'s branch
outcomes), per the product record's scope note.

## Design

### 1. Batched flow report (flow-first grouping)

When step 5 reports on more than one item in the same turn, group by **flow first** — one
header per flow, never merging two flows under one header even if they share a `stage`.

**Header format:**

```
### [이슈 #<n>] <flow 요약, ≤8단어> — <stage 분포 요약>
```

- `<n>` is the flow's owning issue number.
- The ≤8-word restatement appears only on the flow's first mention in the turn (per product
  rule 2); every subsequent header for the same flow in the same turn shortens to
  `### 이슈 #<n>` only — no restatement repeated.
- `<stage 분포 요약>` is a short count/state summary, e.g. `2건 진행 중` or `구현 완료, 검증 대기` —
  not a new prose section, just enough to anchor the header visually.

**Body (one line per item under the header):**

```
- <item> — <stage> → <next>
```

- Ordering within a flow: chronological by lifecycle position (proposal → approval →
  implementation → verification → merge → close), so the reader sees the flow's progress
  top-to-bottom in the order it actually happened, not in arbitrary report order.
- Shared `next`: if two or more items in the same flow are at the same `stage` **and** their
  open branch outcomes are identical, collapse to one shared `next` line under the group
  instead of repeating it per item (product rule: "shared next only within an identical-outcome
  flow+stage group"). Otherwise every item states its own `next`.
- Different flows are always separate header blocks, even if all items across them happen to
  share a `stage` value (e.g. two unrelated flows both "at verification") — they are not
  combined into one "모두 verification 단계" summary.

### 2. Compact single-item form

When only one stage-completion is reported in the turn (no batching), drop the header/body
split and render as a single compact block — same three fields, terser shell:

```
[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>
```

- Still one line per product's compactness rule; the header and body collapse into one line
  because there is nothing to group.
- First-mention-in-turn rule still applies: if the same flow was already restated earlier in
  the turn (e.g. in the content-explanation section above it), use `[이슈 #<n>]` only, no
  restatement.

### 3. Decision-queue numbering

When two or more decision points (pending approvals, merges, or other user choices) are open
across flows in the same turn, list them as one queue, numbered globally across the whole
turn — not restarted per flow:

```
1) [이슈 #<n1>] <flow 요약> · <stage> → <next 선택지 A / B>
2) [이슈 #<n2>] <flow 요약> · <stage> → <next 선택지 A / B>
```

- **Numbering scope**: global to the turn, not per-flow. A per-flow scheme (each flow starting
  its own "1)") would force the user to also track which flow's "1)" they mean — global numbers
  are the only scheme where a bare "1" or "2" is unambiguous.
- **Stability across turns**: numbers are assigned fresh each turn as a rendering convenience,
  not a stored identity. They are not carried over from a previous turn's queue — if the user
  answers "1" this turn, that resolves against *this* turn's rendering only. If items remain
  pending next turn, the queue is re-rendered (and typically re-numbered, since resolved items
  drop out and the remaining ones compact upward) rather than reusing stale numbers. This is
  consistent with issue-43's read-only condition: the number is a presentation artifact
  recomputed at report time, not a persisted queue-slot the orchestrator writes to.
- **Mapping a numeric reply back to an item**: because numbers are only ever valid against the
  queue most recently rendered in the conversation, the orchestrator resolves a bare numeric
  reply ("1 승인", "2는 반려") against the immediately preceding rendered queue in the same
  turn/exchange. Each queue line already carries the `flow` (issue number) needed to route the
  decision to the right PR via loop step 6 — the number is purely a human-facing shorthand for
  that flow reference, never a separate ID the orchestrator stores.

### 4. Example renderings (Korean — user-facing text)

**(a) Batched flow report, 2–3 stages under one flow:**

```
### [이슈 #54] 구조적 맥락 리포팅 — 2건 진행 중
- product 기록 (PR #55) — merge → 다음 단계로 coding 이슈 등록 대기
- ux-design 초안 — implementation → 리뷰 후 승인 요청 예정
```

**(b) Single compact item (no batching):**

```
[이슈 #46] 캐시 디렉터리 오탐 수정 · verification → 테스트 통과 확인, 병합 승인 대기
```

**(c) Decision queue, 2+ pending items:**

```
지금 결정이 필요한 항목이 2건 있습니다:

1) [이슈 #54] 구조적 맥락 리포팅 · approval → 승인(머지) / 반려(재작업)
2) [이슈 #46] 캐시 디렉터리 오탐 수정 · approval → 승인(머지) / 수정 요청

번호로 답해주세요 (예: "1 승인, 2는 재작업").
```

### 5. Empty / edge states

- **No pending decisions**: omit the decision-queue block entirely — do not render an empty
  "0건" queue. The absence of the block itself signals "nothing waiting," which is the existing
  run.md convention (no manufactured empty-state prose).
- **A stage that failed/errored**: `stage` still reports the last-attempted fixed value (e.g.
  `implementation`), but `next` states the rework branch first: `next → 원인 확인 후 재시도 /
  진행 보류`. An error is not a seventh stage value — it is expressed entirely through `next`,
  keeping the six-value vocabulary closed per product's acceptance criterion 2.
- **A flow with only one stage (no history yet)**: renders via the compact single-item form
  (§2) even inside an otherwise-batched turn if it is genuinely the only item for that flow —
  a flow header with a single body line is also acceptable when other flows in the same turn
  are already using the batched header form, for visual consistency across the turn; either
  rendering is compliant as long as it is not duplicated.

## Acceptance-criteria trace (product record §4, all 9)

1. **flow reference on every report** — satisfied: header (§1) and compact form (§2) both open
   with `[이슈 #<n>] <flow 요약>`, mandatory in every rendering.
2. **stage from the fixed six-value vocabulary** — satisfied: every example (§4) uses one of
   `proposal/approval/implementation/verification/merge/close`; the error edge case (§5)
   explicitly keeps the vocabulary closed rather than adding a value.
3. **next per open decision branch, capped at immediately-next stage** — satisfied: all
   examples state one or two branch clauses (e.g. "승인 / 반려") describing only the next step,
   never forecasting further.
4. **structurally distinguishable from issue-34 fields** — satisfied: §1–§3 formats are a
   distinct prefix line/block (`[이슈 #n] 요약 · stage → next`), never interleaved into the
   what/why/what-changed/how-verified prose; that content sits in its own section as before.
5. **never duplicates issue-44 role-classification line** — satisfied: no example restates a
   role name or classification rationale; the role line remains a separate, untouched line per
   existing run.md step 2 convention.
6. **multi-item turns group by flow first, shared next only within identical-outcome
   flow+stage group, no default full restatement per item** — satisfied: §1 states the
   flow-first grouping rule, the shared-next condition verbatim, and the first-mention-only
   restatement rule.
7. **no new stored artifact implied** — satisfied: §3 explicitly states queue numbers are a
   per-turn rendering convenience recomputed at report time, not a persisted structure; all
   fields still sourced from existing state per product's schema definition.
8. **compactness caps stated as explicit limits** — satisfied: ≤8-word flow restatement,
   issue-number-only repeat mention, one-word stage, ≤2 next clauses are all called out
   explicitly in §1–§2.
9. **integrates into existing step 5/6, not a new loop step** — satisfied: this spec is scoped
   as formatting guidance for step 5's reporting and step 6's decision relay (see run.md read
   in preparing this record); it introduces no new numbered loop step, only a numbering
   convention layered onto step 6's existing decision-relay mechanics.

No element in this spec falls outside the 9 criteria above — nothing here is flagged as scope
growth.

## Heuristics note

- **Visible system status**: every report line always shows `stage` and `next` together, so
  the user never has to infer "is this done or not" — the current position and the next action
  are both visible at all times, not just on request.
- **Recognition over recall**: decision-queue numbering (§3) lets the user answer "1" instead
  of recalling and retyping an issue number or PR number; each queue line still shows the issue
  number alongside the number, so recognition is available even if the user forgot what "1"
  was mid-turn.
- **No dead ends**: every decision-queue item (§3) and every compact/batched line (§1, §2)
  carries a non-empty `next`, including the error edge case (§5) — there is no rendering path
  that reports a stage with no stated next action.
- **Consistency with existing run.md conventions**: matches the Korean-language, terse,
  bullet/heading style already used by `orchestrate/commands/run.md` step 5 (e.g. its own
  "1단계/2단계" phrasing and requirement to fill a fixed checklist before asking an open
  question); the empty-state rule in §5 mirrors run.md's existing preference for omission over
  manufactured filler text; the "no default full restatement" behavior in §1 directly extends
  run.md's existing compactness expectations rather than introducing a new visual grammar.

## Open findings

None. This spec satisfies all 9 product acceptance criteria without introducing any element
outside their scope; the coding stage can apply §1–§5 verbatim into `orchestrate/commands/run.md`
step 5/6.

## References

- Product record: `docs/issue-54/reports/product.md`
- Issue: `gh issue view 54`
- Surface being specified into: `orchestrate/commands/run.md`
