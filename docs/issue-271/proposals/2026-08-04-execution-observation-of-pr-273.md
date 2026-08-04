# Proposal — execution observation of PR #273 (issue #271, plan step 2)

Phase 1 artifact (role-handoff contract v3 §19). This proposal states
**what will be checked and against what evidence**. It renders no
verdict, provisional or otherwise; every verdict this role produces lands
in `docs/issue-271/reports/execution-observation.md` in phase 2, after a
human approval.

Companion phase-1 artifacts:
`docs/issue-271/reports/execution-observation/survey.md` (current-state
survey, written first), `.../scout-brief.md` (field sweep, aimed at the
survey's method-unknowns).

## Request

Issue #271's execution plan, step 2: independent execution observation of
step 1 — the **implementation** role's session, delivered as **PR #273**
(`issue-271/implementation` → `main`, merged 2026-08-04T06:00:21Z, merge
commit `c6c4363`). The invoking prompt adds one named sub-question: the
integrity of the conflict-resolution rebase performed on that branch mid-PR,
specifically whether it stands in logical conflict with issue #247's
already-landed changes.

## The three verdict levels that will be checked, declared up front

This role's phase-2 record renders a three-level verdict. Naming them here,
before any evidence discussion, is the phase-1 obligation; each level is
listed with the evidence that will decide it and nothing about how it will
come out.

### Level 1 — OUTCOME: did PR #273 land what issue #271 asked

Checked requirement by requirement, against the merged tree at `c6c4363`
and the four branch commits (`ddc9b0f`, `6cd0ef2`, `1cab34b`, `e2bac95`).

| # | Issue #271 requirement | Evidence the check will use |
|---|---|---|
| O1 | Req 1a — trigger-surface enumeration as the proposal's first output, with a per-surface table and stated mitigations for uncoverable surfaces | The proposal's rows A–H at `c6c4363` (already read, survey §2), re-derived against GitHub's authoritative linking doc — including the two facts the scout sweep surfaced: a commit-message keyword closes the issue **without** the PR appearing as a linked PR, and manual sidebar linking is a text-free surface |
| O2 | Req 1b — same-class sweep ("검사 표면 불완전" elsewhere in the gate system) | Whether the proposal and/or record contain an actual sweep with named members and a stated result; survey S7 records this as unknown |
| O3 | Req 2 — phase signal separated from the closing-keyword predicate, proven red-green through the wired form `--pr <n> --autodetect --closes-only` | The `gates/ci.py` hunks of `1cab34b` (`_phase_from_approval`, rewired `_autodetect_issue_phase`), plus the two `t_autodetect_*` test bodies in `gates/test_closes_gate_ci.py` @ `1cab34b`, read for whether they drive the autodetect path or a narrower `--phase`-supplied call |
| O4 | Req 3 — drain-guard discriminating test restored | The 24-line `test_spawn.py` delta at `c6c4363`, read structurally (survey S3) |
| O5 | Req 4 — commit-message-only closing keyword actually blocked, red-green, on real or isomorphic ground | `t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body` and the record's `closed_checks` live-dry-run entry |
| O6 | Constraints — branch-protection settings and the `closes-gate` context name unchanged; `pr_reference.py`'s #228 judgment core respected | The landed delta's file list (`pr_reference.py` absent from `git diff 1d7df88 c6c4363 --stat`) and the `gates/ci.py` hunks |

### Level 2 — TRAJECTORY: was the phase-1→phase-2 path sound

| # | Trajectory question | Evidence the check will use |
|---|---|---|
| T1 | Did phase 1 precede phase 2 on the branch, with only phase-1 homes written before approval | Commit contents and timestamps of `ddc9b0f` (docs-only, 600 insertions) vs. `6cd0ef2`/`1cab34b` |
| T2 | Was the approval a real human act under contract v3 §19 | `gh issue view 271 --comments`: the single comment body, its author, and its timestamp relative to `6cd0ef2`; `gh pr view 273 --json reviews` returning `[]`, i.e. the two-account path was not used; `docs/specs/approvers.md` membership; single-account mode holds because PR author and approver are the same account |
| T3 | Did the role scout when required, and survey before proposing | Presence and content of `docs/issue-271/reports/implementation/survey.md` and `.../scout-brief.md` at `c6c4363`, and their commit order within `ddc9b0f` |
| T4 | Was the mid-PR rebase handled and disclosed | `e2bac95`'s message and record delta; the timeline's single `head_ref_force_pushed` at 05:58:07Z |
| T5 | Was the self-dispatched hunt real and its finding actually resolved before landing | The record's Hunt section against the `--paginate --slurp` hunk in `gates/ci.py` and the `t_pr_commit_messages_paginates_and_flattens` test, both in `1cab34b` |

### Level 3 — STEP: which specific artifact, if any, is deficient

Level 3 is answered per artifact, not in aggregate. The artifacts that will
each be examined and reported on: `gates/ci.py` @ `1cab34b`;
`gates/test_closes_gate_ci.py` @ `1cab34b`; `test_spawn.py` @ `c6c4363`;
`docs/handbooks/operations.md` @ `c6c4363`;
`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`;
`docs/issue-271/reports/implementation.md`. The specific step-level
questions carried in from survey §3, each currently open:

- **P1** — `_phase_from_approval` reads `spawn._issue_comments(repo, issue)`
  **and** `spawn._issue_comments(repo, pr)` (`gates/ci.py` @ `1cab34b`).
  Contract v3 §19's single-account path names an **issue-level** comment.
  The check: whether the PR-comment surface widens the approval predicate
  beyond the contract, and what `gates/flows.py`'s `_pr_approved` does with
  it — read at the pinned tree `git show c6c4363:gates/flows.py`, cited as a
  pre-existing dependency, never as this role's output.
- **P2** — the branch regex moved from `^issue-(\d+)/` to
  `^issue-(\d+)/([^/]+)$`. The check: what branch shapes the anchored form
  now rejects that the prior form accepted, and whether the resulting
  behaviour is fail-closed.
- **P3** — the three surface fetches in `check()`'s phase-1 branch each
  append a blocking message on failure. The check: whether every failure
  and `None` path is fail-closed, per the scout's fail-open/fail-closed
  criteria (explicit-grant structure, every error branch handled, named
  default).
- **P4** — the reachability fix's own reachability: whether any predicate in
  the new path re-couples routing to the checked expression, the CWE-561 /
  CWE-570-571 shape the issue's F1 describes.
- **P5** — `closed_checks` in the record cite `test_spawn.py:3497`, while the
  post-rebase location is `:3749` (the record's own "What did not work" says
  so). The check: whether each `ref:` in `closed_checks` resolves at
  `c6c4363`.
- **P6** — the record's non-blocking hunt note (`_pr_title`/`_pr_reviews`
  do not wrap `json.loads`) — whether the stated "still a block, not a
  silent pass" reasoning holds against the hunks as landed.

