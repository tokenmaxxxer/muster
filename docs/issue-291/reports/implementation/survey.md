# issue-291 survey

## Scope boundary (checked against overlapping open issues first)

#291 bundles six findings (G1-G6) across three repos plus one local clone.
Only what is committable inside **this** repo (`on-the-record`), on this
branch, is in scope for a PR from this session:

- G1 (org branch protection on `tokenmaxxxer-core`, `repo-status-board`,
  43 rulebooks) and G2 (`on-the-record` ruleset missing review requirement /
  `strict:true`) are GitHub org/repo *settings*, not files in this tree —
  no commit here changes them. They need `gh api ... /branches/main/protection`
  admin calls run directly against GitHub, which is a hard-to-reverse,
  shared-state action outside "commit to a branch, open a PR" scope, and
  is not something this session does unilaterally per the standing
  destructive-action guidance.
- G3 (board cron failures, silent) and G5 (`rsb` exit code) live in
  `repo-status-board`, a different repository. Not reachable from this
  branch.
- G6 (stale local clone at `/home/jwjung/tokenmaxxxer/on-the-record`) is
  outside any git repo (it's a filesystem artifact on the user's machine,
  not tracked source) — nothing to commit.
- **G4** is squarely in this repo: `spawn.py:ledger_write` (~line 2163)
  writes to `runs/ledger.jsonl`, and `runs/` is gitignored
  (`.gitignore:1`). `gates/flows.py:_ledger_read` (line 146) is the only
  reader, and it silently returns `[]` when the file is absent — which is
  exactly what happens in a fresh CI clone of the board, per the issue.
  This is the one piece fixable by a code change landed via PR to this
  repo, so this proposal scopes to G4 only.

Per #363 (fix the generator, not the symptom): the generator here is that
`runs/` is gitignored *and* is the only place ledger entries live — no
step ever moves entries from "local, gitignored" to "committed, shared".
A partial fix that only sanitizes-and-dumps once does not remove the
generator; the fix needs to be a repeatable step wired into the normal
ledger-write path (or a companion command run at the same cadence),
otherwise the board goes stale again the moment nobody remembers to run
it by hand — same failure shape as G3's silent cron.

## Current-state survey (write set this proposal will touch)

- `spawn.py` — `ledger_write()` (~2163-2171) is the sole writer of
  `runs/ledger.jsonl`. No sanitization step exists; entries may contain
  `cwd`, hostnames, or other machine-local paths (grep of `ledger_write`
  call sites shows fields like `pid`, `cwd`, `board_delta`, `outcome`).
- `gates/flows.py` — `_ledger_read()` (146-159) reads only
  `runs/ledger.jsonl`; no fallback path. `_ledger_issue`, and the
  `ledger_entries` filter at line 360, consume its output.
- `.gitignore` — `runs/` is ignored (confirmed line 1: `runs/`).
- No existing test covers `_ledger_read`'s fresh-clone-empty behavior;
  `gates/test_flows.py` / `test_flows.py` exist at repo root and under
  `gates/` (the #398 collision — root `test_gates.py` vs
  `gates/test_gates.py` — is a separate, already-tracked defect, not
  touched here).
- No existing "sanitized extract" concept anywhere in the repo (grepped
  `sanitiz`, `extract`, `ledger` — nothing pre-existing beyond
  `ledger/collect.py`, which is the *review-record* ledger, a distinct
  system from `runs/ledger.jsonl` — different subject, same word).

## Skip-condition check (scout directive)

Scouting (external prior-art sweep) does not apply: this is an internal
data-plumbing fix inside an existing gitignore/CI-fallback pattern
specific to this repo's own architecture (spawn.py / flows.py / board
contract, issue #172). There is no external product category to
benchmark against — the "design decision" is narrow (where the
committed extract lives, what fields are stripped) and settled by
reading the existing board contract (`gates/flows.py` docstring, issue
#172's proposal) rather than by market research. This is the
spec-leaves-no-open-design-decision skip condition.
