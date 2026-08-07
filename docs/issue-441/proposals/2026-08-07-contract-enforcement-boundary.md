---
status: proposed
files:
  - gates/boundary.py
  - gates/test_boundary.py
  - .github/workflows/plan-aware-closes-gate.yml
  - .github/workflows/closure-sweep.yml
  - .github/workflows/issue-bundling-gate.yml
  - .github/workflows/on-the-record-tests.yml
  - .github/workflows/consumer-closes-gate.yml
  - .github/workflows/consumer-closure-sweep.yml
  - docs/specs/enforcement-boundary.md
  - on-the-record/commands/run.md
  - docs/issue-441/reports/architecture.md
---

## Intent

#441 asks for the decision #396 left open: which enforcement mechanisms are
part of the contract `run.md` ships (and must therefore reach consumer
projects), which are legitimately local to this repository, how the
contract-bound ones physically reach a consumer that installs only a plugin,
how `gates/*.py` executes there, and how a consumer can read which contract
clauses are currently unenforced for it.

## Constraints established by the issue and the survey

- Item 1 needs a per-mechanism verdict with a recorded reason, not a
  blanket ship-everything or keep-everything call.
- Item 2's candidates are named in the issue: scaffold, documented setup
  step, or reusable workflow reference (`uses: owner/repo/.github/workflows/x.yml@ref`).
- Item 3 is fatal if skipped: a workflow with no `gates/*.py` present does
  not run, regardless of what item 2 decides.
