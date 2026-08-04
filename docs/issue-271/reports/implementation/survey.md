---
role: implementation
subject: issue-271
loop_state: survey
---

# Current-state survey — closing-trigger surface coverage + phase-predicate coupling (issue #271)

## Scope

Issue #271 asks for a phase-1 proposal only. Scouting ran (not skipped) —
see `scout-brief.md` in this same directory — because two of the four
requirements leave real design choices open: requirement 1 asks which
mechanism should read each newly-covered surface, and requirement 2 offers
two named directions ("independent phase signal" vs. "pull the check out
of the phase branch") without picking one.

## 1. The gate architecture as it exists on `main`

Three files participate in issue-closing-keyword detection, all sharing
one regex family:

- `gates/pr_reference.py` — the judgment logic (issue #228, frozen by
  this issue's own constraints). `_CLOSES_REF` (`pr_reference.py:25`)
  matches a closing-effect keyword immediately followed by `#<issue>`.
  `check_body()` (`:28-62`) takes a PR body string, an issue number, a
  `phase` label, and an optional parsed plan; its only text input is the
  PR body, obtained by `_pr_view()` (`:65-72`) via `gh pr view --json
  body,title` — the title is fetched but immediately discarded
  (`data.get("body", "")`, `:72`; the `title` key is never read anywhere
  in this file).
- `gates/ci.py` — the CI orchestration layer (issue #245). It adds
  `--autodetect` (derive issue + phase from PR metadata when the CI
  trigger can't supply `--issue`/`--phase`) and `--closes-only` (run only
  the Closes gate, skip write_scope/protected-path/deps/record). Issue
  number comes from the head branch name via `_issue_from_branch()`
  (`:60-63`, pattern `^issue-(\d+)/`, second capture group for role
  discarded — same pattern gates.py's `BRANCH_ROLE`,
  `gates/gates.py:465`, keeps). Phase comes from `_phase_from_body()`
  (`:82-87`): phase2 if the body carries a closing keyword aimed at this
  issue, phase1 otherwise. `_phase1_mismatch()` (`:90-102`) is the
  requirement-2 machine check — "a phase-1 PR must not carry a closing
  keyword" — and is invoked only inside `check()`'s `if phase ==
  "phase1":` branch (`:159-164`).
- `.github/workflows/plan-aware-closes-gate.yml` runs `gates/ci.py . --pr
  "$PR_NUMBER" --autodetect --closes-only` on every `pull_request` event
  (`opened, edited, synchronize, reopened`), checking out `gates/ci.py`
  from `main` (not the PR's own copy) so a PR cannot patch the gate to
  pass itself. This is the actual required check registered on `main`'s
  branch protection — confirmed live via API this session:
  `required_status_checks.contexts == ["closes-gate"]`,
  `enforce_admins.enabled == true`.
- `gates/closure_sweep.py` — a separate, advisory-only sweep (issue
  #135) over the whole board; it never blocks a merge, only reports
  drift and optionally posts an issue comment. Its `_refs_issue()`
  (`:29-35`) computes `has_closes` the same way `pr_reference` does, but
  from PR body alone — see §4 below.

## 2. The predicate-coupling defect (already found and recorded: issue
#245 execution-observation, Finding F1)

`_phase_from_body()` and `_phase1_mismatch()` both key off the same
predicate, `_closes_ref_for_issue(body, issue)` (`ci.py:66-79`). Because
phase is *derived from* keyword presence, the one state the
requirement-2 check exists to catch — a PR meant to be phase-1 that
nonetheless carries a closing keyword — is definitionally impossible to
observe: any body with a keyword is already classified `phase2` before
`_phase1_mismatch` is asked to look at it, and that function only runs
under `phase == "phase1"`. Concretely: an issue with no `##
실행 계획` block, or one whose *only* remaining step is the last, plus a
mistaken keyword in the body, autodetects as phase2, and
`pr_reference.check_body`'s phase2 branch (`pr_reference.py:39-51`)
explicitly permits a keyword when the plan shows only the last step
incomplete or no plan at all — so the required check passes and the
merge auto-closes the issue. `docs/issue-245/reports/implementation.md`'s
own requirement-2 verification exercised `pr_reference.check_body`
directly with an explicit `--phase` argument and never drove the
`--autodetect` path the real wiring actually uses, which is why the
emptiness was invisible to that record's own proof.

## 3. The commit-message vector — two real, already-recovered incidents

Confirmed this session by reading GitHub's own event/commit data (`gh pr
view`, `gh api .../commits`, `git log --format=%B`), matching what
`docs/issue-245/reports/execution-observation.md` (§ 존재/범위/귀속,
already-landed observation) and the issue-262 / issue-266
execution-observation records (each role's own Finding 1 / F2) already
established independently:

- A phase-1 proposal PR's description referenced its issue in prose only
  and carried no closing-effect keyword — the required check passed
  clean. The branch's own commit, however, ended its message with a
  closing-effect keyword paired with that issue's number. On merge
  (ordinary merge-commit, not squash), that commit landed on `main` with
  its original message intact, and GitHub's own auto-close fired from
  that commit — not from the PR body the gate had inspected. A human
  reopened the issue roughly five minutes later.
- A second, independent PR shows the same shape as a controlled variant:
  its required check first failed because its *body* carried a closing
  keyword, then passed once that keyword was removed from the body — the
  gate demonstrably fired correctly on the surface it inspects. The PR
  still auto-closed its issue on merge, because one of its branch commits
  independently carried the same keyword/issue-number pairing in its own
  message, a surface the gate never reads. A human reopened this one too,
  roughly 25 seconds apart from the first.

Because the second case isolates "body clean, gate green, commit-message
carries the keyword" as the sole variable, the vector's existence is
measured, not inferred. Both recoveries are recorded in each issue's own
reopen comment and in the cross-referenced execution-observation records
above.

## 4. Surface enumeration — what this survey adds beyond the prior
records

The prior observation records established that a closing-effect keyword
in a *branch commit message* is unreviewed. Issue #271 requirement 1
additionally asks for the surface set to be swept exhaustively, and for a
sweep of other gate-system members sharing the same defect class. Two
findings not present in any prior record:

**a. PR title is a GitHub-documented closing surface, currently unread
entirely.** GitHub's own documentation states that closing keywords are
honored in pull request titles and descriptions, as well as in commit
messages (confirmed this session via GitHub Docs — see scout-brief.md
for the source). Separately, this repository's own merge-commit
template setting (`merge_commit_message: PR_TITLE`, `merge_commit_title:
MERGE_MESSAGE`, read live via `gh api repos/<slug>` this session) means
that on an ordinary merge, the newly created merge commit's *body* is a
verbatim copy of the PR title — confirmed by reading two real merge
commits in this repository's history (`git log -1 --format=%B` on
`fcdea95` and `247051e`, both showing "Merge pull request #N from
...\n\n<PR title text>"). A PR title carrying a closing-effect
keyword would therefore land on `main` inside the merge commit's own
message even with a perfectly clean PR body, through a path neither
`pr_reference.py` nor `ci.py` reads (`_pr_view` fetches `title` and
discards it, §1 above).

**b. `gh pr view --json closingIssuesReferences` does not close this
gap.** GitHub's GraphQL `closingIssuesReferences` field looked, in
principle, like a candidate for reading GitHub's own closing
determination directly instead of re-implementing keyword matching.
Tested directly this session against the real, merged commit-message
incident PR from §3: `gh pr view <pr> --json
closingIssuesReferences,body` returns an **empty** list for that PR,
even though that exact merge is the one that auto-closed its issue. The
field reflects body-derived (and, per its own documented purpose,
manually-linked) closing relationships, not commit-message-derived ones
— corroborated independently in this session's scouting (community
reports of the same gap, see scout-brief.md). This rules out
`closingIssuesReferences` as a substitute for reading commit messages
directly; it remains useful only as a supplementary check for the
manual-link surface named in the proposal's surface table, which has no
text signature at all.

**c. Repository merge settings widen the exposure beyond "merge
commit."** `gh api repos/<slug>` (this session) shows
`allow_squash_merge`, `allow_merge_commit`, and `allow_rebase_merge` all
`true`, with `squash_merge_commit_message: COMMIT_MESSAGES` — meaning a
squash merge's single resulting commit message is, by this repository's
own configured default, the concatenation of the branch's individual
commit messages. A rebase merge replays each original commit with its
original message onto `main` unchanged. Both alternate merge strategies
expose the *same* underlying text (branch commit messages) that a
merge-commit strategy already exposes; this repository's actual history
so far uses merge-commit exclusively (`git log` shows "Merge pull
request #N from ..." commits throughout), but nothing prevents a human
from choosing squash or rebase on the merge button, and the setting
permits it today.

**d. A second gate-system member shares the same input-surface gap.**
`gates/closure_sweep.py`'s `_refs_issue()` (`closure_sweep.py:29-35`)
computes whether a PR "has a closing reference" from `pr_body` alone,
via the same `_CLOSES_REF` regex — commit messages are equally invisible
to it. Unlike `pr_reference.py`/`ci.py`, this is a post-hoc, advisory-only
sweep (`OPEN_PR_ON_CLOSED_ISSUE` / `MERGED_DELIVERY_ISSUE_OPEN`
classifications, `closure_sweep.py:23-24`) that never blocks a merge —
so the practical severity differs from the merge-blocking gate — but its
`classify()` function (`:38-50`) has no branch at all for the shape both
real incidents in §3 actually produced (a merged PR whose *body* carried
no closing reference, whose commit message did, and whose issue is now
correctly `CLOSED` for the wrong reason): neither `OPEN_PR_ON_CLOSED_ISSUE`
(requires `pr_state == "OPEN"`) nor `MERGED_DELIVERY_ISSUE_OPEN` (requires
`issue_state == "OPEN"`) fires, because the issue *did* close. A sweep of
the rest of `gates/` for the same `_CLOSES_REF`/`_pr_view` family
(`grep -rl` this session) found no third member — only these two files
use this detection logic anywhere in the repository.

## 5. The drain-guard regression named by requirement 3

Already fully diagnosed and recorded by `docs/issue-266/reports/execution-observation.md`
Finding F1 (read in full this session): `spawn.py:1884-1892` drains a
pending `session-end` event before evaluating `--follow`'s death check,
a behavior PR #255 feedback put there and issue #266 required kept. The
one test that exercised this ordering,
`test_follow_prioritizes_pending_session_end_over_pid_check`
(`test_spawn.py:3497-3520` as of commit `be53d1e`), builds its "process
looks dead" precondition by calling `spawn.roster_remove(...)` — exactly
the signal issue #266's own landed fix (`spawn.py:1908`,
`if pid is not None and not _alive(pid):`) redefined as *not* death.
Traced against the current predicate: with the drain block
hypothetically deleted, the test's arrange no longer reaches the
`WATCH_CRASH_RC` path at all (entry-absence is no longer a death signal),
so the test would pass identically whether the drain block exists or
not — it stopped discriminating the code it exists to protect, without
its assertions changing. The other eight `WatchFollow` tests either
plant a live `wrapper_pid` (can never crash regardless of the drain
order) or write no `session-end` event at all, so none of them cover
this ordering either.

## 6. Reusable infrastructure for an independent phase signal

`spawn.py` already has the primitives an approval-based phase signal
would need, and one of the three files in this class already imports
`spawn` for unrelated reasons:

- `spawn._approvers(root)` (`spawn.py:798`) reads
  `docs/specs/approvers.md` (currently `JiwonJung94`, `jjongkwann`) into
  a set of GitHub logins.
- `spawn._issue_comments(root, n)` and the exact-string comment-matching
  idiom are already used by `spawn.approve_scope()` (`spawn.py:896-947`)
  for a sibling approval marker (`APPROVE issue-<n>/scope`) — the same
  shape contract v3 s19 defines for phase-2 opening
  (`APPROVE issue-<n>/<role>`, single-account mode) is not implemented
  as a standalone helper anywhere yet, but the exact-string-match-against-
  allowlist logic is a direct, already-proven pattern to copy.
- `gates/closure_sweep.py:21` already does `import spawn` from inside
  `gates/`, so importing `spawn` from `gates/ci.py` for this purpose has
  a direct precedent in the same directory.

## 7. Repository merge/branch-protection facts confirmed live this session

- Branch protection on `main`: `required_status_checks.contexts ==
  ["closes-gate"]`, `enforce_admins.enabled == true` — matches issue
  #271's own framing ("브랜치 보호 활성화 2026-08-04").
  `required_pull_request_reviews` is unset (single-account mode is this
  repository's live default, matching `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`).
- `docs/handbooks/operations.md`'s "Merge gate (CI)" section currently
  describes the check as reading only the PR body via `--autodetect`'s
  body-derived phase; it will need updating once the inspected surface
  changes (doctrine ladder: config/behavior change to a standing gate ->
  handbook, same turn as the phase-2 change).

## Write-set implications for phase 2 (not executed here)

Requirements 2 and 4 need code changes; requirement 3 needs a test-only
change; requirement 1 is satisfied by this survey + the proposal's
surface table and needs no phase-2 code by itself (beyond what
requirement 4 already forces for the commit-message surface). Candidate
touch points, reasoned about in the proposal's Rationale and Constraints:
`gates/ci.py` (orchestration layer, where both the coupling fix and the
new surface reads belong — keeps `gates/pr_reference.py` untouched, per
this issue's own constraint), `gates/test_closes_gate_ci.py` (regression
proof, requirement 4), `test_spawn.py` (regression restoration,
requirement 3), and a new `docs/issue-271/decisions/` entry (the
phase-derivation-mechanism choice is exactly the kind of "library-or-
format choice over a named alternative" the doctrine ladder routes
there). `gates/closure_sweep.py` is named in §4d as a same-class member
but is deliberately left as a documented, not a fixed, gap — see the
proposal's Out of scope section for the reasoning.
