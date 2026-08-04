files:
- gates/ci.py
- gates/test_closes_gate_ci.py
- test_spawn.py
- docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md

Survey: [[survey.md]](../reports/implementation/survey.md). Scout brief:
[[scout-brief.md]](../reports/implementation/scout-brief.md).

## Request

Issue #271 (jjongkwann), following three independent 2026-08-04
observations of the same gap (issues #245, #262, #266): the plan-aware
Closes gate (`gates/pr_reference.py` + `gates/ci.py`, issue #228/#245)
only inspects a PR's description text. Two issues auto-closed for real
that same day because a branch commit's message — not the PR
description — carried a closing-effect keyword; both required a manual
reopen. A third, independent defect was found in the same wiring: the
CI orchestration layer derives which rule-set to apply (the "phase")
from the very same closing-keyword signal the requirement-2 check
("a phase-1 PR must not carry a closing keyword") is supposed to police,
which makes that check structurally unreachable on the code path the
required CI check actually runs. Requested: (1) an exhaustive inventory
of every surface that can make GitHub auto-close an issue, whether each
is inspected today, and a named mitigation for any surface that cannot
be inspected — plus a sweep of the rest of the gate system for other
members of the same "incomplete input surface" defect class; (2) a
concrete fix separating the phase signal from the closing-keyword
predicate so the requirement-2 check becomes reachable; (3) restoration
of the one test that used to make the drain-priority block in
`spawn.py:1884-1892` fail if deleted, whose precondition arrangement
issue #266's own (unrelated, correct) fix quietly invalidated; (4) a
red→green regression proof, run against the actual wired invocation
form (`gates/ci.py . --pr <n> --autodetect --closes-only`), that a PR
whose only closing-effect signal lives in a commit message is blocked.

This is phase 1: research, survey, and this proposal only. No code,
workflow, or branch-protection change is made in this PR. This PR's own
body names `#271` in prose only.

## Trigger surface inventory

Per requirement 1, the first deliverable. Columns: what GitHub itself
honors as a closing surface (per GitHub's own documentation, confirmed
this session — scout-brief.md Source 1/2), whether any gate in this
repository inspects it today, and how to add or why it cannot be added.

| # | Surface | GitHub honors it? | Inspected today? | Coverage path |
|---|---|---|---|---|
| A | PR description text | Yes (documented) | **Yes** — `pr_reference.check_body` via `gh pr view --json body` | Already covered; unchanged by this proposal. |
| B | PR title text | Yes (documented — GitHub's own docs name titles alongside descriptions and commit messages) | No — `_pr_view` fetches `title` and discards it (`pr_reference.py:66-72`) | Apply the existing `_CLOSES_REF` pattern to the fetched title, same as description. Low cost: the field is already in the `gh pr view` response being fetched. |
| C | Each commit's message on the PR branch | Yes (documented; **measured** — both real 2026-08-04 incidents) | No — no code path in `gates/` reads commit messages at all (repo-wide grep, this session) | `gh api repos/<slug>/pulls/<n>/commits`, apply `_CLOSES_REF` to each `commit.message` (the issue's own suggested mechanism). |
| D | Squash-merge commit message | Yes (same text channel as C) | No, but **transitively covered by C**: this repository's squash template (`squash_merge_commit_message: COMMIT_MESSAGES`, confirmed live via `gh api repos/<slug>`) means the squash commit's message *is* the concatenation of the branch's own commit messages — covering C pre-merge covers this path's actual content. | No separate code needed once C is covered; noted here so the enumeration is explicit rather than assumed. |
| E | Rebase-merge replay of branch commits | Yes (same text channel as C) | No, but **transitively covered by C** for the same reason — rebase replays each commit with its original message unchanged. | No separate code needed once C is covered. |
| F | Ordinary merge commit's own message | Yes in principle — this repo's merge-commit template (`merge_commit_message: PR_TITLE`) copies the PR title into the new merge commit's body (confirmed by reading two real merge commits in this repository's history this session) | No directly, but **transitively covered by B** — the merge commit's body is a verbatim copy of the title this proposal already covers pre-merge. | No separate code needed once B is covered. |
| G | A human manually retyping the squash/merge commit message at merge time, diverging from the auto-generated template | Yes | **Cannot be inspected before the fact** — the text does not exist until the merge action itself produces it; every check above runs pre-merge against PR/commit metadata that predates this text. | Not coverable by a pre-merge gate by construction. Mitigation: `gates/closure_sweep.py`'s existing post-hoc board sweep is the recovery path already in use for this whole class of miss (both real incidents in this survey were caught and reversed by a human, not by a gate) — see Out of scope for why this proposal does not also try to extend that sweep's own coverage of the same gap. |
| H | Manually linking an issue to a PR via GitHub's UI (the issue's "Development" sidebar), with no closing-effect keyword text anywhere | Yes — GitHub closes the issue on merge purely from the stored link, no text involved | **Cannot be inspected by any text/regex check** — there is no text surface to read. | Partial mitigation only: `gh pr view --json closingIssuesReferences` reflects manually-linked issues (per GitHub's documented purpose for that field) and could be queried supplementally. Tested this session against a real incident PR and confirmed the field does **not** reflect commit-message-derived closes (empty result on a PR that in fact auto-closed its issue via a commit message) — so it is not a substitute for C, only a narrow supplement for H specifically. This proposal does not add that supplemental check (see Out of scope); it is named here as the one surface this issue's own requested mechanism (regex over text) cannot reach at all, satisfying requirement 1's "사유와 완화책" ask. |

**Same-class sweep (requirement 1's second ask).** One other gate-system
member computes closing-reference presence from PR-description text
alone: `gates/closure_sweep.py`'s `_refs_issue()` (`:29-35`), same root
cause as row C's pre-fix state. Repo-wide grep for the shared regex
family (`_CLOSES_REF`, `_pr_view`) found exactly these two files and no
third. Unlike the merge-blocking gate this proposal fixes,
`closure_sweep.py` never blocks a merge — it only reports drift after
the fact — so leaving it as a documented-but-unfixed instance of the
same class does not reopen the premature-auto-close hole requirement 4
asks to be closed. See Out of scope for why fixing it is not in this
proposal's write set.

## Constraints

- `gates/pr_reference.py`'s `check_body`/`check` judgment logic is
  unchanged by this proposal — the surface-widening and predicate
  separation are both implemented in `gates/ci.py`'s orchestration
  layer, which already wraps every call into `pr_reference`. If phase-2
  execution finds this impossible, that becomes a recorded deviation,
  not a silent scope change.
- The wired CI invocation form stays `gates/ci.py . --pr <n>
  --autodetect --closes-only`; the requirement-4 regression proof must
  exercise this exact form (per the issue's own instruction), not a
  narrower unit call with `--phase` supplied explicitly the way the
  prior (insufficient) requirement-2 proof did.
- Branch protection settings and the `closes-gate` required-check name
  are unchanged (issue's own constraint).
- Both single-account approval mode (issue comment `APPROVE
  issue-<n>/<role>`, this repository's live default) and two-account
  mode (a PR review Approve from a different `approvers.md` account)
  must keep working — matches the same constraint issue #245's own
  wiring proposal already committed to
  (`docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`).
- `spawn.py`'s `_watch`/drain-order code at `:1884-1892` is not modified
  — requirement 3 asks only for the test that discriminates it to be
  restored, not for its behavior to change.

## Rationale

**Chosen (requirement 2): derive the autodetected phase from a human
approval event — the same `APPROVE issue-<n>/<role>` exact-string issue
comment (or differing-account PR review Approve) contract v3 s19
already defines as what opens phase 2 — instead of from closing-keyword
presence in the PR body.** Concretely: extend `_issue_from_branch`'s
regex to also capture the role segment (mirroring
`gates.py:465`'s `BRANCH_ROLE = re.compile(r"^issue-[^/]+/([^/]+)$")`),
then add a phase-derivation path that checks, via `spawn._issue_comments`
and `spawn._approvers` (already imported into `gates/` by
`closure_sweep.py:21`, so this is not a new dependency), whether a
qualifying approval exists for `issue-<n>/<role>`; phase1 if none does,
phase2 if one does — the closing-keyword regex plays no role in this
decision at all. This makes `_phase1_mismatch` reachable exactly when
requirement 2 needs it: a PR on a branch with no qualifying approval yet
(therefore phase1 by this new signal) that nonetheless carries a
closing-effect keyword is now a real, observable state, regardless of
plan shape.

- **Rejected alternative — derive phase from branch name** (the issue's
  own first-named option, "브랜치명"). Rejected because it is not
  actually independent of the ambiguity being resolved: per contract v3
  s19 the branch name (`issue-<n>/<role>`) is identical across phase 1
  and phase 2 for the same role — the same branch carries the phase-1
  proposal commits and, after approval, the phase-2 delivery commits.
  Branch name alone cannot distinguish which stage a given PR on that
  branch is in.
- **Rejected alternative — derive phase from plan-checkbox state alone**
  (the issue's own second-named option, "계획 상태"). Rejected because
  it reproduces the exact gap it's meant to close, just relocated: the
  scenario requirement 2 names as the concrete exposure — "the last
  remaining plan step's phase-1 proposal PR" — is *indistinguishable*
  from "the last remaining plan step's phase-2 delivery PR" using plan
  state alone, since both present as "only the last step incomplete."
  `pr_reference.check_body`'s own existing `only_last_step_incomplete`
  branch (`pr_reference.py:43-51`) already has to treat that shape as
  legitimate for real phase-2 deliveries; deriving phase from the same
  signal would just move the ambiguity from `ci.py` into a new
  plan-reading function without resolving it.
- **Rejected alternative — the issue's third-named option, unconditionally
  run the requirement-2 check outside any phase branch.** Rejected
  because "unconditionally forbid a closing keyword" would false-positive-
  block every legitimate phase-2 delivery PR, which is *required* to
  carry a closing keyword (`pr_reference.check_body`'s phase2 branch,
  `pr_reference.py:52-56`) — this would break requirement 4's own
  regression target category (a real, wanted delivery merge) while
  fixing the false-negative category. The check needs to stay
  conditional on phase; what changes is only how phase is derived.

**Chosen (requirement 1 mechanism): read each new surface directly via
`gh api`/`gh pr view` and apply the existing `_CLOSES_REF` regex, rather
than switching detection over to `closingIssuesReferences`.** Tested
this session (survey.md §4b) against the real commit-message incident:
`closingIssuesReferences` returns empty for a PR that did, in fact,
auto-close its issue via a commit message — adopting it as the primary
mechanism would silently reopen exactly the hole this issue exists to
close, while looking like an improvement (a single GitHub-native query
instead of several regex passes).

- **Rejected alternative — `closingIssuesReferences` as the sole
  detection mechanism.** Rejected on direct evidence (above), not
  theory: the field's own documented scope does not include
  commit-message-derived closes, and this was independently corroborated
  by other projects integrating the same field (scout-brief.md Source
  3). It is left as a *named, unimplemented* supplemental option for
  the one surface (row H) no regex can ever reach — not adopted as part
  of this proposal's write set (see Out of scope).

## What will be done

1. `gates/ci.py`: capture the role segment from the head branch name
   alongside the issue number; add a phase-derivation path that queries
   `spawn._issue_comments`/`spawn._approvers` for a qualifying
   `APPROVE issue-<n>/<role>` signal (single-account) or a
   differing-account PR review Approve (two-account), replacing
   `_phase_from_body` as the autodetect-path's phase source;
   `_phase1_mismatch` moves to run unconditionally whenever the
   independently-derived phase is phase1 (no longer gated by a
   `phase == "phase1"` check whose truth already implied the keyword's
   absence).
2. `gates/ci.py`: add commit-message coverage — fetch
   `gh api repos/<slug>/pulls/<n>/commits`, apply `_CLOSES_REF` to each
   `commit.message`, and feed a positive match into the same
   requirement-2 check path as a body-derived match (row C). Add title
   coverage the same way, reusing the `title` field `_pr_view` already
   fetches and currently discards (row B).
3. `gates/test_closes_gate_ci.py`: new tests — (a) the reachability
   fix: an issue with an empty or last-step-only plan, no qualifying
   approval comment, and a body carrying a closing-effect keyword must
   now block, proven false under the pre-fix code and true after,
   mirroring this file's existing red-green style; (b) requirement 4's
   regression, driven through `ci.check(..., closes_only=True)` with
   `--autodetect` semantics: a clean body, no qualifying approval, and a
   commit-message list carrying the keyword must block; recorded as a
   red run (pre-fix) and a green run (post-fix) in the phase-2
   implementation record, per the issue's own instruction to prove this
   against the actual wired invocation form.
4. `test_spawn.py`: restore a discriminating guard test for
   `spawn.py:1884-1892` by re-arranging
   `test_follow_prioritizes_pending_session_end_over_pid_check` (or an
   equivalent new test) around a live roster entry with a dead
   `wrapper_pid` plus a pending `session-end` event, matching the arrange
   issue #266's own rewritten `:3467` test already uses for the sibling
   case (survey.md §5) — proven red when `spawn.py:1884-1892` is
   temporarily deleted and green with it restored, both runs recorded in
   the phase-2 implementation record.
5. `docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`:
   records the two Rationale choices above (approval-event phase signal
   over branch-name/plan-state; direct multi-surface regex reads over
   `closingIssuesReferences`) as the format/mechanism decision this
   doctrine ladder routes to `docs/issue-<n>/decisions/`.
6. `docs/handbooks/operations.md`'s "Merge gate (CI)" section is updated
   to describe the widened inspected-surface set (title + description +
   commit messages) and the approval-based phase signal, same turn as
   the code change (doctrine ladder).

## Out of scope

- Any change to `gates/pr_reference.py`'s judgment logic (issue #228's
  owned surface; this proposal's own Constraints).
- Extending `gates/closure_sweep.py`'s `_refs_issue()` to also read
  commit messages, despite being named as a same-class member in the
  surface inventory above. It is advisory-only and never blocks a
  merge, it is not named by any of issue #271's four numbered
  requirements, and folding it into this write set would widen the
  frozen scope beyond what those four requirements ask for. Left as a
  documented gap the human may route to its own issue.
- Implementing a `closingIssuesReferences`-based supplemental check for
  row H (manual issue-PR linking with no keyword text). Named and
  reasoned about in the surface inventory and Rationale, but issue #271
  does not ask for full coverage of every row — only an inventory,
  named mitigations for uncoverable rows, and the four numbered fixes.
  Adding it would be new scope discovered mid-proposal, not something
  the issue's four requirements asked for.
- Any change to branch protection settings, the `closes-gate` required
  check's name, or `.github/workflows/plan-aware-closes-gate.yml`'s
  invocation form (issue's own constraint).
- Any change to `spawn.py`'s drain-order behavior at `:1884-1892`
  (requirement 3 restores a test, not a behavior change).
- Two-account-mode-only signals as the *sole* phase-derivation path —
  the chosen mechanism must and will support single-account mode too
  (Constraints).

## How you'll know it worked

- `gates/test_closes_gate_ci.py`'s new tests, run pre-fix and post-fix,
  transcribe a red→green pair for both the reachability fix and the
  commit-message regression (requirement 4), against the actual
  `--autodetect --closes-only` invocation form — both runs' output
  captured in the phase-2 implementation record.
- `test_spawn.py`'s restored guard test fails when
  `spawn.py:1884-1892` is temporarily deleted and passes with it
  restored (requirement 3) — both runs captured in the record.
- `python3 gates/test_closes_gate_ci.py` and `python3 -m pytest
  test_spawn.py -q` are both fully green after the change, with no
  regression in any existing test in either file.
- `docs/handbooks/operations.md`'s "Merge gate (CI)" section states the
  widened surface set truthfully, matching what the shipped code
  actually reads (title, description, commit messages) — checked by
  re-reading the section against the diff at phase-2 completion.
- The surface inventory table above accounts for every row with either
  "covered," "transitively covered," or a named, reasoned mitigation —
  no row left silently unaddressed.
