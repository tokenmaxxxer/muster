files: docs/issue-275/reports/execution-observation.md

## Request

Issue #275's execution plan lists two steps: step 1 `implementation`, step 2
`execution-observation`. Step 1 is landed — PR #276
(https://github.com/tokenmaxxxer/on-the-record/pull/276, head
`issue-275/implementation`, merged 2026-08-04T07:17:23Z as
`236b66ecebe97a6e09a59b5334ac15d466338298`), carrying phase-1 commit
`fabd74b`, phase-2 skeleton `21f91f6`, and phase-2 work `cb6b46a`. This
proposal is step 2's plan: an independent observation of that session's
execution, from its own produced artifacts only.

The three verdict levels this observation will render in phase 2, named here
before any judgment is formed, are the role's fixed set:

1. **Outcome** — did PR #276 and `docs/issue-275/reports/implementation.md`
   land what issue #275's four requirements asked for.
2. **Trajectory** — was the phase-1 → phase-2 path sound: survey before
   proposal, scouting where required, a real §19 human approval before phase-2
   work, and no phase-2 content smuggled into the phase-1 commit.
3. **Step** — which specific artifact, if any, is deficient, at the granularity
   of a single file/hunk/record entry.

Contract §20's per-role-record minimum is the standard applied to the observed
record at the outcome and step levels — in particular §20 item 6, the class
question, which attaches to any record stating a confirmed finding: name the
defect class, and record whether that class was swept for elsewhere (or why it
could not be).

Nothing in this proposal renders any of the three verdicts, provisionally or
otherwise; all three open in phase 2 only, in
`docs/issue-275/reports/execution-observation.md`.

## Constraints

- **Never re-execute the observed task.** No running of
  `gates/test_closes_gate_ci.py`, `test_spawn.py`, or `gates/ci.py`; admissible
  evidence is the PR, its commits, its diff, and the observed role's own record
  and proposal. The observed role's recorded red/green runs are the workpaper —
  a re-run would replace its evidence with mine and prove nothing about what
  that session did.
- **Never read the observed role's present-day `src/` as evidence of what
  happened.** Where a file's content matters, it is read at a named commit
  (`git show <sha>:<path>`), which is the produced artifact, not today's tree.
- **Never edit the observed artifact.** No writes under `gates/`, `src/`,
  `test/`, `test_spawn.py`, `docs/handbooks/`, or
  `docs/issue-275/reports/implementation*`. The only write surface is this
  role's own record, listed in `files:` above.
- **No issue filing.** Under contract v3 issues are user-authored only; any
  confirmed deficiency returns as a finding in this role's record on this
  role's PR, for the human to judge and file.
- **`docs/issue-271/` is unreadable and unwritable from this branch** —
  `board-gate.sh` R4 scopes that tree to `issue-271/<role>` branches. The
  upstream #271 record is therefore out of evidentiary reach here; anything
  about it is established from #275's own artifacts (the issue text quotes
  F1-F4 verbatim, and the observed proposal and record quote the specific
  `ref:` lines at stake) or is not claimed at all.

## Rationale

**Why sha-pinned citations for every verdict, not bare `file:line`.** The scout
brief's immutable-reference must-be, applied to a git repo, is
`file:line @ sha` or a `git show <sha>:path` fact. The alternative considered
was this repo's dominant unpinned-`file:line` convention, which the observed
role itself adopted for in-code comments and which issue #227's observation
already recorded as a known drift cost. Rejected for a verdict record: this
observation's central subject includes citation drift (F1), and the observed
session's own hunt caught a citation of its own that went stale *within the
same commit* (`gates/test_closes_gate_ci.py:350`, `gates/ci.py:165` → `:169`).
A verdict record that repeats the failure mode it is judging cannot be relied
on by the next reader. The observed role's proposal reached the same split
(`:92-113`) for the same two artifact classes; this proposal takes the pinned
side for all of its own verdict claims, which are historical by construction.

**Why fail-without-fix is the standard for the two new tests, and how it is
applied without re-running them.** The scout sweep's regression-test must-be is
that a bug-fix test counts only if it fails on the unpatched version. For F3
that is checkable statically from the diff: the deleted line and the new test's
mock arrangement together determine whether the pre-fix code path would have
returned `phase2` under those exact mocks, and the record states a
reconstruction was run (`closed_checks[0]`). For F4 the same question is asked
of an assertion whose subject is a retained pre-#271 helper — the check is
whether the asserted call can distinguish the two states requirement 4 names,
judged against the record's own non-vacuity note (`closed_checks[2]`) and the
proposal's stated intent (`:163-173`, `:220-227`). Where the artifact's own
recorded evidence does not settle it, the phase-2 record says so and takes the
level no further, rather than substituting a re-run.

