scout: skipped — spec leaves no design decision open (skip condition 2). Issue #236 fully
specifies the rule text (mandatory full URL for decision-pending mentions, number-only allowed on
same-answer repeat, notation format free), the scope (orchestrator reply only, role-session PR
bodies/records excluded), and the constraints (single file, no gate). The only decision left is
where inside `run.md`'s existing structure to place the new bullet — a documentation-placement
question the current-state survey below resolves, not a product/prior-art question scouting would
inform.

# Current-state survey — issue #236

## Where "REPLY STRUCTURE" actually lives

The issue names `on-the-record/commands/run.md` 의 REPLY STRUCTURE 절, but that exact heading
string does not exist in `run.md` — it exists in `on-the-record/hooks/directive.sh:98`, the
English-language per-prompt orchestration directive injected every turn, as a compressed summary
bullet ("REPLY STRUCTURE: every reply opens by re-anchoring the overall flow... Item reports carry
these coordinates (flow, stage, next step) — never a bare item number"). `directive.sh` is
generated/injected text, not the document the issue's constraint names, and the issue explicitly
scopes the edit to "문서 한 곳(`run.md`)" — so `directive.sh` is out of scope regardless of the
heading match.

The actual Korean-language content `directive.sh`'s bullet summarizes lives in `run.md`'s step 5
(`5. **PR 을 설명한다.**`, lines 52-91), specifically the "**구조적 맥락 — flow/stage/next.**"
sub-bullet (lines 67-91) added by issue-54 (`docs/issue-54/proposals/coding.md`, merged as PR #55
per that proposal's upstream). This is the run.md-side analog of directive.sh's "REPLY STRUCTURE"
line — same origin issue, same coordinate-reporting concept (flow/stage/next), just localized to
Korean and split from directive.sh's compressed restatement. This sub-bullet is the natural target.

## Full current text of step 5 (lines 52-91)

```
5. **PR 을 설명한다.** 역할이 올린 PR 을 읽고 사용자에게 요약한다: 무엇을
   제안/보고했고, 지금 1단계(제안)인지 2단계(실행 완료)인지.
   - **1단계 승인 요청 시:** ... (읽고-요약 의무, 절차 위반 문구)
   - **2단계 머지(수용) 요청 시:** ... (읽고-요약 의무, 절차 위반 문구)
   - 모든 승인/머지 요청은 최소한 다음 네 항목을 담아야 한다: 무엇을
     바꾸는가, 왜 바꾸는가, (머지 시) 실제로 무엇이 바뀌었는가, 어떻게
     검증됐는가. 이 요약 없이 여닫힌 질문만 던지는 것은 절차 위반이다.
   - **구조적 맥락 — flow/stage/next.** (flow/stage/next 필드 정의, 단일
     항목·복수 항목 렌더 형식)
```

None of these four existing bullets currently require a link — `flow` is rendered as bare
`[이슈 #<n>]` (issue number only, no URL), and step 5's approval/merge-request prose has no link
requirement either. This confirms the issue's premise: coordinates (flow/stage/next) are mandated,
targets (URLs) are not.

## Adjacent formats that reuse the same bare-number pattern (read-only context, not edit targets)

Three other spots in `run.md` render the same `[이슈 #<n>]` bare-number format, inherited from the
issue-54 format rather than independently specified:

- Step 6 (`6. **사용자의 결정을 중계한다.**`, lines 171-183): the decision-queue block, triggered
  only when 2+ items await a decision (`- **결정 대기 항목이 2건 이상이면**`), renders
  `1) [이슈 #<n1>] ...` / `2) [이슈 #<n2>] ...` with no link.
- Mission board render format (`### 렌더 형식`, lines 129-146): all three status groups (Running /
  Waiting for human decision / Done) reuse "이슈-54의 압축 한 줄 형식" verbatim — bare
  `[이슈 #<n>]`.
- Mission board classify logic (`### 어떻게`, lines 112-127) defines the term
  `waiting-for-human-decision` (line 120) — this is the existing name for exactly the item class
  the issue calls "사용자 결정을 기다리는 항목."

These three spots are not separately named write targets in the issue text, but they matter for
placement: a rule added only inside step 6's decision-queue bullet would not cover step 5's
single-item approval/merge asks (the queue only renders "항목이 2건 이상"; a lone approval request
never enters it), so the new rule cannot live solely in step 6 without under-covering the issue's
own requirement 1 ("사용자 결정을 기다리는 항목... 반드시 링크 포함" — no cardinality
qualifier). See proposal Rationale for the resulting placement decision.

## Write set

- `on-the-record/commands/run.md` — one new bullet inside step 5, sibling to the existing
  "구조적 맥락 — flow/stage/next" bullet (after line 91). No other file.
- No test file, no `.env.example`, no dependency, no migration — `run.md` is a prompt document with
  no test harness (confirmed by issue-54's proposal precedent, which used direct-text-inspection
  verification, not an automated test).
- No gate script currently targets `run.md` (`grep -rn "run\.md" on-the-record/hooks/*.sh` returns
  no hits) — matches the issue's own "게이트 강제는 하지 않는다" constraint; there is nothing to
  wire and nothing to avoid wiring.

## Precedent for proposal shape

`docs/issue-54/proposals/coding.md` (same target file, same step, added the sibling bullet this
proposal now sits next to) and `docs/issue-229/proposals/proposal.md` (small-diff precedent with a
scout-skip survey) both hold Old/New literal-block diffs against the current file text. This
proposal follows the same shape.
