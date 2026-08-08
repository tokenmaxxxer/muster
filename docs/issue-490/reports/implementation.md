---
subject: issue-490
code_under_review:
  - gates/claim_scan.py
  - gates/test_claim_scan.py
loop_state: landed
---

## What was done

Implemented both fixes from `docs/issue-490/proposals/implementation.md`
in `gates/claim_scan.py`:

1. **case0** — `_repo_targets(repo, base=None)` gained an opt-in `base`
   parameter. When `base` is given, targets are sourced from
   `git diff --name-only <base>...HEAD` (diff-scoped) instead of
   whole-repo `git ls-files`. `main()` gained a `--base <ref>` flag that
   threads into it. No `--base` -> unchanged whole-repo behavior
   (constraint preserved).
2. **Base-resolution hard-fail** — when `--base` is supplied but the diff
   command itself fails (bad ref, shallow clone), `_repo_targets` raises
   `BaseResolutionError` instead of falling back to whole-repo
   `git ls-files`; `main()` catches it, prints the git error, and exits
   2. This design was already folded into the proposal's Rationale by
   the after-proposal hunt before this phase-2 build started — this
   record implements the already-revised design, it does not change it.
3. **honest2** — added `_dotted_to_file()` (resolves a leading
   `module` segment of a dotted `module.function`/`module.Class.method`
   citation back to `module.py`) and `_cite_matches()` (verbatim match
   first, then the dotted-derived path, including a `.../module.py`
   suffix match for nested modules). `scan_text()` now calls
   `_cite_matches()` instead of a bare set-intersection.

`gates/test_claim_scan.py`: added
`t_case0_real_but_out_of_diff_target_is_a_finding_when_base_scoped`,
`t_honest2_dotted_function_citation_clears_when_module_in_repo`,
`t_base_resolution_failure_hard_fails_instead_of_falling_back`,
`t_main_hard_fails_on_broken_base_instead_of_scanning_whole_repo`,
`t_dotted_citation_does_not_match_unrelated_same_basename_file` (added
after the before-landing hunt, see "What did not work"). All 14 tests
(9 pre-existing + 5 new) pass:

```
Repro: python3 gates/test_claim_scan.py
14 passed
```

Manual trace of the pilot's exact shapes (proposal's "How you'll know it
worked"):
- case0 shape (`Repro: python3 gates/claim_scan.py --help`, cited file
  real but out-of-diff): `t_case0_...` scans this exact text with
  `repo_targets={"gates/reexecution_gate.py"}` (simulating a diff that
  doesn't include `claim_scan.py` itself) — produces 1 finding,
  reason "근거가 지목하는 대상이 diff/repo 에 없다". Confirmed by the
  green test run above.
- honest2 shape (`Repro: python3 -c "import mod; assert mod.f() ==
  1"`-equivalent, dotted-form citation of a genuinely-tracked module):
  `t_honest2_...` scans a dotted `claim_scan.scan_text(...)` citation
  against `repo_targets={"gates/claim_scan.py"}` — produces 0 findings.
  Confirmed by the green test run above.

Fab1-3/null1-3-shaped coverage (`t_bare_claim_...`,
`t_claim_with_repro_marker_...`, `t_claim_with_fenced_block_...`,
`t_evidence_outside_adjacency_window_...`, `t_no_claim_language_...`,
`t_target_not_in_repo_...`, `t_target_in_repo_clears_...`,
`t_main_exits_nonzero_...`, `t_main_exits_zero_...`) all stay green —
no pre-existing test was modified.

## Why

Basis: `docs/issue-490/proposals/implementation.md` (approved via
`APPROVE issue-490/implementation` on issue #490, 2026-08-08). This
build follows that proposal's "What will be done" verbatim; the
base-resolution hard-fail design was already folded into the proposal
text before this phase-2 build started, per the after-proposal hunt.

## What did not work

- Before-landing warrant hunt (stance 0, `docs/reports/
  2026-08-08-hunt-implementation.md`) found the honest2 fix's basename
  suffix fallback (`any(rt.endswith("/" + derived) ...)`) over-matched:
  a dotted citation of an untouched module cleared just because an
  unrelated diff file shared the same basename in a different
  directory. Expected: the fallback only closes genuinely-nested
  same-file matches. Actual: it also matched unrelated same-named
  files, reopening case0 for dotted citations under `--base`. Fixed by
  requiring the basename-suffix candidate set to be exactly one file
  (`gates/claim_scan.py`'s `_cite_matches`); added
  `t_dotted_citation_does_not_match_unrelated_same_basename_file` as a
  red/green regression.

## closed_checks

- case0 pilot-shape red/green pair: `t_case0_real_but_out_of_diff_target_is_a_finding_when_base_scoped` — code_sha 452afe12271f3dc0865a57d3a6517b5e796a4f6f
- honest2 pilot-shape red/green pair: `t_honest2_dotted_function_citation_clears_when_module_in_repo` — code_sha 452afe12271f3dc0865a57d3a6517b5e796a4f6f
- broken-`--base` hard-fail (unit + CLI): `t_base_resolution_failure_hard_fails_instead_of_falling_back`, `t_main_hard_fails_on_broken_base_instead_of_scanning_whole_repo` — code_sha 452afe12271f3dc0865a57d3a6517b5e796a4f6f
- fab/null-shaped pre-existing coverage stays green (no test modified): full suite run, 14 passed — code_sha 452afe12271f3dc0865a57d3a6517b5e796a4f6f
- before-landing hunt (stance 0) bypass via unrelated same-basename file: `t_dotted_citation_does_not_match_unrelated_same_basename_file` — code_sha 452afe12271f3dc0865a57d3a6517b5e796a4f6f

## Doc placement ladder

- No new env var, config key, dependency, or migration introduced —
  nothing to add to a handbook.
- No library-or-format choice over a named alternative beyond what the
  proposal's own Rationale already recorded (base-resolution hard-fail,
  dotted-form resolution approach) — both already live in
  `docs/issue-490/proposals/implementation.md`'s `## Rationale`; no
  separate `docs/issue-490/decisions/` entry needed.
- No benchmark/investigation numbers produced this phase — the
  fabrication_survival_rate/false_reject_rate metrics referenced by the
  issue are the pre-existing 30-record production window, explicitly
  out of scope (proposal's "Out of scope").

## Open findings

None outstanding. The after-proposal hunt's finding (silent `--base`
fallback reopening case0) was resolved before this phase-2 build began
— the proposal text already reflects the fix, and this implementation
follows that revised text.
