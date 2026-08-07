# Scout brief — issue #424

**Superseded (2026-08-07)**: this brief scouted external fitness-function tooling (jscpd, ArchUnit)
for a proxy-metric approach (duplication/drift/growth counts) that both operator corrections
withdrew. The current proposal answers a different question — per-instance structural
unreachability, patterned on this repo's own `record-fields-gate`/`closes-gate`/`board-gate` — for
which the operator named the precedent to follow directly, so no re-scout was run (internal
precedent fit, not a field survey). Kept as the phase-1 record of what was tried first, per this
directive's own "append, don't erase" instruction for what did not work.

Mode: 1 sweep stage, 2 web searches run in parallel (batched-sequential fallback not needed —
both fired concurrently in one turn), stopped at judge point 1 (saturation: category is small,
converges fast, no build decision would change with another round).

## Must-bes (category: architecture fitness functions / drift gates)

- Run in CI, on every change, unattended — not a periodic report a human must act on
  (Lukas Niessen; platformtoolsmith). Matches this issue's own scope-item-3 argument for a
  per-change mechanical gate over a sweep.
- Threshold/exit-code contract: tool exits nonzero when the measured metric crosses a line, so CI
  can block the PR (jscpd `--exitCode 1` pattern).
- Scope to what's mechanically checkable; fitness functions verify "does this still honor decision
  X", not "is this good architecture" — matches the issue's own honesty requirement.

## Performance axes the field competes on

1. **Speed at every-commit cadence** — jscpd's Rust rewrite exists specifically because the
   Python/JS original was too slow to run per-commit (24-37x speedup cited). Relevant: any
   accumulation gate here must stay cheap enough to run on every PR, not just nightly.
2. **Signal precision** (false-positive rate) — ArchUnit/Deptrac/go-arch-lint scope themselves to
   layer/dependency rules specifically because unscoped duplicate/pattern detection is noisy.

## Adopt / skip

- **Adopt**: exit-code gate wired into the existing `gates/` CI harness (same shape as
  `duplicate_test_basenames`), not a standalone report nobody reads.
- **Skip**: full jscpd-style AST clone detection — overkill for this repo's actual instances
  (call-shape duplication in one file, signature drift across two call sites), and its false-positive
  surface is exactly the kind of "presence-checked but content never read" trap #310/#363 warn about.
  A narrow, named-pattern gate (per instance in the issue) beats a general clone detector here.

## Segment fit

This repo already has a `gates/` fitness-function harness (`gates/gates.py` + `gates/test_*.py`
mirrors); the field's convention (CI-native, exit-code, narrowly scoped) is a direct fit for
extending that harness, not for adopting an external tool — no new dependency needed for the
reachable subset in issue #424.

## Gap line

Current state already has the CI-native, per-PR, exit-code shape (`gates/` harness itself). What's
missing, matching the field's convention of narrow-scoped checks: an actual check for (a) duplicate
command-invocation shapes, (b) call-site signature drift, (c) constant/list growth over N deliveries.
None exist today (see survey.md).

Sources:
- https://lukasniessen.com/blog/155-fitness-functions-guide/
- https://platformtoolsmith.com/blog/operationalizing-adrs-fitness-functions/
- https://dev.to/vvbogdanov/add-a-50x-faster-duplicate-code-gate-to-github-actions-with-jscpd-rs-kml
- https://www.npmjs.com/package/jscpd
