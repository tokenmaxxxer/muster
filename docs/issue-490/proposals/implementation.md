---
subject: issue-490
files:
  - gates/claim_scan.py
  - gates/test_claim_scan.py
  - docs/issue-490/reports/implementation/survey.md
  - docs/issue-490/reports/implementation.md
---

Skip condition applies (pure bugfix): see `docs/issue-490/reports/
implementation/survey.md`'s "Scout skip record" — two exact,
already-diagnosed defects with a pre-registered fix direction, no
category/exemplar research applicable.

## Request

Close two defects in `gates/claim_scan.py` found by the #476 sandbox
pilot, per the pre-registered pivot rule (issue #476's decision rule:
survival > 10% -> widen the trigger; the guardrail `false_reject_rate`
<=5% may not be traded away):
1. **case0**: a fabricated claim citing any real-but-unrelated tracked
   file passes `claim_scan` with 0 findings (whole-repo `git ls-files`
   target sourcing, not diff-scoped).
2. **honest2**: an honest, genuinely-passing repro cited in
   `module.function` dotted form is wrongly rejected because
   `_repo_targets()` only ever yields file-path strings.
Both fixes must keep fab1-3 (caught) and null1-3 (unpunished) passing.

## Constraints

- Fixes confined to `gates/claim_scan.py`'s target-sourcing/matching
  logic — the pilot record states plainly both defects live there, not
  in `gates/reexecution_gate.py`.
- No new dependency, env var, or migration.
- `main()`'s existing no-`--repo`/no-base call shape (used by callers
  that pass an explicit `repo_targets` to `scan_text()` directly, and by
  the existing test suite) must keep working — diff-scoping is additive
  (an opt-in `--base`), not a removal of the whole-repo fallback.
- Test additions land in `gates/test_claim_scan.py` (the file that
  actually imports and exercises `claim_scan`'s internals), not
  `gates/test_reexecution_gate.py` as the issue body names literally —
  see Rationale.

## Rationale

**Where the case0/honest2 tests live.** The issue body says "the
pilot's sandbox corpus becomes a permanent test — `gates/
test_reexecution_gate.py` gains the case0 red-green pair" (and again for
honest2). Considered following that literally. Rejected: the pilot
record this issue itself cites (`docs/issue-476/reports/
execution-observation.md`, "step — which specific artifact, if any, is
deficient") states "Both are in `gates/claim_scan.py`, not `gates/
reexecution_gate.py` — the re-execution stage itself performed correctly
on every case that reached it." `gates/test_reexecution_gate.py`'s
existing suite only drives `run_reexecution`/`write_verdict`/
`read_verdict` against a throwaway git repo+SHA; it never imports
`claim_scan` or calls `scan_text()`, so a case0/honest2 pair placed
there would exercise the wrong module and could not red/green on the
actual fix. `gates/test_claim_scan.py` already imports `claim_scan` and
already has the case0-shaped and honest2-shaped test seeds
(`t_target_not_in_repo_is_a_finding_when_repo_targets_given`,
`t_target_in_repo_clears_when_repo_targets_given`) to extend. Routing
the new pairs there is a same-scope test-placement correction, not a
scope change: still `gates/test_*`, still the pilot's exact two shapes,
still red-before/green-after.

**How case0 is fixed.** Considered dropping `git ls-files` from
`_repo_targets()` entirely and always diffing. Rejected (see survey.md
alternative 1): `main()` is also used as a plain text-linter with no
determinable base (no `--repo`, or a repo with no upstream to diff
against), and removing the whole-repo fallback would turn every such
call into a 0-target set — every honest claim citing a real file would
then also false-reject, trading case0's fix for a worse honest2-shaped
regression everywhere `--base` isn't supplied. Chosen instead: add an
opt-in `--base <ref>` CLI flag (and a `base` parameter on
`_repo_targets()`); when given, `repo_targets` is diff-scoped
(`git diff --name-only <base>...HEAD`, changed files only) instead of
whole-repo `git ls-files`. This is "widen the trigger condition" per
the pre-registered rule: the traceability check now requires a
*diff-relevant* citation, not merely *any real file*, whenever a base is
known — which is the shape the sandbox test exercises (case0's cited
file is real but not part of the diff under test).

**How honest2 is fixed.** Considered AST/text symbol resolution
(survey.md alternative 2, rejected for parsing cost and its own
false-negative surface). Chosen: when a cited target doesn't literally
match `repo_targets`, also try resolving a dotted `module.function` (or
`module.Class.method`) form back to its containing file
(`module` segment + `.py`) and check that derived name against
`repo_targets`. This closes exactly the file-path-vs-dotted-form
mismatch the pilot found, without asserting the function itself exists.

## What will be done

1. `gates/claim_scan.py`:
   - `_repo_targets(repo, base=None)`: when `base` is given, source
     targets from `git diff --name-only <base>...HEAD` (falling back to
     the existing whole-repo `git ls-files` behavior if the diff command
     itself errors, e.g. unknown ref — fail toward the current
     behavior, never toward zero targets/spurious false-rejects).
   - Add a target-resolution helper used wherever cited targets are
     checked against `repo_targets`: for each cited string not found
     verbatim, also try `"<module>.py"` derived from a leading
     `module.rest` dotted segment, and accept if that derived path is in
     `repo_targets`.
   - `main()`: accept `--base <ref>` and thread it into `_repo_targets()`.
2. `gates/test_claim_scan.py`: add a case0-shaped red-then-green pair
   (citing a real-but-out-of-diff file must fail when `--base`/diff
   scoping is active) and a honest2-shaped pair (dotted-function citation
   of a genuinely-tracked module must clear with 0 findings). Confirm
   existing tests (including the fab/null-shaped ones already present)
   stay green by running the file.
3. `docs/issue-490/reports/implementation.md`: phase-2 record per
   contract v3 s19/record-shape-directive.

## Out of scope

- `gates/reexecution_gate.py` and its test file — untouched, per the
  pilot's own root-cause attribution.
- Resolving the "cosmetic" double-count on the literal word `Repro` in
  the `Repro:` marker line itself (pilot: "does not change the
  pass/fail outcome") — not named in the issue's Acceptance criteria.
- Wiring `claim_scan.py --base` into any CI caller (`gates/ci.py`,
  `gates/landing_readiness.py`, etc.) — no such caller exists yet
  (survey: no file calls into `claim_scan`'s internals besides its own
  test file); adding one is a separate decision outside this issue's
  two named defects.
- The 30-record `fabrication_survival_rate` production window — issue
  states explicitly this pivot does not reset it; nothing here touches
  window-counting logic.
- Filing any follow-up issue — this role does not file issues.

## How you'll know it worked

- `python3 gates/test_claim_scan.py` — all tests pass, including the two
  new case0/honest2 pairs and every pre-existing case (fab/null-shaped
  coverage stays green).
- Manual/documented trace in the phase-2 record: case0's exact pilot
  shape (`Repro: python3 gates/claim_scan.py --help`, cited file real
  but out-of-diff) produces >=1 finding when diff-scoped; honest2's
  exact pilot shape (`Repro: python3 -c "import mod; assert mod.f() ==
  1"`) produces 0 findings.
