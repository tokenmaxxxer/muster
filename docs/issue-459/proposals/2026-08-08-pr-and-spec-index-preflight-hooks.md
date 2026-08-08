---
status: proposed
files:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - on-the-record/hooks/spec-index-preflight.sh
  - on-the-record/hooks/test_spec_index_preflight.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
---

## Request

#459: today's two repeat CI failure shapes — a premature or missing
`Closes`-family trailer on a PR, and a spec-index-tracked file changed
without regenerating `docs/specs/reconciled-index.md` — should be caught
in-session, before the PR exists / before the commit lands, not after a
red CI run. Ship two `PreToolUse` hooks in the plugin
(`on-the-record/hooks/**`): one intercepting `gh pr create`/`gh pr edit`
that reads the issue's `## 실행 계획` and the PR body and refuses with the
exact expected trailer; one intercepting `git commit` that refuses when a
tracked spec file is staged with a changed hash and the index wasn't
regenerated in the same commit.

## Constraints

- Must ship inside the plugin (`on-the-record/hooks/**`), not as a
  CI-only workflow — the point is in-session prevention.
- Zero-install: per `contract-guard.sh`'s established pattern, the hooks
  cannot depend on this repo's `gates/` package being importable, since
  consumer repos install the plugin without necessarily checking out
  `gates/`. Checks reimplement the needed logic inline rather than
  `import`ing `gates/pr_reference.py` / `gates/spec_index.py`.
- Both hooks must be wired in `on-the-record/hooks/hooks.json`.
- New `.sh` files under `on-the-record/hooks/` must get a recorded
  verdict row in `docs/specs/enforcement-boundary.md`, or
  `gates/test_boundary.py::t_all_gates_modules_recorded` fails (it scans
  `on-the-record/hooks/*.sh` on disk and requires every one to have a
  row).
- Acceptance names the test files exactly:
  `on-the-record/hooks/test_pr_preflight.py`,
  `on-the-record/hooks/test_spec_index_preflight.py`.
- Fail-open on lookup failure (network/`gh` unavailable), matching every
  existing hook's convention — a check that cannot run must not block an
  unrelated command; what must never happen is silently *approving* a
  case the hook positively determined violates the rule.

## Rationale

