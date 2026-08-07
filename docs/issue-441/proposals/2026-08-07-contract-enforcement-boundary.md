---
status: proposed
files:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/stop-gate.sh
  - spawn.py
  - gates/test_boundary.py
  - docs/specs/enforcement-boundary.md
  - docs/issue-441/reports/architecture.md
---

## Scout: skipped

Skip condition: the spec leaves no design decision open that scouting
external exemplars could inform. This issue derives a boundary internal to
this monorepo's own gate/hook wiring (which of *our own* `gates/*.py`
modules and hooks are contract-bound), constrained by the issue text, the
PR #442 rejection's explicit instructions, and the operator's 2026-08-07
approval-comment follow-up — there is no comparable external product
category (no other project ships a "which of my internal CI scripts is
part of my own published contract" decision) for a sweep to compare
against. Scouting is skipped per the scout-directive's own skip condition.

## Second rework note (operator approval follow-up, 2026-08-07)

The operator approved with two binding changes, applied throughout this
file: (1) `closure_sweep.py` board-wide mode and `spawn_coverage.py` are
reclassified from "CI-supplement / unreached" to **out of scope — operator
decision, 2026-08-07** (item 1 table) — detecting already-drifted state is
not this issue's problem to solve, and the previous wording read as an
unmet obligation rather than a drawn boundary. (2) Item 4's per-session
visibility check is **dropped** (see item 4, rewritten below) rather than
kept: it existed only to make CI-supplement absence observable, and the
CI-supplement's remaining justification (board-wide drift) is now out of
scope, so there is nothing left for the notice to be *for*. The residual
gap it would have reported (human web-UI merges, bare-terminal `gh`/`git`
use) is unreachable by any zero-install signal anyway — no session runs to
print the notice in — so a static line in
`docs/specs/enforcement-boundary.md` carries the same information at lower
cost. `.github/workflows/consumer-closes-gate.yml` and
`consumer-closure-sweep.yml` (the reusable-workflow CI supplement) are
therefore **not built in this delivery** — the acceptance criterion's
"closes-gate 가 실제로 돌아 강제한다" is discharged by the zero-install
`contract-guard.sh` + `spawn.py` preflight baseline instead, per the
operator's approval comment ("무설치 강제로 다시 잡은 것이 옳다"). Building
the reusable CI workflows remains available as future work for the
residual human-UI/bare-terminal gap, which stays recorded as genuinely
unreached, not solved.

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
| `closure_sweep.py`, board-wide case (already-merged PRs, drift discovered later, delivered-but-open state accumulated over time) | none — this is a retrospective state, not one act | none — not attempted | **out of scope — operator decision, 2026-08-07** | operator ruled detecting already-drifted state out of scope for this issue (issue #441 approval comment); this is a deliberate boundary, not a gap this issue failed to close |
| `acceptance_gate.py` (#310, executable `## Acceptance`) | opening a phase-2 session against an issue whose Acceptance is prose-only | **new**: `spawn.py` preflight, before the session starts | contract | stronger than a merge-time check — refuses the session before any work happens, matching #424's "wire out of the wrong state" over "rule to follow" |
| `landing_readiness.py` (#407) | `gh pr merge` on a PR that fails the combined checks/approval/scope-overlap judgment | **new**: folds into the same `contract-guard.sh` pre-merge intercept | contract | same act as `ci.py`/`pr_reference.py`; today this module is advisory-only, this proposal promotes it to blocking inside the hook |
| `spawn_coverage.py` (#330, an issue never spawned) | none — absence of an act over time | none — not attempted | **out of scope — operator decision, 2026-08-07** | same operator ruling: "an issue was filed but a session never started" is an absence-over-time signal, structurally identical to the row above, and detecting it retrospectively is out of scope for this issue |
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

`spawn.py` gains the `acceptance_gate.py` preflight (item 1): before
starting a phase-2 session (an issue with an `APPROVE issue-<n>/<role>`
comment from an approvers.md account already on it —
`gates.ci._approved_roles_on_issue`, the same predicate `ci.py` already
uses to tell phase-1 from phase-2), it runs `acceptance_gate.check` against
that issue and refuses to spawn if the Acceptance section is prose-only.
Phase-1 spawns are unaffected — a phase-1 issue's Acceptance is still being
drafted, not yet the thing being executed against.

No visibility check is added (see the second rework note above for why the
one considered in the prior round was dropped instead of kept). The
reusable-workflow CI supplement from #442 is not built in this delivery;
if it is built later, its installation is a one-time repo fact documented
in `docs/specs/enforcement-boundary.md`, the same as any other opt-in CI
check — it does not need a live per-session notice once board-wide drift
detection (the thing that notice existed to compensate for the unknowable
absence of) is out of scope.

## Item 3 — how `gates/*.py` executes in a consumer, for the mechanisms this delivery ships

`contract-guard.sh` (item 2) needs `acceptance_gate`/`ci`/`pr_reference`/
`closure_sweep`/`landing_readiness`'s check logic to run inside the
consumer's own Claude Code session. It does not vendor a copy: the hook
script is itself the plugin-shipped artifact (no separate `gates/*.py`
install step), and it re-implements the specific read-only `gh api`/`gh pr
view` calls those modules already make, the same access pattern
`gates/ci.py --closes-only` uses today, rather than importing the modules
themselves (which would require shipping `gates/` to the consumer — not
done in this delivery, see the second rework note). `spawn.py`'s
`acceptance_gate` preflight runs the real `gates/acceptance_gate.check`
function directly, because `spawn.py` itself always runs from this
repository's checkout (every caller runs it directly, never a vendored
copy — see "where a consumer unavoidably passes" above), so no execution
gap exists there. The reusable-workflow checkout-pinning mechanics from
#442 (`repository: tokenmaxxxer/on-the-record, ref: main`) remain the
answer for the CI supplement whenever it is built, unchanged in design,
just not built in this delivery.

## Reachable vs. unreached — recorded honestly, per #310

| act | reachable by `contract-guard.sh` (Bash hook)? | reachable by `spawn.py`? |
|---|---|---|
| Claude Code session runs `gh pr merge` / `gh issue close` via its Bash tool | **yes** | n/a |
| Claude Code session runs `git push` to a protected branch via its Bash tool | **yes**, matcher extends to it | n/a |
| Opening a phase-2 session on an issue with prose-only Acceptance | n/a | **yes** |
| A human clicks "Merge pull request" / "Close issue" in the GitHub web UI | **no — no hook fires; no Claude Code session is involved at all** | no |
| A person runs `gh`/`git` from a plain terminal, outside any Claude Code session | **no — hooks are session-scoped** | no |
| Board-wide drift (`closure_sweep.py` full mode, `spawn_coverage.py`) | **out of scope — operator decision, 2026-08-07**, not attempted | **out of scope — operator decision, 2026-08-07**, not attempted |

The middle two rows (human web UI, bare terminal) are genuinely unreached
by the zero-install baseline built in this delivery. They would be caught
only by the CI supplement (branch-protection-required
`consumer-closes-gate.yml`), which is not built here (second rework note)
— recorded plainly as unreached, not folded into "contract" as if solved.
The last row is not "unreached" in that sense at all: the operator ruled
it out of scope, so there is no obligation here for either path to reach
it.

## Item 4 — how a consumer learns which contract clauses are unenforced for them

One mechanism: `docs/specs/enforcement-boundary.md`, generated from the
item 1 table, linked from `run.md` — the static reference, as in #442. The
second-round proposal (#442's rejection) added a live per-session
visibility check on top of this; the operator's approval follow-up asks
this delivery to re-decide it now that board-wide drift detection is out
of scope, rather than let the prior wording stand unexamined. **Decision:
drop it.** The visibility check existed to solve one specific problem —
"nobody can tell which consumer projects installed the CI supplement, so
nobody can act on that gap." With board-wide drift detection itself now
out of scope, and the CI supplement not built in this delivery, there is
no live-and-changing installation fact left to report: whether the CI
supplement is installed becomes exactly as static as everything else in
`docs/specs/enforcement-boundary.md`, and belongs there, not in a
per-session runtime check that would exist for its own sake.

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
  it requires the CI supplement, which is not built in this delivery.
- Detecting already-drifted state (`closure_sweep.py` board-wide mode,
  `spawn_coverage.py`) — **operator decision, 2026-08-07**: out of scope
  for this issue, not a gap it failed to close.
- Building `contract-guard.sh`'s command-matching into a general Bash
  policy engine — scoped to the specific `gh`/`git` acts in the item 1
  table.
- Building `.github/workflows/consumer-closes-gate.yml` /
  `consumer-closure-sweep.yml` (the reusable-workflow CI supplement) —
  deferred; the zero-install baseline discharges this issue's acceptance
  per the operator's approval comment.

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

## What did not work
