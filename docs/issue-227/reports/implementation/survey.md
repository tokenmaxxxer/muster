---
kind: survey
subject: issue-227
date: 2026-08-03
---

# Current-state survey — conditional approval relay

## Issue text and evidence attached

Issue #227 body (조건부 승인 릴레이 규칙 미명문화): the approval-gate recognizes
only an exact-string comment `APPROVE issue-<n>/<역할>` as approval, but the
orchestrator playbook (`/orchestrate:run` step 6, contract v3 s19) states two
separate rules — "approval canon is the issue comment" and "change requests
go via `gh pr comment`" — with **no rule for doing both at once** (conditional
approval). Requirements: (1) codify the canonical conditional-approval form
— token-only comment + feedback in a *separate* comment, with order/location
specified; (2) confirm, with evidence, what the gate actually safely
recognizes; (3) state the relationship to adjacent code defect #224 (this
issue is contract-document-side, not code-side).

Attached real-world evidence (issue #227's own comment, 2026-08-03), both
from the `repo-status-board` (rsb) pilot repo:

- **rsb issue #23** (`tokenmaxxxer/repo-status-board#23`), comment by
  `jjongkwann`, 2026-08-02T16:40:03Z:
  ```
  APPROVE issue-23/implementation

  조건부 승인 — PR #24 리뷰 코멘트(2차 교차 검토 4건)를 phase 2에서 반영할 것.
  ```
  Per issue #227's comment, phase 2 proceeded and committed 18 minutes later
  — i.e. this mixed comment was treated as a valid approval event somewhere
  in the pipeline, without a strictly-matching token ever being posted.

- **rsb issue #20** (`tokenmaxxxer/repo-status-board#20`), comment by
  `JiwonJung94`, 2026-08-01T10:30:31Z:
  ```
  APPROVE issue-20/finance-unit-economics
  (phase 2 반영 사항 — 승인자 피드백 2건: ① ... ② ...)
  ```
  Also followed by phase-2 work and a completion comment — same pattern,
  token as first line, trailing text in the same comment body.

## Where the actual matcher lives (this repo)

Two *different* pieces of code in on-the-record implement string-based
approval detection, for two different purposes:

1. **`spawn.py:917`, `approve_scope()`** (issue #115) — scope approval, a
   phase-1-adjacent gate: `needle = f"APPROVE {subject}/scope"`, matched via
   `c["body"].strip() == needle` (`spawn.py:926`). This hardcodes the literal
   word `scope`, not the role name. **This is the object of adjacent issue
   #224** ("`approve-scope` 문자열 불일치... `/scope` vs 정본 `/role`") — a
   code-side defect, out of scope here.

2. **`gates/flows.py:125-136`, `_pr_approved()`** — this is the function
   whose docstring literally cites contract v3 s19 ("Two detection paths
   from contract v3 s19"): `needle = f"APPROVE {subject}/{role}"` (line 131),
   matched via `c["body"].strip() == needle and c["login"] in approvers`
   (line 132) — i.e. **strict whole-body equality after only leading/
   trailing whitespace stripping**; the second path is a PR review `state ==
   "APPROVED"` from a distinct approvers.md login (line 135-136).
   `_pr_approved()` is consumed only by the status-board reporting path
   (`gates/flows.py:304-333`, populating `decision_queue` /
   `unapproved_open_prs`) — per `on-the-record/commands/run.md:178-181`
   ("보드는 절대 행동을 취하지 않는다 — 집계·표시만 한다"), the board never
   blocks anything; it only reports.

**Empirical run (2026-08-03, this survey) — reproducing the rsb #20/#23
comment shapes as real inputs to the real functions**: per PR #254 reviewer
feedback, the earlier draft of this survey stopped at the structural
argument below ("a longer string cannot equal a shorter prefix of itself")
without actually executing the two gate functions. That argument is not
wrong, but it is not evidence on its own — it substitutes reasoning about
the code for running it. This revision runs both `spawn.py::approve_scope()`
and `gates/flows.py::_pr_approved()` directly, feeding each the real rsb
comment bodies (verbatim) or a needle-isolated variant (see below), with all
GitHub I/O monkeypatched exactly as `test_approve_scope.py`'s existing
harness does (no network, no gate-code change). Script:
`tmp_issue227_repro.py` (repo root, not committed — throwaway evidence
script; reproduce by re-running the snippet below against this branch).

`gates/flows.py::_pr_approved()` — real subject/role names match the
function's own needle shape (`APPROVE {subject}/{role}`), so the two rsb
bodies are used **verbatim, unmodified**:

| input (verbatim body) | subject/role | `_pr_approved()` result |
| --- | --- | --- |
| rsb #23: `"APPROVE issue-23/implementation\n\n조건부 승인 — PR #24 리뷰 코멘트(2차 교차 검토 4건)를 phase 2에서 반영할 것."` | issue-23/implementation | **`False`** |
| rsb #20: `"APPROVE issue-20/finance-unit-economics\n(phase 2 반영 사항 — 승인자 피드백 2건: ① ... ② ...)"` | issue-20/finance-unit-economics | **`False`** |
| control — token only, no trailing text | issue-99/implementation | `True` |
| synthetic supplement — prose *before* the token (issue text says "토큰 앞뒤", real specimens only show *after*; added to cover the "before" half) | issue-99/implementation | **`False`** |

`spawn.py::approve_scope()` — its needle is hardcoded to the literal suffix
`/scope` (line 917), never the role name; feeding it the rsb bodies verbatim
fails immediately on that literal mismatch, which is issue #224's defect,
not this issue's question. To isolate the variable this issue actually asks
about (does trailing/leading prose break the match, holding the needle
itself correct), the same rsb shapes are re-run with the suffix swapped to
`scope`:

| input | `approve_scope()` result |
| --- | --- |
| rsb #23 shape, needle-isolated: `"APPROVE issue-23/scope\n\n조건부 승인 — ..."` | **`SystemExit`** — "승인 코멘트를 못 찾았다" (rejected, no commit made) |
| rsb #20 shape, needle-isolated: `"APPROVE issue-20/scope\n(phase 2 반영 사항 — ...)"` | **`SystemExit`** — rejected, no commit made |
| control — token only | `rc=0`, `loop_state` written to `scope-approved`, commit made |
| synthetic supplement — prose before + token | **`SystemExit`** — rejected |
| reference run — rsb #23 body verbatim, **no** needle isolation | `SystemExit` — rejected (here for the `/scope`-vs-`/role` literal mismatch, i.e. issue #224's defect, confirmed separately and not conflated with the above) |

**Conclusion, now evidence-backed by execution, not just inspection**: both
real gate functions in this repo reject both real rsb comments outright —
`_pr_approved()` returns `False`, `approve_scope()` raises `SystemExit` and
writes nothing. The structural argument from the first draft ("a longer
string cannot equal a shorter prefix of itself") turns out to agree with the
execution, which is itself a useful confirmation, not a substitute for
having run it. Whatever actually let phase 2 proceed in both rsb cases is
not either function in this repo; it is either a human/orchestrator
judgment call at the moment phase 2 was spawned, or a different
(undocumented, out-of-repo) check in a role-side plugin. Either way, the two
real cases currently sit as "technically unapproved" from this repo's own
status-board's point of view even though work already shipped — exactly the
contract-vs-practice gap the issue names, and exactly the moment a
non-canonical-form-handling policy (see proposal) needs to fire.

## The orchestrator playbook's actual gap

`on-the-record/commands/run.md` step 6 (line 183-207) lists, as separate
bullets with no combined case:
- 수정 요구 → `gh pr comment` (line 196)
- 제안 승인 → `gh issue comment <issue-n> --body "APPROVE issue-<n>/<역할>"`,
  with the explicit note "approval-gate 가 이 정확한 문자열만 승인으로
  인정한다" (line 197-198)

Nothing tells the orchestrator what to emit when the user's spoken decision
is "approve, but fix X" in the same breath — which is exactly the situation
both real rsb comments came from. `docs/handbooks/operations.md:309-364`
duplicates the same canon (issue comment is canonical location; PR review
Approve is multi-account-only) without a combined-case recipe either.

## Current state: no policy exists for a role session that sees a
non-canonical near-miss

Issue #227's own comment (2026-08-03) adds a second requirement: a decision
for how a role session that encounters a non-canonical form (token +
prose, mixed in one comment) should behave — the two rsb incidents show a
role/orchestrator session treating such a comment as if it were a valid
approval and proceeding into phase 2 regardless (the empirical run above
confirms neither this repo's own gate function would have agreed). Searching
this repo turns up **no existing code path that reacts to a near-miss
comment at all** — `approve_scope()` and `_pr_approved()` both either match
exactly or produce a plain rejection (`SystemExit` / `False`) with no
distinct signal for "something approval-shaped just failed to match, tell
someone." The role session that actually waits for phase-2 approval (the
`SessionStart` hook surfacing "PR #NNN (OPEN); approvals: ..." into a role's
context, as seen at this very session's start) lives in a separate,
out-of-tree plugin (per the "Write set" section below) — this repo cannot
patch that hook, but it *can* document what that hook (and the orchestrator
relaying to GitHub) should do on a near-miss, the same way it already
documents the two-comment recipe. This is the current-state gap the
proposal's policy decision (warn vs. abort vs. log-only) fills.

## Prior, closed design decisions that bound this issue

`docs/decisions/2026-07-29-permanently-closed-alternatives.md` records that
this project already tried and permanently rejected three
natural-language-parsing designs for approval detection (each leaked a
different way — e.g. the target state's name appearing anywhere in text
read as approval, a negation denylist missing forms, a sentence-scoped
rewrite still minting approval from adversarial phrasing) and settled on
exact-string comment matching specifically *because* "deciding whether two
strings are equal is not a language problem." A separate rejected-alternative
entry: "a model as scheduler" — an LLM must never be the thing deciding its
own authorization; a hook is deterministic, a model's judgment is not. Any
proposal that loosens the matcher (e.g. first-line-only matching, a stop
token, a smarter regex) would re-open exactly the surface this decision
closed. This bounds the solution space hard: the fix has to be on the
recipe/practice side (what gets posted), not the matcher side (how it's
read) — which matches the issue's own constraint.

## Adjacent issue #224 (code-side, not superseded by this issue)

Issue #224 bundles three reliability defects: (1) `approve-scope` string
mismatch — literally `spawn.py:917`'s hardcoded `/scope` vs. the canonical
`/role` suffix that `gates/flows.py:131` already uses correctly; (2) issue
comment fetch has no `--paginate`, so an approval token past the 30th
comment is invisible to the gate; (3) `watch --follow` can loop forever
against a crashed session. None of these three are addressed here — #227 is
document/practice-only and does not touch matcher code, per its own
constraint.

## Write set actually available to this issue

Everything the phase-2 fix can touch lives inside on-the-record's own tree
(this repo — the orchestrator-side plugin source and its docs), *not* in
the role-side plugin that actually gates phase-2 bootstrap (that lives in a
separate plugin repo, e.g. `tokenmaxxxer-core`/`implementation-rulebook`,
outside this repo's tree and outside this issue's write set):

- `on-the-record/commands/run.md` — step 6's relay recipe (has direct edit
  history for exactly this kind of change: commit `7372643`, issue-126,
  "unify approval canon to issue comment").
- `docs/handbooks/operations.md` — mirrors the same canon for human readers
  (lines 309-364).
- A new decision doc under `docs/issue-227/decisions/` — this is a
  wire-format/protocol-recipe decision (doctrine ladder: "a library-or-format
  choice over a named alternative ... -> docs/issue-<n>/decisions/"),
  recording the chosen two-comment recipe, the rejected alternatives, and
  the empirical strict-match evidence above.

No spawn.py, gates/*.py, or other code file needs to change for this issue's
scope.
