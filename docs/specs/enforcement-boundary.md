---
name: enforcement-boundary
description: >
  Which enforcement mechanisms are part of run.md's contract (and must
  reach consumer projects) and which are repo-local, per mechanism,
  derived and enforced by gates/test_boundary.py (issue #441).
---

# Contract enforcement boundary

Every `gates/*.py` module, every `on-the-record/hooks/*.sh` script, and
every `.github/workflows/*.yml` workflow in this repository must have a
row below with a recorded verdict. `gates/test_boundary.py` fails the
build if one is added or renamed with no row here — the boundary is
derived from this file's completeness against the filesystem, not
maintained by hand elsewhere (#333, #376).

Verdict values:
- `contract` — enforces an obligation `run.md` states on a consumer's role
  session; must be reachable by a consumer.
- `contract, CI-supplement` — contract-bound, but its violating act is only
  reachable via the CI supplement (not built in this delivery; see the
  proposal), because the zero-install baseline (plugin hooks + `spawn.py`)
  cannot see it.
- `out of scope — operator decision, 2026-08-07` — detecting already-drifted
  state was explicitly ruled out of scope for issue #441 (operator's
  approval-comment follow-up on that issue); this is a drawn boundary, not
  an unmet obligation. Narrowed by issue #464's ADR
  (`docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`):
  the `closure_sweep.py`/`spawn_coverage.py` board-wide cases are reversed
  (see the `contract, orchestrator-loop` rows below) — #312/#388/#407 stay
  under this original ruling, untouched.
- `contract, orchestrator-loop` — board-wide (multi-subject) case enforced
  zero-install via `spawn.py:roster_watchdog()`'s per-tick sweep call,
  reachable by any consumer running the orchestrator loop; observe-only,
  per issue #464.
- `repo-local` — checks this repository's own source/process, not a
  consumer's; no obligation to reach consumers.
- `n/a (infrastructure)` — router, dispatcher, or read-only feed with no
  standalone clause of its own.

## `gates/*.py`

| mechanism | verdict | reason |
|---|---|---|
| `ci.py` | contract | enforced zero-install via `contract-guard.sh` (phase-2 Closes requirement) and `spawn.py`'s `acceptance_gate` preflight; write-scope/phase-1-must-not-close portions remain CI-supplement (`plan-aware-closes-gate.yml`, not shipped to consumers in this delivery) |
| `pr_reference.py` | contract | phase-2 Closes/Fixes/Resolves requirement enforced zero-install by `contract-guard.sh` |
| `closure_sweep.py` | contract (single-PR case) / **contract, orchestrator-loop** (board-wide case) | single-PR closing-keyword act folds into `contract-guard.sh`; board-wide drift detection is now called each `spawn.py:roster_watchdog()` tick via `find_violations()`, reversing the 2026-08-07 out-of-scope ruling for this row per issue #464's ADR |
| `acceptance_gate.py` | contract | enforced zero-install via `spawn.py` preflight (`require_acceptance_gate`), before a phase-2 session starts |
| `landing_readiness.py` | contract, CI-supplement | advisory scope-overlap/checks judgment; not folded into `contract-guard.sh` in this delivery, remains CI-only where installed |
| `spawn_coverage.py` | **contract, orchestrator-loop** | "an issue was filed but no session ever started" is now checked each `spawn.py:roster_watchdog()` tick via `find_uncovered()`, including on an empty live roster, reversing the 2026-08-07 out-of-scope ruling for this row per issue #464's ADR |
| `issue_bundling.py` | repo-local | this org's own filing hygiene; `run.md` states no such obligation on a consumer's role sessions |
| `skip_gate.py` | repo-local | wraps this repo's own CI invocation of its own test suite |
| `spec_index.py` | repo-local | checks this repo's own `docs/specs/` set, not a consumer's |
| `risk_report.py` | n/a (infrastructure) | non-blocking classifier feeding `gates.py`'s review surface, not itself a clause |
| `gates.py` | n/a (infrastructure) | router/dispatcher to the modules above |
| `flows.py` | repo-local | feeds this repo's own status-board UI |

## `on-the-record/hooks/*.sh` (plugin-shipped)

| mechanism | verdict | reason |
|---|---|---|
| `contract-guard.sh` | contract | new (#441): `PreToolUse`+`Bash`, intercepts `gh pr merge` before it executes; zero-install, ships with the plugin |
| `pr-preflight.sh` | contract | new (#459): `PreToolUse`+`Bash`, intercepts `gh pr create`/`gh pr edit` before the PR body is set, denying a wrong Closes/plain-`#n` trailer for the phase; ports `pr_reference.check_body`/`flows._plan_from_body` inline (zero-install), ships with the plugin |
| `spec-index-preflight.sh` | contract | new (#459): `PreToolUse`+`Bash`, intercepts `git commit` before it lands, denying a staged spec-index-tracked file whose content changed without a matching index regen in the same staged set; ports `spec_index.parse_index` inline (zero-install), ships with the plugin |
| `deliverable-guard.sh` | contract | already shipped; blocks orchestrator-authored deliverables |
| `directive.sh` | contract | already shipped; `UserPromptSubmit` role directive injection |
| `stop-gate.sh` | contract | already shipped; `Stop` hook |
| `record-claim-guard.sh` | contract | new (#457): `PreToolUse`+`Write|Edit|MultiEdit`, session-side write-time mirror of `gates.py`'s record-claim-integrity checks (#310/#330/#331/#332/#333); zero-install, ships with the plugin |
| `role-test-claim-guard.sh` | contract | new (#457): `Stop`, role-session mirror of `gates/skip_gate.py` (#334) and the stub/full-suite integrity lesson behind #435, applied to the reply's own pasted test output; zero-install, ships with the plugin |
| `self-update.sh` | contract | already shipped; `SessionStart` plugin refresh |

## `.github/workflows/*.yml` (retired, issue #460)

The operator ruled (2026-08-08, issue #460) that this repo's own CI red-X
checks — including its own — are retired: all enforcement lives in the
shipped hook surface plus locally runnable gate commands. `.github/workflows/`
is deleted; the table below is the migration record `gates/test_boundary.py`
(via `test_boundary_workflow_migration.py`) checks against, not a listing of
files that still exist.

| mechanism | verdict | replacement |
|---|---|---|
| `on-the-record-tests.yml` | repo-local, deleted | locally runnable `python3 -m pytest` (or `pytest -q`), run by hand or by the orchestrator loop before landing, per the no-mock "build it, run it" phase-2 bar; no shipped hook can run the suite (hooks fire on tool-use events inside a session, not on a schedule or PR event) |
| `plan-aware-closes-gate.yml` | repo-local, deleted | `--closes-only` step: zero-install `on-the-record/hooks/contract-guard.sh` + `spawn.py`'s `acceptance_gate` preflight (see `ci.py` row above). Full-bundle step (write_scope/protected-path/deps/`record_checked_claims`): no zero-install replacement; existing `contract, CI-supplement` drop, runnable locally as `python3 gates/ci.py . --pr <n> --autodetect` |
| `closure-sweep.yml` | repo-local, deleted | single-PR case: zero-install `contract-guard.sh` (see `closure_sweep.py` row above). Board-wide case: now `contract, orchestrator-loop` via `spawn.py:roster_watchdog()` (issue #464 ADR), also runnable locally as `python3 gates/closure_sweep.py` |
| `issue-bundling-gate.yml` | repo-local, deleted | no replacement possible — issue-creation is a GitHub webhook event, unreachable by any Claude Code session hook; runnable locally as `python3 gates/issue_bundling.py <issue#>` |

## `spawn.py`

| mechanism | verdict | reason |
|---|---|---|
| `spawn.py` | contract | not marketplace-shipped, but every caller (including consumers) runs this exact file directly — no per-consumer copy to go stale; carries `require_board`/`require_no_repo_config`/`require_acceptance_gate` preflights |

## Consumer-readable extract

`on-the-record/UNENFORCED-CLAUSES.md` (issue #452) is the derived,
gate-checked extract of this file's `contract, CI-supplement` and
`out of scope — operator decision` rows, shipped inside the deployed
`on-the-record/` tree so a consumer session can read it zero-install.
`gates/test_boundary.py` fails the build if it drifts from this file.

## Reachable vs. unreached by the zero-install baseline

See `docs/issue-441/proposals/2026-08-07-contract-enforcement-boundary.md`
("Reachable vs. unreached" table) for the full act-by-act breakdown. In
summary: a Claude Code session's `gh pr merge`/`git push` and opening a
phase-2 session are reached with zero installation. A human merging or
closing via the GitHub web UI, or a person running `gh`/`git` from a plain
terminal outside any Claude Code session, are not reached by anything in
this delivery — genuinely unreached, not solved, per #310. Board-wide
drift detection is out of scope per the operator decision above, so it is
not "unreached" in that sense — there is no obligation for it here.
