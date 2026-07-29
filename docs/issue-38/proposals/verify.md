---
kind: verify-proposal
loop_state: phase-1
code_under_review: 7f30bf0fbee9b606481646297eec7408b14bdf2f
---

# Issue #38 — verify phase-1 proposal

## Attempt list (phase 2, on Approve)

1. **Re-run 4b's repro against `main` HEAD directly** (not qa's working
   copy) to confirm the defect is present in what actually merged and that
   issue #46 accurately tracks it. `closed_checks`: re-derive (different
   sha than qa's record: qa ran at `8bda829`/pre-merge working tree, this
   verify pass runs at `main`@`7f30bf0f`).
2. **Confirm `go_proxy_layer()`/`CARGO_HOME` wiring by reading `main`'s
   `spawn.py` directly** — check the claims in coding.md's
   `resolved_findings` and `closed_checks` against current code, not
   against the PR description. `closed_checks`: re-derive.
3. **Run `test_spawn.py` against `main`'s checked-out files** to confirm no
   regression since qa's 40/42-pass runs. `closed_checks`: re-derive (test
   count may differ from qa's snapshot since other issues have merged since).
4. **Check whether 4d's scope-out is still the correct call** — read
   `_spawn_one()`'s sandbox invocation on `main` to see if anything changed
   that would make a live nested-spawn verification newly feasible or newly
   necessary; if not, cite qa's `BLOCKED` reasoning rather than re-deriving
   a nested spawn attempt (cost/feasibility argument does not change with
   the code content).

No new attempt paths beyond what qa already covered were identified in
survey — the QA record already exercised AC1/AC2 and 5 edge cases including
the two flagged as open (4b, 4d). This verify pass's job is independent
reproduction of 4b and independent confirmation of the coding claims, not
inventing new edge cases where qa's coverage (merge/dedup, empty-dir,
ad-hoc path, real-sandbox feasibility) already looks complete for this
change's surface.