**Why the deviation gets a defensibility read rather than a pass/fail on
completion alone.** The approved proposal's `files:` header names six paths;
the landed diff touches five. Deviation-management practice makes the
distinction that matters here: the weak form is a bare "no impact", the
defensible form names affected scope, evidence reviewed, and conclusion. So the
check is not merely "was an approved write-set item dropped" but "does the
record's stated rationale carry those three parts, and is the blocker it names
mechanically real from evidence this session can see." Judging completion alone
would either over-penalize a structurally impossible write or under-penalize an
undocumented drop.

**Why §20 item 6 is checked separately from the record's other content.** Items
1-5 apply to every record; item 6 attaches only when the record states a
confirmed finding, which this one does (Hunt finding 1, `:188-195`). Checking
it separately keeps two different things apart: the sweep the record *does*
carry (the `_issue_comments` union's other habitats, `:212-216`) belongs to the
F3 defect class, and item 6's question is asked about the confirmed finding's
own class. Merging the two would let one sweep silently answer for a class it
never covered.

## What will be done

Phase 2, on approval, writes `docs/issue-275/reports/execution-observation.md`
— the independence statement first, then the three verdicts in order, each
verdict-bearing sentence carrying a sha-pinned citation adjacent to it. The
checks feeding each level:

- **Outcome.** Requirement-by-requirement (1/F3, 2/F2, 3/F1, 4/F4) against the
  landed artifacts: `git show cb6b46a` hunks for `gates/ci.py`,
  `gates/test_closes_gate_ci.py`, `test_spawn.py`,
  `docs/handbooks/operations.md`; the record at
  `docs/issue-275/reports/implementation.md`; and the diffstat's coverage of
  the approved proposal's six-path `files:` set. Requirement 3's two-part ask
  (correct the citations *and* settle the sha-pinning question in the proposal)
  is scored on both parts.
- **Trajectory.** Commit order and timestamps (`fabd74b` 06:50:19Z → PR opened
  06:50:37Z → issue comment id 5175585081 06:51:15Z → `21f91f6` 07:01:21Z →
  `cb6b46a` 07:14:11Z → merge 07:17:23Z); `git show fabd74b --stat` to confirm
  the phase-1 commit carries only the two phase-1 homes; §19 single-account
  path checked against the comment's exact body, its author's presence in
  `docs/specs/approvers.md`, its issue-level provenance (`/issues/275/comments`
  on a number that is an issue, not a PR), and `gh pr view 276 --json reviews`
  being empty; the observed role's `survey.md` and `scout-brief.md` existence
  and commit provenance for survey-before-proposal and the scout obligation.
- **Step.** Per-artifact: (a) F3's test as a fail-without-fix discriminator;
  (b) F4's assertion against requirement 4's behavioral ask; (c) KO/EN parity
  of `docs/handbooks/operations.md` after the same commit changed both sides;
  (d) whether each `closed_checks` `ref:` resolves in the landed tree, verified
  with `git show cb6b46a:<path>` rather than today's files; (e) §20 items 1-6
  against the record, with item 6 asked about Hunt finding 1's own defect class
  (stale intra-commit self-citation) and whether a sweep for that class is
  recorded or its absence explained.

Any confirmed deficiency is written in the four-part blameless shape — impact,
timeline, root cause, action item — scaled to a single finding, with the
timeline kept to timestamped facts and its causal reading placed under root
cause. Levels with nothing to report state "not applicable, because X" rather
than being omitted.

## Out of scope

- Re-verifying the correctness of `gates/ci.py`'s approval predicate as code
  (whether the closes-gate is *right*) beyond what the requirements asked —
  this is an observation of execution, not a code review of the gate.
- Issue #271 / PR #273 themselves, and the contents of
  `docs/issue-271/reports/`, per the branch-scope constraint above.
- The two follow-on items the observed record flags (the blocked
  `docs/issue-271/` `ref:` corrections; the same comment-union shape in
  `gates/flows.py` `comments_for()` and `spawn.py` `approve_scope()`) — these
  may be *named* in the record as context for a finding, but this role neither
  fixes them nor files issues for them.
- Any edit to the observed role's artifacts, including "obvious" citation
  fixes.

## How you'll know it worked

- `docs/issue-275/reports/execution-observation.md` exists on branch
  `issue-275/execution-observation`, committed with a `Subject: issue-275`
  trailer, with `loop_state` moved through its transitions.
- The independence statement precedes the first verdict-bearing sentence in
  document order, not merely appearing somewhere in the file.
- All three levels — outcome, trajectory, step — are present; none is silently
  omitted, and any that does not apply says so with its reason.
- Every verdict-bearing sentence carries an adjacent citation, and each such
  citation is either a commit sha, a `file:line` inside a named commit, or a
  GitHub URL/comment id — spot-checkable by a reader who has only this
  repository and the PR.
- No file outside `files:` above is modified by this role's branch, checkable
  with `git diff --stat main...issue-275/execution-observation`.
