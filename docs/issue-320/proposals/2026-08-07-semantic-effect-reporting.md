---
status: proposed
files:
  - on-the-record/commands/run.md
  - test_run_md_semantic_reporting.py
---

## Request

Issue #320: the orchestrator's reports (run.md step 5's PR summaries, and the Mission Board) name
*addresses* — issue numbers, PR titles, file/commit lists — instead of the *effect* the operator
actually cares about: which problem no longer exists, what it used to cost, what's newly possible,
what's still broken. The operator: "사용자는 어떤 문제가 해결됐고 어떤 문제를 줬었고 어떤게 남았고
그런거만 중요할거아냐." Per #310, this must land as an executable check that fails on regression, or
the record must say plainly why no such check is possible for the uncheckable part.

## Constraints

- Single instruction file plus one test, matching the #54/#236 precedent shape for this exact
  section — no new subsystem, no new hook wiring.
- Must not alter the existing 1단계/2단계 phase-identification obligation, the flow/stage/next
  triad (#54), or the clickable-URL rule (#236) — new sibling content only, byte-for-byte
  preservation of what's already there (survey.md confirmed the current wording).
- The requirement targets the orchestrator's *own conversational reports* (step 5, Mission Board) —
  role-session PR bodies/records stay out of scope, same boundary #236 already drew for this
  section.
- Overlap check against sibling issues from the same 2026-08-07 filing batch: the issue text names
  one directly-related sibling — the approval-content issue ("같은 misalignment ... 하지만 다른
  순간에 표면화된다"). That issue concerns the *asking* moment (proposal-approval prompts); #320
  concerns the *reporting* moment (PR/board summaries). Fixing #320's step-5/board wording does not
  touch the approval-prompt wording that sibling issue owns — the two stay separate as the issue
  text itself says they must ("Fixing one does not fix the other"). No other open issue in the
  batch names run.md's step 5 or Mission Board sections.
- Per #310: a check that can only inspect the *instruction* (not a live conversational reply) must
  say so plainly rather than imply it verifies runtime output.

## Rationale

Chose to add one new sibling bullet to step 5 (naming the four effect-framing elements: resolved
problem, prior cost, newly possible, still broken) plus a matching one-line addition to the Mission
Board's render-format note, backed by a grep-style test asserting run.md's text contains the
required framing language — the same shape `test_vocab_coherence_roles.py` already uses to check
role-catalog prose content, and the same shape #236 used for the URL rule.

Considered building a runtime gate that inspects the orchestrator's actual chat output for
enumeration-only patterns (e.g., regex-flagging replies that are just `#<n>` lists with no
prose framing) and blocking the turn. Rejected: no hook in this repo fires on conversational text
delivered to the user — hooks in `on-the-record/hooks/` fire on tool calls and file writes
(`directive.sh`, `deliverable-guard.sh`, `self-update.sh`), not on the assistant's reply stream.
Building that mechanism would be a new subsystem, not a fix to one instruction file, and the issue's
own acceptance language ("If the requirement is genuinely not mechanically checkable, the record
must say so and say why") anticipates exactly this case rather than demanding it.

Also considered leaving the check as prose-only (no test at all), matching #54/#236's original
landing. Rejected per #310, filed the same day: a sentence added to a doc is explicitly listed there
as a non-discharge — this issue is now within #310's scope and must either name an executable
artifact or say explicitly why none exists for the unchecked portion.

## What will be done

1. In `on-the-record/commands/run.md` step 5 ("PR 을 설명한다."), add one new sibling bullet (after
   the existing "구조적 맥락 — flow/stage/next" bullet, before "링크 의무") requiring every PR/board
   summary to frame the change as: (a) 어떤 문제가 해결/제거됐는가, (b) 그 문제가 있었을 때 무엇을
   비용/지장으로 치렀는가, (c) 지금부터 무엇이 새로 가능해졌는가, (d) 아직 무엇이 남았는가/고쳐지지
   않았는가 — explicitly stating that a bare list of issue numbers or PR titles does not satisfy
   this, and that item-number enumeration is only a linking mechanism (per #236), never the report's
   substance.
2. Add a matching one-line note to the Mission Board section's render-format instructions: each
   flow's one-liner must still fit the fixed `[이슈 #<n>] <flow 요약> · <stage> → <next>` shape
   (#54's format is not replaced), but the `<flow 요약>` for a `done` item must name the resolved
   problem/effect, not a restated PR title.
3. Add `test_run_md_semantic_reporting.py`, structured like `test_vocab_coherence_roles.py`: reads
   `on-the-record/commands/run.md`, asserts step 5 and the Mission Board section contain the four
   required effect-framing terms/phrases and the explicit "bare enumeration doesn't satisfy this"
   line, and fails if a future edit strips them.
4. State explicitly, in the record's acceptance section, that this test verifies the *instruction*
   text only — it cannot execute a live orchestrator turn and grade the resulting prose, and name
   that as the acknowledged unverifiable remainder per #310's escape hatch.

## Out of scope

- The sibling approval-content issue's asking-moment wording — separate issue, separate section of
  run.md, explicitly excluded by the issue text itself.
- Any hook/gate that inspects live conversational output — no such mechanism exists in this repo;
  building one is out of scope for a single-file doc fix.
- Role-session PR bodies and `docs/issue-<n>/reports/<role>.md` record formats — #320 and its #236
  precedent both scope this to the orchestrator's own reply, not role output.
- Retroactively rewriting past session transcripts or the Mission Board's stored-vs-computed
  behavior (it stays a computed-not-stored view, per run.md's existing "하지 않는 것" section).

## How you'll know it worked

`pytest test_run_md_semantic_reporting.py` fails on `main` today (no such framing text exists yet)
and passes once the two `run.md` edits land — an executable artifact that fails on regression, per
#310. The test cannot and does not claim to verify that a live orchestrator reply actually uses the
framing; that gap is named explicitly in the phase-2 record as the unverifiable remainder, with the
reason (no hook observes conversational output) stated per #310's own allowance for a named,
justified exception.
