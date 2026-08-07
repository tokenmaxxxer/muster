# Survey — issue #318

## Where approval-request content is generated

The orchestrator has no PreToolUse gate over its own conversational output
(confirmed in the open #298 — "orchestrator is the only unenforced actor,"
9 gates constrain role sessions, 1 constrains the orchestrator, and that
one only checks write scope). So the only place that shapes what an
approval request says is prose: `on-the-record/commands/run.md`, step 5
("PR 을 설명한다"), the sub-bullets for "1단계 승인 요청 시" and "2단계
머지(수용) 요청 시".

Current text (`on-the-record/commands/run.md`, step 5) requires exactly
four items across both request kinds:

- 1단계: (1) 무엇을 바꾸려 하는가, (2) 왜, (3) 어떻게
- 2단계: (1) 무엇이 바뀌었는가, (2) 어떻게 검증됐는가
- shared closing line: "최소한 다음 네 항목을 담아야 한다: 무엇을
  바꾸는가, 왜 바꾸는가, (머지 시) 실제로 무엇이 바뀌었는가, 어떻게
  검증됐는가."

None of these four cover: what was investigated and concluded, what
becomes possible/impossible afterward, what alternative was considered
and rejected (and why), or what risk/tradeoff the operator accepts by
saying yes — all six items the operator's issue text names explicitly.

Also present in step 5, structurally separate: the flow/stage/next block
(이슈-54) and the link-obligation bullet (이슈-236). Both were added the
same way — a prose bullet appended to run.md, no executable check. #310
(filed the same day, still open) calls this exact pattern out as one of
the four "looks like compliance but isn't" discharges (a sentence added
to a doc). #318 explicitly inherits that constraint via its own
Acceptance section.

## Precedent for the same class of change

`git log -S"링크 의무" -- on-the-record/commands/run.md` → commit
`2808632` (issue-236 phase 2): a prose bullet added to run.md with no
test. That is the shape #310 now disqualifies as a discharge.

No existing test reads `on-the-record/commands/run.md` as data (checked
`grep -rn "run.md" test_spawn.py test_flows.py test_gates.py spawn.py
gates/*.py` — the only two `run.md` mentions are docstrings about the
*execution-plan* parser, `gates/flows.py`, which parses **issue bodies**,
not run.md itself). So there is no established pattern in this repo yet
for mechanically checking a prose instruction file's content — this
would be new.

## What #318 does NOT cover (sibling-issue boundary)

- **#298** — orchestrator has no gate *declared* over its own
  conversational output (a `Stop` hook capable of this exists in Claude
  Code but is not declared in this plugin's hooks.json — see the
  corrected "Constraint check" section below). Declaring that hook and
  wiring it into `on-the-record/hooks/hooks.json` is general
  orchestrator-output enforcement infrastructure — #298's stated
  subject, not #318's. #318 owns the six-item requirement and a
  pure, hook-independent function that checks a message string against
  it; #298 owns deciding whether/how a `Stop` hook calls that function
  at runtime, alongside whatever else #298 gates.
- **#303** — hardcoded-list-edit anti-pattern (verification-environment
  cache paths). Unrelated surface.
- **#309** — memory-note anti-pattern. Unrelated surface.
- **The *number* of approval requests** — the issue's own "Note on
  scope" says this is separate and filed separately; #318 only fixes
  *content*, never touches when/how often a request is raised.
- **#236 (link obligation)** and **이슈-54 (flow/stage/next)** — already
  live in the same step-5 bullet list; #318 adds to that same list
  without altering those two blocks.

## Constraint check — mechanical enforceability (corrected 2026-08-07)

**Correction.** An earlier version of this survey stated that "there is
no file the orchestrator writes that a PreToolUse gate could inspect at
the moment the question is asked" and that runtime enforcement of the
orchestrator's own chat message was "out of reach without the gate
infrastructure #298 would need to build." That is wrong, and PR #338 was
rejected on exactly this point (review comment, 2026-08-07).

The fact: Claude Code's `Stop` hook exists and fires when the assistant
finishes a turn. It receives `last_assistant_message` — the turn's final
assistant message **body text** — plus `session_id`/`transcript_path`.
Its return can set `decision: "block"` + `reason` to block that response
outright, or `hookSpecificOutput.additionalContext` to inject a
requirement without blocking. (`transcript_path` is written
asynchronously and may not yet contain the current turn, so
`last_assistant_message` is the field to read.) Source: Claude Code
hooks reference, https://code.claude.com/docs/en/hooks.md, checked
2026-08-07.

This means the orchestrator's own conversational output — the exact
surface an approval request is written on — **is** inspectable and
blockable. It was not built in this plugin (`on-the-record/hooks/hooks.json`
declares only `SessionStart`, `UserPromptSubmit`, `PreToolUse`), but
absence of a declaration is not absence of the capability. The correct
reading is: reachable in principle, requires a new hook declaration to
reach in this plugin — not "unreachable."

## Root cause — how the wrong premise got recorded as "confirmed"

The original survey's claim was built by reading this plugin's own
`on-the-record/hooks/hooks.json` (which event types are currently
*declared*) and the open #298 issue text (which frames the orchestrator
as having "no gate infrastructure at all"), and treating the union of
those two — configuration plus a sibling issue's framing — as if it were
a statement about what Claude Code's hook system is *capable of*. Both
sources are true on their own terms: hooks.json really does declare only
three events, and #298 really does argue the orchestrator lacks a
PreToolUse-style *enforcement gate*. Neither source was ever a claim
about which hook events exist upstream. The survey never consulted the
Claude Code hooks reference itself — the one document that could have
answered "does a hook exist that sees the orchestrator's own reply" —
before writing "confirmed" against a sentence that generalized from
"not declared here" to "not possible anywhere."

This is the same failure class already on record as #287 ("확인 못 한
것을 확인해서 깨끗한 것으로 보고" — reporting something as checked-clean
when what was actually checked was narrower than the claim). The
proximate fix here is factual (read the primary source before writing
"confirmed"); the standing fix — making "confirmed" require a named,
checkable source rather than an inference from adjacent config — is not
re-litigated in this issue, since #318's scope is approval-request
content, not survey-methodology enforcement.

## What IS reachable within #318's write set, corrected

Two things now sit inside #318, not one:

1. **The run.md text itself** stays the executable spec role/orchestrator
   sessions read before acting, and a regression test over its six
   required marker phrases is still worth keeping — it catches someone
   silently stripping a requirement from the instructions, which a
   runtime message-content check does not (a Stop hook only fires on
   turns that actually happen; it says nothing about whether the
   instruction that should produce those turns is still there to read).
2. **A pure content-check function** — given a candidate approval-request
   message string, decide whether all six required items are present,
   returning enough detail to drive either a `block` decision or an
   `additionalContext` nudge. This function is ordinary code: it has no
   dependency on hooks.json, fires no hook, and is fully unit-testable
   with string fixtures the same way `gates/flows.py`'s markdown parsing
   is tested today.

What stays out of #318 (see updated boundary section below): actually
*declaring* the `Stop` hook in `on-the-record/hooks/hooks.json` and
wiring it to call the function above. That declaration is general
orchestrator-output enforcement infrastructure — the exact thing #298's
own text frames as its subject ("orchestrator is the only unenforced
actor... building that surface is the entire subject of the already-open
#298"). Building the checker here and leaving its hook wiring to #298
keeps #318 and #298 from silently merging into one issue, which is the
same item-7 principle the original proposal already invoked for a
different alternative.
