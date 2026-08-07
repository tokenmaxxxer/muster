# Survey — issue #396

## What ships to a consumer today

`.claude-plugin/marketplace.json` lists plugin `on-the-record` with
`source: "./on-the-record"`. That directory contains only:

```
on-the-record/commands/run.md
on-the-record/hooks/{hooks.json,self-update.sh,directive.sh,deliverable-guard.sh}
```

Nothing else in this repository is inside that path, so nothing else
installs into a consumer's `.claude/plugins/` tree. Confirmed empirically:
`/home/jwjung/project-rich` (a live consumer checkout) has no `.github/`
directory at all — no closes-gate workflow, no CI.

Repo-root paths NOT under `on-the-record/`: `gates/` (ci.py,
closure_sweep.py, pr_reference.py, gates.py, flows.py),
`.github/workflows/plan-aware-closes-gate.yml`, `spawn.py`, `roles/`,
`ledger/`, `bench/`, `tests/`, top-level `test_*.py`, `docs/`.

## How spawn.py reaches consumers despite not being "installed"

`spawn.py` lives at repo root, outside `on-the-record/`, so it is not
part of the plugin bundle either. But it is not read by the consumer's
Claude session — it is run by the **operator**, from their local
`on-the-record` checkout, to spawn role sessions that operate *against*
a consumer repo (clone it, run a role session in it, open a PR against
it). Its behavior (TTL marker placement, Playwright cache mount) shapes
those spawned sessions and therefore does reach consumer projects, even
though the file itself never lands in the consumer's plugin directory.
This is a different reach mechanism than the plugin's `commands/hooks`
(installed vs. orchestrator-side), and the issue's own classification
already separates them this way.

## Today's ten merged PRs (2026-08-07, via `gh pr list --state merged`), by touched paths

| PR | touches | class |
|---|---|---|
| #370 | `.github/workflows/*`, `gates/ci.py` | repo-local |
| #368 | `spawn.py` | consumer-reaching |
| #364 | `gates/ci.py` | repo-local |
| #361 | `conftest.py`, `test_approve_scope.py` | repo-local |
| #317 | `spawn.py` | consumer-reaching |
| #307 | `spawn.py` | consumer-reaching |
| #297 | `spawn.py` | consumer-reaching |
| #293 | `spawn.py` | consumer-reaching |
| #283 | `spawn.py` | consumer-reaching |
| #281 | `gates/pr_reference.py` | repo-local |

6 of 10 consumer-reaching (spawn.py, all orchestrator-side), 4 of 10
repo-local (`gates/`, `.github/workflows/`, top-level test harness).
None of the ten touch `on-the-record/commands` or `on-the-record/hooks`
directly. `docs/**` changes are excluded from this table (records, not
behavior).

## What project-rich lacks, precisely

This repo enforces, at merge time via `.github/workflows/plan-aware-closes-gate.yml`
running `gates/ci.py` (which imports `gates/closure_sweep.py`,
`gates/pr_reference.py`, `gates/flows.py`, `gates/gates.py`):
- the phase-1/phase-2 closes-gate (a phase-1 PR must not carry `Closes #n`;
  a phase-2 PR must)
- the full GitHub closing-keyword match (#280/#281)
- record-evidence lookup via the PR's own head ref, not local tree state (#284, #369)
- the closure sweep (detects delivered-but-unclosed work)

project-rich has none of this: no `.github/workflows/` directory exists,
so no workflow runs on any PR, so nothing there checks `Closes #n`
correctness, nothing sweeps for delivered-but-open work, and nothing
enforces the phase discipline `on-the-record/commands/run.md` describes
to that same project's role sessions. The contract text is installed;
its enforcement is not.

## Existing precedent for shipping repo files into a consumer

None. No command in `on-the-record/commands/` currently writes files
into the invoking repository's tree (`grep` over `on-the-record/**/*.md`
for `.github` or `workflow` returns nothing). `/init`-style commands
(outside this repo) do write files via Claude Code's own Write tool
during a session, which is the closest existing mechanism a slash
command has available — a plugin cannot ship a raw file drop into
`.github/workflows/` at install time; a plugin command CAN instruct the
in-session Claude to write one.

## Skip conditions

Neither scout skip condition applies (not a pure bugfix; design
decisions are open on all four points the issue raises), so scouting
would normally run. Scouting is skipped here because the deliverable is
not product-shaped — it's an internal boundary/enforcement decision
with no external exemplar category to benchmark against (no comparable
"plugin ships CI enforcement to consumer repos" product to survey); the
relevant field is this repository's own marketplace.json, plugin
directory, and git history, all covered above.
