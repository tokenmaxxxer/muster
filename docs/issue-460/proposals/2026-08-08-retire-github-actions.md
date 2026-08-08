---
status: proposed
files:
  - .github/workflows/on-the-record-tests.yml
  - .github/workflows/plan-aware-closes-gate.yml
  - .github/workflows/closure-sweep.yml
  - .github/workflows/issue-bundling-gate.yml
  - docs/specs/enforcement-boundary.md
  - on-the-record/UNENFORCED-CLAUSES.md
  - on-the-record/commands/run.md
  - gates/test_boundary.py
  - gates/test_boundary_workflow_migration.py
---

## Request

Delete this repo's own `.github/workflows/` — the operator has ruled
that CI red-X checks, including this repo's own, are retired; all
enforcement lives in the shipped hook surface plus locally runnable
gate commands. For each deleted workflow, name its replacement surface
or record the deliberate drop in `on-the-record/UNENFORCED-CLAUSES.md`.
Update `docs/specs/enforcement-boundary.md` accordingly, and list the
branch-protection required-check names for the operator to remove.

## Constraints

- No workflow files may remain in `.github/workflows/`.
- Every deleted workflow needs a named replacement surface (shipped
  hook, or a locally runnable command documented in the contract/
  orchestrator loop) or a recorded drop in `UNENFORCED-CLAUSES.md` —
  nothing may silently lose coverage.
