# Survey — issue-459: PR-create/spec-index preflight hooks

## Scope confirmed
Issue #459 has no `## 실행 계획` block — single-step delivery, phase-1
proposal references `#459` plainly (no Closes).

## Existing logic to reuse (not duplicate)

- `gates/pr_reference.py`: `check_body(issue, body, phase, plan)` already
  implements the exact rule needed — phase-1 requires plain `#n`, no
  Closes/Fixes/Resolves; phase-2 requires the closing keyword unless the
  issue's plan has incomplete steps other than the last one (issue #228
  logic), in which case it *blocks* Closes instead. This is precisely the
  "expected trailer" rule #459 asks for (`Closes #n` on final step, `Refs
  #n` otherwise) — for a plain-#n phase-1 case the existing code phrases
  it as "PR 본문에 '#n' 참조가 없다"; the plan-aware case is handled by the
  incomplete-steps branch already.
- `gates/flows._plan_from_body(body)`: parses `## 실행 계획` into
  `[{step, roles, done}, ...]`, handles code-fence skipping. This is what
  extracts "issue's 실행 계획" per #459's requirement text.
- `gates/spec_index.py`: `check(repo)` / `parse_index(index_path)` already
  compute the tracked-file drift (recorded sha256 vs actual) against
  `docs/specs/reconciled-index.md`. `update(repo)` is the exact regen
  path the preflight should point at.

## Existing hook pattern (on-the-record/hooks/*.sh)

- `contract-guard.sh` is the closest precedent: `PreToolUse` + `Bash`
  matcher, regex-matches the target subcommand (`gh pr merge`) out of
  `tool_input.command`, resolves target cwd (cd-prefix / `-R`/`--repo` /
  URL forms), and denies via exit code 2 with a stderr message. Crucially
  it is **zero-install**: it does not `import` from `gates/`, it
  re-implements the needed check inline in a Python heredoc
  (`IFS='' read -r -d '' GUARD <<'PY' ... PY`), because the plugin ships
  standalone into consumer repos that may not have `gates/` checked out.
  Both new hooks must follow the same zero-install shape — read-only `gh`
  calls (`gh issue view --json body`) or local file reads
  (`docs/specs/reconciled-index.md`, staged diff), no dependency on the
  `gates/` package being importable.
- `deliverable-guard.sh` is the `Write|Edit|MultiEdit|NotebookEdit`
  PreToolUse precedent for local-file-based denial (no `gh` needed).
- `ORCHESTRATE_OFF` env var is the existing kill-switch every hook checks
  first (`case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac`).
- Subject/phase resolution precedent: `gates/ci.py._approved_roles_on_issue`
  — an `APPROVE issue-<n>/<role>` comment from an `docs/specs/approvers.md`
  account on the issue means phase-2; contract-guard.sh already re-derives
  this the same way. The new PR-create hook needs the same phase
  determination (to know whether Closes is required or forbidden) plus
  the issue number, which contract-guard.sh derives from the current
  branch name pattern `issue-<n>/<role>` when no explicit flag is given —
  same derivation applies here since `gh pr create` runs from the subject
  branch.

## Wiring surface

- `on-the-record/hooks/hooks.json`: `PreToolUse` array already has a
  `Bash` matcher entry (`contract-guard.sh`). A `Bash`-matched hook fires
  on every Bash command already (contract-guard.sh itself regex-filters
  internally) — the new hooks can share the same `Bash` matcher entry
  (add two more `command` entries to the existing hooks array) rather
  than adding new matcher blocks, mirroring how contract-guard.sh already
  self-filters on `gh pr merge`.
- `gates/test_boundary.py`: derives the "actual mechanisms" set from
  `on-the-record/hooks/*.sh` on disk and requires every one of them to
  have a recorded verdict row in `docs/specs/enforcement-boundary.md`.
  Adding two new `.sh` files means **that spec file must gain two new
  rows** in the same commit, or `test_boundary.py::t_all_gates_modules_recorded`
  fails. Confirmed `docs/specs/enforcement-boundary.md` is not itself a
  `docs/specs/reconciled-index.md`-tracked file (grep found no match), so
  editing it needs no `spec_index.py --update` regen.
- `docs/specs/enforcement-boundary.md` existing rows for
  `contract-guard.sh` / `deliverable-guard.sh` / `stop-gate.sh` give the
  exact row shape to copy: `| \`name.sh\` | contract | one-line note |`.

## Naming (issue text vs. issue's own acceptance-check filenames)

Issue body says hooks should be `on-the-record/hooks/**`, acceptance
checks name `on-the-record/hooks/test_pr_preflight.py` and
`on-the-record/hooks/test_spec_index_preflight.py` explicitly — so the
test filenames are fixed by the issue. The `.sh` hook filenames
themselves aren't pinned by acceptance text; following the existing
`<verb>-guard.sh` / `<verb>-gate.sh` naming split (contract-guard.sh
denies before an *act*, spec_index.py is called a "gate"), `pr-preflight.sh`
and `spec-index-preflight.sh` match the issue's own "PR-create preflight"
/ "Spec-index preflight" section headers most directly — picked over
`*-guard.sh` naming since the issue text uses "preflight" as the term of
art for both, twice each.

## What today's three failures looked like (for red-case fidelity)

- #447 / #458: `Closes #n` present while plan still has incomplete steps
  other than the final one — `pr_reference.check_body`'s
  `only_last_incomplete` branch already returns the exact denial text for
  this shape.
- #448: phase-2 delivery PR with no Closes/Fixes/Resolves at all — the
  `if not m or int(m.group(2)) != issue` branch.
- #455: `run.md` (a `docs/specs/reconciled-index.md`-tracked file, per
  `grep` of that index) changed in a commit without a
  `gates/spec_index.py --update` regen — `spec_index.check()`'s hash
  mismatch branch.

## Alternatives considered (feeds proposal Rationale)

1. **Import `gates/pr_reference.py` and `gates/spec_index.py` directly**
   from the hook scripts (via `sys.path` manipulation) instead of
   reimplementing the checks inline. Rejected: breaks the zero-install
   contract `contract-guard.sh`'s own header comment states — the plugin
   ships into consumer repos that clone `on-the-record/` as a plugin
   directory without necessarily checking out this project's `gates/`
   package, so an `import gates.pr_reference` would `ImportError` in
   exactly the repos the hook is meant to protect.
2. **One combined hook script for both preflights** instead of two
   separate `.sh` files. Rejected: the two checks fire on disjoint
   `tool_input.command` shapes (`gh pr create|edit` vs `git commit`) and
   the issue's own acceptance section names two separate test files
   (`test_pr_preflight.py`, `test_spec_index_preflight.py`) — splitting
   matches the existing one-hook-per-guarded-act granularity
   (`contract-guard.sh` only guards `gh pr merge`, not merge+create
   together).
