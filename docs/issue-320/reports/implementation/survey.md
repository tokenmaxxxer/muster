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

That is the ceiling available here too: a test can assert `run.md` *instructs* the effect-framing
the operator wants (structural proxy — the instruction exists and names the required elements), but
no test in this repository can execute a real reporting turn and grade whether the orchestrator's
free-text reply actually satisfied it — the same limitation #236's proposal already stated for the
sibling URL rule. The proposal will state this limitation explicitly rather than claim a check it
cannot deliver, per #310's own escape hatch ("if genuinely not mechanically checkable, the record
must say so and say why").

## Write set implied

- `on-the-record/commands/run.md` — step 5 sibling bullet + Mission Board render-format note, same
  pattern as #54/#236.
- One new test file (analogous role to `test_vocab_coherence_roles.py`) asserting the required
  effect-framing keywords are present in step 5 and the Mission Board section of `run.md`.

## Alternatives visible from this survey

1. **Prose-only edit, no test** — rejected outright: this is exactly the fourth non-discharge #310
   names ("a sentence added to a doc does not discharge a requirement").
2. **Gate/hook that inspects the orchestrator's actual chat reply at runtime** — no such mechanism
   exists in this repo (hooks fire on tool calls/file writes, not on conversational text sent to the
   user); building one is a new subsystem far outside a single-file doc edit and isn't what #320
   asked for.
3. **Grep-based test on the instruction file itself** (chosen) — the same ceiling `test_vocab_coherence_roles.py`
   already accepted for role-catalog prose; verifies the instruction is present and durable against
   accidental deletion, explicitly short of verifying live output.
