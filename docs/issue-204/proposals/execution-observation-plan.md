# Proposal — issue #204 execution-observation, phase-2 verification method

Status: proposal (phase 1). No verdict is rendered anywhere in this document — this
section states which of the three verdict levels will be checked and against what
evidence, per this role's phase-1 facet requirement.

## What phase 2 will check, and against what evidence

**Outcome** — did PR #211 (commits `dd65451`, `0ab22b4`, merge `cfeb3c5`) land what
issue #204's three numbered requirements asked, resolved against the four judgment
items this session's task instruction named:

- 요구 1 (network-blocked, `pytest test_spawn.py test_gates.py` → 0 fail): checked
  by reading `implementation.md`'s own recorded transcript (`152 passed in 18.01s`)
  against `survey.md`'s independently-recorded pre-fix baseline
  (`18 failed, 134 passed in 7.20s`) and post-fix spike (`152 passed in 12.74s`) —
  both already read this session (survey.md, this proposal's accompanying survey) —
  for internal consistency, not by this role re-executing pytest. This role's
  directive prohibits re-running the observed role's code
  ("PROHIBITED, always: never re-run the observed role's code — its actual produced
  artifacts... are the only admissible evidence, never a re-execution of its task").
  This mirrors issue-197's own execution-observation proposal's resolution of the
  identical tension (`docs/issue-197/proposals/execution-observation-plan.md`,
  "Outcome" section): citations from the observed role's own record stand in for
  live re-verification.
- 요구 2 (open-network no-regression): checked against `implementation.md`'s
  `setdefault` non-clobber proxy (ambient-override assert + `152 passed in 14.15s`
  re-run), which is the only citable evidence found this session for this
  requirement. The task instruction also names an "orchestrator" figure ("네트워크
  열린 로컬, 동일 명령 152 passed 13초") that does not appear in any file read this
  session — no commit SHA, file:line, or PR/issue comment URL backs it yet. Phase 2
  will either locate a citable artifact for that figure before using it as evidence,
  or state plainly that requirement 2's evidence is limited to the proxy already in
  `implementation.md`, consistent with the citation-adjacency rule (no verdict
  sentence without an adjacent, real source).
- `setdefault` non-clobber (요구 3): checked via direct reading of `conftest.py:14-15`
  (already confirmed this session to use `os.environ.setdefault`, not assignment) and
  `implementation.md`'s §검증 2 assert transcript — a static/citation check, not a
  re-execution question, since the observed role's own record already contains the
  assert's output.
- Hunt open-finding disposition (요구 4): checked against the hunt record's FINDING
  and `implementation.md`'s "Open findings" section, judging whether the
  not-a-regression / outside-frozen-write-set argument holds and whether the finding
  is separate-issue-worthy or safely ignorable — a judgment call phase 2 will make
  explicitly, citing both documents.

**Trajectory** — was the `implementation` role's phase-1→phase-2 path sound: did it
survey before proposing (`docs/issue-204/reports/implementation/survey.md`, already
read in full — shows a scout-skip record, full 18-failure inventory, and a spike
measurement taken before any repo file was written, i.e. hypothesis tested before
being committed), get real human approval before phase 2 specifically (`APPROVE
issue-204/implementation`, 2026-08-02T12:11:58Z, already read from the issue's
comments, cross-referenced against `dd65451`'s authored timestamp 12:34:09Z — after
approval, consistent), and keep its write set to what the approved proposal declared
(proposal's `files:` frontmatter: `conftest.py` + 3 fixture JSONs — already checked
this session against `git show dd65451 --stat`'s actual 4 changed files: exact
match, no extra files, `spawn.py`/`test_spawn.py`/`test_gates.py` untouched as the
proposal's Constraints required).

**Step** — which specific artifact, if any, is deficient. Candidates already surfaced
this session (not judged):

1. Whether the hunt's open finding (non-pytest entry points — `python3 test_gates.py`,
   `python3 -m unittest test_spawn.py` — still hit the network because `conftest.py`
   is a pytest-only auto-import hook) should be a separate issue-worthy defect, or is
   legitimately ignorable given the approved proposal's own Out-of-scope list already
   named `test_gates.py`'s non-pytest collection as a distinct, unaddressed redesign
   before this implementation started.
2. Whether the task instruction's uncited "orchestrator 실측 152 passed 13s" figure
   for requirement 2 can be traced to a real citable artifact, or whether phase 2's
   requirement-2 evidence must rest solely on `implementation.md`'s own ambient-proxy
   measurement.

Any deficiency finding will carry the four-part blameless shape (impact, timeline,
root cause, action item) this role's directive requires.

## Method constraint carried into phase 2

Every verdict-bearing sentence in the phase-2 record will name its source (commit
SHA, file:line, or PR/issue comment URL) immediately adjacent, per this role's
directive. This role's directive prohibits phase 2 from re-running
`pytest`/`spawn.py` under any instruction, including this session's own task text
asking for an "independent reconfirmation" of 요구 1 — that reconfirmation will be
satisfied by cross-checking the two independently-recorded transcripts already
identified above (`implementation.md`'s and `survey.md`'s), not by executing
anything.

## Gate check before phase 2 opens

As of this session, issue #204's only comment is `APPROVE issue-204/implementation`
— no `APPROVE issue-204/execution-observation` comment exists, and no PR review
Approve exists on any PR for the `issue-204/execution-observation` branch (none is
open yet, per `gh pr list --state all --search "head:issue-204/execution-observation"`,
which returns empty). Per role-handoff contract v3 s19, phase 2 does not open until
one of those two approval paths is satisfied for this role specifically, from a
`docs/specs/approvers.md` account (`JiwonJung94` or `jjongkwann`) — and, if the path
taken is a PR review Approve, from an account other than this PR's author. This
repo's own issue-197 precedent for this exact role (`APPROVE
issue-197/execution-observation` posted as a standalone issue comment, separate from
`APPROVE issue-197/implementation`) shows this gate is actually exercised here, not
a formality. This proposal, the accompanying survey, and the PR that carries them are
this session's phase-1 output; phase 2 (the actual verdict record at
`docs/issue-204/reports/execution-observation.md`) is deferred to a future session
after approval.
