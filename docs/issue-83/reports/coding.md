# Issue #83 — Coding Record

loop_state: phase2-complete

## Upstream basis

- Issue #83 (rename muster -> on-the-record).
- PR #84 phase-1 proposal: `docs/issue-83/proposals/coding.md`.
- Approval: issue-level comment "APPROVE issue-83/coding" by JiwonJung94 (approvers.md account), 2026-07-29.

## Why

Execute the approved rename proposal exactly: marketplace metadata, `orchestrate/` -> `on-the-record/` directory move with its internal path references, and a prose sweep of remaining "muster"/"orchestrate" mentions in docs and scripts, per the constraints in the proposal (historical docs, `.muster-cache`, test fixtures untouched).

## What was done

Executed proposal steps 1-7 exactly:
1. `.claude-plugin/marketplace.json`: `name` -> `"tokenmaxxxer"`; `orchestrate` entry -> `name: "on-the-record"`, `source: "./on-the-record"`.
2. `git mv orchestrate on-the-record`; `plugin.json` name updated; `directive.sh`/`self-update.sh` `mk=` path -> `tokenmaxxxer`; `run.md` local doc variable renamed.
3. `README.md`, `README.ko.md`, `protocol.md`, `protocol.ko.md`: full sweep of muster/orchestrate/tokenmaxxxer-muster/repo-slug mentions.
4. `spawn.py`: prose mentions renamed; `.muster-cache` dir name and `"muster-probe"` field left untouched (out of scope).
5. `wakes.py`, `bench/run.py`: one prose mention each renamed.
6. `test_gates.py`: prose mentions renamed; fixture strings untouched. `test_spawn.py`: no product-name prose present, no changes needed.
7. `tests/run-orchestrate-tests.sh` (not in the original file list) needed a one-line path fix (`../orchestrate/hooks` -> `../on-the-record/hooks`) because it mechanically broke from the step-2 `git mv` — kept in scope as a direct consequence of the frozen move, not new scope.

Verification run (see closed_checks): grep sweep confirms all remaining muster/orchestrate hits are the intentionally-excluded classes (historical docs/runs, `.muster-cache`, `muster-probe`, env-var identifiers, test fixtures, historical filename citations, generic-English "musters"/"orchestrator" usage, and `directive.sh`/`self-update.sh`/`deliverable-guard.sh` internal prose which item 2 of the proposal froze to only the `mk=` line). `py_compile` on spawn.py/wakes.py passes. marketplace.json is valid JSON. `test_spawn.py` passes (56/56). `test_gates.py` has one failure (`t_board_reads_loop_state`), confirmed via `git stash` to fail identically on the pre-rename tree — pre-existing, unrelated to this change, not touched.

PR note added (see below / PR body): the GitHub repo rename `tokenmaxxxer/muster` -> `tokenmaxxxer/on-the-record` is a user-side follow-up, not performed in this repo.

## What did not work

- Initial attempt to inspect other roles' prior coding.md examples via `git cat-file -p main:docs/issue-80/reports/coding.md` was blocked by the board-gate hook (string-matches the path regardless of read-only intent) — worked around by writing the record from the contract v3 s19/s20 requirements directly instead.

## Open findings

None raised against this work.

## Next steps

None — proposal scope fully executed and verified. Any repo rename or further "muster" identifier renames (env vars, `.muster-cache`) are explicitly out of scope per the approved proposal.

## Open-finding resolution path

No open findings currently block progress. Should the warrant-hunter or a reviewer raise a blocking finding, it will be addressed and logged here as resolved_findings before further commits, per the coding-progress gate.

## closed_checks

- check: grep sweep for residual muster/orchestrate mentions outside excluded classes — clean
- check: python3 -m py_compile spawn.py wakes.py — pass
- check: marketplace.json JSON validity — pass
- check: test_spawn.py full suite — 56/56 pass
- check: test_gates.py full suite — 1 pre-existing failure (t_board_reads_loop_state), confirmed unrelated via git stash comparison
