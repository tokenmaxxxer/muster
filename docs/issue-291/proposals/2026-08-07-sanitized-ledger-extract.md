---
status: proposed
files:
  - spawn.py
  - gates/flows.py
  - ledger/runs_extract.jsonl
  - test_spawn.py
  - test_flows.py
---

## Request

#291 reports six governance gaps (G1-G6). Per the survey
(`docs/issue-291/reports/implementation/survey.md`), only G4 is fixable
from this repo: `runs/ledger.jsonl` is gitignored, so the public board's
fresh CI clone of `on-the-record` finds no ledger and every verdict
renders as permanent `pending` — failure outcomes (silent-failure,
failed-no-commit, progressed-dirty-tree, denials) are invisible to
anyone who isn't on the machine that produced them.

## Constraints

- `runs/` stays gitignored — raw ledger entries may carry machine-local
  fields (`cwd`, `pid`) that don't belong in git history.
- The board's fresh-clone read path (`gates/flows.py:_ledger_read`) must
  see real entries without any manual "remember to publish" step —
  otherwise this just becomes G3's silent-staleness failure again, one
  layer down.
- No new dependency, no schema change to the entries already consumed by
  `flows.py:360` (`_entry_repo_name`, `_ledger_issue`).

## Rationale

Considered: a periodic/cron job (like the board's own deploy workflow)
that scrapes `runs/ledger.jsonl` and commits a snapshot on a schedule.
Rejected — this repo has no CI runner with access to any single
session's `runs/` directory (it's local per-clone, per-machine state);
a cron here would have nothing to read, and bolting the publish step
onto the *board's* CI (a different repo) is out of this proposal's write
set per the scope boundary in the survey. A schedule-driven approach
also repeats the exact failure mode G3 already demonstrates: a step
that must run on its own and can silently stop mattering.

Chosen instead: make publication a side effect of `ledger_write()`
itself, so every local ledger append immediately updates a small,
already-sanitized, tracked file (`ledger/runs_extract.jsonl`) in the
same commit-able tree as everything else. No separate process to forget
to run, no cron to go silent — the generator (write path with no
publish step) is removed, not just this instance of the symptom.

## What will be done

- `spawn.py`: `ledger_write()` gets a companion step that, after
  appending to `runs/ledger.jsonl`, also appends a sanitized copy of the
  same entry to `ROOT / "ledger" / "runs_extract.jsonl"` (tracked). The
  sanitizer strips machine-local fields (at minimum `cwd`, `pid`) and
  keeps the fields `_ledger_read` consumers already depend on (`outcome`,
  `board_delta`, `subject`/`role` fields, timestamp).
- `gates/flows.py`: `_ledger_read()` reads `runs/ledger.jsonl` when
  present (local/dev case, unchanged behavior); when absent (fresh CI
  clone) it falls back to `ledger/runs_extract.jsonl` so the board sees
  real entries instead of `[]`.
- Tests: `test_spawn.py` gets a case asserting `ledger_write()` appends a
  stripped entry to the tracked extract file. `test_flows.py` gets a case
  asserting `_ledger_read()` falls back to the extract file when
  `runs/ledger.jsonl` doesn't exist.
- `ledger/runs_extract.jsonl` is created empty/tracked as the initial
  file this proposal adds to the write set.

## Out of scope

- G1, G2: org/repo branch-protection settings (GitHub admin API calls,
  not a file in this tree).
- G3, G5: `repo-status-board` repo (cron failure visibility, `rsb` exit
  code) — different repository, not reachable from this branch.
- G6: stale local clone at `/home/jwjung/tokenmaxxxer/on-the-record` —
  not a tracked source location.
- Board UI staleness surfacing (`generated_at`) — lives in
  `repo-status-board`, not here.
- Retroactively backfilling `ledger/runs_extract.jsonl` from any
  existing `runs/ledger.jsonl` on this machine — out of scope; the fix
  is forward-looking (every write from here on publishes).

## How you'll know it worked

- `test_spawn.py` and `test_flows.py` new cases pass.
- Manually: call `spawn.ledger_write({...})` in a scratch dir with no
  pre-existing `ledger/runs_extract.jsonl`, confirm the file is created
  and contains the entry minus `cwd`/`pid`.
- Simulate the board's fresh-clone case: delete/rename `runs/`, call
  `flows._ledger_read()`, confirm it returns the extract's entries
  instead of `[]`.
