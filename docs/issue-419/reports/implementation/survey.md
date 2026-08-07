---
kind: survey
date: 2026-08-07
subject: issue-419
role: implementation
---

# Current-state survey — issue-419

## Scope check against #310/#330/#363

- `gates/gates.py:712` (`reach_check`, issue #330) requires a record to name diff-external files
  that reference a path the PR deleted or renamed. It is keyed on **path strings** via
  `git grep -F <old_path>`. None of #419's four measured instances is a deleted/renamed path —
  `orphaned_references` (`gates.py:675`) literally cannot fire on any of them (no `D` status, no
  rename, in any of the four).
- `docs/issue-363/proposals/2026-08-07-generator-analysis-gate.md` (not yet merged — no
  `proposal_generator_section` in `gates/gates.py` today, confirmed by `grep -n
  proposal_generator_section gates/gates.py` returning nothing) requires a proposal to declare
  `generator: fixed|deferred`. That is a claim about causal reach ("did you fix the thing that
  produced this"), not about spatial reach ("where else does this exact shape appear right
  now"). A proposal can honestly write `generator: fixed` for the one call site it touched and
  say nothing about the sibling call site three lines up — #363's gate has nothing to say about
  that, confirmed by reading its `## What will be done` (gates.py, ci.py, test_gates.py,
  generator-guard.sh — none of it scans for repeated shapes).
- There is currently **no mechanical convention** in this repo for declaring two functions or
  call sites as siblings. Checked: `grep -rn "sibling\|짝\|read-only" gates/*.py roles/*.py` finds
  only prose in docstrings (`gates/flows.py:49` "sibling `_issue_list_all()` idiom", `spawn.py`'s
  `core_root()`/`core_version()` docstrings calling each other "짝" / symmetric read-only
  counterpart). Nothing parses these; they are for a human reader only. This confirms the
  issue's own item 2 is still open — no sibling relationship in this codebase is machine-visible
  today.

## The four measured instances, checked against what exists

1. **`gh api` argument-shape divergence (#388).** `gates/ci.py` — checked current call sites
   (`grep -n '"gh", "api"' gates/ci.py`): `ci.py:104` (`gh api repos/.../pulls/.../commits`, no
   `-f`, plain GET) and `ci.py:205` (`gh api -X GET repos/.../contents/...`, explicit `-X GET`
   added per the `#388` comment at `ci.py:190`). The instance itself is already fixed by hand;
   the shape that produced it — same command, divergent flag vectors, no mechanism relating them
   — is still unenforced. A **new** third `gh api` call site with an `-f` and no `-X GET` would
   pass every check in this repo today.
2. **Sibling call site missed (`core_root`/`core_version`, #313).** No mechanical pairing exists
   (see above). The docstrings say "짝"/"symmetric" but nothing reads that word. This is squarely
   the issue's item 2: a sibling relationship would need a machine-visible declaration to be
   checkable at all, and none exists yet in this codebase.
3. **Same rule, three shapes (#312/#317/#284, closes-gate phase defect).** This is not a
   call-site or path pattern — it is the same *requirement* re-derived independently three times
   from different trigger conditions in what appears to be `gates/gates.py`'s closes-gate logic
   and its callers. No existing check groups "logic that implements the same named rule" across
   files; this is the least mechanically tractable of the four (confirmed by re-reading #330's
   own survey, which separately concedes it misses the "optional-requirement case" — the same
   family).
4. **Fix location moved, siblings left (#297→#313).** This is a *migration completeness* problem
   (a writer moved, readers of the old on-disk shape were not updated) — closer to
   `orphaned_references`' shape (moved/changed thing, un-updated consumers) but the "old thing"
   here is a **data format on disk**, not a path string, so `git grep -F <old_path>` does not
   apply. Would need enumerating known writers/readers of a given on-disk marker format, which
   this repo does not currently track anywhere.

## Mechanical feasibility (what's reachable, stated per the issue's own honesty requirement)

- **Reachable now, no new convention:** grouping `subprocess.run` call sites in the diff (and,
  for full coverage, in the touched files) by first-two-argv-elements (e.g. `["gh", "api"]`,
  `["git", "grep"]`) and flagging when their argument *shapes* diverge (presence/absence of
  `-f`/`-X`/other flags) across sites of the same command. This generalizes the exact #388
  pattern. It is a syntactic check over `subprocess.run(...)` call expressions — parseable via
  `ast`, no network, no new dependency.
- **Reachable only with a new, prospective convention:** sibling-function pairing. Nothing in
  this codebase declares siblings machine-readably today. A check can require a structured
  marker (e.g. a `# sibling: <qualified_name>` comment immediately above a `def`) and then, when
  a PR's diff touches a function carrying that marker, require the record to mention the sibling
  by name — same shape as `reach_check`'s "mention it in the record" pattern (`gates.py:712`).
  This **cannot** retroactively find `core_root`/`core_version`-style pairs that predate the
  marker; it only prevents the *next* one from going unmentioned once someone adds the marker.
- **Not reachable by any check proposed here:** instance 3 (rule re-derived in three shapes
  across independently-written logic — no syntactic invariant ties the three together) and
  instance 4 (on-disk format migration completeness — would need a registry of known
  writers/readers per format that does not exist). Both are named explicitly rather than implied
  covered.

## Prior art in this repo for the chosen shape

- `gates/gates.py:712` `reach_check` — "did the record mention the diff-external thing" pattern,
  reused directly for the sibling-marker check.
- `gates/gates.py:738` `duplicate_test_basenames` — whole-tree (not diff-only) structural scan,
  precedent for scanning argument shapes across the whole touched-file set rather than only the
  literal diff hunks.
- `docs/issue-363/proposals/2026-08-07-generator-analysis-gate.md` — precedent for a structured,
  parseable claim line (`generator: fixed|deferred`) over free prose; the same shape fits a
  `siblings: none|<names>` claim line.

## Skip conditions checked

Neither scout-directive skip condition applies (this is not a pure bugfix, and #419 explicitly
leaves open design decisions 1-4 in its own text) — scouting could apply, but #419 is a
repo-internal mechanism-design question with no external product category to benchmark against;
the relevant "field" is this repo's own prior mechanisms (#330, #363, #398), surveyed above, not
an external product sweep. This is recorded per the scout-directive's own scope: it governs
product-shaped and comparable-deliverable work, and this deliverable's comparables are the
repo's own prior gates, which this survey already reads directly.

