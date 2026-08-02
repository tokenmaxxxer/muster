# Proposal — issue #205 execution-observation, phase-2 verification method

Status: proposal (phase 1). No verdict is rendered anywhere in this document —
this section states which of the three verdict levels will be checked and
against what evidence, per this role's phase-1 facet requirement.

## What phase 2 will check, and against what evidence

**Outcome** — did PR #210 (sole commit `ded7993`, merge `86bf624`) land what
issue #205's four numbered requirements asked, judged against the approved,
revised proposal (`docs/issue-205/proposals/session-end-defects.md`, revision
`ee0c740`) rather than the issue body alone, since the proposal is the
user-approved interpretation of the issue. Evidence: the `ded7993` diff (already
read in full this session via `gh pr diff 210`) against each of the "What will be
done" 5 items and each of the four numbered 요구사항; the `spawn.py`/`test_spawn.py`/
`.gitignore` current-`HEAD` reads already done this session (survey's "Current-state
facts" section) confirming the diff matches current `HEAD` with no intervening
touch; and the `gates/flows.py` static read already done (survey, item 4) for the
non-breakage requirement. No execution of `spawn.py`/`gates/flows.py`/`test_spawn.py`
will be performed by this role — this role's directive prohibits re-running the
observed role's code, mirroring issue-197's and issue-201's execution-observation
proposals' own resolution of the same tension in favor of the standing protocol.
Where the observed role's own record (`implementation.md`) already contains a
live pytest-run transcript (§검증 1-3), that citation may be used as evidence
without this role re-executing anything — per the same precedent. The one
partially-unverified item flagged in the survey (item 2's manual gitignore
reproduction, resting on the record's citation plus static `.gitignore`/
`git ls-files` facts rather than this role's own live `touch` reproduction) will
be judged on that citation, not re-run, since reproducing it would require
mutating the real repo's working tree outside this role's read-only research
scope.

**Trajectory** — was the `implementation` role's phase-1→phase-2 path sound: did
it survey before proposing (its own `survey.md`, already read in full — shows a
located-defect-then-proposal pattern with an explicit scout skip record), get
real human approval before phase 2 specifically (`APPROVE issue-205/implementation`,
2026-08-02T12:19:34Z, already read from the issue's comments), keep its write set
to what the approved proposal declared (`files: spawn.py, .gitignore, test_spawn.py`
— checked in the survey against `git show ded7993 --stat`'s exact 4-file diff, one
of which, `docs/issue-205/reports/implementation.md`, is the record itself and so
expected outside the code write-set — confirmed clean, no stray file, unlike
issue-197's precedent which found one), and honor the mid-phase-1 constraint
relaxation's own stated scope (the "existing tests unchanged" constraint was
relaxed, per `ee0c740`'s commit message, only for tests that assert the defect
itself — whether the actual test change stayed within that relaxation, or reached
further, is checked against the full `FailClosedDowngrade`/`Clean` class reads
already done in the survey). Evidence: the approval timestamp cross-referenced
against PR #206's and PR #210's merge/commit timestamps (done in the survey — 2
seconds between approval and PR #206's merge, consistent with issue-197's
documented automated-merge-on-approval pattern); whether PR #206's own review
history (not yet fetched this session) corroborates the "orchestrator relay, user
decision" characterization in `ee0c740`'s commit message is a phase-2 gap to
close, not resolved here.

**Step** — which specific artifact, if any, is deficient. The primary candidate
already surfaced (not judged): `docs/issue-205/reports/implementation.md`'s
frontmatter `code_under_review` field cites `ee0c740` (a docs-only, phase-1
proposal-revision commit, confirmed via `git show ee0c740 --stat` to touch no
code) rather than `ded7993` (the actual code-and-record commit whose diff the
same frontmatter's `closed_checks` test-run results could only have been produced
against) — a candidate citation-accuracy defect in the observed role's own
record, structurally analogous in kind (a frontmatter/self-citation defect) to
issue-197's execution-observation Finding 1 (a write-set-discipline defect), though
different in substance. Also in scope, per the invoking prompt's explicit
requirement: the commit-bisection judgment on the two issue-201-registered
tests — whether the orchestrator hypothesis (that `1c230db`'s `.warrant-hunt.count`
deletion caused the fail→pass flip) holds, and whether "fixed" or "condition
disappeared" is the accurate characterization, resolved on the diff-level and
survey-citation evidence the phase-1 survey already gathered (§"Bisection
candidate") rather than by re-running pytest at either commit — this role's
standing prohibition on re-executing the observed role's code applies equally to
bisecting it by execution; a diff-content bisection (does the candidate commit's
diff touch the file/lines the test failure depends on) is the method this
proposal adopts instead, and the survey has already gathered the two commits'
full diffs plus both issues' own surveys' independently-reproduced failure/pass
transcripts as citable evidence. Any deficiency finding will carry the four-part
blameless shape (impact, timeline, root cause, action item) this role's directive
requires.

## Method constraint carried into phase 2

Every verdict-bearing sentence in the phase-2 record will name its source
(commit SHA, file:line, or PR/issue comment URL) immediately adjacent, per this
role's directive. No file will be cited as evidence of "what happened"
independent of a diff, commit, or comment citation. Where a file:line citation
into current `HEAD` is used, it is used only where already confirmed identical to
`ded7993`'s diff state — confirmed this session via `git log --oneline` showing
only issue-204's `conftest.py`/fixture-only commits (`eda5bd2`, `dd65451`,
`0ab22b4`) after `ded7993` on `main`, none of which touch `spawn.py`,
`test_spawn.py`, `.gitignore`, or `gates/flows.py` per their own declared write
sets (survey, "What was read" section).

## Gate check before phase 2 opens

As of this session, issue #205's only comment is `APPROVE issue-205/implementation`
— no `APPROVE issue-205/execution-observation` comment exists, and no PR review
Approve exists on any PR for the `issue-205/execution-observation` branch (none is
open yet, per `gh pr list --state all --search "head:issue-205/execution-observation"`,
which returns empty). Per role-handoff contract v3 s19, phase 2 does not open
until one of those two approval paths is satisfied for this role specifically,
from a `docs/specs/approvers.md` account (`JiwonJung94` or `jjongkwann`) — and, if
the path taken is a PR review Approve, from an account other than this PR's
author. This proposal, the accompanying survey, and the PR that carries them are
this session's phase-1 output; phase 2 (the actual verdict record at
`docs/issue-205/reports/execution-observation.md`) is deferred to a future
session after approval.
