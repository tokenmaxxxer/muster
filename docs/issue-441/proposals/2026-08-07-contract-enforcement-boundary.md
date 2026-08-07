---
status: proposed
files:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/stop-gate.sh
  - spawn.py
  - gates/boundary.py
  - gates/test_boundary.py
  - .github/workflows/consumer-closes-gate.yml
  - .github/workflows/consumer-closure-sweep.yml
  - .github/workflows/plan-aware-closes-gate.yml
  - .github/workflows/closure-sweep.yml
  - .github/workflows/issue-bundling-gate.yml
  - .github/workflows/on-the-record-tests.yml
  - docs/specs/enforcement-boundary.md
  - on-the-record/commands/run.md
  - docs/issue-441/reports/architecture.md
---

## Rework note (supersedes the PR #442 version of this file)

PR #442 was rejected. Its conclusion — a consumer must hand-add a caller
workflow file, called "unavoidable" by the proposal itself — leaves the
exact shape #310 forbids: unenforced-by-default becomes
enforced-only-if-installed, and installation is unobservable, so the two
are practically the same state. The rejection's instruction: stop starting
from "what must a consumer install" and start from "where does a consumer
pass with no action of their own." This version does that. It keeps item 2
and item 3's CI-reference mechanics from #442 (they are sound) but
demotes them from primary path to supplement, and it completes item 1's
table to all 11 `gates/*.py` modules plus `spawn.py` and the plugin hooks,
per the rejection's explicit instruction.

## Intent

#441 asks for the decision #396 left open: which enforcement mechanisms are
part of the contract `run.md` ships (and must therefore reach consumer
projects), which are legitimately local to this repository, how the
contract-bound ones physically reach a consumer that installs only a
plugin, how `gates/*.py` executes there, and how a consumer can read which
contract clauses are currently unenforced for it. The rework adds a fifth,
operator-stated requirement: minimum enforcement must stand for a consumer
who installs nothing at all.

## Constraints established by the issue, the survey, and the PR #442 rejection

- Item 1 needs a per-mechanism verdict with a recorded reason, covering
  every module under `gates/`, not a subset (rejection, explicit).
- For each contract clause, identify the **act** that violates it and
  determine whether that act passes a reachable gate — a hook the plugin
  already installs, or `spawn.py` (the only path that starts a role
  session, run directly rather than vendored, so no consumer-side copy to
  go stale). CI workflows are a supplement for what those two do not
  reach, never the primary path (rejection, explicit).
