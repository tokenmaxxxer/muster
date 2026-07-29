---
kind: verify-survey
loop_state: phase-1
code_under_review: 7f30bf0fbee9b606481646297eec7408b14bdf2f
---

# Issue #38 — verify phase-1 survey

## Records read

- `docs/issue-38/reports/coding.md` (phase-2-complete): hybrid design —
  `PACKAGE_REGISTRY_HOSTS` merged into `allowedDomains`, `PACKAGE_CACHE_DIRS`
  probed via `os.path.exists` and mounted read-only into `allowRead`,
  `go_proxy_layer()` layering `file://<host GOMODCACHE>/cache/download` in
  front of `GOPROXY` for `--issue` spawns, `CARGO_HOME` deliberately not used
  as the cargo registry probe (semantic mismatch — `CARGO_HOME` is the parent
  of `registry/`), npm/pip/cargo/Maven explicitly left without GOPROXY-style
  layering (documented limitation, not silently dropped).
- `docs/issue-38/reports/qa.md` (phase-2-complete, PR #41): executed AC1/AC2
  and 5 edge cases against `spawn.py` on `main` at PR #39's merge
  (`8bda829`). PASS on suite/AC1/AC2/4a/4c/4e. **4b**: reproduced a real
  defect — `os.path.exists` at spawn.py:364 accepts a file path, so a
  `PACKAGE_CACHE_DIRS` env var pointing at a file gets mounted into
  `allowRead` and fed into a broken `file://<file>/cache/download` GOPROXY
  source; filed for human triage, since resolved as **issue #46** (open,
  unfixed — correctly out of this PR's frozen write set). **4d**: judged
  infeasible to execute live (would require a nested `claude -p` spawn from
  inside a spawned session) — left `BLOCKED`, not silently dropped.

## Attempts run against `main` (own reproduction, not a restatement)

1. **Re-derive 4b independently.** Built a fresh temp file, set
   `GOMODCACHE` to it, called `spawn.role_settings("coding")` and
   `spawn.go_proxy_layer()` against `main`'s `spawn.py` (checked out clean,
   not the QA session's copy). Reproduced: file path accepted into
   `allowRead`, broken `file://<file>/cache/download,...` GOPROXY string
   produced. Confirms the defect is present in what actually merged, not
   just in QA's working copy — and confirms it is still open (spawn.py:364
   is still `os.path.exists`, matching issue #46's unresolved state).
   **Outcome: not-reproduced-as-new — matches qa's existing #46 filing
   exactly; no new defect.**
2. **Confirm GOPROXY/CARGO_HOME wiring on `main`.** Read `spawn.py` lines
   30-83 and 1580-1600 on `main` directly (not coding's working tree).
   `PACKAGE_CACHE_DIRS` has `(None, "~/.cargo/registry")` as claimed;
   `go_proxy_layer()` is called only inside `if issue is not None:`, matching
   both coding's and qa's description of the ad-hoc-path gap.
   **Outcome: not-reproduced (claims hold as recorded).**
3. **Full test suite against `main`'s working files.** `git checkout main --
   spawn.py test_spawn.py && python3 -m pytest test_spawn.py -q` →
   `42 passed`. **Outcome: not-reproduced (no regression).**
4. **Seam check: sandbox-disabled role path.** All 9 `roles/*.json` files
   have `sandbox.enabled: true` on `main` — the "additive-only,
   `sandbox.enabled`-gated" claim has no role to exercise the disabled
   branch against, so this remains an assertion about code structure
   (`if sb0.get("enabled"):` guards both blocks), not something exercisable
   today. Not a defect — noted as scope, not filed.

## Verdict direction (pending phase-2 write)

No new defect found beyond what qa already surfaced and got triaged as
issue #46. 4b reproduces cleanly and independently against `main` and its
open-issue status is current and correct. 4d's scope-out reasoning
(external sandbox-runtime enforcement, untestable from this harness without
a live nested spawn) holds up on inspection — not a gap this verify session
can close either, for the same reasons qa gave. Leaning **cleared, no
unresolved blocking finding** — 4b is filed and tracked (advisory/tracked,
not blocking this PR's merge since it was correctly scoped out of the
frozen write set), 4d is an honest, bounded unknown, not a defect.
