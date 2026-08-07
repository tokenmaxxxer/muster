---
status: proposed
files:
  - on-the-record/commands/run.md
  - on-the-record/hooks/report-framing-check.sh
  - test_run_md_semantic_reporting.py
  - test_report_framing_check.py
---

## Revision note (why this version differs from the rejected one)

PR #342 was rejected for a factual error in the original Rationale, the same error #338's review
caught for the sibling issue #318: the claim that no hook in this repo observes the orchestrator's
own conversational reply. That is false — Claude Code's `Stop` hook fires when a turn ends, receives
`last_assistant_message` (the turn's final assistant message body), and can `decision: "block"` it.
The rejected proposal's own escape-hatch language ("if genuinely not mechanically checkable...") was
therefore invoked for a requirement that *is* mechanically checkable, which is exactly what #310
exists to prevent. `docs/issue-320/reports/implementation/survey.md` now carries a corrected section
and a root-cause note on how the error got written down as confirmed (same failure class as #287:
the survey verified a narrower claim — this plugin's `hooks.json` declares three events — and
reported the broader, unchecked claim — no such hook can exist — as though it had been verified too).

This revision keeps the original grep-based `run.md`-text test (still useful as an instruction-drift
guard) but adds a `Stop`-hook runtime check as the primary mechanism, and resolves the hook-ownership
question the #342 review raised: see Constraints.

## Request

Issue #320: the orchestrator's reports (run.md step 5's PR summaries, and the Mission Board) name
*addresses* — issue numbers, PR titles, file/commit lists — instead of the *effect* the operator
actually cares about: which problem no longer exists, what it used to cost, what's newly possible,
what's still broken. The operator: "사용자는 어떤 문제가 해결됐고 어떤 문제를 줬었고 어떤게 남았고
그런거만 중요할거아냐." Per #310, this must land as an executable check that fails on regression.

## Constraints

- Single instruction file, one new hook handler, and two tests — no new subsystem beyond the one
  `Stop`-hook script this issue actually needs.
- Must not alter the existing 1단계/2단계 phase-identification obligation, the flow/stage/next
  triad (#54), or the clickable-URL rule (#236) — new sibling content only, byte-for-byte
  preservation of what's already there.
- Scope stays the orchestrator's *own conversational reports* (step 5, Mission Board) — role-session
  PR bodies/records stay out, same boundary #236 already drew.
- Overlap with the sibling approval-content issue (#318) stays as the issue text requires: #318
  covers the *asking* moment, #320 covers the *reporting* moment. Fixing #320 does not touch #318's
  wording.
- **Hook-declaration ownership (new, required by the #342 review).** #318 and #320 both need a
  `Stop`-hook check on `last_assistant_message`, and `hooks.json`'s `Stop` key can only be declared
  once without the two entries clobbering each other. #338's review directed #318 to build the
  `Stop`-hook design first for its own issue. Resolution: **whichever of #318/#320 lands on `main`
  first declares `hooks.json`'s `Stop` entry** (a single event key whose `hooks` array can hold
  multiple command handlers — `report-framing-check.sh` for #320's check, and #318's own handler for
  its check, each independently matched by what kind of reply they're looking at). **Whichever lands
  second adds its handler script and appends one entry to the existing `Stop` array — it does not
  re-declare the `Stop` key.** This proposal's write set therefore includes
  `on-the-record/hooks/report-framing-check.sh` (the handler script, buildable and testable
  independently of `hooks.json`) but conditions the `hooks.json` wiring step on landing order,
  stated explicitly in "What will be done" below rather than assumed.
- Per #310: the grep-based `run.md` text check verifies the *instruction*, not a live reply; the
  `Stop`-hook check verifies the *live reply* directly. The proposal states plainly which check
  covers which claim rather than letting one stand in for the other.

## Rationale

Chose a `Stop`-hook check (`report-framing-check.sh`) as the primary mechanism: it reads
`last_assistant_message`, detects a PR/board report turn by structural markers already mandated in
run.md (the 1단계/2단계 header, or the Mission Board's `[이슈 #<n>] ... · <stage> → <next>` line
shape), and requires the four effect-framing elements — resolved problem, prior cost, newly
possible, still broken — to actually appear in that text, returning `decision: "block"` with a
`reason` naming which element is missing when they don't. This directly checks what #320 asked for:
the operator's actual reply, not a proxy for it.

Considered keeping only the grep-based `run.md`-text test (the original, rejected approach) as the
sole check. Rejected: it verifies that the instruction *exists*, never that a given reply *complied*
with it — an orchestrator could satisfy the grep test while still sending an address-only summary,
which is the exact defect #320 was filed against. Kept the grep test as a secondary, complementary
guard (it catches the instruction itself being silently weakened or deleted in a later edit, which
the `Stop` hook alone would not catch — a `Stop` hook checking for "does the reply match this
pattern" says nothing if the pattern itself has been quietly removed from run.md).

Considered having #320 also declare `hooks.json`'s `Stop` key outright, independent of #318.
Rejected per the #342 review's explicit instruction: #318 and #320 sit on the same hook, and two
independent declarations of `Stop` in the same `hooks.json` would silently clobber one or the other
depending on merge order (only the last-loaded `Stop` array key wins in a JSON object, i.e. one
issue's check would go dark with no error). The ownership rule above (first-to-land declares, second
appends) avoids that without either issue blocking on the other's landing order being known in
advance.

## What will be done

1. In `on-the-record/commands/run.md` step 5, add one new sibling bullet (after the existing
   "구조적 맥락 — flow/stage/next" bullet, before "링크 의무") requiring every PR/board summary to
   frame the change as: (a) 어떤 문제가 해결/제거됐는가, (b) 그 문제가 있었을 때 무엇을
   비용/지장으로 치렀는가, (c) 지금부터 무엇이 새로 가능해졌는가, (d) 아직 무엇이 남았는가/고쳐지지
   않았는가 — stating a bare issue-number/PR-title list does not satisfy this.
2. Add a matching one-line note to the Mission Board's render-format instructions: the fixed
   `[이슈 #<n>] <flow 요약> · <stage> → <next>` shape (#54) stays, but a `done` item's `<flow 요약>`
   must name the resolved problem/effect, not a restated PR title.
3. Add `on-the-record/hooks/report-framing-check.sh`: reads `last_assistant_message` from stdin
   (Stop-hook input shape), detects a PR/board report turn by the step-5 header or Mission Board
   line markers, and checks for language indicating each of the four framing elements. Missing
   element(s) → `decision: "block"` with a `reason` naming which element(s) are absent. Not a report
   turn → no-op (pass through).
4. Wire the handler into `hooks.json`'s `Stop` event, conditioned on landing order per the
   Constraints rule: if `hooks.json` has no `Stop` key when this PR is built, add it with
   `report-framing-check.sh` as its sole entry; if #318 has already added a `Stop` key by then,
   append `report-framing-check.sh` as a second entry in that key's `hooks` array instead of
   redeclaring the key, and record which case applied in the phase-2 record.
5. Add `test_run_md_semantic_reporting.py` (unchanged in shape from the original proposal): asserts
   step 5 and the Mission Board section of `run.md` contain the four framing terms and the
   "bare enumeration doesn't satisfy this" line.
6. Add `test_report_framing_check.py`: feeds `report-framing-check.sh` synthetic
   `last_assistant_message` payloads — one address-only reply (expect `block`), one reply carrying
   all four elements (expect pass-through), one non-report reply (expect no-op) — asserting exit
   behavior and the `block` reason names the missing element.

## Out of scope

- The sibling approval-content issue #318's asking-moment wording and its own `Stop`-hook check
  logic — separate issue, separate handler script, coordinated only on the shared `hooks.json` key
  per Constraints above.
- Role-session PR bodies and `docs/issue-<n>/reports/<role>.md` record formats.
- Retroactively rewriting past session transcripts or the Mission Board's stored-vs-computed
  behavior.
- Any semantic/LLM-graded quality check of *how well* the four elements are expressed — the hook
  checks for their presence (structural/keyword-level), not literary quality; a reply that names all
  four badly still passes, matching #236's existing precedent for this section's ceiling.

## How you'll know it worked

`pytest test_run_md_semantic_reporting.py` fails on `main` today and passes once the two `run.md`
edits land. `pytest test_report_framing_check.py` fails today (script doesn't exist) and passes once
`report-framing-check.sh` correctly blocks the address-only synthetic reply and passes the
four-element one. Together these are the executable artifacts #310 requires: the instruction-text
check and the live-reply check, each verifying a distinct claim and each named as covering only that
claim.
