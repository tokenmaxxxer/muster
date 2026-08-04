---
role: implementation
subject: issue-262
loop_state: survey
---

# Current-state survey — `_always_writable()` proposal-file pattern (issue #262)

## Scout skip record

Skipped. This is a pure bugfix: an internal CI gate script's hardcoded
filename glob does not match this repo's actual proposal-naming practice,
discovered by a real dry-run failure (issue #245, PR #257). There is no
product-shaped surface here — no user-facing flow, no external category
with a "best-in-class" to compare against — only an internal fnmatch
pattern to correct against this repo's own file history. Where a genuine
design choice exists (which replacement glob, whether to bind it to the
branch's issue number), it is resolved below by reading this repo's own
`gates/gates.py`/`test_gates.py` conventions and actual `docs/issue-*/`
history, not by scouting an external field.

## What exists today

- **The bug, exact location**: `gates/gates.py:472-475`, `_always_writable(role)`:
  ```python
  def _always_writable(role: str) -> list[str]:
      return [f"docs/issue-*/reports/{role}.md",
              f"docs/issue-*/reports/{role}/**",
              f"docs/issue-*/proposals/{role}.md"]
  ```
  The third entry hardcodes the phase-1 proposal file as exactly
  `<role>.md`. It has exactly one caller: `role_scope()` at
  `gates/gates.py:518` (`allowed = allowed + _always_writable(role)`),
  which is itself called only from `gates/ci.py:172`
  (`bad += gates.role_scope(repo, branch)`) inside `ci.check()`, gated
  behind `if pr is not None` and skipped entirely whenever
  `closes_only=True` (`gates/ci.py:165-166`). No other function in the
  repo reads or calls `_always_writable`.
- **Actual proposal-file naming practice, surveyed directly**
  (`find docs -path "*/proposals/*" -name "*.md"`, 90 files across
  `docs/issue-*/proposals/` and the two root-level `docs/proposals/`):
  three shapes coexist, and none of them is guaranteed to be `<role>.md`:
  - `<role>.md` — the majority of older entries, e.g.
    `docs/issue-100/proposals/coding.md`,
    `docs/issue-227/proposals/implementation.md`,
    `docs/issue-236/proposals/implementation.md`,
    `docs/issue-258/proposals/implementation.md`.
  - `<date>-<slug>.md` (no role name in the filename at all) — the
    convention `proposal-shape-directive` and recent practice actually
    use, e.g. `docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`
    (this issue's own trigger case), `docs/issue-145/proposals/2026-07-31-coding-superpowers-cleanup-and-record-fix.md`,
    `docs/issue-155/proposals/2026-07-31-coding-fulfils-marker-gate.md`,
    `docs/issue-73/proposals/2026-07-29-coding-v3-doc-sync.md`.
  - Free-form slug, no date, no role token — e.g.
    `docs/issue-132/proposals/session-end-trichotomy.md`,
    `docs/issue-160/proposals/role-taxonomy.md`,
    `docs/issue-172/proposals/flows-json.md`,
    `docs/issue-68/proposals/board-proposal.md`.
  - Multiple *different* roles can each have their own proposal file
    inside the **same** issue tree, e.g. `docs/issue-31/proposals/`
    holds `coding.md`, `qa.md`, and `verify.md` side by side — this
    matters for the side-effect check below.
- **The bug is real and reproduced.** Built a throwaway pytest case
  (`role_scope()` called directly, no repo mutation — deleted after
  running, not part of this write set) against a synthetic repo with a
  `implementation` role whose `write_scope` is `["src/**", "test/**"]`,
  committing a date-slug file at
  `docs/issue-262/proposals/2026-08-04-always-writable-fix.md` on branch
  `issue-262/implementation`. Current (unpatched) `_always_writable`:
  `role_scope()` returns
  `["write_scope 이탈: docs/issue-262/proposals/2026-08-04-always-writable-fix.md
  (역할 implementation, 허용: src/**, test/**, docs/issue-*/reports/implementation.md,
  docs/issue-*/reports/implementation/**, docs/issue-*/proposals/implementation.md)"]`
  — blocked (red), matching the issue's cited PR #257 failure exactly.
- **This bug is currently masked, not fixed, in production.** Issue #245
  discovered this same defect via the same dry-run and, rather than fix
  `gates/gates.py` (outside its own approved write set), scoped the
  `.github/` required check to `gates/ci.py --closes-only`
  (`docs/issue-245/reports/implementation.md` "Rationale for deviations"
  item 1, "Open findings" item 1). `--closes-only` skips `role_scope`
  entirely (`gates/ci.py:165-166`), so today's required CI check never
  invokes `_always_writable` at all — the bug sits latent, blocking only
  if/when someone re-widens the required check to the full `ci.check()`
  bundle (which requirement 3 below asks this issue to re-evaluate,
  separately from actually flipping it).
- **`fnmatch` semantics confirmed**: this repo's gate matching uses
  Python's stdlib `fnmatch.fnmatch()` throughout (`gates/gates.py:67`,
  `:190`, `:524`), not a path-aware glob library. `fnmatch.translate()`
  turns `*` into a regex `.*`, which matches `/` exactly the same as
  `**` does — there is no functional difference between `foo/*` and
  `foo/**` in this codebase's matching (verified directly: both match a
  flat file and a file nested inside a subdirectory identically). The
  existing sibling line, `f"docs/issue-*/reports/{role}/**"`
  (`gates/gates.py:474`), already uses `**` purely as a stylistic
  "any depth" signal, not because `fnmatch` needs it. A replacement
  pattern for the proposals entry should follow that same existing
  stylistic convention for consistency, even though a single `*` would
  match identically.
- **Side effect of a blanket `docs/issue-*/proposals/**` widening,
  checked directly (issue's requirement 1 explicitly asks this to be
  reviewed):**
  - *Other issue trees*: **not a new opening.** `_always_writable`'s
    issue segment is already `docs/issue-*` (unbound to any specific
    issue number) in the *current, unpatched* code — `role_scope()`
    never threads the branch's own issue number into
    `_always_writable()` at all (`BRANCH_ROLE = re.compile(r"^issue-[^/]+/([^/]+)$")`
    at `gates/gates.py:465` captures only the role group; the issue
    segment `[^/]+` is matched but discarded). A `coding` branch can
    already touch `docs/issue-9999/proposals/coding.md` today, for any
    9999, regardless of which issue it's actually working. Loosening the
    filename segment from `{role}.md` to `**` does not touch this
    already-unbound issue segment — it stays exactly as broad (or
    narrow) as it already was.
  - *Same issue tree, different role's proposal file*: **this is a new
    opening**, confirmed by reproduction. Today, an `implementation`
    branch can only ever match `docs/issue-<n>/proposals/implementation.md`
    — it cannot touch `docs/issue-31/proposals/qa.md`. A file-glob widened
    to `docs/issue-*/proposals/**` drops the role-name filter entirely,
    so an `implementation` branch's `role_scope()` would no longer flag
    writing to `docs/issue-31/proposals/qa.md` as a `write_scope` breach
    (confirmed: `role_scope()` returns `[]`, not a violation, under the
    widened pattern in the same synthetic-repo harness). This is a real,
    if narrow, trade-off: it matters only for the specific case of one
    role's branch committing into a path shaped like another role's
    proposal file inside a shared issue tree — see Rationale in the
    proposal for why it's accepted rather than engineered around.
- **No test currently exercises `_always_writable`'s proposal-file
  pattern.** `test_gates.py`'s `role_scope` tests
  (`test_gates.py:824-919`) cover in-scope writes, judgment-role
  src-blocking, cross-role record-blocking, non-role-shaped branches,
  write_scope.md overrides, and undeclared write_scope — none commits a
  file under `docs/issue-*/proposals/` at all, so the reported defect has
  zero regression coverage today.

## Write set (confirmed)

- `gates/gates.py` — `_always_writable()`, one entry
  (the proposal-file glob), matching the survey finding above.
- `test_gates.py` — new regression test(s): the currently-red
  date-slug-proposal case (must go red against the pre-fix pattern,
  green after), per issue requirement 2.

No other file is implicated. `gates/ci.py`'s `--closes-only` branching,
`.github/workflows/`, and `pr_reference.py`'s judgment logic are read
(above) for context but not written — matching the issue's own
Constraints.

## Alternatives visible from this survey (for the proposal's Rationale)

- **A: widen the proposal-file entry to `docs/issue-*/proposals/**`**
  (drop the `{role}.md` filename constraint entirely, keep the existing
  unbound issue segment) — vs. **B: also bind the issue segment to the
  branch's own issue number** (extend `BRANCH_ROLE` to capture the issue
  number, thread it through `_always_writable(issue, role)`) — B would
  require changing `_always_writable`'s signature and its one call site,
  a materially larger diff than the one-line fix the reported defect
  needs, and it does not even close the one side effect this survey
  found to be real (same-issue-tree, cross-role proposal-file writes) —
  issue-31's `coding.md`/`qa.md`/`verify.md` triple shows that pattern is
  itself legitimate existing practice, not something an issue-scoped
  glob would or should prevent.
- **A vs. C: require the role name to appear somewhere in the filename**
  (e.g. `docs/issue-*/proposals/*{role}*`) — rejected by the survey's own
  naming-practice data: `session-end-trichotomy.md`, `role-taxonomy.md`,
  `flows-json.md`, and the issue's own trigger file
  `2026-08-03-plan-aware-closes-gate-wiring.md` (role `coding`) carry no
  role token at all. A role-token-constrained pattern would still block
  the exact class of file this issue reports as broken.
- **A vs. D: leave `_always_writable` unfixed, keep the required CI check
  permanently on `--closes-only`** — this is issue #245's current
  landed state; rejected because issue #262 requirement 3 explicitly asks
  for a fresh re-evaluation of widening the required check now that the
  defect can be fixed, not a decision to leave it masked indefinitely.
