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

- **#298** — orchestrator has no gate infrastructure at all (structural,
  repo-wide). #318 is one instance under that umbrella; building the
  general PreToolUse-style enforcement for orchestrator prose is #298's
  scope, not #318's. #318 only needs *some* executable artifact that
  fails on regression for its own narrow requirement (per #310's own
  acceptance test, "prose does not discharge" does not mean "must ship
  full runtime enforcement" — it means the requirement must be traceable
  to something that fails when it regresses).
- **#303** — hardcoded-list-edit anti-pattern (verification-environment
  cache paths). Unrelated surface.
- **#309** — memory-note anti-pattern. Unrelated surface.
- **The *number* of approval requests** — the issue's own "Note on
  scope" says this is separate and filed separately; #318 only fixes
  *content*, never touches when/how often a request is raised.
- **#236 (link obligation)** and **이슈-54 (flow/stage/next)** — already
  live in the same step-5 bullet list; #318 adds to that same list
  without altering those two blocks.

## Constraint check — mechanical enforceability

The requirement ("approval request must contain six analysis items") is
about the CONTENT of a live conversational turn the orchestrator session
produces — there is no file the orchestrator writes that a PreToolUse
gate could inspect at the moment the question is asked (unlike role
sessions, whose deliverables are files gated by board-gate /
approval-gate / trailer-gate). Runtime enforcement of "did the
orchestrator's actual chat message contain X" is out of reach without
the gate infrastructure #298 would need to build (a PostToolUse-style
transcript check does not exist in this plugin).

What IS reachable within #318's write set: run.md is itself the
executable spec the orchestrator session reads before acting — a
regression test that parses the file and asserts the required elements
are present in the approval-request instruction block gives exactly what
#310 asks for: an artifact that fails the moment someone strips a
required item from the instructions (same shape as the existing
`test_flows_plan_*` tests, which parse markdown text as data). It does
not verify a specific live approval message; it verifies the spec that
governs every future one has not silently regressed. The proposal states
this scope plainly rather than claiming more.