**Reimplement the check logic inline vs. `import gates.pr_reference`/
`gates.spec_index` from the hook scripts.** Importing would be less code
and would guarantee the hook and the CI gate never drift out of sync.
Rejected because it breaks the zero-install contract that
`contract-guard.sh`'s own header comment establishes as the standing
rule for this plugin: `on-the-record/hooks/**` ships standalone into
consumer repos, and those repos are not guaranteed to have this
project's `gates/` directory checked out at all — an `import
gates.pr_reference` would `ImportError` in exactly the repos the hook
exists to protect, silently disabling the hook (or, worse, crashing the
tool call it's supposed to gate). `contract-guard.sh` already made this
exact tradeoff for the analogous `gh pr merge` case and accepted the
duplication; the two new hooks follow the same precedent for
consistency and because the underlying constraint (repos without
`gates/`) applies equally to them.

**One combined hook script for both preflights vs. two separate `.sh`
files.** A single script would mean one less `hooks.json` entry.
Rejected: the two checks fire on disjoint `tool_input.command` shapes
(`gh pr create|edit` vs `git commit`), the issue's acceptance section
already names two separate test files, and the existing pattern is one
hook per guarded act (`contract-guard.sh` only guards `gh pr merge`, not
merge+create together) — splitting keeps that granularity and keeps
each script's fail-open surface (network vs. local-file-only) distinct
instead of mixing a `gh`-dependent check and a pure-local-diff check in
one script.

## What will be done

1. `on-the-record/hooks/pr-preflight.sh` — `PreToolUse`/`Bash`, filters
   on `gh pr create`/`gh pr edit` inside `tool_input.command` (same
   regex-and-return-early style as `contract-guard.sh`). Resolves the
   subject issue number from the current branch (`issue-<n>/<role>`,
   same derivation `contract-guard.sh` uses for `-R`/`cd`/URL forms —
   here the base case is enough since `gh pr create` runs from the
   subject branch), and the phase via the existing `APPROVE
   issue-<n>/<role>` comment convention (`gh issue view --comments`,
   same rule `gates/ci.py._approved_roles_on_issue` encodes). Extracts
   the PR body text from the command itself (`--body`/`--body-file`
   argument — no PR exists yet to `gh pr view`), parses the issue's `##
   실행 계획` block into `[{step, done}, ...]` (port of
   `flows._plan_from_body`'s regex/fence-skip logic), and applies the
   same rule `gates/pr_reference.check_body` already encodes: phase-1 →
   require plain `#n`, forbid Closes/Fixes/Resolves; phase-2 with
   incomplete non-final plan steps → forbid Closes/Fixes/Resolves
   (blocks #447/#458's shape); phase-2 otherwise → require
   Closes/Fixes/Resolves (blocks #448's shape). Denies (exit 2) with the
   exact expected trailer named in the message. Fail-open (exit 0) on
   any `gh` lookup failure, unresolved branch pattern, or missing
   `--body`/`--body-file` (nothing to check yet, e.g. an interactive
   `gh pr create` prompt).
2. `on-the-record/hooks/test_pr_preflight.py` — red/green cases for all
   three of today's shapes (#447/#458 premature-Closes,
   #448 missing-Closes) plus the phase-1 plain-`#n` case, driven against
   the script's extracted pure-function core (body text + parsed plan +
   phase in, deny-message-or-none out) — same testable-without-network
   shape `gates/pr_reference.check_body` already has, so the shell
   wrapper stays a thin `gh`/regex glue layer.
3. `on-the-record/hooks/spec-index-preflight.sh` — `PreToolUse`/`Bash`,
   filters on `git commit`. Reads `docs/specs/reconciled-index.md` from
   the working tree (port of `spec_index.parse_index`'s row regex), gets
   the staged file set via `git diff --cached --name-only`, and for each
   tracked path that's staged, recomputes its sha256 against the staged
   *content* (`git show :<path>` — the about-to-be-committed blob, not
   the working-tree file) and compares to the index's recorded hash. If
   any tracked staged file's content-hash differs from the recorded hash
   **and** `docs/specs/reconciled-index.md` itself is not also staged
   with an updated matching hash, deny (exit 2) naming the file and the
   regen command (`python3 gates/spec_index.py --update`). Fail-open
   when `docs/specs/reconciled-index.md` doesn't exist or isn't
   readable, or `git diff --cached` fails (e.g. not a git repo yet).
4. `on-the-record/hooks/test_spec_index_preflight.py` — red (tracked
   file staged with changed content, index not updated in the same
   staged set) / green (index updated with the matching new hash in the
   same staged set) pair, against the script's pure-function core (rows
   + staged-path→content-hash map in, deny-or-none out).
5. `on-the-record/hooks/hooks.json` — add `pr-preflight.sh` and
   `spec-index-preflight.sh` as two more `command` entries inside the
   existing `PreToolUse`/`Bash` matcher block (same block
   `contract-guard.sh` is already in), preserving `contract-guard.sh` as
   the first entry.
6. `docs/specs/enforcement-boundary.md` — add two rows (contract,
   zero-install, one line each per existing row style) for
   `pr-preflight.sh` and `spec-index-preflight.sh`, next to the existing
   `contract-guard.sh` / `deliverable-guard.sh` / `stop-gate.sh` rows.

## Out of scope

- CI-supplement workflow versions of either check (e.g. a
  `.github/workflows/*.yml` twin) — issue #459 asks only for the
  in-session shipped-hook path; `gates/pr_reference.py` and
  `gates/spec_index.py` already exist for CI.
- Extending `pr_reference.check_body`'s underlying rule (e.g. new plan
  syntaxes) — this proposal ports the existing rule to fire earlier, it
  does not change what the rule says.
- `closure_sweep.py`'s board-wide retrospective case — out of scope per
  the operator's 2026-08-07 ruling already recorded in
  `docs/specs/enforcement-boundary.md`.
- `landing_readiness.py` folding into a hook — not part of #459's two
  named failure shapes.

## How you'll know it worked

- `python3 on-the-record/hooks/test_pr_preflight.py` passes, covering
  red cases for #447/#458 (premature Closes with incomplete non-final
  plan steps) and #448 (missing Closes on final-step delivery), plus a
  green phase-1 plain-`#n` case.
- `python3 on-the-record/hooks/test_spec_index_preflight.py` passes,
  covering a red case (tracked file's staged content changed, index not
  regenerated in the same staged set) and a green case (index
  regenerated with the matching hash in the same staged set).
- `python3 gates/test_boundary.py` passes with both new `.sh` files
  present and recorded in `docs/specs/enforcement-boundary.md`.
- Manually: on this branch, staging a `docs/specs/reconciled-index.md`-tracked
  file with an unregenerated hash and running `git commit` is refused by
  `spec-index-preflight.sh` with the regen command named.
