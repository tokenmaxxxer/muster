---
status: proposed
files:
  - gates/consumer_boundary.py
  - gates/test_consumer_boundary.py
  - .github/workflows/plan-aware-closes-gate.yml
  - docs/issue-396/decisions/consumer-boundary-mechanisms.md
  - docs/handbooks/operations.md
  - docs/issue-396/reports/implementation.md
---

## Request

A consumer project that installs the `on-the-record` plugin gets only
`on-the-record/commands` and `on-the-record/hooks`; everything under
`gates/`, `.github/workflows/`, and `spawn.py`'s local-file effects stays
in this repository. Nobody had written down which of today's ~30 fixes
reach a consumer versus stay repo-local, whether that boundary is
maintained by hand (a recurrence of #333/#376) or derived, whether each
gate mechanism belongs shipped or repo-local by design, or how a
consumer without any `.github/workflows/` gets the CI-side enforcement
`run.md`'s contract text describes. Issue #396 asks for a derived
boundary, a per-mechanism decision (including "correctly repo-local" as
a valid outcome, argued), a stated answer for how CI reaches a
consumer, and a convention for a fix to state its own reach.

## Constraints

- Item 1 must be computed, not a hand-maintained list (#333, #376).
- Item 2 is a decision per mechanism, not a blanket "ship everything."
- Item 3 must pick and argue one answer (scaffold / documented setup
  step / reusable workflow reference), not restate the question.
- Per #310, acceptance needs an executable artifact, not prose.
- Stay inside `docs/issue-396/**` plus the specific mechanism files
  listed above; no unrelated gate refactors.

## Rationale

Considered shipping `gates/` and `.github/workflows/` into
`on-the-record/` so plugin install carries them into the consumer's
tree directly (a literal copy/scaffold). Rejected: `gates/*.py` needs a
GitHub Actions runner with repo write access to post check results and
call the GitHub API for PR state — a plugin's installed surface
(commands run inside a Claude session, hooks run on session/tool
events) has neither. Copying the workflow file into every consumer repo
also reintroduces exactly the drift problem #333/#376 already named:
consumer copies pin to whatever revision they installed at and silently
diverge from fixes landed here afterward (#284, #369, #383 would never
reach a project-rich that scaffolded once and never re-ran the
scaffold).

Chose instead: keep `.github/workflows/plan-aware-closes-gate.yml` as
the enforcement source of truth in this repo, but convert it to a
reusable workflow (`on: workflow_call`) that a consumer's own five-line
workflow file calls with `uses:
tokenmaxxxer/on-the-record/.github/workflows/plan-aware-closes-gate.yml@main`.
The consumer still needs one small file (there is no way around that —
a plugin cannot install a workflow file into a repo's `.github/`
directory at install time), but its content never needs to change again
after a fix lands here, because the checkout inside the reusable
workflow's own steps pulls `gates/*.py` fresh from this repo at
whatever ref the consumer pins (`@main` or a tag). That is the
"reusable workflow reference" branch of item 3, chosen over "scaffold"
(copies drift) and over "documented setup step" alone (a step with no
artifact behind it is exactly the #377 shape the issue calls out).

## What will be done

1. **Derived boundary (item 1).** `gates/consumer_boundary.py`: reads
   `.claude-plugin/marketplace.json`, resolves the local-source plugin
   paths (entries whose `source` is a `./`-relative path — currently
   only `on-the-record`), walks `git ls-files`, and classifies every
   tracked path as `shipped` (under a local plugin's source dir) or
   `repo-local` (everything else), plus a third bucket
   `orchestrator-effect` for `spawn.py` specifically (documented reason:
   read by the operator's local checkout, not installed, but shapes
   spawned sessions against consumer repos — see survey.md). Runs as
   `python gates/consumer_boundary.py --classify`, exits 0, prints the
   table; this is the executable artifact acceptance under #310 can
   point at — rerunning it after any future PR reproduces today's
   classification without anyone maintaining a list.
2. **Test.** `gates/test_consumer_boundary.py` asserts the three
   buckets are non-overlapping and that `on-the-record/commands/run.md`
   and `on-the-record/hooks/hooks.json` classify as `shipped`, `gates/ci.py`
   and `.github/workflows/plan-aware-closes-gate.yml` classify as
   `repo-local`, and `spawn.py` classifies as `orchestrator-effect`.
3. **Per-mechanism decisions (item 2).**
   `docs/issue-396/decisions/consumer-boundary-mechanisms.md` records,
   for each of `gates/` (repo-local by design — needs a CI runner and
   repo-scoped GitHub API access a plugin hook doesn't have; reachable
   instead via the reusable-workflow call), `.github/workflows/plan-aware-closes-gate.yml`
   (repo-local as the canonical definition, reachable via
   `workflow_call`), `spawn.py` (already reaches consumers via
   orchestrator effect — no mechanism change needed, only the
   classification above), and `on-the-record/commands` + `hooks`
   (already shipped — no change).
4. **Reusable workflow (item 3).** Add `on: workflow_call` (with the
   existing `pull_request` trigger kept) to
   `.github/workflows/plan-aware-closes-gate.yml` so it is callable from
   another repo; document the five-line consumer-side caller file
   contents in `docs/handbooks/operations.md`.
5. **Reach convention (item 4).** `docs/handbooks/operations.md` gets a
   short convention: an implementation record states, per change,
   whether it reaches consumers (touches `on-the-record/**`, or
   `spawn.py`/its orchestrator effects, or is newly reachable via the
   reusable workflow) or stays repo-local, using the three buckets
   `consumer_boundary.py` defines — so "fixed" going forward names its
   own reach instead of leaving it for issue #396-shaped audits to
   reconstruct after the fact.

## Out of scope

- Retrofitting a reach label onto the ten PRs already classified in
  survey.md — that table stands as the one-time audit the issue asked
  for; the convention in item 5 applies going forward.
- Actually scaffolding the five-line caller file into project-rich or
  any other consumer repo — that is a per-consumer action for the
  operator, not a change to this repository.
- Rewriting `gates/*.py` internals; only the workflow trigger changes.

## How you'll know it worked

- `python gates/consumer_boundary.py --classify` runs and reproduces
  the shipped / repo-local / orchestrator-effect table without a
  hand-maintained list backing it.
- `pytest gates/test_consumer_boundary.py` passes.
- `.github/workflows/plan-aware-closes-gate.yml` is valid as both a
  direct-trigger workflow (unchanged local behavior) and a
  `workflow_call` target (new).
- `docs/issue-396/decisions/consumer-boundary-mechanisms.md` names a
  decision and reason for every mechanism in scope, including any
  correctly-repo-local outcome.
