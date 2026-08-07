# Survey — issue-298

## Scope of the change

The orchestrator (this plugin, `on-the-record`) is not a role session — it
never runs under `CLAUDE_ROLE`, and it has no `core` plugin dependency
(`on-the-record/.claude-plugin/plugin.json` declares none; `deliverable-guard.sh`
is self-contained bash+python, unlike `core/hooks/*.sh` which sources
`core/hooks/lib/gate-lib.sh`). The write set for this issue is therefore
entirely inside this repo's own plugin, `on-the-record/`, plus its test
suite.

## Current enforcement surface (`on-the-record/hooks/`)

- `hooks.json` wires three hooks: `SessionStart -> self-update.sh`,
  `UserPromptSubmit -> directive.sh`, `PreToolUse(Write|Edit|MultiEdit|
  NotebookEdit) -> deliverable-guard.sh`.
- `deliverable-guard.sh` (the one existing orchestrator gate): denies a
  deliverable write (`src/`, `test/`, `docs/`) in a board repo when
  `CLAUDE_ROLE` is unset. Two defects, both confirmed by #287 and still
  present on this branch:
  - **S4**: `except ValueError: sys.exit(0)`, non-dict payload -> exit 0,
    missing `file_path` -> exit 0. Header comment claims "fail closed on
    non-0/2" but that trap only catches crashes (non-0/2 *process* exit);
    a parse failure inside the python one-liner deliberately `sys.exit(0)`s,
    which is an ALLOW, not a crash. This is the one deviation from the
    project's fail-closed PreToolUse convention (contrast with
    `core/hooks/approval-gate.sh`, which denies on `except ValueError`).
  - **S5**: both the bash prefilter (`*test/*`) and the python regex
    `(^|/)(src|test|docs)/` match only the literal singular `test/`
    segment. `tests/` (plural, the layout this very repo uses —
    `tests/run-orchestrate-tests.sh`, `tests/fixtures/`) never matches, so
    a deliverable write under `tests/` in a board repo is never denied.
- No other orchestrator-only gate exists. The commands/run.md prose lists
  four procedural obligations (read the proposal before relaying approval,
  verify checks before merging, re-read the board after a merge, relay
  only user-stated decisions) with zero mechanical backing — issue #298's
  own count (8+ role gates vs 1 orchestrator gate) is verified by reading
  `roles/*.json` role gates are external to this repo (they live in
  `tokenmaxxxer-core` and the per-domain rulebooks, out of this repo's
  write reach) but the *pattern* they follow is the thing to mirror.

## The house pattern being mirrored (execution-observation's eo-state)

Read from `/home/jwjung/tokenmaxxxer/rulebooks/execution-observation-rulebook/execution-observation/plugins/eo-state/hooks/`:

- `state.sh` (`SessionStart reset` / `PostToolUse mark`): writes a
  single-file timestamp marker (`.claude/.eo-read-marker`) on a
  best-effort substring match against the raw hook payload
  (`docs/issue-*/(reports|proposals)/` or `gh (api|pr)`). `SessionStart`
  deletes the marker first so a stale marker from a previous session can
  never vouch for a read that never happened this session.
- The consuming gate (`eo-methodology-gate`, in a sibling plugin) refuses
  a record write when the marker is absent — the marker producer and the
  refusing gate are two separate hooks/plugins, not one script.
- This project's own `core/hooks/approval-gate.sh` +
  `core/hooks/gh-guard.sh` are the best-in-class examples of the
  PreToolUse-gate shape actually already enforcing role obligations:
  fail-closed trap (`gate_trap_fail_closed`), a kill switch with the
  narrowed on-spelling default (`gate_kill_switch_active`), a Bash-token
  scan (`gate_bash_write_targets` / manual regex token extraction) to
  catch shell-spelled acts, and a `deny()`/`allow()` pair that always
  exits 2/0. `on-the-record`'s own `deliverable-guard.sh` predates this
  and re-derived a thinner, buggier version of the same shape (the S4/S5
  defects above are exactly the ones `gate-lib.sh`'s header comment says
  this pattern already fixed once, in `core`).

