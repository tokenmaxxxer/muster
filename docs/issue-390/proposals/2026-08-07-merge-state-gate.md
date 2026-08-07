---
status: proposed
files:
  - .github/workflows/merge-state-gate.yml
  - gates/test_merge_state_gate.py
  - docs/issue-390/decisions/merge-state-reverification.md
---

files:
- .github/workflows/merge-state-gate.yml
- gates/test_merge_state_gate.py
- docs/issue-390/decisions/merge-state-reverification.md

## Request

A PR's green attests to the state it was verified against, not the state it
lands in, and nothing notices when that state moves. Three instances today:
a sweep whose branch predates a callee's arity change (#383-shape), a fix
verified in a local worktree where CI's own checkout structurally cannot
match (#369-shape), and a test that mocks the exact boundary its own defect
lives in (#388-shape). Establish what re-runs a verification against landing
state, and state which of the three it would have caught.

## Constraints

- Do not rebuild #323/#324's write-set overlap mechanism — confirmed by
  survey (`docs/issue-390/reports/implementation/survey.md`) that no such
  mechanism exists yet in this repo (both issues open, no code found); item
  4 of #390 is deferred to those issues, not attempted here.
- Do not touch `gates/ci.py`'s existing `closes-gate` job or its required-check
  registration — this is an additive, independent check, per the same
  additive pattern #245/#284 already used for `closes-gate` itself.
- The mechanism must state, per PR, which of the three #390 shapes it
  covers — silently claiming full coverage is exactly the failure #390
  reports.
- No new dependency, no new secret; the existing `GITHUB_TOKEN` and
  `actions/checkout` are sufficient.

## Rationale

Considered continuous re-verification: re-run every open PR's tests against
`main` on every push to `main` (a periodic or push-triggered sweep across
all open PRs), independent of any one PR's own activity. Rejected: it scales
with `open PRs × pushes to main`, is the more expensive shape, and still
only re-establishes the same property (does this PR's code run against
current `main`?) that a per-PR merge-ref check gets more cheaply and with a
GitHub-native trigger (`synchronize`) that already fires whenever the PR's
own branch or its target moves.

Considered staleness bookkeeping: have a PR's record declare what it
verified against (a base SHA) and have a gate compare that SHA to `main`'s
current tip, failing when they diverge (addresses #390 item 2/3 directly).
Rejected as the sole mechanism: comparing SHAs proves the base moved, not
that the PR still passes against the new base — a PR could be stale by one
irrelevant commit (harmless) or stale by one signature change (fatal), and
SHA comparison can't tell them apart without also running something. Actually
running the merge result subsumes SHA-staleness detection: a PR that no
longer passes against current `main` fails regardless of why, and a PR that
still passes is not stale in any way that matters. SHA bookkeeping is
deferred as a possible later optimization (skip a rerun when the base
hasn't moved) — not required for correctness now.

## What will be done

Add `merge-state-gate.yml`: a `pull_request` workflow (`opened`, `synchronize`,
`reopened`) that checks out GitHub's computed merge ref
(`refs/pull/<n>/merge`, the PR branch merged onto current `main` — the same
ref GitHub itself uses to compute mergeability) instead of the PR head or a
`main`-pinned ref, then runs this repo's existing local test scripts
(`test_gates.py`, `test_flows.py`, `test_spawn.py`, `test_approve_scope.py`,
`test_vocab_coherence_roles.py`, `gates/test_closes_gate_ci.py` — all
already network-free per their own docstrings) against that merged tree.
The job fails the required check when any script exits non-zero.

Per the sibling `plan-aware-closes-gate.yml`'s own documented caveat
(`.github/workflows/plan-aware-closes-gate.yml:4-8`): a workflow reporting a
check status is not the same as that check blocking a merge — it must also
be registered as a required status check under branch protection (Settings
> Branches), or it reports and blocks nothing. This proposal names that
registration step explicitly as part of "what will be done," not left
implicit — landing this workflow without registering it reproduces the
exact "green attests, nothing enforces" shape #390 is about, one layer up.
The registration step itself is a repo-settings change outside this
proposal's write set (not a file edit); it is called out here so it is not
silently skipped, per warrant hunt stance 0 (after-proposal, this proposal,
2026-08-07) — `docs/reports/2026-08-07-hunt-issue-390-merge-state-gate.md`.

This re-establishes the attestation at the state the PR would actually land
in, not the state it was authored against — directly targeting the
stale-base shape. Coverage, stated per #390's requirement:

- **Stale base (#383-shape): caught.** The merge ref includes `main`'s
  current tip; a caller still passing the old arity would `TypeError` when
  the merged tree's tests import and exercise it, exactly as it would after
  a real merge.
- **Wrong environment (#369-shape): caught.** The job runs in a GitHub
  Actions checkout — the same structural environment (`gh api`
  content-fetch, no local PR worktree) production CI already uses for
  `closes-gate`. A fix whose correctness quietly depended on local-worktree
  file presence fails here the same way it fails in the real gate, instead
  of only in a human's worktree where the dependency happens to hold.
- **Mocked boundary (#388-shape): not caught, and not mechanically
  reachable by this mechanism.** Re-running a test that patches
  `subprocess.run` still re-runs the same mock, in any environment, against
  any base — the defect is inside the argument list the mock accepts
  unconditionally. Landing-time re-verification changes *when and against
  what* a test runs, not *what the test actually checks*; it cannot recover
  coverage a test was never designed to have. Closing this shape needs
  test-design review (e.g. asserting on captured argv), which is out of
  scope for a landing-time gate.

Score stated once, not implied: **2 of 3**.

Record the mechanism and its stated non-coverage in
`docs/issue-390/decisions/merge-state-reverification.md`, including why SHA-
staleness bookkeeping (items 2/3) was deferred rather than built now.

## Out of scope

- Items 2 and 3 (declared verification dependencies; stating verification
  context alongside a result) beyond what this decision doc records as
  deferred — no code changes for either in this proposal.
- Item 4 (write-set/signature overlap detection) — blocked on #323/#324.
- Closing the mocked-boundary gap (#388-shape) — needs test-design changes
  to `gates/test_closes_gate_ci.py`'s own tests, not a landing-time gate;
  flagged, not fixed, here.
- Any change to `gates/ci.py`'s existing `closes-gate` job.

## How you'll know it worked

`gates/test_merge_state_gate.py` constructs the #383 shape directly and
runs the acceptance check without needing GitHub Actions: it builds two
commits in a throwaway git repo — a "main" commit that changes a function's
arity, and a "branch" commit (based on the pre-change commit) whose only
caller still uses the old arity — merges them into a synthetic merge tree
the same way `refs/pull/<n>/merge` would, and asserts that running the
target test module against the merge tree fails with the arity `TypeError`,
while running the same test module against the branch commit alone (its own
base) passes. This is the executable artifact per #310: it fails today
(no merge-state gate exists) and passes once `merge-state-gate.yml`'s
underlying re-run logic is in place and correctly wired to the merge ref.
