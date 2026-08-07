---
kind: proposal
date: 2026-08-07
subject: issue-419
role: implementation
---

files: gates/gates.py, gates/ci.py, gates/test_gates.py

## Request

A fix that lands for the reported instance and never asks where else the same shape occurs
(#419). Four measured instances from this repo's own history in one day: a `gh api` argument-
vector divergence (#388, already fixed by hand), an unwired sibling function (`core_root`/
`core_version`, #313), the same rule re-derived in three trigger shapes (#312/#317/#284), and a
migrated on-disk format whose old readers were left in place (#297→#313). #419 asks (1) whether
delivery must state where else the pattern occurs and what makes that falsifiable, (2) which
sibling relationships are mechanically derivable here, (3) whether this extends #363's
generator-analysis mechanism or stands beside it, (4) whether the honest ceiling is a prompt or a
check. It also requires stating, as a count against the four named instances, how many this
mechanism would have caught — not implying full coverage.

## Constraints

- No new dependency, no new env var, no schema/migration.
- `gates/gates.py` and `gates/ci.py` are under `PROTECTED_ROOT_DIRS` (`gates.py:26`) — this PR's
  diff routes to mandatory human review regardless of this check's own content. Expected.
- Per #310: acceptance is an executable artifact that runs, not a heading. Per #390: this is
  checked against `python3 -m pytest -q --ignore=gates` (main's `gates/` subtree cannot collect
  standalone per #398 — module-name collision between `gates/test_gates.py` and the root
  `test_gates.py`) plus `python3 -m pytest gates/test_gates.py -q` run directly inside `gates/`.
- Must not change the return shape or call signature of any existing function in
  `gates/gates.py`'s `ALL` registry — only add new entries, following #363's own stated
  constraint on the same file.
- Two independent checks, not one broad claim: a **syntactic** check reachable without any new
  convention (argument-shape divergence across same-command call sites) and a **prospective**
  check that requires a new, explicit marker (sibling declaration) — because the survey found no
  machine-readable sibling relationship exists in this codebase today, and a check cannot verify
  an assertion (`## Reach`-style mention) about a relationship that is declared nowhere.

## Rationale

**Considered: extending #363's `## Generator` section with a required `## Recurrence` sub-claim
("this same shape also occurs at: ...") — rejected as the sole mechanism.** #363's gate checks
*presence and shape* of a claim, never its *truth* — that is named explicitly as its own ceiling.
A `## Recurrence` prose line has the identical failure mode #363's own issue text warns against:
a required heading whose content is never read is a symptom fix for the symptom-fix problem.
Unlike #363's `generator: fixed|deferred` (which at least forces a binary, falsifiable-in-shape
claim), "where else does this occur" has no shape that stays falsifiable without a check *behind*
it deriving candidates independently. So it is not adopted as a bare heading; instead, two of the
mechanically derivable candidate classes get real checks that compute candidates themselves
(argument-shape divergence: computed via `ast`; sibling mention: computed via a new declared
marker, checked the same way `reach_check` already checks path mentions), and only the *residual*
prose claim (siblings marked `none`) still relies on self-report — smaller and named as such,
not the whole mechanism.

**Considered: standing beside #363 as an entirely separate proposal vs. living inside it —
decided beside, not inside.** #363's write set (`gates.py`, `ci.py`, `test_gates.py`,
`generator-guard.sh`) is about *causal* self-report (did you fix the generator). This proposal is
about *spatial* self-report (does the same shape recur) and needs its own detector logic
(`ast`-based call-site grouping) that #363's mechanism has no reason to carry. Bundling the two
would make #363's `## Generator` section also respond to argument-shape scanning it was never
scoped for — a second, unrelated requirement crammed under one heading is exactly what #363's own
proposal explicitly avoided doing to `proposal-shape-gate.sh`'s seven sections. Argued per the
issue's own instruction not to default silently.

**Considered: a single "structural similarity" detector using AST diffing / normalized-source
hashing across the whole repo to catch all four instance shapes generically — rejected.** The
issue states plainly that a general "structurally identical but not textually identical" checker
is not decidable and a proposal claiming to solve it in general is dishonest. A generic AST-
similarity pass over every function would also produce a flood of unrelated false positives (any
two `for`-loops over a list look "structurally similar"), which would train reviewers to ignore
the check — worse than not having it. Rejected in favor of two narrow, named patterns actually
observed in this repo's own history.

**Considered: covering instance 3 (rule re-derived in three trigger shapes) and instance 4
(migrated format, stale readers) in this same PR — rejected, named as out of scope below rather
than silently dropped.** The survey found no syntactic invariant linking three independently-
written implementations of "the same rule," and no existing registry of on-disk-format
writers/readers to check completeness against. Building either would mean inventing a taxonomy
this repo does not yet have any instance-based evidence for beyond the single case each — the
issue's own warning against claiming general coverage applies here directly.

## What will be done

1. **`gates/gates.py`** — add `subprocess_call_shape_divergence(work: Path) -> list[str]`:
   - Walk `_committed_changes` / touched Python files (reuse `changed_files()`), parse each with
     `ast.parse`, and collect every `subprocess.run`/`subprocess.check_output`/`subprocess.Popen`
     call whose first positional argument is a list literal of string constants (skip anything
     dynamically built — fail-closed by *not claiming coverage*, not by blocking; this check
     only ever flags what it can statically read).
   - Group calls **across the whole tracked-file tree, not per-file and not diff-only** (an
     after-proposal warrant hunt on this proposal, stance: bypass-the-gate, reproduced that the
     real #388 shape is spread across `gates/closure_sweep.py`, `spawn.py`, and `gates/ci.py`,
     not co-located in one file — a per-file or diff-only grouping would never have caught the
     instance the check is modeled on; whole-tree scanning follows `duplicate_test_basenames`'s
     own precedent, `gates.py:738`, for this reason) by their first two argv elements (e.g.
     `("gh", "api")`, `("git", "grep")`). Within a group of 2+ anywhere in the tree, compute each
     call's flag set (elements
     starting with `-`, positionally-normalized: presence of `-X`, `-f`, etc.) and flag when the
     flag sets diverge in a way that changes the operation's *semantics* for a fixed, small,
     named list of known-dangerous flags (`-X`/`--method`, `-f`/`--field` for `gh api`, mirroring
     the exact #388 shape) rather than any divergence at all — this keeps the check narrow to the
     observed pattern, not "any two calls differ."
   - Register as `"subprocess_call_shape_divergence"` in `ALL`.
2. **`gates/gates.py`** — add a sibling-marker convention and its check,
   `sibling_mention_check(work: Path, record_text: str) -> list[str]`:
   - New marker syntax: a comment line `# sibling: <dotted.name>` immediately preceding a `def`
     (or `class`) in a touched Python file. When the diff touches a function/method carrying this
     marker, the changed record (`docs/issue-<n>/reports/<role>.md`) must mention the sibling's
     name in a `## Siblings` section — same "mention it, don't parse a sentence" matching style
     as `reach_check` (`gates.py:735`, substring match against the section body).
   - No marker present anywhere in the touched file → nothing to check, returns `[]` (this is the
     named prospective limit: it cannot retroactively find `core_root`/`core_version`).
   - Register as `"sibling_mention_check"` in `ALL`.
3. **`gates/ci.py`** — wire both into the same non-`--closes-only` chain that runs
   `record_enums`/`reach_check`/etc. (`ci.py:275-278`), passing the changed record's text to
   `sibling_mention_check` the same way `reach_check` already receives `record_text`.
4. **`gates/test_gates.py`** — unit tests: for `subprocess_call_shape_divergence`, a fixture repo
   reproducing the exact #388 shape (two `gh api` calls, one with `-f`+no `-X`, one with `-X
   GET`) must flag, and a fixture with two calls sharing identical flag sets must not. For
   `sibling_mention_check`: a marked pair with the sibling mentioned in `## Siblings` passes; the
   same pair with no mention fails; a file with no marker at all returns `[]` regardless of
   record content.
5. Apply `# sibling: core_version` / `# sibling: core_root` markers to the actual pair in
   `spawn.py` as the first real instance of the new convention, demonstrating it against the one
   pair the issue names by name — not a synthetic fixture only.

## Out of scope

- Instance 3 (same rule in three trigger shapes) and instance 4 (migrated on-disk format, stale
  readers) — no mechanical detector proposed; named here per the issue's own honesty requirement
  rather than implied covered by the two checks above.
- Retroactively marking every sibling pair in the codebase beyond `core_root`/`core_version` —
  the convention is prospective; a repo-wide sibling-pairing audit is a separate, larger proposal
  this one does not bundle in.
- Verifying that a `## Siblings` mention is *substantively correct* (i.e., that the author
  actually updated the sibling correctly, not just typed its name) — mirrors `reach_check`'s own
  admitted ceiling (mention, not correctness).
- Extending the argument-shape check beyond `subprocess` call sites to, e.g., HTTP client calls
  or SQL query builders — no second instance of that shape exists yet in this repo's own history
  to justify generalizing past the observed #388 pattern.
- Any change to `proposal-shape-gate.sh` or the seven-section directive — out of this role's
  write access (same constraint #363's proposal already recorded).

## How you'll know it worked

- `python3 -m pytest gates/test_gates.py -k "subprocess_call_shape_divergence or sibling_mention" -v`
  passes, run once, output shown in the phase-2 record (per #416: a behavior claim comes from
  running it, not reading it).
- Run `python3 -m pytest -q --ignore=gates` from the repo root once, and separately
  `python3 -m pytest gates/test_gates.py -q` from inside `gates/` (per #398, main's `gates/`
  subtree cannot collect standalone alongside the root `test_gates.py` — both outputs recorded,
  not just the one that happens to pass).
- Re-run `subprocess_call_shape_divergence` against a synthetic fixture reproducing the exact
  #388 diff (pre-fix state: `-f` with no `-X GET` beside a plain `gh api` call) and confirm it
  flags — this is the initial/broken state, not only the already-fixed current state, per #416's
  requirement that an acceptance corpus exercise more than the fixed end-state.
- The phase-2 record states, as a count against the four named instances: this mechanism would
  have caught instance 1 (#388's argument-shape divergence, reproduced above) and would catch
  instance 2 (#313's sibling miss) **only after** the `# sibling:` marker is applied — demonstrated
  here on the one real pair named by the issue, not a synthetic-only fixture. Instances 3 and 4
  are not caught and are named as such — 1 of 4 caught outright, 1 of 4 caught prospectively once
  marked, 2 of 4 explicitly out of reach.
