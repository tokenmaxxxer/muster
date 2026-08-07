# Survey: issue #390 — verification perishes, nothing re-establishes it at landing

## Reproducing the three instances

**Stale base (#383-shape).** `gates/ci.py:197` `_phase2_record_evidence(repo, pr,
branch, issue)` is 4-arg today. Its one call site (`gates/ci.py:351`) already
passes 4 args — #369 already fixed the call site on `main`. A branch cut
before that fix, calling the 3-arg form, would `TypeError` the moment its
sweep ran against current `main`; nothing but a human diff-read would show
it, because the branch's own CI run (against its own stale base) is green.
Confirmed by reading history: `gates/ci.py` git-blame shows the 4-arg
signature landed in the #369 merge (commit `4b7a365`/`58212aa`, both in
`git log` head).

**Wrong environment (#369-shape).** `.github/workflows/plan-aware-closes-gate.yml`
is the only workflow in this repo. It checks out `ref: main` unconditionally
(line 33) and reads PR content only via `gh api .../contents` — deliberately,
per its own comment (lines 25-36), to close a trust-boundary hole (a PR
editing `gates/ci.py` to pass itself). `_phase2_record_evidence`
(`gates/ci.py:197-219`) reads the phase-2 record from the PR **head branch**
via `gh api`, not from the local checkout — this is exactly #369's fix. The
defect it fixed: an earlier version read the record from the local working
tree, which holds `main`'s content in CI (since checkout is pinned to
`main`) but held the PR branch's content in every local worktree a session
verifies from. Same code, two environments, one property differed.

**Mocked boundary (#388-shape).** Not yet reproduced by running code — #388
is referenced by the issue as already landed. `subprocess.run` appears
throughout `gates/ci.py` (e.g. `_fetch_ref_file:181`, `_pr_is_cross_repo:230`).
A test that patches `subprocess.run` wholesale proves only that the call
happened, not that its `argv` was correct — a defect entirely inside the
argument list is invisible to that mock by construction, in any environment,
under any re-run policy. This shape is a test-design defect, not an
environment or staleness defect.

## #323 / #324 — write-set overlap: does it cover function-signature drift?

Both issues are **open, unimplemented**, filed the same day as #390.
`grep` across `gates/`, `test_*.py`, and `.github/workflows/` for
`write_set`/`write-set`/`overlap` finds **no code** — the phrase "write set"
exists only as prose convention in proposal/report frontmatter
(`docs/issue-*/proposals/*.md`, `docs/issue-*/reports/*.md`), checked by
whoever reads it, not by any script. There is nothing to reuse and nothing
to avoid rebuilding: #323/#324 do not yet provide a mechanism at any
granularity, file-level or signature-level. Per the issue's own boundary
section, this is consistent with "overlap detection tells you to look, it
does not invalidate a stale green" — but here there is not even a "look"
yet. Item 4 of #390 is therefore not actionable as "don't rebuild X" (X
doesn't exist); it is blocked on #323/#324 landing, and out of scope for
this proposal.

## CI re-verification: what exists today

`plan-aware-closes-gate.yml` is the **only** CI workflow in the repo. It
runs `gates/ci.py`'s metadata-only gate (`closes-gate` job) — it never
checks out a PR branch's code, never runs the test suite (`test_*.py`,
`gates/test_*.py`), and never simulates a merge. There is no CI job of any
kind that re-establishes a PR's tests against the state the PR would
actually land in. Whatever attests to "tests pass" for a PR today comes
entirely from a session's own local run, in a local worktree, against
whatever base that worktree happened to be branched from.

## #310 / #330 / #331 / #377 — no local infrastructure found

None of `docs/issue-310/`, `docs/issue-330/`, `docs/issue-331/`,
`docs/issue-377/` exist in this repo, and no `docs/decisions/` entry
references them. They are referenced by number in #390's own text as
prior/adjacent decisions; this repo carries no code or doc artifact under
those numbers to build on or defer to beyond the acceptance-shape rule
(#310: prose does not discharge acceptance) already visible as a norm across
every other proposal in `docs/issue-*/proposals/`.

## Write set this proposal expects

- `.github/workflows/merge-state-gate.yml` (new) — CI job that checks out
  the GitHub-computed merge ref (`refs/pull/<n>/merge`) instead of the PR
  head, and runs the test suite there.
- `gates/ci.py` — no change expected; existing `closes-gate` job is
  untouched, this is an additive, independent required check.
- `docs/issue-390/decisions/` — the design record for why merge-ref
  re-verification is the mechanism, and the explicit non-coverage of the
  mocked-boundary shape.
