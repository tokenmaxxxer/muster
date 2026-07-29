---
loop_state: phase1
code_under_review: 36d75c5c5dfe5f91d176ba59cac8bc3de48ccc20
---

# Current-state survey — issue-35 (review)

Scope: audit the merged fix (commit `36d75c5`, PR #47) against issue #35's
text. Survey is from the diff and issue text only — the coding report
(docs/issue-35/reports/coding.md) is intentionally not treated as the
spec; it is read afterward only to identify what closed_checks can be
cited vs re-derived.

## Requirement extraction (from issue #35 text, verbatim)

| # | Requirement | Source clause |
|---|---|---|
| R1 | Strip `MUSTER_ROLE_MODEL` before the truthiness check in `spawn_cmd` | "Fix: strip the value before the truthiness check" |
| R2 | Whitespace-only value behaves like unset (no `--model` flag/value reaches the role session argv) | "so whitespace-only behaves like unset" |
| R3 | Empty-string / unset behavior stays unchanged (already-correct fallback) | "This is inconsistent with the empty-string case, which correctly falls back to the default model" (implies non-regression) |
| R4 | Test added next to the existing `SpawnCmd` cases | "Cover with a test next to the existing SpawnCmd cases" |

Note: the issue text names only `spawn_cmd`. The merged diff also touches
a second site — the `--dry-run` reflection branch in `main()` and its
test helper `_dry_run_output` — which is not named in the issue. That is
additional scope, tracked separately below (not a requirement to verify
against, but relevant to an over-reach check).

## Sampling

Full audit, not sampled: total diff is 4 lines in `spawn.py` + 42 lines in
`test_spawn.py`, well under one session's pace budget. No derivation
needed.

## code_under_review
`36d75c5c5dfe5f91d176ba59cac8bc3de48ccc20` (the fix commit, merged via PR
#47 into `main` at `7f30bf0`).

## closed_checks disposition
`docs/issue-35/reports/coding.md` carries one closed_checks entry
(code_sha: HEAD, i.e. the commit itself) claiming "whitespace-only
MUSTER_ROLE_MODEL no longer reaches --model in spawn_cmd or --dry-run
reflection." Since HEAD at write time resolves to the same commit under
review here, the sha matches — but the claim bundles both the required
(`spawn_cmd`) and the extra (`--dry-run`) site into one check, and covers
behavior (R2) but not non-regression (R3) or test placement (R4). Re-derive
all four requirements independently in the proposal's execution phase
rather than citing this compound entry wholesale.
