# Issue #341 — current-state survey

## Skip condition

This issue leaves a real design decision open (how far a mechanical
check can reach into orchestrator prose), so the scout/survey-skip
conditions do not apply. This is a survey, not a skip record.

## What the issue actually reports

`spawn.py` spawns worktree-isolated sessions; sessions wait mostly on
model latency, not shared resources — confirmed by reading `spawn_cmd`
(spawn.py:2328) and grepping the file for any concurrency primitive:
no `Semaphore`, no counter capping simultaneous spawns, no queue gating
spawn count. The only numeric cap in the file is `RESPAWN_MAX_ATTEMPTS`
(spawn.py:1738), which bounds *automatic re-spawns after a crash*, not
concurrent spawns — a different constraint the orchestrator did not
invoke. So the issue's central fact — "there is no slot limit" — checks
out against the code as of this survey.

## Where orchestrator claims live (or don't)

Traced every place an orchestrator turn's content can end up committed
to git, to find what a gate could bind to:

- **Conversational replies to the user** (where "슬롯 대기" was said):
  never persisted anywhere. `on-the-record/commands/run.md`'s Mission
  Board section is explicit that the board "저장되는 파일이 아니다 —
  매번 ... 그 자리에서 계산해서 렌더링한다" (not a stored file —
  recomputed and rendered fresh every time), and forbids adding new
  fields to back it beyond `loop_state` + live `gh` state. There is no
  git-tracked artifact here at all.
- **`gh issue edit --body`, 실행 계획 (Execution Plan) block**: the one
  place orchestrator-authored structured content *does* land in a
  diffable location (run.md:~275-330). Its grammar (`step N role ‖
  role`) has no field for constraints/dependencies beyond step ordering
  itself, and `closure_sweep.py` only reads it for `flows[].plan`
  reporting — nothing validates step-to-step claims against code.
- **`runs/ledger.jsonl`**: referenced in run.md ("사후 회계는
  runs/ledger.jsonl 에 있다") as a post-hoc accounting log, but it does
  not exist in this checkout and nothing in spawn.py's spawn path (grep
  for `ledger`) writes orchestrator-stated *reasons* to it — only, per
  its stated purpose, spawn/exit accounting.
- **Role session PRs / records** (`docs/issue-<n>/reports/<role>.md`):
  these are the role sessions' own records, not the orchestrator's; the
  orchestrator does not author them, and role sessions don't relay the
  orchestrator's prior-turn claims into them.

Conclusion: today, nothing the orchestrator says in the turn where it
states a constraint is committed to git. `gates/gates.py`'s entire
design (confirmed reading gates.py:1-100) is diff-based — it checks
`git diff --name-status` against `origin/main...HEAD` and fails closed
when the diff itself can't be read. A regex/keyword gate over
orchestrator prose has nothing to diff against, because the prose was
never a commit.

## Adjacent precedent already established (not re-litigated here)

- **#310** names the exact failure shape this issue is the "constraint-
  shaped sibling" of, and explicitly bans the four non-discharges: a
  behavior promise, a memory note, a hardcoded list edit, a doc
  sentence. Any fix here that resolves to "add a sentence to run.md"
  is banned by #310, and the issue text repeats that ban directly.
- **#324** (scheduling behavior — nothing computes real parallelism)
  and **#327** (idle time untreated as a defect) are both explicitly
  out of scope per the issue's own Boundary section; agreed as drawn —
  neither would have caught the *invented claim* itself, only symptoms
  adjacent to it (see next section).
- **#298** (orchestrator is the only actor no gate constrains) — this
  issue is a concrete instance cited there, not absorbed into it.
- **#333** (numbers asserted by hand, not derived) is named as this
  issue's sibling — a limit is a number wearing an operational hat.

## Boundary-drawing check (asked for by the invoking instructions)

Read all three referenced issues' current text (#324, #327, #298) via
`gh issue view`. The boundary as drawn holds up: #324 is about the
absence of a parallelism computation, #327 is about idle time not
being flagged, #298 is about the orchestrator generally being
ungated. None of the three, even fully resolved, would have caught
"the orchestrator asserted a false enforcer for a real constraint" —
that requires binding a claim to its named enforcer, which is what
this issue is specifically about. No correction proposed to the
boundary.

## Write surfaces this proposal will touch

- `test_gates.py` or a new small test module — a regression test
  anchored to the issue's own falsifiable fact (spawn.py has no
  concurrency limit today), so a *future* invented capacity claim that
  someone tries to make real by actually adding a limit to spawn.py
  becomes a visible, diffed decision instead of a silent addition.
- `docs/issue-341/reports/implementation.md` (this issue's own
  record, written in phase 2) — must state, per #310's own acceptance
  clause and this issue's Acceptance section, whether the general
  claim ("orchestrator prose constraints have a named enforcer") is
  mechanically checkable, and why or why not.
- No change to `on-the-record/commands/run.md` beyond what's
  structurally necessary is in scope — a bare advisory sentence there
  is the exact non-discharge both #310 and this issue's invocation
  prohibit.

## Alternatives considered during survey (for the proposal's Rationale)

1. **Keyword/regex gate over orchestrator chat transcripts** — rejected
   at survey stage: there is no transcript artifact committed to git
   for a gate to scan (see above), and even if session logs were
   captured, classifying "waiting for slot" as a false-constraint claim
   vs. a legitimate one is a natural-language judgment call, which is
   exactly the kind of check gates.py's own docstring says a mechanical
   gate must refuse to attempt ("불확실하면 막는다" — a gate that must
   guess is worse than no gate, because it launders a guess as
   enforcement).
2. **Require constraint claims to route through a new spawn.py flag
   that logs to runs/ledger.jsonl, then gate the ledger** — considered
   more seriously; rejected for the proposal's core mechanism (though
   noted as the real structural prerequisite if the project wants
   enforcement here) because the routing itself stays voluntary: the
   orchestrator can still state a constraint in the chat turn without
   ever calling the flag, which is exactly what happened in the
   incident this issue reports. Building the flag does not, by itself,
   close the gap the issue names.
