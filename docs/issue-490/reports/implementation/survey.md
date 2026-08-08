---
subject: issue-490
---

## Scout skip record

Skip condition applies: **pure bugfix**. Issue #490 names two exact,
already-diagnosed defects in `gates/claim_scan.py` (root-caused and
reproduced in `docs/issue-476/reports/execution-observation.md`,
Findings 1-2) and a pre-registered pivot rule dictating the fix
direction ("survival > 10% -> widen the trigger condition"). No
category/exemplar research applies to a single-file gate-logic bugfix;
scouting is skipped for that reason.

## Write set found by reading the code

- `gates/claim_scan.py` — the only file with the two defects.
  - `_repo_targets()` (lines ~112-121): sources `repo_targets` from
    `git ls-files` (whole tracked-file set), never `git diff`. Any
    claim citing *any* real tracked file — related or not — passes the
    traceability check. This is case0's bypass shape (pilot: `Repro:
    python3 gates/claim_scan.py --help` cites a real, unrelated file;
    0 findings).
  - `TARGET_RE` (lines ~33-36) extracts dotted `module.function` forms
    (e.g. `mod.f`) from evidence text, but `_repo_targets()` only ever
    yields file-path strings (`mod.py`). An honest repro cited as
    `mod.f()` never matches any file-path target, so it is wrongly
    rejected. This is honest2's false-reject shape (pilot: `Repro:
    python3 -c "import mod; assert mod.f() == 1"`; 2 findings on a
    genuinely-passing repro).
  - `main()` (lines ~124-146): CLI entry, currently takes no `--base`
    argument — no diff-scoping mechanism exists to source case0's fix
    from.
- `gates/test_claim_scan.py` — existing unit test file for exactly this
  module (`gates/claim_scan.py`), net-free, no external repo. This is
  the natural home for the case0/honest2 red-green pairs: the
  regressions are in `_repo_targets()`/`TARGET_RE` matching logic
  inside `claim_scan.py`, not in `gates/reexecution_gate.py` (confirmed
  by the pilot: "Both are in `gates/claim_scan.py`, not
  `gates/reexecution_gate.py` — the re-execution stage itself performed
  correctly on every case that reached it").
- `gates/reexecution_gate.py` / `gates/test_reexecution_gate.py` — read,
  unaffected. The issue body names `gates/test_reexecution_gate.py` as
  the test-pair home, but the pilot record it cites states plainly both
  defects live in `claim_scan.py`'s target-matching logic, and
  `test_reexecution_gate.py`'s existing suite (`gates/
  test_reexecution_gate.py`) only exercises `run_reexecution`/
  `write_verdict`/`read_verdict` against a throwaway repo+SHA, with no
  `claim_scan` import or text-scanning surface to attach a citation-form
  case to. Filing case0/honest2 there would test the wrong module.
  Proposal routes them to `gates/test_claim_scan.py` instead — noted as
  a deliberate deviation from the issue's literal file name, not a
  scope change (still gates/test_*, still the pilot's two shapes,
  still red before the fix / green after).
- No other file references `_repo_targets`, `TARGET_RE`, or
  `claim_scan.scan_text` (`grep -rn "claim_scan\." gates/*.py` besides
  `claim_scan.py`/`test_claim_scan.py` itself returns nothing calling
  into these internals).
- No dependency, env var, or migration surface touched — pure Python
  stdlib (`re`, `subprocess`, `pathlib`) already imported in
  `claim_scan.py`.

## Alternatives considered while reading the code

1. **Fix `_repo_targets()` unconditionally to diff-only** (drop
   `git ls-files` entirely). Rejected: `claim_scan.main()` and
   `scan_text()` are also exercised as a pure text-linter with no base
   ref available (e.g. a bare `python3 gates/claim_scan.py <file>` with
   no `--repo`/no git history, or a first-commit repo with no upstream
   to diff against) — existing tests
   (`t_target_in_repo_clears_when_repo_targets_given`) pass an explicit
   `repo_targets` set directly to `scan_text()`, bypassing
   `_repo_targets()` entirely, so that path is unaffected either way,
   but `main()`'s CLI callers with a repo and no meaningful base would
   regress to 0 targets (spurious findings on every honest claim) if
   `ls-files` were removed outright.
2. **Resolve dotted `module.function` forms by parsing the file for a
   matching `def function` name** (real symbol resolution). Rejected:
   requires reading and parsing every candidate `.py` file's AST or
   text on every scan — real cost and real false-negative surface
   (decorated/nested defs, non-Python targets) for a traceability check
   whose only job is "does the cited *file* exist," not "does the cited
   *symbol* exist." The pilot's honest2 finding is specifically about
   file-path vs. dotted-form mismatch, not symbol existence; resolving
   `mod.f` -> `mod.py` (module-name-to-file mapping) closes exactly that
   gap without the parsing cost.