- Item 4: an unenforced clause must be legible to a consumer, not merely
  absent (#310).
- The boundary must be *derived*, not a hand-maintained list (#333, #376),
  and verified by a test that fails when the derivation and reality
  diverge (`test_gates.py` per the issue's acceptance criteria — implemented
  as `gates/test_boundary.py` in this proposal, following this repo's
  `test_<module>.py` naming next to the module it tests).
- Acceptance requires running `closes-gate` in one real consumer project,
  not reasoning about it (#416).

## Per-mechanism decision (item 1)

| mechanism | verdict | reason |
|---|---|---|
| `plan-aware-closes-gate.yml` / `gates/pr_reference.py`, `gates/ci.py` (phase-1/phase-2, `Closes #N`, write-scope) | **contract** | `run.md` states these obligations as things a role session and its PR must do; a consumer installing `run.md` is told these rules apply to them. Enforcement must travel with the description or #310 reproduces across the repo boundary. |
| `closure-sweep.yml` / `gates/closure_sweep.py` | **contract** | `run.md` (per the survey, lines ~276, ~344) describes closing-keyword/delivered-but-open discipline that only `closure_sweep.py` detects; the text ships already, so the detector must be reachable too. |
| `issue-bundling-gate.yml` / `gates/issue_bundling.py` | **repo-local** | Checks issue-*creation* hygiene for how `tokenmaxxxer/*` projects file issues (#328). `run.md` does not state a bundling obligation for role sessions or their PRs — this is process discipline for the issue author's own habit in this org, not a clause a consumer's `run.md` copy asserts. Kept local; recorded here so the judgment isn't merely absent. |
| `on-the-record-tests.yml` | **repo-local** | Runs `on-the-record`'s own pytest suite against its own PRs. A consumer has no reason to run on-the-record's test suite; nothing in `run.md` claims it does. |
| `on-the-record/hooks/*.sh` | **contract, already shipped** | No action needed — already reaches consumers via the plugin. Listed for completeness of the per-mechanism table. |

## Item 2 — how a contract-bound mechanism reaches a consumer

**Decision: reusable workflow reference**, not a scaffold and not a
documented manual-setup step alone.

Argument: a scaffold (files a consumer copies once) drifts the moment
`on-the-record` fixes the gate — the consumer's copy is now stale and
nothing detects it, reproducing exactly the "description ships, backing
doesn't" shape one layer down. A purely-documented setup step has the same
problem plus depends on the consumer actually reading and following docs
before an issue makes it visible. A reusable workflow reference
(`uses: tokenmaxxxer/on-the-record/.github/workflows/consumer-closes-gate.yml@main`)
means the consumer's own thin workflow file never changes; fixes to the gate
logic land the moment `on-the-record`'s `main` updates, with no consumer
action. This matches how `plan-aware-closes-gate.yml` already treats trust:
it deliberately never runs PR-supplied code, only code pinned to a fixed
external ref — a reusable-workflow caller is the same trust shape, just
initiated from a different repository.

Consumers still need one documented one-time step — add a caller file
(≈10 lines) invoking the reusable workflow, since a plugin genuinely cannot
install `.github/workflows/*`. That step is unavoidable and is recorded in
`docs/specs/enforcement-boundary.md`, not hidden as "automatic."

## Item 3 — how `gates/*.py` actually executes in a consumer

The reusable workflow's own `checkout` step is pinned to
`repository: tokenmaxxxer/on-the-record, ref: main` (not the calling repo,
not the calling ref) — the same pinning `plan-aware-closes-gate.yml` already
uses for its own repo, just made explicit about which repo. This is what
makes `gates/*.py` present in the job's filesystem regardless of which
project's workflow invoked it. The gate then talks to the *consumer's* PR
purely through `gh` CLI / GitHub API calls (`--pr`, `github.repository`,
`GH_TOKEN`) exactly as `gates/ci.py --closes-only` already does today — it
was already written to never read the invoking repo's working tree for its
closes-only mode (survey, `pr_reference.py` trust-boundary note). Concretely:
new thin wrapper workflows `consumer-closes-gate.yml` / `consumer-closure-sweep.yml`
add `on: workflow_call` and parameterize `github.repository` /
`secrets: inherit`; `plan-aware-closes-gate.yml` and `closure-sweep.yml`
become thin callers of the same job for this repo, so there is exactly one
implementation of each job, not a fork.

Not chosen: shipping `gates/*.py` inside the plugin directory. Rejected
because the plugin has no CI execution context (it only runs inside a role
session, per the plugin's actual shape — `commands/` + `hooks/`) — there is
nothing in a consumer's repo that would invoke plugin-shipped Python during
their own PR checks without the consumer writing the exact same
`.github/workflows/*.yml` caller file anyway. Checkout-from-source removes
the duplicate-and-drift failure mode that shipping-in-plugin would still
have (plugin version and gate version could diverge silently).

## Item 4 — how a consumer learns which contract clauses are unenforced for them

`docs/specs/enforcement-boundary.md` is generated content (not hand
authored per consumer) stating, per mechanism, contract-vs-repo-local and
the reason from the table above; it ships as part of `on-the-record`'s own
docs and is linked from `run.md` itself, so a consumer reading the contract
text finds the boundary one hop away instead of having to infer it. The
mechanical backstop is `gates/test_boundary.py`: it derives the *actual*
shipped set from `marketplace.json` + the plugin directory contents (per
#333/#376, computed not maintained) and fails if a workflow file exists
whose backing script (`gates/*.py` it invokes) is absent from what a
`workflow_call` caller could reach, or if a mechanism in the per-mechanism
table above has no recorded verdict — this is the acceptance criterion's
"a gate with no recorded judgment must not silently exist" made executable.

## Out of scope

- Retrofitting `issue-bundling-gate.yml` or `on-the-record-tests.yml` for
  consumer use — decided repo-local above.
- Any change to `run.md`'s prose beyond adding the one link to
  `docs/specs/enforcement-boundary.md`.
- Building the boundary derivation as a general-purpose plugin-shipping
  framework — scoped to this repository's two consumer-bound gates.

## How this will be verified

- `gates/test_boundary.py` passes and fails correctly when a mechanism is
  added to `.github/workflows/` without a recorded verdict (mutation check).
- `python3 -m pytest -q` (no `--ignore`) run and reported.
- `closes-gate` actually invoked against a real PR in one live consumer
  project (`project-rich`, named in #396/#441) via the reusable workflow,
  with the run's result (not just its existence) shown.

## What did not work
