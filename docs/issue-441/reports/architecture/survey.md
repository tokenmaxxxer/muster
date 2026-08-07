# Survey — issue #441: contract/enforcement boundary across repositories

## Current state (measured)

Shipped to a consumer (`.claude-plugin/marketplace.json` → `on-the-record/`
plugin source):

```
on-the-record/commands/run.md   (contract text)
on-the-record/hooks/*.sh        (in-session hooks: directive, deliverable-guard, stop-gate, self-update)
```

Not shipped, repo-root only:

```
gates/*.py            (ci.py, pr_reference.py, closure_sweep.py, acceptance_gate.py,
                        landing_readiness.py, issue_bundling.py, skip_gate.py,
                        spawn_coverage.py, risk_report.py, flows.py, gates.py, spec_index.py)
.github/workflows/*.yml
  plan-aware-closes-gate.yml   (PR gate, `pull_request`, checks out `ref: main` — never
                                 the PR head — then runs `gates/ci.py --closes-only`
                                 and the full `gates/ci.py` bundle)
  closure-sweep.yml            (board-wide sweep, `push`+cron+dispatch, runs
                                 `gates/closure_sweep.py --post`)
  issue-bundling-gate.yml      (issue-opened comment check, runs `gates/issue_bundling.py`)
  on-the-record-tests.yml      (runs this repo's own pytest suite on PR head)
```

Confirmed against `project-rich` (live consumer, per #396): no `.github/workflows/`,
no `gates/` — none of the above exists there. `run.md` still describes the
`Closes #N` / phase-1-must-not-close / write-scope obligations as if backed.

## Key design fact already present in the code (load-bearing for the proposal)

`plan-aware-closes-gate.yml` already checks out `main` by fixed `ref:` rather
than the triggering PR's head, specifically so the gate script can't be
neutralized by the PR it's gating (trust-boundary comment in the file itself).
`closure-sweep.yml` checks out the default ref of whatever repo it runs in
(currently always this repo, since it triggers on `push: main` here).

This means the checkout-pinning pattern needed to let a *foreign* repo pull
`gates/*.py` from `tokenmaxxxer/on-the-record` at run time is not a new
mechanism — it's the same `actions/checkout@v4` step with an added
`repository:` pin, applied to a workflow already built to run against
fixed, external script content instead of caller-supplied content.

## What run.md's contract actually promises vs. what's enforced here

- Phase-1/phase-2 gating, `Closes #N` discipline, write-scope discipline →
  enforced by `plan-aware-closes-gate.yml` + `gates/ci.py` + `gates/pr_reference.py`.
- Closing-keyword / delivered-but-open consistency across the board →
  enforced by `closure_sweep.py` via `closure-sweep.yml`.
- Issue-bundling discipline (#328: one issue, one problem) → enforced by
  `issue_bundling.py` via `issue-bundling-gate.yml`, but this checks issue
  *creation*, not PR content, and is scoped to how *this* project's operator
  files issues — not a `run.md`-stated obligation on role sessions.
- This repository's own test suite passing → `on-the-record-tests.yml`,
  entirely internal (verifies `on-the-record`'s own source, not a consumer's).

## Gap this issue closes

No file anywhere states, per mechanism, whether it ships. #396 established
*that* the gap exists; nothing computes or records the per-mechanism verdict,
nothing lets a consumer install the CI-side pieces (plugins cannot install
`.github/workflows/`), and nothing tells a consumer which contract clauses in
their copy of `run.md` are currently unenforced.

## Addendum (PR #442 rework) — full `gates/` inventory and the reachable-without-installation question

PR #442's per-mechanism table covered 5 rows (`ci.py`, `closure_sweep.py`,
`issue_bundling.py`, `on-the-record-tests.yml`, plugin hooks) and was
rejected for two reasons: it was incomplete (`gates/` has 11 non-test
modules, not 5), and every contract-verdicted row routed enforcement
through a GitHub Actions workflow a consumer must hand-add — a step the
proposal itself called unavoidable, which the operator rejected as not a
fix (installation state is unknowable, so unenforced-until-installed is
indistinguishable from unenforced).

Full inventory, `gates/*.py` (11 modules, excluding `test_*.py`):

| module | what it checks | triggering act (if any) |
|---|---|---|
| `ci.py` | phase-1/phase-2 bundle: `Closes #N`, write-scope, orchestrator-authored-deliverable ban | `gh pr merge` on the delivering PR |
| `pr_reference.py` (#126) | PR body references its own issue | `gh pr create` / `gh pr merge` |
| `closure_sweep.py` | closing-keyword / delivered-but-open consistency, board-wide | retrospective board state, not one act |
| `acceptance_gate.py` (#310) | issue's `## Acceptance` names an executable artifact or `unverifiable:` reason | opening a phase-2 session against the issue (i.e. `spawn.py`) |
| `landing_readiness.py` (#407) | per-PR merge-readiness (checks + approval + scope overlap) | `gh pr merge` (same act as `ci.py`) |
| `spawn_coverage.py` (#330) | an open issue with no session ever spawned against it | absence of an act — nothing to intercept |
| `issue_bundling.py` (#328) | one-issue-one-problem hygiene at filing time | `gh issue create` — this org's own filing habit, not a `run.md` clause |
| `skip_gate.py` (#334) | pytest skip-vs-pass exit code | this repo's own `pytest` invocation |
| `spec_index.py` (#336) | this repo's own `docs/specs/` content-hash drift | this repo's own doc edits |
| `risk_report.py` (#319) | non-blocking risk classification, feeds `gates.py`'s review surface | none (advisory only) |
| `gates.py` | manifest/write-set router `gates.py` dispatches to | (infrastructure, not a standalone clause) |
| `flows.py` (#172) | read-only status-board data | none (read-only) |

Plus `spawn.py` itself (not under `gates/`, not shipped via the plugin
marketplace, but the only path that starts a role session — every
consumer that uses `on-the-record` at all runs this exact file, since it
is invoked directly rather than vendored/copied) and the four
`on-the-record/hooks/*.sh` scripts (already reach consumers via the
plugin, kept fresh per session by `self-update.sh`'s own TTL pull — unlike
a workflow YAML a consumer copies once, these do not go stale).

This addendum is why the rework starts from "where does a consumer pass
with no action of their own" rather than "what does a consumer need to
install" — see `docs/issue-441/proposals/2026-08-07-contract-enforcement-boundary.md`.