- An act with no reachable zero-install gate must be recorded as
  genuinely unreached, not papered over with a CI mechanism the consumer
  may or may not have installed (#310).
- Item 4: an unenforced clause must be legible to a consumer, including
  whether the CI supplement is installed for them right now — "legible"
  means observable per-session, not just documented once in a spec file
  a consumer would have to think to open.
- The boundary must be *derived*, not a hand-maintained list (#333, #376),
  verified by a test that fails when a `gates/*.py` module, hook, or
  workflow has no recorded verdict.
- Acceptance requires running the enforcement in one real consumer
  project **that has done no installation work** (rejection, explicit;
  tightens #442's "one live consumer project" to specify its state).

## Where a consumer unavoidably passes, with no action of their own

Two paths exist today, before this proposal changes anything:

1. **Plugin hooks** (`on-the-record/hooks/hooks.json`) — installed once
   with the plugin, then run on every matching tool call for the life of
   the session, refreshed by `self-update.sh`'s own TTL pull so they do
   not go stale the way a copied workflow file would. Current wiring:
   `SessionStart` → `self-update.sh`, `UserPromptSubmit` → `directive.sh`,
   `PreToolUse` (matcher `Write|Edit|MultiEdit|NotebookEdit`) →
   `deliverable-guard.sh`, `Stop` → `stop-gate.sh`. `PreToolUse` matches
   only file-write tools today; it does not see `Bash` at all, so
   `gh pr merge`, `gh issue close`, and `git push` currently pass through
   unseen. Adding a `Bash` matcher puts a gate **in front of** those
   commands, before they execute — the same trust shape core's
   `board-gate.sh`/`approval-gate.sh` already occupy for a different act,
   so this is not a new kind of gate, just this repository's own
   contract-enforcement gate moved to sit where those already sit.
2. **`spawn.py`** — the only way to start a role session. Not shipped via
   the plugin marketplace, but not vendored either: every caller, this
   repo included, runs this exact file directly, so there is no per-consumer
   copy that can drift from it. A check added here runs identically for
   every consumer the moment they call it, with zero installation step.

Everything below is organized around these two paths and what they do and
do not reach.

## Item 1 — per-mechanism verdict (complete: 11 `gates/*.py` modules, `spawn.py`, the 4 plugin hooks, 4 workflows)

| mechanism | violating act | reachable path | verdict | reason |
|---|---|---|---|---|
| `ci.py` (phase-1/phase-2, `Closes #N`, write-scope, orchestrator-authored-deliverable ban) | `gh pr merge` on the delivering PR | **new**: `PreToolUse`+`Bash` in `contract-guard.sh`, intercepts before merge | contract | `run.md` states these as obligations on a role session's PR; enforcement must travel with the text (#310) |
| `pr_reference.py` (#126) | `gh pr create` / `gh pr merge` with a body not referencing its issue | **new**: same `contract-guard.sh` intercept | contract | same reasoning; folds into the same pre-merge check as `ci.py`, same act |
| `closure_sweep.py`, single-PR case (closing-keyword present on the delivering PR) | `gh pr merge` without a closing keyword linking the issue | **new**: same `contract-guard.sh` intercept, checked at merge time | contract | the specific violating act (this merge, this PR) is interceptable even though the module's full board-wide mode is not (see next row) |
| `closure_sweep.py`, board-wide case (already-merged PRs, drift discovered later, delivered-but-open state accumulated over time) | none — this is a retrospective state, not one act | CI only (`consumer-closure-sweep.yml`, supplement) | contract, CI-supplement | nothing to intercept: the violation is an absence discovered later, so periodic/triggered scanning is structurally required, not a design choice |
| `acceptance_gate.py` (#310, executable `## Acceptance`) | opening a phase-2 session against an issue whose Acceptance is prose-only | **new**: `spawn.py` preflight, before the session starts | contract | stronger than a merge-time check — refuses the session before any work happens, matching #424's "wire out of the wrong state" over "rule to follow" |
| `landing_readiness.py` (#407) | `gh pr merge` on a PR that fails the combined checks/approval/scope-overlap judgment | **new**: folds into the same `contract-guard.sh` pre-merge intercept | contract | same act as `ci.py`/`pr_reference.py`; today this module is advisory-only, this proposal promotes it to blocking inside the hook |
| `spawn_coverage.py` (#330, an issue never spawned) | none — absence of an act over time | CI only (`consumer-closure-sweep.yml`, supplement) or unreached if not installed | contract, CI-supplement, **honestly unreached without it** | there is no act to intercept; "no session was ever started" cannot be caught by gating a tool call. Recorded here per #310 rather than left off the table, which is the specific defect the rejection named |
| `issue_bundling.py` (#328) | `gh issue create` with bundled scope | (could be hooked, not chosen) | repo-local | this org's own filing hygiene; `run.md` states no such obligation on a consumer's role sessions |
| `on-the-record-tests.yml` / this repo's own `pytest` | n/a | n/a | repo-local | verifies `on-the-record`'s own source, not a consumer's |
| `skip_gate.py` (#334) | this repo's own `pytest` run reporting skips as pass | n/a | repo-local | wraps this repo's own CI invocation of its own suite |
| `spec_index.py` (#336) | edits to this repo's own `docs/specs/` without index update | n/a | repo-local | checks this repo's own doc set, not a consumer's |
| `risk_report.py` (#319) | none — advisory only | n/a | n/a (infrastructure) | non-blocking classifier feeding `gates.py`'s review surface, not itself a clause |
| `gates.py` | none — router/dispatcher | n/a | n/a (infrastructure) | dispatches to the modules above; not a standalone clause |
| `flows.py` (#172) | none — read-only | n/a | repo-local | feeds this repo's own status board UI |
| plugin hooks (`directive.sh`, `deliverable-guard.sh`, `stop-gate.sh`, `self-update.sh`) | — | already shipped, `PreToolUse`/`UserPromptSubmit`/`Stop`/`SessionStart` | contract, already shipped | listed for table completeness; `deliverable-guard.sh`'s matcher gains `Bash` per this proposal (new script `contract-guard.sh`, not a rewrite of the existing deny-only file-write guard) |
| `spawn.py` | — | itself is the reach point | contract | not marketplace-shipped, but run directly by every caller — see "where a consumer unavoidably passes" above |

## Item 2 (rework) — primary path is zero-install; CI is the supplement, and its absence is now observable

**Primary**: `contract-guard.sh`, a new `PreToolUse` hook matched on `Bash`,
ships with the plugin like the three existing hook scripts. It inspects
the command before execution (same deny-before-effect shape as
`deliverable-guard.sh`) and, for `gh pr merge` / `gh pr create` / `gh issue close`
matching a delivering PR in a `run.md`-governed session, runs the checks
from the `ci.py` / `pr_reference.py` / `closure_sweep.py` (single-PR) /
`landing_readiness.py` rows above via `gh api`/`gh pr view` calls (the
same read-only GitHub-API access those modules already use — no local
checkout needed, so no trust-boundary change from what `deliverable-guard.sh`
already does today). This reaches every consumer who has the plugin
installed, which is the same population `run.md` itself already reaches —
no additional installation, because it is not a new artifact, it is a new
matcher line on an artifact already present.

`spawn.py` gains the `acceptance_gate.py` preflight (item 1) and, separately,
a **visibility check**: at session start, if the target repo has no
`.github/workflows/consumer-closes-gate.yml` (or equivalent caller), it
prints a one-line notice to the operator that CI-side board-wide sweeps
(`closure_sweep.py` board-wide mode, `spawn_coverage.py`) are not installed
for this repo. This is what answers the rejection's "nobody knows which
projects installed it, so nobody can act on it": installation state
becomes an observed, printed fact on every session in every consumer
repo, not a silent unknown. It does not make the CI supplement
zero-install — it makes its absence impossible to not notice.

**Supplement**: the reusable-workflow mechanics from #442 are kept
unchanged in their design (`uses: tokenmaxxxer/on-the-record/.github/workflows/consumer-closes-gate.yml@main`,
checkout pinned to `tokenmaxxxer/on-the-record@main` rather than the
caller's ref or working tree, exactly matching `plan-aware-closes-gate.yml`'s
existing trust shape) but are now positioned as covering only what the
zero-install path structurally cannot reach — see next section — plus the
board-wide, periodic checks (`closure_sweep.py` full mode, `spawn_coverage.py`)
that have no single act to intercept. A consumer still adds one caller
file to get this layer; the difference from #442 is that its absence no
longer produces an unknowable gap — `spawn.py`'s visibility check reports
it every session, and the baseline (merge-time and session-start checks
above) already stands without it.

## Item 3 — unchanged from #442: how `gates/*.py` executes in a consumer

Kept as designed in #442: the reusable workflow's `checkout` step is
pinned to `repository: tokenmaxxxer/on-the-record, ref: main`, giving the
job `gates/*.py` regardless of which project's workflow invoked it, and it
talks to the consumer's PR purely through `gh`/API calls, matching how
`gates/ci.py --closes-only` already operates. `contract-guard.sh` (item 2,
new) uses the same read-only API pattern rather than a checkout, since it
runs inside an existing session rather than a fresh CI job — no new
execution model, same access pattern read twice.

## Reachable vs. unreached — recorded honestly, per #310

| act | reachable by `contract-guard.sh` (Bash hook)? | reachable by `spawn.py`? |
|---|---|---|
| Claude Code session runs `gh pr merge` / `gh issue close` via its Bash tool | **yes** | n/a |
| Claude Code session runs `git push` to a protected branch via its Bash tool | **yes**, matcher extends to it | n/a |
| Opening a phase-2 session on an issue with prose-only Acceptance | n/a | **yes** |
| A human clicks "Merge pull request" / "Close issue" in the GitHub web UI | **no — no hook fires; no Claude Code session is involved at all** | no |
| A person runs `gh`/`git` from a plain terminal, outside any Claude Code session | **no — hooks are session-scoped** | no |
| Board-wide drift (`closure_sweep.py` full mode, `spawn_coverage.py`) | no — no single act to intercept | no |

The bottom three rows are genuinely unreached by the zero-install baseline.
They are only caught if the CI supplement (branch-protection-required
`consumer-closes-gate.yml` / scheduled `consumer-closure-sweep.yml`) is
installed — which requires the consumer to configure branch protection
referencing the workflow, an installation act like #442's, kept here
because no zero-install substitute exists for a human bypassing the tool
entirely. This is recorded plainly rather than folded into the "contract"
verdict as if solved: per item 2's visibility check, a consumer without it
is told so every session, closing the specific complaint that installation
state was unknowable — the residual gap itself is not closed, and is not
claimed to be.

## Item 4 — how a consumer learns which contract clauses are unenforced for them

Two mechanisms, not one:

1. `docs/specs/enforcement-boundary.md`, generated from the item 1 table,
   linked from `run.md` — the static reference, as in #442.
2. `spawn.py`'s session-start visibility check (item 2) — the live,
   per-session signal that does not require a consumer to go read a spec
   file to find out their own installation state. This is the piece #442
   was missing: a document a consumer must think to open does not solve
   "nobody knows which projects installed it" by itself; a notice printed
   at the one point every consumer unavoidably passes does.

`gates/test_boundary.py` (kept from #442, scope widened): derives the
shipped/local set from `marketplace.json` + plugin contents, and now also
asserts every module under `gates/`, every `on-the-record/hooks/*.sh`
script, and `spawn.py` has a row in the item 1 table with a recorded
verdict — failing if any of the 11+ mechanisms above is added or changed
with no verdict recorded, which is the acceptance criterion's "a gate
with no recorded judgment must not silently exist" made executable, now
over the complete set rather than 5 of 14.

## Out of scope

- Retrofitting `issue_bundling.py`, `skip_gate.py`, `spec_index.py`,
  `on-the-record-tests.yml` for consumer use — decided repo-local above,
  unchanged from #442.
- Closing the human-web-UI / bare-terminal gap for a consumer who installs
  nothing — recorded as genuinely unreached, not solved, per #310; solving
  it requires the CI supplement, which remains consumer-installed.
- Building `contract-guard.sh`'s command-matching into a general Bash
  policy engine — scoped to the specific `gh`/`git` acts in the item 1
  table.

## How this will be verified

- `gates/test_boundary.py` passes and fails correctly when a mechanism
  (module, hook, or workflow) is added with no recorded verdict.
- `python3 -m pytest -q` (no `--ignore`) run and reported.
- In one live consumer project (`project-rich`, per #396/#441) **that has
  installed nothing** — no `.github/workflows/`, no `gates/`, plugin only:
  - a role session's attempted `gh pr merge` on a PR missing `Closes #N`
    is denied by `contract-guard.sh` before the merge executes, shown as
    an actual denied tool call, not reasoning about one (#416).
  - `spawn.py` invoked against an issue with prose-only Acceptance refuses
    to start the session, shown as an actual refusal.
  - `spawn.py`'s session-start output shows the CI-supplement-absent
    notice for that repo.

## What did not work