- `docs/specs/enforcement-boundary.md` is the existing derived,
  gate-checked source of truth for this exact bookkeeping (#441/#452);
  extend it rather than starting a second document.
- Branch-protection changes are an operator/admin action this session
  cannot make — list the check names, do not attempt the API call.

## Rationale

**Extend `enforcement-boundary.md`'s existing `.github/workflows/*.yml`
table with a "deleted, replacement" column, rather than writing a new
standalone migration-table document.** Considered writing a fresh
`docs/issue-460/...` migration table instead: rejected because
`gates/test_boundary.py` already derives its per-mechanism verdict table
from the filesystem and already fails the build on an unrecorded
mechanism; issue #460's acceptance check
("`gates/test_boundary.py` asserts a migration table entry per deleted
workflow, cross-referenced against `UNENFORCED-CLAUSES.md`") reads as
"extend the mechanism this repo already uses for exactly this
bookkeeping," not "build a second, competing source of truth for the
same four filenames." A standalone table would drift from the boundary
spec the moment either one is edited alone.

**Leave `issue_bundling.py` at its existing `repo-local` verdict rather
than moving it into `UNENFORCED-CLAUSES.md`.** Considered promoting it
to a `CI-supplement`/`out of scope` row like `closure_sweep.py`'s
board-wide case: rejected because `UNENFORCED-CLAUSES.md` is defined
(both in its own header and in `gates/test_boundary.py`'s
`t_unenforced_clauses_file_matches_spec_exactly`) as the extract of
`run.md`-stated *contract* clauses the zero-install baseline doesn't
reach for a consumer. `issue_bundling.py` was never a contract clause —
`run.md` states no such obligation on a consumer's role sessions, it is
this org's own filing hygiene. Filing it under `UNENFORCED-CLAUSES.md`
would misrepresent a repo-local convenience check as a dropped consumer
obligation. Its migration-table row instead says plainly: no hook
equivalent is possible (issue creation is a GitHub webhook event, not
something a Claude Code session hook observes), and the gate is now
runnable only as `python3 gates/issue_bundling.py <issue#>`.

## What will be done

1. Delete all four `.github/workflows/*.yml` files.
2. In `docs/specs/enforcement-boundary.md`'s `.github/workflows/*.yml`
   table, add a `replacement` column and fill it per workflow:
   - `on-the-record-tests.yml` → locally runnable `python3 -m pytest`
     (or `pytest -q`), to be run by hand or by the orchestrator loop
     before landing, per the no-mock "build it, run it" phase-2 bar
     already in force. No shipped hook can run the suite (hooks fire on
     tool-use events inside a session, not on a schedule or PR event).
   - `plan-aware-closes-gate.yml` → split into its two steps:
     - `--closes-only` step: already replaced zero-install by
       `on-the-record/hooks/contract-guard.sh` + `spawn.py`'s
       `acceptance_gate` preflight (existing `ci.py` boundary-spec row).
     - full-bundle step (write_scope/protected-path/deps/
       `record_checked_claims`): no zero-install replacement exists;
       recorded as the existing `contract, CI-supplement` drop,
       runnable locally as `python3 gates/ci.py . --pr <n> --autodetect`.
   - `closure-sweep.yml` → single-PR case already replaced by
     `contract-guard.sh`; board-wide case already recorded as the
     existing `out of scope — operator decision, 2026-08-07` drop,
     runnable locally as `python3 gates/closure_sweep.py`.
   - `issue-bundling-gate.yml` → no replacement possible (issue-creation
     event unreachable by any session hook); stays `repo-local`, now
     runnable only as `python3 gates/issue_bundling.py <issue#>`.
3. `on-the-record/UNENFORCED-CLAUSES.md` needs no new rows — the two
   genuine consumer-facing drops this change touches
   (`closure_sweep.py` board-wide, and `ci.py`'s full-bundle checks via
   `landing_readiness.py`'s existing row) are already present. Confirm
   this by running `gates/test_boundary.py` after the edit.
4. Add `gates/test_boundary_workflow_migration.py` with two checks
   matching issue #460's acceptance criteria: (a) `.github/workflows/`
   is absent or empty; (b) every one of the four deleted workflow
   filenames has a migration-table row in `enforcement-boundary.md`
   whose `replacement` column is non-empty, and any row naming a
   `CI-supplement`/`out of scope` drop is cross-referenced by name in
   `UNENFORCED-CLAUSES.md`. Wire it into `gates/test_boundary.py`'s
   own `_run` list so `python3 gates/test_boundary.py` covers it.
5. Correct `on-the-record/commands/run.md`'s pre-merge instruction
   (~line 258-262): today it treats "`gh pr checks` returns nothing" as
   an anomaly to flag to the user before merging. After this change
   every PR in this repo will have zero checks, always — rewrite that
   branch so it no longer asks the same now-expected question on every
   merge, while keeping the "a failed check blocks merge" rule for
   consumer repos that do wire CI.
6. Report the branch-protection required-check names to remove for the
   operator to relay: `test` (from `on-the-record-tests.yml`),
   `closes-gate` (from `plan-aware-closes-gate.yml`), `bundling-gate`
   (from `issue-bundling-gate.yml`), `closure-sweep` (from
   `closure-sweep.yml`) — exact names read from each workflow's `jobs:`
   key, which is what GitHub records as the required-check name.

## Out of scope

- Actually calling the GitHub branch-protection API to remove required
  checks — operator/admin action per the issue text.
- Building a shipped-hook or `spawn.py`-preflight replacement for the
  `ci.py` full-bundle checks or for board-wide `closure_sweep.py` —
  both are pre-existing, already-recorded drops from #441; closing them
  is a separate issue's scope, not this one's.
- Building any GitHub-webhook-reachable replacement for
  `issue_bundling.py` — no such surface exists in this contract (issue
  creation is outside any Claude Code session's hook surface).

## How you'll know it worked

- `ls .github/workflows/` is empty or the directory is gone.
- `python3 gates/test_boundary.py` passes, including the new
  `test_boundary_workflow_migration.py` checks wired into it.
- `python3 -m pytest gates/test_boundary_workflow_migration.py -q`
  passes standalone.
- `docs/specs/enforcement-boundary.md` has a non-empty replacement
  entry for each of the four deleted workflow names.
- `run.md`'s pre-merge step no longer instructs asking the user about
  absent checks as an anomaly.