### Rebase integrity (the prompt's named sub-question) — method, stated in advance

`git range-diff old_base..old_head new_base..new_head` is the canonical
tool and is **not available here**: survey S5 establishes the pre-rebase
SHAs are unrecoverable (timeline exposes only the post-force-push head
`e2bac95`, branch deleted 06:00:23Z, no reflog in this clone), and GitHub
publishes no reflog for unreachable heads. The substitute the field uses,
per the scout brief, is adopted verbatim: re-review `git diff 1d7df88
c6c4363` three-dot-style as if the branch were a brand-new PR against the
base that already contained issue #247, and ask the **semantic-conflict**
question — textually clean, logically wrong — on each file both changes
touch. Concretely:

- **R1** `spawn.py` — issue #247's `9d1394f` rewrote it; the #271 delta must
  contain no `spawn.py` line at all (survey §2 records it absent from the
  `--stat`; the check confirms it hunk-level).
- **R2** `test_spawn.py` — #247 added `SessionEndVerdict` /
  `SelfTriggeredRespawn` tests; the check is whether the 24-line #271 delta
  is confined to `test_follow_prioritizes_pending_session_end_over_pid_check`
  and leaves every #247-added test present at `c6c4363`.
- **R3** `docs/handbooks/operations.md` — three parties wrote here (#247's
  abandoned-work section, #245's F3 "Blocking for real" wrap-up via PR #272,
  #271's own gate paragraphs). The check is whether all three texts coexist
  at `c6c4363` without one asserting what another denies.
- **R4** the record's post-rebase test-count claims (206/206, 26/26, 10/10)
  are the author's own execution evidence. This role does not re-run them —
  the check is confined to whether the claim is internally consistent with
  the landed delta (e.g. a test-count claim that the delta's added/removed
  test functions contradict).

## What this observation will NOT do

- **Not re-run** any of the observed role's code or tests. The scout brief
  records mutation testing / re-execution as the formally correct
  kill-evidence for a discriminating-test claim and as prohibited for this
  role; the phase-2 record will state that execution boundary explicitly
  rather than blurring a structural read into a run.
- **Not edit** anything under the observed role's paths — no `src/`, no
  `test/`, no `docs/issue-271/reports/implementation*`. Findings return only
  through this role's own record on this role's own PR.
- **Not file an issue.** Under contract v3, issues are user-authored only. A
  finding that warrants one is written up with its evidence in the record
  and left for the human to act on.
- **Not re-open** issue #271's design decisions. Whether the approved
  proposal was the right design is settled; the question is whether the
  session executed it.

## How you'll know it worked

- `docs/issue-271/reports/execution-observation.md` exists on this branch
  and is committed, with `loop_state` transitioned at each phase change.
- The independence statement precedes every verdict-bearing sentence in it.
- All three levels appear, including any level written as "not applicable,
  because X" rather than silently omitted.
- Every verdict-bearing sentence names its source — commit SHA, `file:line`,
  or PR/issue comment URL — adjacent to the verdict, not elsewhere in the
  document.
- Each of O1–O6, T1–T5, P1–P6, R1–R4 is answered or explicitly recorded as
  unresolvable with the reason.
- Any deficiency finding carries the four-part blameless shape — impact,
  timeline, root cause, action item — scaled to the finding.
