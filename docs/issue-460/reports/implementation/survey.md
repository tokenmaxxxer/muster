# Survey — issue #460: retire this repo's GitHub Actions

## Current `.github/workflows/` (4 files, all to be deleted)

| workflow | trigger | what it runs | who else already runs the same gate |
|---|---|---|---|
| `on-the-record-tests.yml` | `pull_request` → main | `pytest -q` (whole suite, on PR head) | nothing — this is the only place the suite runs |
| `plan-aware-closes-gate.yml` | `pull_request` opened/edited/sync/reopened → main | `gates/ci.py --pr <n> --autodetect --closes-only`, then `gates/ci.py --pr <n> --autodetect` (full bundle) | `--closes-only` portion already duplicated zero-install by `on-the-record/hooks/contract-guard.sh` (`PreToolUse`+`gh pr merge`) and `spawn.py`'s `acceptance_gate` preflight, per `docs/specs/enforcement-boundary.md`'s `ci.py` row. The full-bundle step (write_scope/protected-path/deps/`record_checked_claims`) has **no** zero-install equivalent — same doc already marks this `contract, CI-supplement`. |
| `closure-sweep.yml` | `push` main, daily cron, `workflow_dispatch` | `gates/closure_sweep.py --post` (board-wide multi-PR/subject×role sweep) | single-PR closing-keyword act already folds into `contract-guard.sh` per the boundary spec. Board-wide drift detection has no replacement anywhere — already recorded as `out of scope — operator decision, 2026-08-07` in the boundary spec and shipped in `on-the-record/UNENFORCED-CLAUSES.md`. |
| `issue-bundling-gate.yml` | `issues: opened` | `gates/issue_bundling.py <issue#>`, posts a comment on violation | nothing. Issue-creation is not an event any Claude Code hook can observe (hooks fire inside a role session, not on GitHub issue webhooks) — there is no shipped-hook equivalent possible. Boundary spec already marks `issue_bundling.py` `repo-local` ("this org's own filing hygiene; `run.md` states no such obligation on a consumer's role sessions") — i.e. never a contract clause, so it was never subject to `UNENFORCED-CLAUSES.md` in the first place. |

## Existing infra that already maps this territory

`docs/specs/enforcement-boundary.md` (issue #441/#452) already carries a
per-mechanism verdict table for every `gates/*.py`, every
`on-the-record/hooks/*.sh`, and every `.github/workflows/*.yml` file,
including a `.github/workflows/*.yml` section that labels all four
current workflows `repo-local` ("runs against this repo's own board/PRs/
suite"). `gates/test_boundary.py` already fails the build if any
`gates/`, `hooks/`, or `.github/workflows/` file lacks a recorded verdict
row — the table is derived from the filesystem, not hand-maintained.

`on-the-record/UNENFORCED-CLAUSES.md` (issue #452) already ships the
derived, gate-checked extract of every `contract, CI-supplement` /
`out of scope — operator decision` row — `closure_sweep.py` (board-wide
case) and `landing_readiness.py` are already there. `spawn_coverage.py`
too, unrelated to this issue's workflow set.

So most of the "replacement or recorded drop" bookkeeping issue #460 asks
for **already exists** from #441/#452 — this issue's job is (a) delete
the files, (b) make the now-true statement ("no `.github/workflows/`
remain") checkable, (c) close the one real gap: `plan-aware-closes-gate.yml`'s
full-bundle step (write_scope/protected-path/deps/`record_checked_claims`)
is CI-supplement today with no local-command pointer written down
anywhere consumer-visible, and `issue-bundling-gate.yml` has never been
given any verdict-table row that says what happens to it once the
workflow is gone (its `repo-local` verdict predates deletion and doesn't
by itself record "this can now only be run manually").

## Consequential file: `on-the-record/commands/run.md`

`run.md` (not currently in this repo's `docs/issue-460` scope list, but
directly contradicted by the change) instructs the landing role, before
merging any PR, to read `gh pr checks <n>`; if checks are absent
entirely, treat that as an anomaly and ask the user rather than silently
treating "no checks" as "pass" (`run.md` ~line 258-262). Once every
workflow is deleted, `gh pr checks` will report zero checks on **every**
PR, always — the "anomaly, ask" branch would fire on 100% of merges. This
is a direct behavioral consequence of this issue's own change and needs
a one-line correction in the same PR, or every future landing session
stalls asking the same now-expected question. Added to the write set.

## Branch protection

No way to read this repo's actual branch-protection required-checks list
from a worktree (`gh api repos/:owner/:repo/branches/main/protection`
needs push access this session may not have, and it is explicitly an
operator/admin action per the issue text: "the operator relays the admin
change"). The proposal will list the check names to remove by name
(`test`, `closes-gate`, `bundling-gate`, `closure-sweep`) for the
operator to relay, per the issue's own instruction — not attempt the API
call.

## Alternatives considered during survey

- **Keep `on-the-record-tests.yml` alone, drop the rest.** Rejected:
  issue #460 states the operator requirement plainly — *this repo's own*
  Actions are not needed either, CI red-X including this repo's own is
  retired. A partial keep contradicts the acceptance criterion
  (`gates/test_boundary.py` asserts `.github/workflows/` is absent or
  empty) directly.
- **Write a brand-new migration-table document.** Rejected in favor of
  extending `docs/specs/enforcement-boundary.md`'s existing
  `.github/workflows/*.yml` table with a "deleted, replacement" column
  (see proposal) — issue #460's acceptance check
  (`gates/test_boundary.py` asserts a migration-table entry per deleted
  workflow, cross-referenced against `UNENFORCED-CLAUSES.md`) reads
  naturally as extending the boundary spec's derived-and-checked table
  rather than starting a second, competing source of truth for the same
  four filenames.
