---
status: proposed
files:
  - gates/gates.py
  - gates/ci.py
  - test_gates.py
  - docs/specs/platform-capabilities.md
  - docs/issue-376/reports/implementation/survey.md
  - docs/issue-376/proposals/2026-08-07-capability-reachability-gates.md
---

## Request

Issue #376: capability that already works has no way for an actor to be
told it exists, so it gets rebuilt or is wrongly concluded impossible.
Four named 2026-08-07 instances: an unread `decision_queue` field, a
`Stop` hook nobody checked exists on the platform, a dead `writeset()`
gate (`spec.md` never produced), and a `record_enums` gate wired but
unreachable because the only CI workflow always runs `--closes-only`.
Acceptance requires an executable artifact, not prose, and requires
distinguishing what is derivable from the repo from what is not (a
platform capability cannot be indexed from this repo and needs its own
answer path). No human-maintained index is acceptable — that repeats the
defect under a new name.

## Constraints

- Must not be, or read like, a hand-maintained capability list.
- Must be run against the four named instances and report a number, not
  an implication of full coverage.
- Must not overlap or duplicate #330 (reach check) or #333
  (derived-numbers) — both checked in the survey and found unimplemented
  (open issues, no code); nothing to extend.
- `record_fulfils_diff` (`gates.py:411`) is the one existing
  claim-to-mechanism precedent — checked and found too narrow to reuse
  (its ground truth is git-diff file status, not call-graph or
  cross-file reference presence).
- Per #363's generator framing: the fix should target the class of
  defect (a registered gate unreachable from the real CI entry point),
  not just patch `writeset`/`record_enums` by name.

## Rationale

**Chosen approach**: two small, purely-derived gate functions —
(a) a CI-reachability check over `gates.ALL`'s registry against
`gates/ci.py::check()`'s actual call graph, and (b) a
documented-schema-field-has-a-consumer check over `docs/specs/*.md`
tables — plus one explicit, unchecked prose fact for the one instance
(#2, the `Stop` hook) that is a platform property no repo-local check
can confirm.

**Alternative considered and rejected — a maintained capability
registry** (a JSON/YAML file enumerating "capabilities" with
descriptions and consumers, checked for staleness). Rejected because
it is exactly the shape the issue calls out as the same defect wearing
a new file: the registry itself would need someone to notice and add
every new capability, which is the identical failure mode that let
`decision_queue` and `writeset()` go unnoticed in the first place. A
derived check that reads the actual registry (`gates.ALL`) and the
actual schema docs (`docs/specs/*.md`) already in the tree has no
separate list to drift from.

**Alternative considered and rejected — extending `record_fulfils_diff`
to cover "capability consumed" claims**. Rejected because its
mechanism is bound to git commit diff status (create/delete/rename of a
literal path) — there is no diff-derived fact for "is this JSON field
read anywhere" or "is this function called under real CI flags."
Reusing its opt-in per-record marker shape for a structurally different
ground truth would produce a check that looks like it shares
machinery with #155's precedent but actually duplicates none of its
logic — false economy, not reuse.

**Alternative considered and rejected — a general "impact analysis"
gate that answers #330's whole scope** (what does any change reach).
Rejected as over-scope: #330 is broader (any change's blast radius) and
is itself unimplemented and open; building it here to solve #376 would
silently absorb #330's issue instead of coordinating with it, which the
issue's own boundary section warns against.

## What will be done

1. `gates/gates.py`: add `ci_reachable_gates(d, cfg)` — parses
   `gates/ci.py`'s source for calls to `gates.<name>(` and reports, for
   every `name` in `gates.ALL`, whether it is (a) called at all, and (b)
   called before the `if closes_only: return bad` line (i.e., reachable
   when `closes_only=True`, the only mode the real workflow ever
   passes). A gate registered but failing either check is a finding.
2. `gates/gates.py`: add `schema_field_orphans(d, cfg)` — for each
   `docs/specs/*.md` file, extracts field names from its schema tables
   (rows shaped `| \`name\` | type | notes |` under a `### N.N` schema
   heading), then greps the rest of the tree (excluding the spec file
   itself, its declared implementation module if named in the doc, and
   test files) for each name. A field with zero hits outside its own
   producer/tests/spec is a finding.
3. `gates/ci.py`: wire `ci_reachable_gates` into `check()` **before**
   the `if closes_only: return bad` line — the defect it exists to catch
   is exactly "gate present but not reachable under `--closes-only`," so
   it must itself run under `--closes-only` or it reproduces the same
   defect it checks for. `schema_field_orphans` is repo-wide (not
   diff-scoped) and independent of PR content, so it is wired the same
   way — unconditional, not gated behind `closes_only`.
4. `test_gates.py`: unit tests for both, including a regression fixture
   that reproduces the `writeset` (never called) and `record_enums`
   (called but past the `closes_only` guard) shapes and asserts both are
   flagged; and a fixture reproducing `decision_queue` (documented field,
   zero outside references) for the orphan check.
5. `docs/specs/platform-capabilities.md` (new, short): one stated fact —
   Claude Code's hook system supports more event types than
   `on-the-record/hooks/hooks.json` currently configures (naming the
   currently-configured three and pointing to where the full event list
   is authoritative); a survey concluding "no hook can observe X" must
   check this file's pointer, not just the repo's configured
   `hooks.json`, before writing that conclusion down. Explicitly labeled
   in the doc as unchecked/unmechanizable — a platform fact, not a
   repo-derived claim.
6. Run both new gates against the four named instances and record the
   count in this PR's report: `ci_reachable_gates` is expected to catch
   #3 (`writeset`, never called) and #4 (`record_enums`, called past the
   guard) — 2 of 4. `schema_field_orphans` is expected to catch #1
   (`decision_queue`) — 1 of 4, additive. #2 (`Stop` hook) is covered
   only by the prose pointer in step 5, not by either gate — stated as
   such, not implied as covered. Combined: 3 of 4 instances get a
   mechanical answer; 1 of 4 gets an explicit "this is not derivable
   from the repo, here is where to look instead."

## Out of scope

- Fixing `roles/implementation.json`'s `loop_state` enum drift itself
  (that is #147's scope per #377's boundary section: "#147 ... should
  stay scoped to that vocabulary").
- Producing `spec.md` files or otherwise making `writeset()`'s
  enforcement branch active — this proposal makes its dead-ness
  detectable, not live.
- Building #330's general reach-check or #333's derived-numbers
  mechanism — both remain open, separate issues.
- A UI, CLI subcommand, or query interface for "what capabilities
  exist" — the two gates are CI-time checks (fail when the defect
  exists), not an interactive discovery tool. The issue's acceptance
  criterion is an executable artifact that fails on regression, not a
  search interface.

## How you'll know it worked

- `python3 -m pytest -q test_gates.py -k "ci_reachable or schema_field_orphans"`
  passes, including the regression fixtures for the `writeset`/
  `record_enums`/`decision_queue` shapes.
- Running `gates.ci_reachable_gates` and `gates.schema_field_orphans`
  against the current tree (before any other fix lands) reproduces
  findings for `writeset`, `record_enums`, and `decision_queue` — 3 of
  the 4 named instances, reported as a number in the phase-2 record, not
  implied as complete coverage of all four.
- `docs/specs/platform-capabilities.md` exists and is referenced by name
  in this proposal for instance #2, with no gate claiming to check it.
