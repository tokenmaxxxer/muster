---
subject: issue-320
---

# Survey — issue #320

## What the issue names

`on-the-record/commands/run.md`, step 5 ("PR 을 설명한다.") and the Mission Board section: the
orchestrator's reply-shape rules for reporting role-session results and rendering board state to
the user. The operator's complaint is that these replies enumerate item addresses (issue numbers,
PR titles) instead of translating them into the operator's frame: what problem no longer exists,
what it cost before, what's newly possible, what's still broken.

## Current state of the write surface

Read `on-the-record/commands/run.md` step 5 in full (already quoted in the parent conversation).
It currently mandates, per PR report:
- phase identification (1단계 제안 / 2단계 실행완료)
- for phase 1: 무엇을 바꾸려 하는가 / 왜 / 어떻게 (read from the proposal file)
- for phase 2: 무엇이 바뀌었는가 / 어떻게 검증됐는가 (read from diff/commits)
- flow/stage/next structural coordinates (issue #54)
- clickable URL requirement for decision-pending items (issue #236)

None of these fields ask for the *effect* framing the operator wants: prior cost, resolved state,
newly-possible state, remaining breakage. "무엇이 바뀌었는가" as currently worded is satisfiable by
naming files/commits — exactly the enumeration the operator is objecting to. The Mission Board
section (same file, below step 5) renders per-flow one-liners as `[이슈 #<n>] <flow 요약, ≤8단어> ·
<stage> → <next>` — also address/coordinate-shaped, not effect-shaped.

## Prior additions to this same section (precedent for shape)

- #54 added the flow/stage/next triad as a *new sibling bullet*, explicitly preserving the four-item
  승인/머지 요약 obligation byte-for-byte.
- #236 added the clickable-URL rule the same way: one new sibling bullet, single-file edit, no gate
  wired (`docs/issue-236/proposals/*.md` states plainly "No gate enforcement — orchestrator replies
  aren't a gate-checkable surface").

Both precedents are prose-only requirements added to an LLM-facing instruction file, with **no
mechanical test** verifying the orchestrator's actual conversational output honors them — because
conversational output is not a file on disk a gate can read. #310 was filed the same day as #320 and
did not exist when #54/#236 landed, so this issue is the first in this area required to either name
an executable artifact or say explicitly why none exists.

## What is and isn't mechanically checkable here

Checked whether any existing gate/test reads `run.md` content (`grep -rl run.md gates/ test_*.py`):
none does. `test_vocab_coherence_roles.py` is the one existing precedent in this repo for a test
that greps an instruction/config file's *text* for required or forbidden vocabulary (there: role
JSON `decides`/`use_when`/`produces` fields must not carry routing vocabulary) — a check on the
authored instruction, not on runtime LLM behavior.

**Correction (this revision).** The PR #342 review rejected the original version of this section
for a factual error, the same one #338's review caught in issue #318: the original text asserted
"no hook in this repo fires on conversational text delivered to the user — hooks in
`on-the-record/hooks/` fire on tool calls and file writes." That is false. Claude Code's `Stop` hook
fires when the assistant finishes a turn, receives `last_assistant_message` — the turn's final
assistant message body, i.e. exactly the orchestrator's PR/board report text this issue is about —
and can return `decision: "block"` (with `reason`) to reject that reply, or
`hookSpecificOutput.additionalContext` to inject a requirement without blocking. Source: Claude Code
hooks reference (https://code.claude.com/docs/en/hooks.md), confirmed 2026-08-07; also recorded in
#298's comment thread, which both #338's and #342's reviews point to.

**How the wrong premise got written down as confirmed.** The command actually run was
`grep -rl run.md gates/ test_*.py` plus a read of `on-the-record/hooks/hooks.json`, which lists three
declared events (`SessionStart`, `UserPromptSubmit`, `PreToolUse`). That command answers "which
events does *this plugin's config* register" — a statement about this repository's current
configuration. It does not answer "which events can Claude Code's hook system fire on" — a statement
about the platform's capability, which would have required reading Claude Code's hook documentation,
not this repo's `hooks.json`. The survey conflated the two and reported the narrower, checked fact
(three events declared here) as though it were the broader, unchecked fact (no hook observes
conversational text, full stop). Nothing in the original survey text flagged that the two claims were
different in scope; the stronger claim was written as settled when only the weaker one had been
verified. This is the same failure class already on record in #287: reporting something as confirmed
when what was actually checked was a narrower proxy for it, without noting the gap between the two.
The concrete lesson for future surveys in this repo: absence of a hook *declaration* in this plugin's
own config is evidence about this plugin's current wiring, never evidence about what the underlying
platform supports — the latter needs the platform's own docs, checked directly, before being stated
as a conclusion.

**Revised ceiling.** With the `Stop` hook available, the primary runtime check for this issue's
"bare enumeration" problem is checkable directly: a `Stop` hook can read `last_assistant_message`,
detect whether the turn is a PR/board report by structural markers already in scope (e.g. the `[이슈
#<n>]` board-line format, or the phase-identification header run.md step 5 already mandates), and
require the four effect-framing elements (resolved problem / prior cost / newly possible / still
broken) actually be present in that literal text — not just present in the instruction file. The
grep-based `run.md`-text check from the original proposal is still worth keeping, but now as a
*complementary* instruction-drift guard (catches the instruction itself being silently weakened),
not as the primary or only check, since a stronger runtime check is now known to exist. This matches
the correction #338's review already required for the sibling issue #318, which sits on the same
`Stop` hook substrate — see the proposal's Constraints for how hook-declaration ownership between
#318 and #320 is resolved so the two proposals don't both try to own `hooks.json`'s `Stop` entry.

## Write set implied

- `on-the-record/commands/run.md` — step 5 sibling bullet + Mission Board render-format note, same
  pattern as #54/#236.
- One new test file (analogous role to `test_vocab_coherence_roles.py`) asserting the required
  effect-framing keywords are present in step 5 and the Mission Board section of `run.md`.
- `on-the-record/hooks/report-framing-check.sh` (new) — the `Stop`-hook handler that reads
  `last_assistant_message`, detects a PR/board report turn, and blocks a reply missing the four
  effect-framing elements. Declaring this script is #320's write set; declaring `hooks.json`'s `Stop`
  event entry itself is not (see proposal Constraints for the ownership split with #318).

## Alternatives visible from this survey

1. **Prose-only edit, no test** — rejected outright: this is exactly the fourth non-discharge #310
   names ("a sentence added to a doc does not discharge a requirement").
2. **`Stop`-hook check on the orchestrator's actual chat reply at runtime** (chosen as primary,
   corrected from the rejected original) — the `Stop` hook receives `last_assistant_message` and can
   `decision: "block"` a reply that fails the effect-framing check, so this is available and is what
   #320 actually needs: a check on the live report, not a proxy for it.
3. **Grep-based test on the instruction file itself** (kept, demoted to complementary) — the same
   ceiling `test_vocab_coherence_roles.py` already accepted for role-catalog prose; verifies the
   instruction text is present and durable against accidental deletion. Useful as a drift guard
   alongside the runtime check, not as a substitute for it now that the runtime check is known to be
   possible.
