# issue-44 — coding: phase-1 survey (current-state)

Survey of the current state relevant to issue #44 ("orchestrate: role-selection guide — stop
defaulting every request to coding"), covering `orchestrate/commands/run.md` as it stands today,
what issue-34 already landed in it, what issue-43 changed (and did not change), and what
`docs/issue-43/reports/feasibility.md` concluded that this proposal must honor.

## 1. What run.md currently says about role selection

`orchestrate/commands/run.md` (read in full on branch `issue-44/coding`, no local edits) has no
explicit role-classification step. The loop section ("당신의 루프") is:

1. requirement → issue draft → `gh issue create` after user confirmation.
2. "누구를 깨울지" — run `spawn.py wake -C <repo>`, read the board, and propose the role(s) that
   WAKES-ON points to **in one paragraph**. The text already distinguishes mechanically-decidable
   wake edges from judgment edges: "기계로 판정 불가한 줄(product·ops 의 내용 판단)은 '못 잰다'로
   말한다 — '안 깨어났다'로 옮기지 마라" (lines 21-23) — i.e. when a wake edge can't be judged
   mechanically, the orchestrator must say "can't be measured," not silently treat it as "did not
   wake."
3. spawn the role in the background.
4. explain the PR.
5. relay the user's decision (comment / approve / merge / close).

Before spawning ("띄우기 전에 확인할 것"), step 1 says "역할이 맞는가" — read the target role's
`roles/<role>.json` catalog (`decides` / `use_when` / `produces`) and cite it as the basis for
which role to wake; "요청과 역할이 어긋나면 띄우지 말고 되물어라" (if the request and the role
don't match, don't spawn — ask again).

**Gap**: nothing in the current text requires the orchestrator to *state a classification* before
drafting the issue (step 1 of the loop, which precedes role selection at step 2). The "역할이
맞는가" check in the preconditions section is a check against one already-chosen role's catalog,
not a request-type classification that picks among feasibility / product / ux-design / coding
before the issue is even drafted. This is exactly the gap issue #44 reports empirically (coding
6x, qa 2x, verify 1x, no product/ux-design/reflect/ops proposed, and research-first only happened
because the user asked for it in issue #43).

## 2. What issue-34's summary obligations require

Issue-34 landed as PR #47 (commit `2253f9d`, "feat(issue-34): mandate read-before-ask summaries
in orchestrate approval loop"), now present in run.md step 4 ("PR 을 설명한다", lines 33-47). It
requires that before *any* approval/merge request to the user, the orchestrator must have actually
read the relevant files (proposal for phase-1 approval, diff/commits for phase-2 merge) and fill a
fixed four-item summary — what's changing, why, (at merge time) what actually changed, how it was
verified — before asking a closed yes/no question; skipping straight to "a PR is up, approve?" is
called a procedure violation (절차 위반) in the text itself.

This is a **downstream** gate (it governs how the orchestrator asks for approval on a PR that
already exists) and does not touch role selection (which happens **upstream**, before the issue is
even drafted). Issue #44's classification obligation is a new, separate obligation that belongs at
step 1 of the loop (or as new step 1.5), not a replacement for or a duplicate of issue-34's gate.
The two are compatible and can literally reuse the same "explicit statement + violation framing"
pattern issue-34 already established, for consistency of voice.

## 3. What issue-43 changed

Issue #43 ("research: how do existing multi-agent systems handle human wait time, goal drift, and
status visibility") is closed, with its phase-1 survey + proposal merged as PR #45
(`docs-issue-43/reports/feasibility/survey.md`, `docs/issue-43/proposals/feasibility.md`) and its
phase-2 verdict recorded at `docs/issue-43/reports/feasibility.md`. **Crucially, issue-43's own
scope is wait-time productivity / goal-drift guarding / status visibility (mission board,
decision-queue batching, parking lot) — a different topic from issue #44's role-selection gap.**
`git log --oneline -- orchestrate/commands/run.md` shows the last commit touching run.md is
issue-34's `2253f9d`; issue-43 has **not yet edited run.md** — its verdict only authorizes opening
a *separate design issue* for the orchestrate procedure (still not filed as of this survey), which
will presumably propose mission-board/batching/parking-lot changes to run.md later.

**Practical consequence for issue #44**: there is no live conflict today — run.md is unedited by
issue-43 — but issue #44 explicitly notes "whichever lands second must integrate, not overwrite."
Since issue-43's design issue is not yet filed, issue #44's phase-2 edit (a future session) should
land its role-selection section in a way that doesn't presuppose or foreclose issue-43's eventual
mission-board/batching change to the same "당신의 루프" section (e.g. avoid renumbering the whole
loop from scratch; insert as a clearly delimited step so a later insertion doesn't have to
re-diff the whole loop).

## 4. What the feasibility report concluded, and its conditional-go conditions

`docs/issue-43/reports/feasibility.md` (verdict: **CONDITIONAL-GO** on opening the design issue
for the orchestrate procedure) lists four conditions carried over from the approved proposal:

1. Design must specify the mission board strictly as a **read view** over existing report files —
   no new mutable state competing with `docs/issue-<n>/reports/<role>.md` as ground truth.
2. Design must show decision-queue batching cannot merge into, or substitute for, individual PR
   Approve acts — batching is UI aggregation only, never a bulk-approve action.
3. Design must define parking-lot → issue-promotion criteria explicitly, or drop the parking lot.
4. The design issue must re-run three unverified survey angles (Devin/Cursor/Copilot Workspace,
   OpenHands/SWE-agent, AutoGen/CrewAI/LangGraph) with search access before finalizing its
   mechanism choice.

Conditions 2-4 are specific to the mission-board/batching/parking-lot mechanisms and don't apply
to issue #44's role-selection guide (a text-only addition to the loop, not a new mechanism,
queue, or automated decision). **Condition 1's underlying principle does generalize** and this
proposal honors it explicitly: the role-selection guide must not introduce any new file or store
as a second source of truth — it is pure procedure text inserted into `run.md`, reasoning stated
in conversation each time (per issue #44's own requirement), not persisted to a new doc/board file
that would compete with `docs/issue-<n>/reports/<role>.md`. No new mutable state is proposed here.

The feasibility report's broader posture — every candidate mechanism must be additive, reversible,
and must not become a bypass for a human-only decision (its threat-model probe: "a batching UI
silently becoming a bulk-approve action" would violate "silence is not consent") — is echoed by
issue #44's own violation framing ("defaulting to coding without stating the classification is a
procedure violation") and by the requirement that judgment lines (product/ops) be answered with an
explicit proposal rather than silently passed over. Both issues converge on the same underlying
rule: the orchestrator must never let a judgment call default silently; it must be stated in
conversation and reasoned about.

## Summary of gaps this proposal must close

- No classification step exists before issue drafting (loop step 1) — issue #44's core ask.
- No request-type → leading-role mapping table exists anywhere in run.md.
- No explicit "defaulting to coding without classification is a violation" framing exists (only
  the analogous violation framing issue-34 added, for the approval-summary gate).
- The existing "product·ops 의 내용 판단...'못 잰다'" line (run.md line 22-23) stops at labeling
  the judgment line unmeasurable; it does not yet require an explicit proposal be made every time
  such a line appears — issue #44 asks for that obligation to be added.
