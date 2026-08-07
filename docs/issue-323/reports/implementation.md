---
code_under_review: HEAD
loop_state: phase-2-complete
---

# Implementation record — issue #323

Phase 1 proposal: `docs/issue-323/proposals/conflict-methodology.md` (approved: issue #323 comment "APPROVE issue-323/implementation").

## Binding conditional-approval feedback

The comment following the APPROVE token is binding, not merely advisory. It ties this issue to sibling #324's rejected PR #339 (PR #339 was returned because it chose a `spec.md` `write:` glob as source of truth for write-set claims — measured 0 files matching that glob in this repo). The reviewer's ruling: this issue's `files:` frontmatter choice becomes the repo-wide authoritative source, and #324 must consume it rather than build a second parser. Concretely required:

1. Expose the `files:`-frontmatter parser as a reusable unit `scripts/check-write-set-conflicts.sh` other scripts/roles can consume, not private to this script.
2. Measure and record the proportion of on-disk proposals lacking `files:` frontmatter (the `unknown` bucket), rather than silently dropping them.

No conflict with the phase-1 proposal's `## What will be done` — the proposal already named `files:` frontmatter as the claim source; the feedback only tightens *how* the parser must be exposed (reusably) and adds the measurement requirement. Both are satisfied within the frozen write set: `scripts/check-write-set-conflicts.sh` defines its frontmatter-parsing function so it can be sourced (`source scripts/check-write-set-conflicts.sh --source-only`, function definitions only, no side effects) by another script without invoking the full conflict-check `main`, and the measured ratio is recorded below and in the spec.

## Measurement (proposal's `files:` vs `unknown` bucket)

Counted directly against this branch's `docs/issue-*/proposals/*.md` (all issue trees, not just #323/#324):

- Total proposal files: 111
- Carrying `files:` frontmatter: 75 (67.6%)
- Missing `files:` frontmatter (`unknown` bucket): 36 (32.4%)

Recorded in `docs/specs/parallel-conflict-methodology.md` under "Known limitation" so the ratio is visible to whoever next touches the methodology, per the feedback's "measure that ratio and record it" instruction.

## What was done

1. `docs/specs/parallel-conflict-methodology.md` — the adapted conflict methodology: claim source (`files:` frontmatter of an open PR's phase-1 proposal), liveness signal (PR open/closed state), overlap detection (pairwise path intersection across distinct issues' open-PR write sets), conflict definition, resolution recording location, and the cheapest-to-revert-yields resolution rule (applied by whichever session's overlap is detected later).
2. `scripts/check-write-set-conflicts.sh` — reads `files:` frontmatter from every proposal under an issue with a currently-open PR (`gh pr list`), computes pairwise path intersections across distinct issues, and exits non-zero listing overlaps lacking a resolution record. The frontmatter-parsing function (`parse_files_frontmatter`) is defined so the file can be sourced (`source scripts/check-write-set-conflicts.sh --source-only`) to reuse the parser without running the conflict-check `main` — this is the reusable-parser requirement from the binding feedback.
3. `test/check-write-set-conflicts.test.sh` — sources the script, fixtures two proposals with an overlapping path and no resolution record (asserts non-zero exit, offending path in output), and a second fixture pair with a resolution record present (asserts exit 0). Ran directly: `bash test/check-write-set-conflicts.test.sh` → `ALL TESTS PASSED` (both fixtures, after the fix below).
4. `docs/handbooks/operations.md` — one bilingual cross-reference addition (Korean + English, matching the doc's existing style) under the "게이트/Gates" section, pointing at the checker and the spec, noting it is not yet wired into the CI gate.

## What did not work

- Wrote `has_resolution_record`'s grep pattern as an unanchored substring match (`grep -q "issue #${n}\|issue-${n}"`) — expected it to only match an intentional cross-reference to issue `n`; actual: it also matched any record mentioning a *different* issue number that contains `n` as a digit-substring (e.g. issue 3 vs 34, issue 3 vs 323), silently downgrading a real unresolved conflict to "RESOLVED". Caught by the before-landing warrant-hunter (stance 3, reproduced with a concrete grep example). Fixed by anchoring the match with `grep -qE "issue #${n}([^0-9]|\$)|issue-${n}([^0-9]|\$)"`; re-ran the test suite after the fix, still `ALL TESTS PASSED`.

## Warrant hunt

- Dispatched before-landing, stance 3 (rotation index, "assume the rule as written cannot hold — find the state nothing maintains"), diff size ~350 lines / 5 files → 120s cap, one stance.
- Result: **FINDING** — see "What did not work" above. Recorded at `docs/reports/2026-08-07-hunt-issue-323-conflict-methodology.md`.
- resolved_findings: the anchoring finding above — fixed in `scripts/check-write-set-conflicts.sh::has_resolution_record`, test suite re-run green after the fix (code_sha: this record's `code_under_review: HEAD`).

## closed_checks

- check: `test/check-write-set-conflicts.test.sh` (both fixtures: unresolved-overlap non-zero-exit, resolved-overlap zero-exit) — result: PASS — code_sha: HEAD (this record's `code_under_review`).
- check: `bash -n scripts/check-write-set-conflicts.sh` (syntax check) — result: PASS — code_sha: HEAD.

## Reach beyond this issue's own acceptance (per #330)

Per the phase-1 proposal's own "Reach beyond..." section: phase 2 adds a new script, its test, and a spec, but does not wire the checker into any existing gate/hook — nothing already-enforced changes behavior, so no in-flight role session's current behavior is invalidated. The one piece of already-on-disk state this makes load-bearing once a future issue wires it into a gate: the 36 proposals (32.4% of 111) that carry no `files:` frontmatter — those issues' write-set claims are invisible to this checker (`unknown` bucket, not silently treated as "no claim = no conflict possible"). This delivery does not correct those proposals; flagged as a known limitation in the spec, not fixed in scope (mirrors the phase-1 proposal's own stated limitation, now with the measured number attached).

## Doc-placement ladder — completed items

- [x] Library-or-format choice over a named alternative (adopting `files:` frontmatter as the repo-wide write-set-claim format, per the binding feedback, over the `spec.md`/`write:` glob alternative #324's rejected PR #339 tried) → recorded here and in `docs/specs/parallel-conflict-methodology.md`.
- [x] No new env var, config key, dependency, or migration introduced — nothing else to place on the handbook ladder beyond the one `operations.md` cross-reference already in the frozen write set.

## Rationale for deviations

None — phase 2 executed exactly what `## What will be done` in the approved proposal specifies, with the binding feedback satisfied inside the same frozen write set (no new file added, no scope widened). The one deviation from a first draft (the grep-anchoring bug) is recorded above under "What did not work," not here — it was a bug caught and fixed within the same unit of work, not a divergence from the proposal's plan.

## Open findings

None open. The one warrant-hunt finding (grep-anchoring bug) is fixed and closed per `resolved_findings` above.

## Next steps

None required to close this issue's delivery. Out-of-scope items named in the phase-1 proposal remain future work for other issues: wiring this checker into an actual CI/PreToolUse gate, backfilling `files:` frontmatter onto the 36 proposals that lack it, and #324's consumption of `parse_files_frontmatter`/`find_open_issue_proposals` for its own scheduling work.
