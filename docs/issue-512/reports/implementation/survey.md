---
name: issue-512-survey
description: Current-state survey for porting the checks from #419 and #424 into deployed authoring-time hooks
---

# Survey: porting `gates/ci.py`/`gates/accumulation.py` checks to plugin hooks

## What exists today

- `gates.subprocess_call_shape_divergence(work: Path)` (in `gates/gates.py`)
  walks the whole tree (`git ls-files *.py`), groups `subprocess.run`/
  `check_output`/`check_call`/`Popen` calls by `(argv[0], argv[1])`, and
  flags a command whose call sites disagree on `_SEMANTIC_FLAGS`
  presence. Repo-wide, not diff-scoped — deliberately, per its own
  docstring ("전-트리 관례").
- `gates.sibling_mention_check(work, record_text)` (in `gates/gates.py`)
  needs two inputs: the diff (`gates.changed_files(work)`, a git call) and
  a specific record's text (fetched via `gh` in `gates/ci.py`, keyed off
  the PR's head branch → `issue-<n>/<role>` → the branch's own
  `docs/issue-<n>/reports/<role>.md`). Only runs when `pr is not None` in
  `ci.py`'s `check()` — the local-only call path has no way to pick a
  record.
- `gates/accumulation.py`'s `check_accumulation_claim(work, body)` diffs
  `work` against `HEAD` (working tree + staged) to find changed files,
  falls back to `git ls-files` (whole tree) when the diff is empty,
  classifies shape 1 (three-or-more inline subprocess calls in one
  changed `.py` file) or shape 5 (`roles/*.json`), and requires a
  `## Accumulation` line in `body` (the **proposal** body, not a record)
  when either shape is touched. Registered `repo-local` in
  `docs/specs/enforcement-boundary.md` — "not wired into any
  consumer-reachable preflight" is the exact gap #512 asks to close.

## `gates/ci.py`'s status as an entry point

`gates/ci.py`'s own docstring says its runner "disappeared when GitHub
Actions were retired (#460)" — confirmed: no `.github/workflows/` file
invokes it (only `contract-guard.sh`/`spawn.py` reach `pr_reference.py`,
`acceptance_gate.py`, `closure_sweep.py` per the boundary table). Both
checks are reachable only via `test_gates.py` unit tests today —
matching the issue's "called by nothing but its own unit test" claim for
`accumulation.py`, and the same is true of `ci.py`'s own runner for the
#419 pair.

## The established porting pattern (issue #457)

`on-the-record/hooks/record-claim-guard.sh` is the precedent this issue
follows: a `PreToolUse` (`Write|Edit|MultiEdit`) bash hook that reads the
JSON payload from stdin, extracts `tool_input.file_path` and the new
content fragment (`content`/`new_string`/`edits[].new_string` — Edit only
ever sees the changed fragment, never the whole file), re-implements the
check **inline in Python** (not `import gates`) because the hook ships
standalone inside the plugin and must run on an arbitrary target repo
with no `gates` package on `sys.path`, and derives the target repo root
by walking up from `cwd` looking for `.git` — never assuming
`CLAUDE_PROJECT_DIR` points at the marketplace repo. Deny is `sys.exit(2)`
plus stderr; fail-closed wrapper (`trap ... exit 2`) around the whole
script. `docs/specs/enforcement-boundary.md`'s `record-claim-guard.sh`
row records this as "ports `gates.py`'s ... checks inline (zero-install),
ships with the plugin."

This resolves the "call-shape checks... into deployed plugin hooks...
anchored to the target project root; no dependence on running inside the
marketplace repo" requirement directly: reuse the same shape, don't
invent a new one.

## Diff-scope mismatch (the tradeoff issue #512 names)

- `subprocess_call_shape_divergence` is repo-wide by design (needs two or
  more call sites to compare; a single-file diff view can't see a
  divergent sibling call site elsewhere in the tree).
- `sibling_mention_check` is diff-scoped already (only checks files the
  session is touching) but needs the **record text**, which a `ci.py`
  PR-context caller fetches over `gh api` from the PR's head branch — a
  `PreToolUse` hook has no PR yet (writes happen before the PR exists) and
  no `gh` round-trip budget per keystroke.
- `check_accumulation_claim` needs the **proposal body**, which at
  `PreToolUse` time for a code write may not have been written yet
  (proposal precedes code under the warrant-directive's phase-1/phase-2
  split, but nothing stops a session writing code before the proposal
  text is finalized) or may already be finalized in a file (a proposal
  markdown file under `docs/`) that the hook can read directly instead of
  needing PR-body network access.

## `closure_sweep.py` / watchdog-tick precedent (requirement 4)

`docs/specs/enforcement-boundary.md`'s `contract, orchestrator-loop` rows
(`closure_sweep.py`, `spawn_coverage.py`) show the exact wiring shape
requirement 4 asks to reuse: `spawn.py`'s `roster_watchdog()` calls
`find_violations()`/`find_uncovered()` each tick, board-wide, observe-only
("reports, closes nothing" — `closure_sweep.py`'s own docstring). This is
the model for a trend-measurement addition: no new blocking gate, an
advisory report appended alongside the existing sweep output.

## Required-field-presence strengthening (requirement 3)

`_ACCUMULATION_HEADING` in `gates/accumulation.py` today checks heading
existence only. `docs/issue-424/reports/architecture/survey.md`'s cited
precedent (#416) already establishes "field presence, not free-text
interpretation" as the house pattern — the same shape
`record-claim-guard.sh` uses for `unverifiable:`/`checked:` lines (regex
match on a labeled sub-field, no LLM judgment). A same-shape strengthening
for `## Accumulation` is: require the heading's body to contain a
labeled sub-line (a bare non-empty line is not enough; a recognizable
field marker is) rather than just the heading token.

## Gap this proposal must close in `docs/specs/enforcement-boundary.md`

Three new/changed rows: the two new hook scripts (`contract`,
zero-install, ships with plugin) and `accumulation.py`'s existing
`repo-local` row flips to reflect that its logic is now *also* reachable
via a hook (the module itself stays `repo-local` as the CI/pytest entry
point continues to exist; the hook is a new, separately-listed row,
matching how `record-claim-guard.sh` sits next to `gates.py`'s untouched
original functions).

## Skip-condition check

Does not apply — this is a design proposal (which hook fires when, how
much of the diff-vs-repo-wide tradeoff to accept, whether/how to
strengthen the accumulation field check, whether to add watchdog-tick
trend measurement) with real alternatives to weigh; scouting is scoped to
this repo's own established patterns (`record-claim-guard.sh`,
`closure_sweep.py`) per scout-directive's "non-product roles scout the
best of their own deliverable's kind" — no external product category
applies to an internal enforcement-hook design, so the sweep target is
precedent-in-repo, already covered above.