`on-the-record` has no dependency on `core` or its `gate-lib.sh` (checked:
`on-the-record/.claude-plugin/plugin.json` lists no plugin dependencies,
and `deliverable-guard.sh` is fully self-contained). The new hooks in this
issue's write set will follow the *same shape* (fail-closed trap, kill
switch, deny/allow, marker file) but as self-contained bash+python,
matching `deliverable-guard.sh`'s existing style rather than importing
`core`.

## What must be recorded to gate the two acts

The two acts named in the issue's acceptance criteria are both `gh`
Bash invocations from the orchestrator's own (non-role) session:

- `gh issue comment <n> --body "APPROVE issue-<n>/<role>"` — must be
  refused when the orchestrator has not read that issue's proposal
  (`docs/issue-<n>/proposals/*`) this session. `commands/run.md` step 5
  already prescribes reading the proposal file with `Read`, or catching
  it via `gh pr diff`/`gh pr view` on the phase-1 PR — either is a
  plausible "read" signal, mirroring eo-state's own best-effort substring
  approach rather than requiring one exact tool.
- `gh pr merge <n> ...` — must be refused unless `gh pr checks <n>` (or
  the raw API/graphql equivalent) was run for PR `n` this session, and the
  last recorded result was not failing. Verified live: `gh pr checks <n>`
  is the actual command (`gh pr checks 293` printed a real check-name/
  conclusion table above). When no checks exist at all for a repo (#291:
  44 of 48 repos have none), `gh pr checks <n>` exits non-zero with a
  distinct message ("no checks reported") rather than reporting a
  failure — that case needs its own explicit exemption path per the
  issue's acceptance criteria, not a silent pass-through.

Both markers need to be *per-subject* (per issue number / per PR number),
unlike eo-state's single global marker — the orchestrator juggles several
issues in flight (the mission-board loop in `run.md` is explicitly
multi-flow), so "was #298's proposal read" and "was #293's proposal read"
are different facts. State file: a single JSON file under
`.claude/.orchestrator-state.json` (siblings to eo-state's
`.claude/.eo-read-marker`) with `reads: {"<issue-n>": <epoch>}` and
`checks: {"<pr-n>": {"status": "pass"|"fail"|"no-checks", "at": <epoch>}}`.
`SessionStart` resets it (same stale-marker justification as eo-state).

## Test pattern to mirror

`tests/run-orchestrate-tests.sh` already exists in this repo and tests
`deliverable-guard.sh` end-to-end (spins up a temp git repo, feeds a
PreToolUse JSON payload on stdin, asserts the exit code). This is this
repo's existing analogue of `run-role-gates-tests.sh` (confirmed present
in `technical-writing-rulebook/tests/technical-writing/`, not in this
repo — this repo's role gates live in `core`/rulebooks, out of reach).
The new orchestrator-gate test suite follows the same harness shape
(`report()` helper, temp `git init` fixtures, stdin JSON, exit-code
assertions) as `run-orchestrate-tests.sh` already uses, since that file
*is* this repo's `run-role-gates-tests.sh` counterpart for gates it can
actually reach.

## Write set (confirmed, nothing new discovered outside it)

- `on-the-record/hooks/orchestrator-state.sh` (new) — marker producer
- `on-the-record/hooks/orchestrator-gate.sh` (new) — the two PreToolUse
  refusals + the no-checks exemption path
- `on-the-record/hooks/deliverable-guard.sh` (edit) — fix S4 (fail closed
  on unparseable payload) and S5 (`tests/` coverage) from #287
- `on-the-record/hooks/hooks.json` (edit) — wire the two new hooks
- `tests/run-orchestrator-gates-tests.sh` (new) — dedicated suite for the
  two new hooks
- `tests/run-orchestrate-tests.sh` (edit) — add regression cases for the
  deliverable-guard S4/S5 fixes (same file already covers that hook)
- `on-the-record/commands/run.md` (edit) — one line per obligation noting
  it is now mechanically enforced, not just prose (no behavior change to
  the procedure itself)
