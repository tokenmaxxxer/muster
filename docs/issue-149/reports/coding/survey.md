# issue-149 — phase-1 current-state survey

## What exists today

`roles/*.json` already carries `decides`/`use_when`/`produces` per role
(`roles/coding.json`, `roles/review.json`, ...), but these are prose only —
`spawn.py:2058` reads `decides`/`use_when` purely to print `spawn.py roles`
output. No code reads `produces`. There is no `write_scope` key anywhere in
`roles/*.json` today (grepped, 0 hits).

Path enforcement that *does* run lives in `gates/gates.py`:
- `is_protected()` / `PROTECTED_ROOT_DIRS` etc. — a fixed deny-list
  (`.github`, `roles`, `gates`, secrets globs, ...) applied to every PR
  regardless of role. This blocks infra/pipeline tampering, not
  role-vs-produces mismatches.
- `writeset(d, cfg)` — compares changed files against `write:` lines
  parsed out of a **task-level `spec.md`** (router-only object, one per
  spawned task; not present for human-opened PRs — `ci.py`'s docstring
  explains why it's excluded from the CI entrypoint). This is scoped to a
  single task's plan, not to "this role's allowed output categories."
  It also fails closed only when a `spec.md` exists but declares nothing;
  when there is no `spec.md` at all it silently returns just the
  protected-path violations.
- `record_enums()` — checks `docs/issue-<n>/reports/<role>.md`
  frontmatter fields against `roles/<role>.json`'s `record_fields` enum.
  This is the one place gates.py already resolves "which role does this
  changed file belong to" from the **file path itself**
  (`RECORD_PATH = r"^docs/issue-[^/]+/reports/([^/]+)\.md$"`), not from
  branch name — worth reusing the same path-derived-role approach rather
  than inventing a second one.
- `ci.py:check()` — the CI entrypoint that a human-opened or landed PR
  runs through. It does NOT know which role authored the PR: no branch
  name, no role argument. It only takes `repo`, optional `pr`/`issue`/
  `phase`. `pr_reference.py` similarly takes `issue`/`phase` but not role.
- `board-gate.sh` (a Claude Code hook, not a Python gate — surfaced
  directly in this session: "writing docs/issue-139/ requires branch
  issue-139/coding") already derives **role from branch name**
  (`issue-<n>/<role>`) at write time inside a session, but this is a
  local pre-write hook, not a PR-diff gate `gates/ci.py` runs — it never
  fires for a PR opened from an already-pushed branch reviewed after the
  fact, and only exists in the interactive-session harness.

## Gap this issue targets

No gate compares "what a PR actually changed" against "what that PR's
*role* is declared to produce" (`roles/<role>.json`'s `produces` prose).
Nothing stops (A) a judgment role (feasibility/review/qa/verify) writing
`src/`-shaped implementation, or (B) coding writing another role's
`docs/issue-<n>/reports/<other-role>.md` verdict/record. The issue body
names two real incidents of exactly this leak. `writeset`/`is_protected`/
`record_enums` are the three existing mechanisms nearest to this need but
none of them do it: `writeset` is per-task-spec not per-role, and
`is_protected`/`record_enums` are fixed-purpose (infra deny-list; enum
values inside an already-role-scoped record file).

## Write surface for a fix

- `roles/*.json` (9 files) — add a `write_scope` key per role: allow-list
  of path glob patterns.
- `gates/gates.py` — new check function (role resolved from branch name,
  same shape as `board-gate.sh`'s derivation) comparing changed files
  against the role's `write_scope`.
- `gates/ci.py` — wire the new check in, sourcing role from the PR's head
  branch (`gh pr view --json headRefName`, alongside the existing `body`
  fetch in `pr_reference.py`).
- `test_gates.py` — allow/deny/fail-closed cases for the new check.
- No schema/migration concern (`roles/*.json` has no consumer beyond
  `spawn.py`'s print path and now the new gate).

## Cross-repo note (item 4 of the issue: infra-repo write_scope override)

`roles/<role>.json`'s `path` field already points at a *separate* rulebook
repo per role (`$TOKENMAXXXER_RULEBOOKS/<role>-agent-rulebook`) — the
`decides`/`produces`/`write_scope` declared here in on-the-record describe
the role in the abstract, while the board repo a role actually writes into
(this repo, for issue-149) can have any layout (no `src/` exists in
*this* repo at all — coding's `produces` says "src/·test/ 코드" but this
repo's own code lives at root: `spawn.py`, `test_*.py`, `gates/*.py`).
A fixed `write_scope` in on-the-record's `roles/*.json` cannot be literally
correct for every board repo; the issue explicitly asks for a per-repo
override point. Full design of that override lives in the proposal.

## Scout: skipped

Skip condition applied: no product-shaped or exemplar-comparable design
surface. This is an internal CI/gate mechanism for an existing
multi-repo agent-orchestration harness with no external product category
to benchmark against (there is no "best-in-class role-scoped merge gate"
product to scout) — the issue itself fully specifies the two failure
shapes to close and points at the two existing gate mechanisms
(`gates.py`'s protected-path/`writeset` style) as the pattern to extend.
